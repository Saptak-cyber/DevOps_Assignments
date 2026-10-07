"""Seed the clinic's doctor roster

Revision ID: 0002_seed_doctors
Revises: 0001_clinic_schema
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_seed_doctors"
down_revision = "0001_clinic_schema"
branch_labels = None
depends_on = None

DOCTORS = [
    ("Dr. Ananya Rao", "General Medicine", "G-01"),
    ("Dr. Vikram Mehta", "Paediatrics", "G-04"),
    ("Dr. Farah Siddiqui", "Dermatology", "1-02"),
    ("Dr. Rohan Iyer", "Orthopaedics", "1-05"),
]

doctors = sa.table(
    "doctors",
    sa.column("full_name", sa.String),
    sa.column("specialty", sa.String),
    sa.column("room", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(doctors, [{"full_name": n, "specialty": s, "room": r} for n, s, r in DOCTORS])


def downgrade() -> None:
    # Bound parameters, not string-built SQL (Bandit B608).
    op.execute(doctors.delete().where(doctors.c.full_name.in_([n for n, _, _ in DOCTORS])))
