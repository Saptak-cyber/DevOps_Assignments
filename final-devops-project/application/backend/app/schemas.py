from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AppointmentStatus = Literal["SCHEDULED", "CHECKED_IN", "COMPLETED", "CANCELLED", "NO_SHOW"]
ACTIVE_STATUSES = ("SCHEDULED", "CHECKED_IN", "COMPLETED", "NO_SHOW")

PHONE_PATTERN = r"^\+?[0-9][0-9 \-]{6,18}$"


def _to_clinic_wall_clock(value: datetime) -> datetime:
    """Store appointment times as naive wall-clock values.

    Naive input is taken as clinic local time. Offset-aware input is normalised to
    UTC first so the same instant never produces two different rows.
    """
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(second=0, microsecond=0)


# ---------- doctors ----------
class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    room: str = Field(default="", max_length=20)
    active: bool = True


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    specialty: str
    room: str
    active: bool


class DoctorBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    specialty: str
    room: str


# ---------- patients ----------
class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(pattern=PHONE_PATTERN)
    email: str | None = Field(default=None, max_length=160)


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: str
    email: str | None
    created_at: datetime


class PatientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: str


# ---------- appointments ----------
class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int | None = None
    patient: PatientCreate | None = Field(
        default=None, description="Register a walk-in patient inline instead of passing patient_id"
    )
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=120)
    reason: str = Field(default="", max_length=200)
    notes: str = ""

    @field_validator("scheduled_at")
    @classmethod
    def normalise(cls, value: datetime) -> datetime:
        return _to_clinic_wall_clock(value)

    @model_validator(mode="after")
    def exactly_one_patient(self):
        if (self.patient_id is None) == (self.patient is None):
            raise ValueError("Provide either patient_id or patient, not both")
        return self


class AppointmentUpdate(BaseModel):
    doctor_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=120)
    reason: str | None = Field(default=None, max_length=200)
    status: AppointmentStatus | None = None
    notes: str | None = None

    @field_validator("scheduled_at")
    @classmethod
    def normalise(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _to_clinic_wall_clock(value)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    scheduled_at: datetime
    ends_at: datetime
    duration_minutes: int
    reason: str
    status: AppointmentStatus
    notes: str
    doctor: DoctorBrief
    patient: PatientBrief
    created_at: datetime
    updated_at: datetime


# ---------- stats ----------
class DoctorLoad(BaseModel):
    doctor_id: int
    full_name: str
    specialty: str
    booked: int
    booked_minutes: int


class StatsOut(BaseModel):
    date: date
    total: int
    scheduled: int
    checked_in: int
    completed: int
    cancelled: int
    no_show: int
    upcoming_7_days: int
    active_doctors: int
    patients: int
    by_doctor: list[DoctorLoad]
