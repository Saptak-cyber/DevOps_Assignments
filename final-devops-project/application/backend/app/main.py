import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import appointments, doctors, patients

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("clinicdesk")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Front-desk API for booking and tracking clinic appointments.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# /metrics: request count, latency histogram and in-progress gauge per handler.
Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/metrics", "/health", "/ready"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    """Liveness: the process is up and serving HTTP. Deliberately does not touch the DB."""
    return {"status": "UP"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    """Readiness: only send traffic here if the database answers and migrations have run."""
    try:
        db.execute(text("SELECT 1 FROM doctors LIMIT 1"))
    except SQLAlchemyError as exc:
        log.warning("readiness check failed: %s", exc.__class__.__name__)
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "database": "unreachable"})
    return {"status": "READY", "database": "ok"}
