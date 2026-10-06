# Session 17 DevSecOps dashboard (instructor's demo app) — hardened image.
# Changes vs. the class Dockerfile: pinned deps, gunicorn instead of the Flask
# dev server, no pip cache, non-root user, OCI labels, healthcheck.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001

EXPOSE 5001
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5001/health')" || exit 1

# --no-control-socket: gunicorn 26 otherwise tries to create ~/.gunicorn/gunicorn.ctl,
# which fails on the read-only root filesystem used in Kubernetes.
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--no-control-socket", "--access-logfile", "-", "app.app:app"]
