# ---------- Stage 1: build the dependency tree ----------
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./

# Install into a self-contained prefix that can be copied wholesale into the
# runtime stage. If a package needed gcc to compile a C extension, the compiler
# would live here and never reach the final image.
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

# Copy the installed packages out of the builder stage.
COPY --from=builder /install /usr/local

COPY app.py ./

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 5000

# Gunicorn, not app.run(). Flask's dev server is single-threaded, has no
# graceful restart, and prints a warning telling you not to use it in production.
#   -w 2        two worker processes
#   -b 0.0.0.0  bind on all interfaces inside the container
#   app:app     module "app", WSGI callable "app"
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]
