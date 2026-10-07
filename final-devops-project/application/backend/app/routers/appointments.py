from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Appointment, Doctor, Patient
from ..schemas import (
    ACTIVE_STATUSES,
    AppointmentCreate,
    AppointmentOut,
    AppointmentStatus,
    AppointmentUpdate,
    DoctorLoad,
    StatsOut,
)
from .patients import register_patient

router = APIRouter(prefix="/api", tags=["appointments"])

MAX_DURATION = timedelta(minutes=120)


def clinic_today() -> date:
    return datetime.now(ZoneInfo(settings.clinic_timezone)).date()


def _get_appointment(db: Session, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Appointment {appointment_id} not found")
    return appt


def _get_bookable_doctor(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Doctor {doctor_id} not found")
    if not doctor.active:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"{doctor.full_name} is not taking bookings")
    return doctor


def _ensure_slot_free(
    db: Session, doctor: Doctor, start: datetime, minutes: int, ignore_id: int | None = None
) -> None:
    """Reject the booking if it overlaps another non-cancelled appointment for the doctor."""
    end = start + timedelta(minutes=minutes)
    stmt = select(Appointment).where(
        Appointment.doctor_id == doctor.id,
        Appointment.status != "CANCELLED",
        Appointment.scheduled_at < end,
        Appointment.scheduled_at > start - MAX_DURATION,
    )
    if ignore_id is not None:
        stmt = stmt.where(Appointment.id != ignore_id)
    for other in db.scalars(stmt).unique():
        if other.scheduled_at < end and other.ends_at > start:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"{doctor.full_name} already has an appointment from "
                f"{other.scheduled_at:%H:%M} to {other.ends_at:%H:%M} on {other.scheduled_at:%d %b}",
            )


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    on: date | None = Query(None, description="Only appointments on this clinic date (YYYY-MM-DD)"),
    doctor_id: int | None = None,
    status_: AppointmentStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(Appointment).order_by(Appointment.scheduled_at, Appointment.id)
    if on is not None:
        day_start = datetime.combine(on, time.min)
        stmt = stmt.where(Appointment.scheduled_at >= day_start, Appointment.scheduled_at < day_start + timedelta(days=1))
    if doctor_id is not None:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if status_ is not None:
        stmt = stmt.where(Appointment.status == status_)
    return db.scalars(stmt).unique().all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return _get_appointment(db, appointment_id)


@router.post("/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    doctor = _get_bookable_doctor(db, payload.doctor_id)
    if payload.patient_id is not None:
        patient = db.get(Patient, payload.patient_id)
        if patient is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Patient {payload.patient_id} not found")
    else:
        patient = register_patient(db, payload.patient)

    _ensure_slot_free(db, doctor, payload.scheduled_at, payload.duration_minutes)
    appt = Appointment(
        doctor=doctor,
        patient=patient,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.put("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appt = _get_appointment(db, appointment_id)
    if appt.status == "CANCELLED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Cancelled appointments can't be changed; book a new one")

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    doctor = appt.doctor
    if "doctor_id" in changes and changes["doctor_id"] != appt.doctor_id:
        doctor = _get_bookable_doctor(db, changes["doctor_id"])

    moved = {"doctor_id", "scheduled_at", "duration_minutes"} & changes.keys()
    if moved and changes.get("status", appt.status) != "CANCELLED":
        _ensure_slot_free(
            db,
            doctor,
            changes.get("scheduled_at", appt.scheduled_at),
            changes.get("duration_minutes", appt.duration_minutes),
            ignore_id=appt.id,
        )

    changes.pop("doctor_id", None)
    appt.doctor = doctor
    for key, value in changes.items():
        setattr(appt, key, value)
    db.commit()
    db.refresh(appt)
    return appt


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = _get_appointment(db, appointment_id)
    if appt.status in ("CANCELLED", "COMPLETED"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Appointment is already {appt.status.lower()}")
    appt.status = "CANCELLED"
    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = _get_appointment(db, appointment_id)
    db.delete(appt)
    db.commit()


@router.get("/stats", response_model=StatsOut, tags=["stats"])
def stats(
    on: date | None = Query(None, description="Clinic date to summarise; defaults to today"),
    db: Session = Depends(get_db),
):
    day = on or clinic_today()
    start = datetime.combine(day, time.min)
    end = start + timedelta(days=1)

    counts = dict(
        db.execute(
            select(Appointment.status, func.count(Appointment.id))
            .where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
            .group_by(Appointment.status)
        ).all()
    )

    upcoming = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < start + timedelta(days=7),
            Appointment.status.in_(("SCHEDULED", "CHECKED_IN")),
        )
    )

    load_rows = db.execute(
        select(
            Doctor.id,
            Doctor.full_name,
            Doctor.specialty,
            func.count(Appointment.id),
            func.coalesce(func.sum(Appointment.duration_minutes), 0),
        )
        .outerjoin(
            Appointment,
            (Appointment.doctor_id == Doctor.id)
            & (Appointment.scheduled_at >= start)
            & (Appointment.scheduled_at < end)
            & (Appointment.status.in_(ACTIVE_STATUSES)),
        )
        .where(Doctor.active.is_(True))
        .group_by(Doctor.id, Doctor.full_name, Doctor.specialty)
        .order_by(Doctor.full_name)
    ).all()

    return StatsOut(
        date=day,
        total=sum(counts.values()),
        scheduled=counts.get("SCHEDULED", 0),
        checked_in=counts.get("CHECKED_IN", 0),
        completed=counts.get("COMPLETED", 0),
        cancelled=counts.get("CANCELLED", 0),
        no_show=counts.get("NO_SHOW", 0),
        upcoming_7_days=upcoming or 0,
        active_doctors=len(load_rows),
        patients=db.scalar(select(func.count(Patient.id))) or 0,
        by_doctor=[
            DoctorLoad(doctor_id=i, full_name=n, specialty=s, booked=c, booked_minutes=int(m))
            for i, n, s, c, m in load_rows
        ],
    )
