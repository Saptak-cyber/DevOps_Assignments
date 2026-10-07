# syntax=docker/dockerfile:1
# ---------- stage 1: build a self-contained virtualenv ----------
FROM python:3.14-alpine AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt \
 && pip uninstall -y pip

# ---------- stage 2: small Alpine runtime, non-root ----------
# Alpine instead of Debian slim: the slim base carried 44 unfixed HIGH CVEs
# (util-linux, ncurses, systemd libs) that this app never uses.
FROM python:3.14-alpine AS runtime
LABEL org.opencontainers.image.title="clinicdesk-backend" \
      org.opencontainers.image.description="ClinicDesk FastAPI backend" \
      org.opencontainers.image.source="https://github.com/Saptak-cyber/DevOps_Assignments"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    RUN_MIGRATIONS=true
# pip/setuptools are not needed at runtime; removing them also removes their CVE surface.
RUN pip uninstall -y pip setuptools wheel 2>/dev/null; \
    addgroup -g 10001 -S app && \
    adduser -u 10001 -G app -S -D -H -s /sbin/nologin app
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=root:root alembic.ini docker-entrypoint.sh ./
COPY --chown=root:root alembic ./alembic
COPY --chown=root:root app ./app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
