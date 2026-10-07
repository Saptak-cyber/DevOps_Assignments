"""Test fixtures.

Tests never touch PostgreSQL: each test gets a brand-new in-memory SQLite database,
wired into the app through FastAPI's dependency override for ``get_db``.
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"  # set before the app imports its settings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Doctor

SEED_DOCTORS = [
    # (name, specialty, room, active)
    ("Dr. Test Physician", "General Medicine", "T-1", True),
    ("Dr. Test Paediatrician", "Paediatrics", "T-2", True),
    ("Dr. On Leave", "Dermatology", "T-3", False),
]


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestingSession() as session:
        session.add_all(
            [Doctor(full_name=n, specialty=s, room=r, active=a) for n, s, r, a in SEED_DOCTORS]
        )
        session.commit()
    yield TestingSession
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def doctor_id(client):
    return client.get("/api/doctors").json()[0]["id"]


@pytest.fixture()
def book(client, doctor_id):
    """Helper that books an appointment and returns the response."""

    def _book(when="2026-10-08T10:00", minutes=30, doctor=None, phone="+91 98765 43210", name="Priya Nair"):
        return client.post(
            "/api/appointments",
            json={
                "doctor_id": doctor or doctor_id,
                "patient": {"full_name": name, "phone": phone},
                "scheduled_at": when,
                "duration_minutes": minutes,
                "reason": "Follow-up",
            },
        )

    return _book
