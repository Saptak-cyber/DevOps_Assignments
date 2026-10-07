"""Create doctors, patients and appointments tables

Revision ID: 0001_clinic_schema
Revises:
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_clinic_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("specialty", sa.String(80), nullable=False),
        sa.Column("room", sa.String(20), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("email", sa.String(160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("reason", sa.String(200), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="SCHEDULED"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('SCHEDULED','CHECKED_IN','COMPLETED','CANCELLED','NO_SHOW')", name="ck_appointments_status"
        ),
        sa.CheckConstraint("duration_minutes BETWEEN 10 AND 120", name="ck_appointments_duration"),
    )
    op.create_index("ix_appointments_doctor_time", "appointments", ["doctor_id", "scheduled_at"])
    op.create_index("ix_appointments_status", "appointments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_doctor_time", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("patients")
    op.drop_table("doctors")
