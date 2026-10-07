from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Patient
from ..schemas import PatientCreate, PatientOut

router = APIRouter(prefix="/api/patients", tags=["patients"])


def register_patient(db: Session, payload: PatientCreate) -> Patient:
    """Create a patient, or return the existing record for the same phone number."""
    existing = db.scalar(select(Patient).where(Patient.phone == payload.phone))
    if existing is not None:
        return existing
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.flush()
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(
    q: str | None = Query(None, max_length=60, description="Filter by name or phone"),
    db: Session = Depends(get_db),
):
    stmt = select(Patient).order_by(Patient.full_name).limit(200)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Patient.full_name.ilike(like), Patient.phone.like(like)))
    return db.scalars(stmt).all()


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Patient.id).where(Patient.phone == payload.phone)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"A patient with phone {payload.phone} already exists")
    patient = register_patient(db, payload)
    db.commit()
    db.refresh(patient)
    return patient
