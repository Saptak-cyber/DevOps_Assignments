from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Doctor
from ..schemas import DoctorCreate, DoctorOut

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorOut])
def list_doctors(
    include_inactive: bool = Query(False, description="Also return doctors who are not taking bookings"),
    db: Session = Depends(get_db),
):
    stmt = select(Doctor).order_by(Doctor.full_name)
    if not include_inactive:
        stmt = stmt.where(Doctor.active.is_(True))
    return db.scalars(stmt).all()


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Doctor {doctor_id} not found")
    return doctor


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor
