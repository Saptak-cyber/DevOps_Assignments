# ClinicDesk — Final DevOps Project

**Author:** Saptak Banerjee
**Course:** SST DevOps & Cloud [SWE]
**Session:** 21 — Final DevOps Project & Troubleshooting
**Source material:** [`devops-heros/session21-python`](https://github.com/Nency-Ravaliya/devops-heros/tree/main/session21-python) (TaskBoard reference: architecture only, the application is my own)

**Environment:** macOS (Apple silicon), Docker Desktop 29.6, Python 3.14, Node 25, Helm 4.3, kubeconform 0.8, Terraform 1.16 with AWS provider 6.67 against a real AWS account in `ap-south-1`. Every output block below is a real capture; account IDs are masked as `<account-id>`.

> **Progress:** the application, Docker, local security scans, Kubernetes manifests, Helm chart and the Terraform plan are done (sections 1–8, 10, 11 partly). Sections marked _Phase 2 — pending_ are filled in once CI, the cluster deployment, monitoring, GitOps and the troubleshooting challenge have been run.

---

## Table of Contents

| # | Section | Status |
| --- | --- | --- |
| 1 | [Project overview](#1-project-overview) | done |
| 2 | [Architecture diagram](#2-architecture-diagram) | done |
| 3 | [Technologies used](#3-technologies-used) | done |
| 4 | [Application setup](#4-application-setup) | done |
| 5 | [Docker setup](#5-docker-setup) | done |
| 6 | [Kubernetes deployment](#6-kubernetes-deployment) | manifests written and validated; cluster run pending |
| 7 | [Helm deployment](#7-helm-deployment) | chart written, linted, rendered; install pending |
| 8 | [Terraform infrastructure](#8-terraform-infrastructure) | init / validate / plan done; apply + destroy pending |
| 9 | [CI/CD pipeline](#9-cicd-pipeline) | pending |
| 10 | [DevSecOps implementation](#10-devsecops-implementation) | local scans done; CI gates pending |
| 11 | [Monitoring](#11-monitoring) | `/metrics` done; Prometheus + Grafana pending |
| 12 | [GitOps](#12-gitops) | pending |
| 13 | [Troubleshooting](#13-troubleshooting) | pending |
| 14 | [Screenshots](#14-screenshots) | in progress |
| 15 | [Lessons learned](#15-lessons-learned) | in progress |
| | [Cleanup](#cleanup) | |

---

## 1. Project overview

**ClinicDesk** is the front-desk system for a small multi-specialty clinic. A receptionist sees the whole day on one board, one column per doctor, and can book, check in, reschedule and cancel patients from it.

What it does:

- **Day board** — every doctor's appointments laid out on a time grid; colour shows the visit state (expected, waiting, seen, did not arrive, cancelled). Clicking a free space in a doctor's column opens the booking form for that slot.
- **Booking** — book a new walk-in patient (name + phone) or a returning patient (search by name/phone). The API refuses to double-book a doctor and says exactly which slot clashes.
- **Visit flow** — check in, mark as seen, mark did-not-arrive, undo, add front-desk notes, reschedule, cancel (cancelling frees the slot; a cancelled record is locked).
- **Daily stats** — totals per state, per-doctor load (count and minutes booked), visits booked over the next 7 days.

### REST API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness: process is up (never touches the DB) |
| GET | `/ready` | Readiness: DB reachable and migrated, else `503` |
| GET | `/metrics` | Prometheus metrics (request count, latency histogram) |
| GET | `/docs` | Swagger UI |
| GET / POST | `/api/doctors` | List active doctors / add a doctor |
| GET | `/api/doctors/{id}` | One doctor |
| GET / POST | `/api/patients` | Search patients (`?q=`) / register a patient (phone is unique) |
| GET | `/api/appointments` | List, filter by `on=YYYY-MM-DD`, `doctor_id`, `status` |
| POST | `/api/appointments` | Book (with `patient_id` or an inline new `patient`) — `409` on a clash |
| GET / PUT / DELETE | `/api/appointments/{id}` | Read / reschedule, change status, notes / delete |
| POST | `/api/appointments/{id}/cancel` | Cancel and free the slot |
| GET | `/api/stats?on=` | Day summary and per-doctor load |

### What is different from the TaskBoard reference

GRADING.md requires the application domain to be your own. ClinicDesk shares only the DevOps shape (FastAPI + PostgreSQL + React behind nginx, Helm, Terraform, EKS). The app itself is new: three related tables instead of one, booking rules (overlap detection, inactive doctors, cancel locking), a timezone-aware stats endpoint, and a time-grid UI instead of a task table. The platform layer also goes further than the reference: Alpine runtime images with zero HIGH/CRITICAL CVEs, read-only root filesystems, a `restricted` Pod Security namespace, a startup/readiness/liveness probe split, migrations serialised with a PostgreSQL advisory lock, Secret-based DB credentials, a StatefulSet + PVC for PostgreSQL, and EBS CSI + metrics-server add-ons in Terraform so the PVC and HPA actually work on EKS.

### Repository layout

```text
final-devops-project/
├── application/
│   ├── backend/              FastAPI app, Alembic migrations, pytest suite, Dockerfile
│   │   ├── app/              config, db, models, schemas, routers/{doctors,patients,appointments}.py
│   │   ├── alembic/versions/ 0001_clinic_schema.py, 0002_seed_doctors.py
│   │   ├── tests/            conftest.py + 23 tests (SQLite in memory)
│   │   ├── Dockerfile        multi-stage, python:3.14-alpine, uid 10001
│   │   └── docker-entrypoint.sh  migrate (with retries), then exec uvicorn
│   ├── frontend/             React 19 + Vite 8 app, nginx template, Dockerfile (node build -> nginx-unprivileged)
│   └── scripts/seed-demo.sh  books a realistic demo day through the public API
├── docker/                   docker-compose.yml (+ .env.example)
├── kubernetes/               namespace, ConfigMap, Secret template, Postgres StatefulSet+PVC, Deployments, Services, Ingress, HPA, kustomization
├── helm/clinicdesk/          chart with values.yaml, values-dev.yaml, values-prod.yaml
├── terraform/                VPC + EKS (+ EBS CSI pod identity), outputs, tfvars example
├── security/  monitoring/  gitops/  .github/workflows/   (Phase 2)
├── screenshots/
└── README.md
```

---

## 2. Architecture diagram

```mermaid
flowchart LR
  dev([Developer]) -->|git push| gh[(GitHub repo)]
  gh --> ci[GitHub Actions<br/>pytest + vite build<br/>SAST / SCA / secrets<br/>docker build + Trivy]
  ci -->|push :sha| ghcr[(GHCR images)]
  ci -->|bump image tag| gitops[(gitops/ values)]
  gitops --> argo[Argo CD]
  tf[Terraform] -->|VPC + EKS| eks
  subgraph eks [Kubernetes cluster: minikube locally / EKS on AWS]
    direction LR
    ing[Ingress nginx<br/>clinicdesk.local] -->|/| fe[frontend x2<br/>nginx :8080]
    ing -->|/api| be[backend x2..6<br/>FastAPI :8000]
    fe -->|/api proxy| be
    be --> pg[(PostgreSQL<br/>StatefulSet + PVC)]
    hpa[HPA] -.scales.-> be
    prom[Prometheus] -.scrapes /metrics.-> be
    graf[Grafana] --> prom
  end
  argo -->|helm sync| eks
  ghcr -.pull.-> eks
  user([Receptionist browser]) --> ing
```

Request path: the browser only ever talks to one origin. In Docker Compose, nginx in the frontend container proxies `/api/*` to `backend:8000`; in Kubernetes the Ingress sends `/api` straight to the backend Service and everything else to the frontend Service. The backend reads non-secret settings from a ConfigMap and DB credentials from a Secret, and runs `alembic upgrade head` on start-up before serving.

---

## 3. Technologies used

| Layer | Technology | Version (pinned) |
| --- | --- | --- |
| Frontend | React, Vite, `@vitejs/plugin-react`, Atkinson Hyperlegible Next (self-hosted font) | 19.3.0, 8.3.3, 6.1.2, 5.3.0 |
| Frontend runtime | `nginxinc/nginx-unprivileged` (non-root, port 8080) | 1.30-alpine-slim (nginx 1.30.5) |
| Backend | FastAPI, Uvicorn, Pydantic, pydantic-settings | 0.142.2, 0.54.0, 2.13.5, 2.15.0 |
| Data | SQLAlchemy, Alembic, psycopg 3, PostgreSQL | 2.1.3, 1.20.0, 3.3.6, 18 (alpine) |
| Metrics | prometheus-fastapi-instrumentator | 8.1.0 |
| Tests | pytest, httpx2 (Starlette TestClient transport) | 9.1.1, 2.13.1 |
| Containers | Docker, Docker Compose, BuildKit multi-stage | Docker 29.6.1 |
| Orchestration | Kubernetes manifests + Kustomize, Helm 3/4 chart (`apiVersion: v2`) | Helm 4.3.0 |
| IaC | Terraform, `terraform-aws-modules/vpc`, `/eks`, `/eks-pod-identity`, AWS provider | 1.16.4, 6.7.3, 21.26.0, 2.9.0, 6.67.0 |
| Cloud | AWS VPC, NAT gateway, EKS 1.36 (AL2023 nodes, t3.medium), EBS CSI, metrics-server | `ap-south-1` |
| Security | Trivy, pip-audit, npm audit, kubeconform, gitleaks | 0.75.0, 2.10.1, npm 11.8, 0.8.0, 8.30.1 |
| CI/CD, GitOps, monitoring | GitHub Actions, GHCR, Argo CD, kube-prometheus-stack | Phase 2 |

---

## 4. Application setup

### 4.1 Backend: run the tests

The suite has 23 tests over 4 files and covers every endpoint group (meta, doctors, patients, appointments, stats). `tests/conftest.py` gives each test a fresh **in-memory SQLite** database through FastAPI's `dependency_overrides`, so tests never touch PostgreSQL. `pytest.ini` sets `pythonpath`, `testpaths`, strict markers, and turns any `DeprecationWarning` raised from `app.*` into an error.

```bash
cd application/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```

```
$ python --version
Python 3.14.3

$ pytest -v --color=no -p no:cacheprovider
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0 -- <venv>/bin/python3.14
rootdir: /Users/saptakbanerjee/myDocuments/3rd_Year/DevOps/DevOps_Assignments/final-devops-project/application/backend
configfile: pytest.ini
testpaths: tests
plugins: platformdirs-4.12.3, anyio-4.15.1
collecting ... collected 23 items

tests/test_appointments.py::test_book_appointment_registers_walk_in_patient PASSED [  4%]
tests/test_appointments.py::test_book_with_existing_patient_id PASSED    [  8%]
tests/test_appointments.py::test_booking_requires_exactly_one_patient_reference PASSED [ 13%]
tests/test_appointments.py::test_unknown_or_inactive_doctor_cannot_be_booked PASSED [ 17%]
tests/test_appointments.py::test_double_booking_same_doctor_is_rejected PASSED [ 21%]
tests/test_appointments.py::test_back_to_back_slots_are_allowed PASSED   [ 26%]
tests/test_appointments.py::test_update_status_and_reschedule PASSED     [ 30%]
tests/test_appointments.py::test_reschedule_into_taken_slot_is_rejected PASSED [ 34%]
tests/test_appointments.py::test_cancel_frees_the_slot_and_locks_the_record PASSED [ 39%]
tests/test_appointments.py::test_list_filters_by_date_and_status PASSED  [ 43%]
tests/test_appointments.py::test_delete_appointment PASSED               [ 47%]
tests/test_appointments.py::test_duration_bounds_are_enforced PASSED     [ 52%]
tests/test_doctors_patients.py::test_list_doctors_hides_inactive_by_default PASSED [ 56%]
tests/test_doctors_patients.py::test_create_and_fetch_doctor PASSED      [ 60%]
tests/test_doctors_patients.py::test_create_patient_and_reject_duplicate_phone PASSED [ 65%]
tests/test_doctors_patients.py::test_patient_phone_is_validated PASSED   [ 69%]
tests/test_meta.py::test_root_describes_service PASSED                   [ 73%]
tests/test_meta.py::test_health_is_up PASSED                             [ 78%]
tests/test_meta.py::test_ready_checks_database PASSED                    [ 82%]
tests/test_meta.py::test_metrics_exposes_prometheus_format PASSED        [ 86%]
tests/test_meta.py::test_openapi_lists_core_routes PASSED                [ 91%]
tests/test_stats.py::test_stats_summarise_one_day PASSED                 [ 95%]
tests/test_stats.py::test_stats_default_to_today PASSED                  [100%]
```

What the tests pin down, beyond happy-path CRUD: overlapping bookings for the same doctor return `409` while back-to-back slots are fine; rescheduling into a taken slot is refused; cancelling frees the slot and locks the record; inactive doctors cannot be booked; durations outside 10–120 minutes and bad phone numbers are `422`; `/ready` really queries the DB; `/metrics` emits `http_requests_total` per handler; the stats endpoint does not count a cancelled visit as doctor load.

**Screenshot:** ![pytest -v, 23 passed](./screenshots/01-pytest-pass.png)

### 4.2 Backend: run against PostgreSQL directly

```bash
export DATABASE_URL='postgresql+psycopg://clinicdesk:<password>@localhost:5432/clinicdesk'
alembic upgrade head          # 0001 creates the 3 tables, 0002 seeds the doctor roster
uvicorn app.main:app --reload --port 8000     # Swagger: http://localhost:8000/docs
```

Instead of one `DATABASE_URL`, the container images take `DB_HOST`, `DB_PORT`, `DB_NAME` (ConfigMap) and `DB_USER`, `DB_PASSWORD` (Secret) and build the URL themselves (`app/config.py`), so the password never has to live inside a connection string in a ConfigMap.

Design decisions worth knowing:

- **Appointment times are clinic wall-clock values** (`2026-10-07T16:00`, no offset), which is how a front desk thinks; offset-aware input is normalised to UTC first. "Today" for `/api/stats` is computed in `CLINIC_TIMEZONE` (default `Asia/Kolkata`), so a pod running in UTC still rolls over at local midnight.
- **Migrations on start-up are safe with many replicas**: `alembic/env.py` takes `pg_advisory_xact_lock` before migrating, so two backend pods starting together cannot race on DDL. The entrypoint retries for up to 60 s while PostgreSQL comes up.
- **Liveness vs readiness**: `/health` is a pure process check; `/ready` runs `SELECT 1 FROM doctors` and returns `503` on failure, so a DB outage pulls pods out of the Service instead of restarting them in a loop.

### 4.3 Frontend: install and build

```
$ node --version
v25.6.0

$ npm ci --no-audit --no-fund

added 21 packages in 561ms

$ npm run build

> clinicdesk-frontend@1.0.0 build
> vite build

vite v8.3.3 building client environment for production...
transforming...
✓ 23 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                                                0.60 kB │ gzip:  0.35 kB
dist/assets/atkinson-hyperlegible-next-latin-ext-wght-normal-C6vrW8VD.woff2   19.09 kB
dist/assets/atkinson-hyperlegible-next-latin-wght-normal-BcXVPD7q.woff2       33.99 kB
dist/assets/index-DPXIatko.css                                                11.41 kB │ gzip:  3.44 kB
dist/assets/index-BQfMdHMb.js                                                236.86 kB │ gzip: 74.12 kB
```

Dependencies are pinned exactly and installed from `package-lock.json` with `npm ci`. The bundle has no third-party runtime requests (the font is bundled), which is what lets nginx send a strict `Content-Security-Policy`. In development `npm run dev` proxies `/api` to `localhost:8000` (see `vite.config.js`).

### 4.4 The running app

The board for 7 October after seeding a demo day (section 5.4), with a few visits moved through check-in, seen and did-not-arrive. The selected appointment's details and actions are on the right:

![ClinicDesk day board](./screenshots/03-app-dashboard.png)

Booking a slot that clashes: the form shows the API's `409` message verbatim, naming the clashing slot. Changing the start to 13:00 then booked it successfully.

![Booking conflict message](./screenshots/04-app-booking-conflict.png)

Phone width (390 px): the header wraps, the board scrolls sideways inside its own frame and the page itself never scrolls horizontally. Swagger UI is served by the backend at `/docs`.

| Mobile | Swagger UI |
| --- | --- |
| ![Mobile layout](./screenshots/05-app-mobile.png) | ![Swagger UI](./screenshots/06-swagger-docs.png) |

---

## 5. Docker setup

### 5.1 Images

| Image | Dockerfile | Base images | User | Size |
| --- | --- | --- | --- | --- |
| `clinicdesk-backend` | [`application/backend/Dockerfile`](./application/backend/Dockerfile) | `python:3.14-alpine` (build: venv + wheels, runtime: venv copied in, pip removed) | `10001:10001` | 212 MB |
| `clinicdesk-frontend` | [`application/frontend/Dockerfile`](./application/frontend/Dockerfile) | `node:24-alpine` build stage, `nginxinc/nginx-unprivileged:1.30-alpine-slim` runtime | `101` (nginx) | 30.5 MB |

Notes:

- Backend: two stages so compilers/pip caches never reach the runtime image; `pip`, `setuptools` and `wheel` are uninstalled from the runtime; app files are owned by root and the process runs as uid 10001, so the app cannot modify its own code. A `HEALTHCHECK` hits `/health` with the Python stdlib (no curl in the image).
- Frontend: Node only exists in the build stage. The runtime is the official *unprivileged* nginx (listens on 8080, no root). The nginx config is a template rendered at start by the image's `envsubst` hook, so the same image proxies to `backend:8000` in Compose and to `clinicdesk-backend:8000` in Kubernetes via `BACKEND_UPSTREAM`. It adds `nosniff`, `X-Frame-Options: DENY` and a CSP, caches hashed `/assets/` for a year and exposes `/healthz` for probes.
- [`docker/docker-compose.yml`](./docker/docker-compose.yml) builds both images from `../application/...`, waits on health checks (`postgres` healthy → `backend` healthy → `frontend`), does not publish PostgreSQL to the host, sets memory limits (256/256/64 MB, Docker shares 8 GB with minikube), and runs the backend with `read_only: true`, `cap_drop: [ALL]` and `no-new-privileges`. The DB password defaults to a local-only value and can be overridden from `docker/.env` (see `.env.example`).

### 5.2 `docker compose up --build`

```bash
cd docker
docker compose up --build -d
```

```
$ docker compose up --build -d
...
#12 [frontend runtime 1/3] FROM docker.io/nginxinc/nginx-unprivileged:1.30-alpine-slim@sha256:3af0c10d960cc2502427fe1219c52989d309e7d65596869c60a34fd2fa2406f0
#14 [frontend build 1/8] FROM docker.io/library/node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1
#15 [backend build 1/4] FROM docker.io/library/python:3.14-alpine@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72
#16 [backend runtime 3/7] WORKDIR /app
#17 [backend runtime 6/7] COPY --chown=root:root alembic ./alembic
#18 [backend build 2/4] RUN python -m venv /opt/venv
#19 [backend runtime 5/7] COPY --chown=root:root alembic.ini docker-entrypoint.sh ./
#20 [backend runtime 2/7] RUN pip uninstall -y pip setuptools wheel 2>/dev/null;     addgroup -g 10001 -S app &&     adduser -u 10001 -G app -S -D -H -s /sbin/nologin app
#21 [backend build 3/4] COPY requirements.txt .
#22 [backend runtime 4/7] COPY --from=build /opt/venv /opt/venv
#23 [backend build 4/4] RUN pip install --upgrade pip && pip install -r requirements.txt  && pip uninstall -y pip
#24 [backend runtime 7/7] COPY --chown=root:root app ./app
#25 [frontend build 8/8] RUN npm run build
#26 [frontend runtime 2/3] COPY --chown=root:root nginx/default.conf.template /etc/nginx/templates/default.conf.template
#27 [frontend build 4/8] RUN npm ci --no-audit --no-fund
#28 [frontend build 3/8] COPY package.json package-lock.json ./
#29 [frontend build 5/8] COPY index.html vite.config.js ./
#30 [frontend build 2/8] WORKDIR /app
#31 [frontend build 6/8] COPY public ./public
#32 [frontend build 7/8] COPY src ./src
#33 [frontend runtime 3/3] COPY --chown=root:root --from=build /app/dist /usr/share/nginx/html
...
 Image clinicdesk-backend:local Built 
 Image clinicdesk-frontend:local Built 
 Network clinicdesk_default Creating 
 Network clinicdesk_default Created 
 Volume clinicdesk_pgdata Creating 
 Volume clinicdesk_pgdata Created 
 Container clinicdesk-postgres-1 Creating 
 Container clinicdesk-postgres-1 Created 
 Container clinicdesk-backend-1 Creating 
 Container clinicdesk-backend-1 Created 
 Container clinicdesk-frontend-1 Creating 
 Container clinicdesk-frontend-1 Created 
 Container clinicdesk-postgres-1 Starting 
 Container clinicdesk-postgres-1 Started 
 Container clinicdesk-postgres-1 Waiting 
 Container clinicdesk-postgres-1 Healthy 
 Container clinicdesk-backend-1 Starting 
 Container clinicdesk-backend-1 Started 
 Container clinicdesk-backend-1 Waiting 
 Container clinicdesk-backend-1 Healthy 
 Container clinicdesk-frontend-1 Starting 
 Container clinicdesk-frontend-1 Started 
```

The image layers were already in the BuildKit cache from the earlier builds, so in the full log each step is followed by `CACHED`; the filtered lines above (in BuildKit's step order) show the two stages of each image: `[backend build]` / `[backend runtime]` and `[frontend build]` (Node, `npm ci`, `npm run build`) / `[frontend runtime]` (only the `dist/` folder and the nginx template are copied in). Compose starts the containers strictly in dependency order because each `depends_on` uses `condition: service_healthy`.

**Screenshot:** ![docker compose up --build](./screenshots/02-compose-up.png)

### 5.3 Containers, users, migrations

```
$ docker compose ps
NAME                    IMAGE                       COMMAND                  SERVICE    CREATED          STATUS                             PORTS
clinicdesk-backend-1    clinicdesk-backend:local    "sh /app/docker-entr…"   backend    24 seconds ago   Up 18 seconds (healthy)            0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
clinicdesk-frontend-1   clinicdesk-frontend:local   "/docker-entrypoint.…"   frontend   24 seconds ago   Up 12 seconds (health: starting)   0.0.0.0:3000->8080/tcp, [::]:3000->8080/tcp
clinicdesk-postgres-1   postgres:18-alpine          "docker-entrypoint.s…"   postgres   24 seconds ago   Up 24 seconds (healthy)            5432/tcp

$ docker compose exec backend id
uid=10001(app) gid=10001(app) groups=10001(app)

$ docker compose exec frontend id
uid=101(nginx) gid=101(nginx) groups=101(nginx)

$ docker compose logs backend | head -9
backend-1  | INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
backend-1  | INFO  [alembic.runtime.migration] Will assume transactional DDL.
backend-1  | INFO  [alembic.runtime.migration] Running upgrade  -> 0001_clinic_schema, Create doctors, patients and appointments tables
backend-1  | INFO  [alembic.runtime.migration] Running upgrade 0001_clinic_schema -> 0002_seed_doctors, Seed the clinic's doctor roster
backend-1  | INFO:     Started server process [1]
backend-1  | INFO:     Waiting for application startup.
backend-1  | INFO:     Application startup complete.
backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
backend-1  | INFO:     127.0.0.1:60484 - "GET /health HTTP/1.1" 200 OK

$ docker images --format 'table {{.Repository}}:{{.Tag}}	{{.Size}}' | grep -E 'REPOSITORY|clinicdesk'
REPOSITORY:TAG                               SIZE
clinicdesk-frontend:local                    30.5MB
```

Both application containers run as non-root (`uid=10001(app)` and `uid=101(nginx)`). PostgreSQL has no host port. The backend log shows the entrypoint applying both Alembic revisions before Uvicorn starts, then the Docker health check calling `/health`.

### 5.4 API checks with curl (CRUD on appointments)

```
$ curl -s localhost:8000/health
{"status":"UP"}
$ curl -s -w '\nHTTP %{http_code}\n' localhost:8000/ready
{"status":"READY","database":"ok"}
HTTP 200

$ curl -s localhost:8000/api/doctors | python3 -m json.tool
[
    {
        "id": 1,
        "full_name": "Dr. Ananya Rao",
        "specialty": "General Medicine",
        "room": "G-01",
        "active": true
    },
    {
        "id": 3,
        "full_name": "Dr. Farah Siddiqui",
        "specialty": "Dermatology",
        "room": "1-02",
        "active": true
    },
    {
        "id": 4,
        "full_name": "Dr. Rohan Iyer",
        "specialty": "Orthopaedics",
        "room": "1-05",
        "active": true
    },
    {
        "id": 2,
        "full_name": "Dr. Vikram Mehta",
        "specialty": "Paediatrics",
        "room": "G-04",
        "active": true
    }
]

$ curl -s -X POST localhost:8000/api/appointments -H 'Content-Type: application/json' -d '{"doctor_id":1,"scheduled_at":"2026-10-07T16:00","duration_minutes":30,"reason":"Persistent cough","patient":{"full_name":"Rohit Bose","phone":"+91 98300 12345"}}' | python3 -m json.tool
{
    "id": 1,
    "scheduled_at": "2026-10-07T16:00:00",
    "ends_at": "2026-10-07T16:30:00",
    "duration_minutes": 30,
    "reason": "Persistent cough",
    "status": "SCHEDULED",
    "notes": "",
    "doctor": {
        "id": 1,
        "full_name": "Dr. Ananya Rao",
        "specialty": "General Medicine",
        "room": "G-01"
    },
    "patient": {
        "id": 1,
        "full_name": "Rohit Bose",
        "phone": "+91 98300 12345"
    },
    "created_at": "2026-10-06T23:41:34.385039Z",
    "updated_at": "2026-10-06T23:41:34.385042Z"
}

$ curl -s localhost:8000/api/appointments/1 | python3 -c 'import sys,json; a=json.load(sys.stdin); print(a["id"], a["status"], a["scheduled_at"], a["patient"]["full_name"], "->", a["doctor"]["full_name"])'
1 SCHEDULED 2026-10-07T16:00:00 Rohit Bose -> Dr. Ananya Rao

$ curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8000/api/appointments -H 'Content-Type: application/json' -d '{"doctor_id":1,"scheduled_at":"2026-10-07T16:15","duration_minutes":30,"patient":{"full_name":"Anita Roy","phone":"+91 98300 54321"}}'
{"detail":"Dr. Ananya Rao already has an appointment from 16:00 to 16:30 on 07 Oct"}
HTTP 409

$ curl -s -X PUT localhost:8000/api/appointments/1 -H 'Content-Type: application/json' -d '{"status":"CHECKED_IN","notes":"Arrived 10 min early"}' | python3 -c 'import sys,json; a=json.load(sys.stdin); print(a["id"], a["status"], repr(a["notes"]), a["updated_at"])'
1 CHECKED_IN 'Arrived 10 min early' 2026-10-06T23:41:34.469918Z

$ curl -s -X PUT localhost:8000/api/appointments/1 -H 'Content-Type: application/json' -d '{"scheduled_at":"2026-10-07T17:00","duration_minutes":45}' | python3 -c 'import sys,json; a=json.load(sys.stdin); print(a["id"], a["scheduled_at"], "->", a["ends_at"])'
1 2026-10-07T17:00:00 -> 2026-10-07T17:45:00

$ curl -s -X POST localhost:8000/api/appointments/1/cancel | python3 -c 'import sys,json; a=json.load(sys.stdin); print(a["id"], a["status"])'
1 CANCELLED

$ curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8000/api/appointments/1/cancel
{"detail":"Appointment is already cancelled"}
HTTP 409

$ curl -s -o /dev/null -w 'HTTP %{http_code}\n' -X DELETE localhost:8000/api/appointments/1
HTTP 204

$ curl -s -w '\nHTTP %{http_code}\n' localhost:8000/api/appointments/1
{"detail":"Appointment 1 not found"}
HTTP 404

$ curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8000/api/appointments -H 'Content-Type: application/json' -d '{"doctor_id":1,"scheduled_at":"2026-10-07T18:00","duration_minutes":300,"patient_id":1}'
{"detail":[{"type":"less_than_equal","loc":["body","duration_minutes"],"msg":"Input should be less than or equal to 120","input":300,"ctx":{"le":120}}]}
HTTP 422
```

Create → read → update (check-in with notes, then reschedule to 17:00 for 45 min) → cancel → delete → `404`, plus the three error paths: overlapping booking `409`, second cancel `409`, duration 300 `422` with the exact validation message.

**Screenshot:** ![curl CRUD against the API](./screenshots/07-api-curl-crud.png)

### 5.5 Frontend on :3000, nginx proxying `/api`, database contents

The seed script talks to port **3000**, so every booking below went browser-path style through nginx's `/api` proxy rather than straight to the backend:

```
$ BASE_URL=http://localhost:3000 application/scripts/seed-demo.sh 2026-10-07
201 09:00 Meera Krishnan
201 09:30 Imran Qureshi
201 10:15 Lakshmi Pillai
201 11:30 Sanjay Kulkarni
201 09:15 Aarav Sharma
201 10:00 Diya Banerjee
201 14:00 Kabir Malhotra
201 10:00 Nisha Verma
201 12:00 Tanvi Deshpande
201 09:30 Harish Gowda
201 15:30 Fatima Sheikh

$ curl -sI localhost:3000/ | grep -iE '^(HTTP|content-type|x-frame|x-content|content-security)'
HTTP/1.1 200 OK
Content-Type: text/html
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'

$ curl -s localhost:3000/ | grep -oE '<title>.*</title>|/assets/index-[^"]+'
<title>ClinicDesk</title>
/assets/index-BQfMdHMb.js
/assets/index-DPXIatko.css

$ curl -s localhost:3000/healthz
ok

$ curl -s 'localhost:3000/api/appointments?on=2026-10-07&doctor_id=1' | python3 -c 'import sys,json; [print(a["scheduled_at"][11:16], a["status"].ljust(10), a["patient"]["full_name"]) for a in json.load(sys.stdin)]'
09:00 SCHEDULED  Meera Krishnan
09:30 SCHEDULED  Imran Qureshi
10:15 SCHEDULED  Lakshmi Pillai
11:30 SCHEDULED  Sanjay Kulkarni

$ curl -s 'localhost:3000/api/stats?on=2026-10-07' | python3 -m json.tool
{
    "date": "2026-10-07",
    "total": 11,
    "scheduled": 11,
    "checked_in": 0,
    "completed": 0,
    "cancelled": 0,
    "no_show": 0,
    "upcoming_7_days": 11,
    "active_doctors": 4,
    "patients": 12,
    "by_doctor": [
        {
            "doctor_id": 1,
            "full_name": "Dr. Ananya Rao",
            "specialty": "General Medicine",
            "booked": 4,
            "booked_minutes": 120
        },
        {
            "doctor_id": 3,
            "full_name": "Dr. Farah Siddiqui",
            "specialty": "Dermatology",
            "booked": 2,
            "booked_minutes": 50
        },
        {
            "doctor_id": 4,
            "full_name": "Dr. Rohan Iyer",
            "specialty": "Orthopaedics",
            "booked": 2,
            "booked_minutes": 75
        },
        {
            "doctor_id": 2,
            "full_name": "Dr. Vikram Mehta",
            "specialty": "Paediatrics",
            "booked": 3,
            "booked_minutes": 80
        }
    ]
}
```

```
$ docker compose -f docker/docker-compose.yml exec postgres psql -U clinicdesk -d clinicdesk -c '\dt' -c 'SELECT version_num FROM alembic_version' -c 'SELECT d.full_name AS doctor, count(a.id) AS booked FROM doctors d LEFT JOIN appointments a ON a.doctor_id = d.id GROUP BY d.full_name ORDER BY 1'
                List of tables
 Schema |      Name       | Type  |   Owner    
--------+-----------------+-------+------------
 public | alembic_version | table | clinicdesk
 public | appointments    | table | clinicdesk
 public | doctors         | table | clinicdesk
 public | patients        | table | clinicdesk
(4 rows)

    version_num    
-------------------
 0002_seed_doctors
(1 row)

       doctor       | booked 
--------------------+--------
 Dr. Ananya Rao     |      4
 Dr. Farah Siddiqui |      2
 Dr. Rohan Iyer     |      2
 Dr. Vikram Mehta   |      3
(4 rows)
```

The `psql` output confirms the four tables (three app tables plus `alembic_version` at `0002_seed_doctors`) and that the per-doctor counts in the database match `/api/stats`.

### 5.6 Tear down

```
$ docker compose down -v
 Container clinicdesk-frontend-1 Stopping 
 Container clinicdesk-frontend-1 Stopped 
 Container clinicdesk-frontend-1 Removing 
 Container clinicdesk-frontend-1 Removed 
 Container clinicdesk-backend-1 Stopping 
 Container clinicdesk-backend-1 Stopped 
 Container clinicdesk-backend-1 Removing 
 Container clinicdesk-backend-1 Removed 
 Container clinicdesk-postgres-1 Stopping 
 Container clinicdesk-postgres-1 Stopped 
 Container clinicdesk-postgres-1 Removing 
 Container clinicdesk-postgres-1 Removed 
 Volume clinicdesk_pgdata Removing 
 Network clinicdesk_default Removing 
 Volume clinicdesk_pgdata Removed 
 Network clinicdesk_default Removed 

$ docker compose ps -a
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS

$ docker volume ls --filter name=clinicdesk
DRIVER    VOLUME NAME
```

`-v` also removes the `pgdata` named volume, so the next `up` starts from an empty, freshly migrated database. The two images are kept for the Kubernetes phase.

---

## 6. Kubernetes deployment

Raw manifests live in [`kubernetes/`](./kubernetes) and apply with Kustomize (`kubectl apply -k kubernetes/`). They cover everything Session 21 lists:

| File | Objects | Notes |
| --- | --- | --- |
| `00-namespace.yaml` | Namespace `clinicdesk` | labelled `pod-security.kubernetes.io/enforce: restricted`, every pod below complies |
| `01-configmap.yaml` | ConfigMap `clinicdesk-config` | `DB_HOST`, `DB_PORT`, `DB_NAME`, timezone, log level, `BACKEND_UPSTREAM` |
| `02-secret.example.yaml` | Secret `clinicdesk-db` (**template only**) | placeholder `REPLACE_ME`, excluded from `kustomization.yaml`; real secret created with `kubectl create secret generic` (command in the file) |
| `10-postgres.yaml` | headless Service + StatefulSet with `volumeClaimTemplates` (1 Gi PVC) | runs as uid 70, `pg_isready` readiness/liveness probes |
| `20-backend.yaml` | Deployment (2 replicas) + ClusterIP Service :8000 | startup, liveness (`/health`), readiness (`/ready`) probes; requests/limits; read-only root FS; `envFrom` ConfigMap + `secretKeyRef` |
| `30-frontend.yaml` | Deployment (2 replicas) + ClusterIP Service :80 → 8080 | `/healthz` probes; emptyDirs for `/tmp` and nginx `conf.d` so the root FS can be read-only |
| `40-ingress.yaml` | Ingress `clinicdesk.local` | `/api` → backend, `/` → frontend, `ingressClassName: nginx` |
| `50-hpa.yaml` | HPA backend 2–6 @70 % CPU, frontend 2–4 @75 % | `autoscaling/v2`, scale-down stabilisation 120 s |
| `kustomization.yaml` | — | pins image tags (`kustomize edit set image ...:<sha>`) |

Validated offline against the Kubernetes JSON schemas (no cluster needed):

```
$ kubectl kustomize kubernetes | kubeconform -strict -summary -
Summary: 11 resources found parsing stdin - Valid: 11, Invalid: 0, Errors: 0, Skipped: 0

$ kubeconform -strict -summary kubernetes/02-secret.example.yaml
Summary: 1 resource found in 1 file - Valid: 1, Invalid: 0, Errors: 0, Skipped: 0

$ kubectl kustomize kubernetes | grep -E '^kind:' | sort | uniq -c
   1 kind: ConfigMap
   2 kind: Deployment
   2 kind: HorizontalPodAutoscaler
   1 kind: Ingress
   1 kind: Namespace
   3 kind: Service
   1 kind: StatefulSet
```

Deploying these to a cluster, `kubectl get pods/svc/ingress/hpa` and the HPA load test: _Phase 2 — pending_.

---

## 7. Helm deployment

Chart: [`helm/clinicdesk`](./helm/clinicdesk) (`apiVersion: v2`, chart 0.1.0, app 1.0.0).

| Template | What it renders |
| --- | --- |
| `configmap.yaml`, `secret.yaml` | ConfigMap; DB Secret **only if** `database.existingSecret` is empty. The password is taken from values, else reused from the live Secret via `lookup` (so upgrades never lock PostgreSQL out), else generated. |
| `backend-deployment.yaml`, `backend-service.yaml` | backend Deployment + Service; a `checksum/config` annotation rolls pods when the ConfigMap changes |
| `frontend-deployment.yaml`, `frontend-service.yaml` | frontend Deployment + Service |
| `postgres.yaml` | headless Service + StatefulSet + PVC (`postgres.enabled=false` switches to `externalDatabase.host`, e.g. RDS) |
| `ingress.yaml` | toggled by `ingress.enabled`, optional TLS |
| `hpa.yaml` | one HPA per component when `autoscaling.enabled`; Deployments drop `replicas:` so Helm and the HPA don't fight |
| `servicemonitor.yaml` | toggled by `monitoring.serviceMonitor.enabled` (needs the Prometheus Operator CRDs) |
| `NOTES.txt` | post-install instructions (port-forward or Ingress URL) |

| Values file | Purpose |
| --- | --- |
| `values.yaml` | defaults: 2 replicas, HPA on, chart-managed Secret, ServiceMonitor off |
| `values-dev.yaml` | minikube: 1 replica each, HPA off, Ingress `clinicdesk.local` |
| `values-prod.yaml` | EKS: HPA 2–8 backend, `existingSecret: clinicdesk-db` (GitOps-safe), 5 Gi PVC on `ebs-csi-default-sc` (the StorageClass Terraform's EBS CSI add-on creates), Ingress on, ServiceMonitor on |

```
$ helm version --short
v4.3.0+gbec5b06

$ helm lint helm/clinicdesk -f helm/clinicdesk/values-dev.yaml
==> Linting helm/clinicdesk

1 chart(s) linted, 0 chart(s) failed

$ helm lint helm/clinicdesk -f helm/clinicdesk/values-prod.yaml
==> Linting helm/clinicdesk

1 chart(s) linted, 0 chart(s) failed

$ helm template clinicdesk helm/clinicdesk -n clinicdesk -f helm/clinicdesk/values-dev.yaml | grep -E '^kind:' | sort | uniq -c
   1 kind: ConfigMap
   2 kind: Deployment
   1 kind: Ingress
   1 kind: Secret
   3 kind: Service
   1 kind: StatefulSet

$ helm template clinicdesk helm/clinicdesk -n clinicdesk -f helm/clinicdesk/values-prod.yaml --set backend.image.tag=3f9c2ab --set frontend.image.tag=3f9c2ab | grep -E '^kind:' | sort | uniq -c
   1 kind: ConfigMap
   2 kind: Deployment
   2 kind: HorizontalPodAutoscaler
   1 kind: Ingress
   3 kind: Service
   1 kind: ServiceMonitor
   1 kind: StatefulSet

$ helm template clinicdesk helm/clinicdesk -n clinicdesk -f helm/clinicdesk/values-prod.yaml --set backend.image.tag=3f9c2ab --set frontend.image.tag=3f9c2ab | grep -E 'image:|storageClassName|host:|existingSecret|secretKeyRef' | sort | uniq -c
   2                 secretKeyRef: {name: clinicdesk-db, key: password}
   2                 secretKeyRef: {name: clinicdesk-db, key: username}
   1           image: "ghcr.io/saptak-cyber/clinicdesk-backend:3f9c2ab"
   1           image: "ghcr.io/saptak-cyber/clinicdesk-frontend:3f9c2ab"
   1           image: "postgres:18-alpine"
   1         storageClassName: ebs-csi-default-sc
   1     - host: "clinicdesk.example.com"

$ kubeconform -v
v0.8.0

$ helm template clinicdesk helm/clinicdesk -n clinicdesk -f helm/clinicdesk/values-dev.yaml | kubeconform -strict -summary -schema-location default -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' -
Summary: 9 resources found parsing stdin - Valid: 9, Invalid: 0, Errors: 0, Skipped: 0

$ helm template clinicdesk helm/clinicdesk -n clinicdesk -f helm/clinicdesk/values-prod.yaml | kubeconform -strict -summary -schema-location default -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' -
Summary: 11 resources found parsing stdin - Valid: 11, Invalid: 0, Errors: 0, Skipped: 0
```

`helm lint` passes for both environments. The dev render has a Secret and no HPA; prod has no Secret (it references the pre-created `clinicdesk-db`), two HPAs and a ServiceMonitor, and CI-style `--set backend.image.tag=<sha>` lands in the image references. Both renders validate cleanly, including the ServiceMonitor against its CRD schema.

**Screenshot:** ![helm lint and template](./screenshots/10-helm-lint-template.png)

`helm upgrade --install`, `helm list`, upgrade and rollback on a cluster: _Phase 2 — pending_.

---

## 8. Terraform infrastructure

Files in [`terraform/`](./terraform): `versions.tf` (Terraform ≥ 1.10, AWS provider `~> 6.0`, default tags, commented S3 backend with native locking), `variables.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars.example`, `.gitignore` (state, plans, real tfvars, `.terraform/`). `.terraform.lock.hcl` is committed so CI resolves the same provider builds.

What `main.tf` builds:

- **VPC** (`terraform-aws-modules/vpc` 6.7.3): `10.42.0.0/16`, 2 public + 2 private subnets in `ap-south-1a/b`, **one** NAT gateway (cheaper for a classroom; production would use one per AZ), subnet tags for load balancers.
- **EKS** (`terraform-aws-modules/eks` 21.26.0): cluster `clinicdesk-eks`, Kubernetes **1.36** (the current EKS default in `ap-south-1`), public endpoint (CIDRs configurable), the caller becomes cluster admin via an access entry, nodes in private subnets.
- **Managed node group** `general`: `t3.medium`, AL2023, on-demand, **min 1 / desired 2 / max 3**.
- **Add-ons**: `vpc-cni` and `eks-pod-identity-agent` before compute, `coredns`, `kube-proxy`, **`metrics-server`** (the HPA needs it) and **`aws-ebs-csi-driver`** with an IAM role through EKS Pod Identity (`terraform-aws-modules/eks-pod-identity` 2.9.0) and `defaultStorageClass.enabled`, so the PostgreSQL PVC binds to a gp3 volume.
- **Outputs**: VPC/subnet IDs, NAT IP, cluster name/endpoint/version, node groups, and `configure_kubectl` (the `aws eks update-kubeconfig` command).

```bash
cd terraform
source <path>/awsenv.sh          # exports AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / region, kept outside the repo
terraform init && terraform fmt -recursive -check && terraform validate && terraform plan -out=tfplan
```

```
$ terraform version
Terraform v1.16.4
on darwin_arm64
+ provider registry.terraform.io/hashicorp/aws v6.67.0
+ provider registry.terraform.io/hashicorp/cloudinit v2.4.1
+ provider registry.terraform.io/hashicorp/null v3.3.2
+ provider registry.terraform.io/hashicorp/time v0.14.2
+ provider registry.terraform.io/hashicorp/tls v4.4.1

Your version of Terraform is out of date! The latest version
is 1.16.5. You can update by downloading from https://developer.hashicorp.com/terraform/install

$ aws sts get-caller-identity --query '{Account:Account,Arn:Arn}' --output table
----------------------------------------------------------------------
|                          GetCallerIdentity                         |
+--------------+-----------------------------------------------------+
|    Account   |                         Arn                         |
+--------------+-----------------------------------------------------+
|  <account-id>|  arn:aws:iam::<account-id>:user/terraform-sandbox   |
+--------------+-----------------------------------------------------+

$ terraform init -input=false
Initializing the backend...

Initializing modules...

Initializing provider plugins...
- Reusing previous version of hashicorp/time from the dependency lock file
- Reusing previous version of hashicorp/cloudinit from the dependency lock file
- Reusing previous version of hashicorp/null from the dependency lock file
- Reusing previous version of hashicorp/aws from the dependency lock file
- Reusing previous version of hashicorp/tls from the dependency lock file
- Using previously-installed hashicorp/time v0.14.2
- Using previously-installed hashicorp/cloudinit v2.4.1
- Using previously-installed hashicorp/null v3.3.2
- Using previously-installed hashicorp/aws v6.67.0
- Using previously-installed hashicorp/tls v4.4.1

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.

$ terraform fmt -recursive -check && echo 'fmt: no changes needed'
fmt: no changes needed

$ terraform validate
Success! The configuration is valid.

$ terraform plan -input=false -out=tfplan
...
data.aws_availability_zones.available: Read complete after 0s [id=ap-south-1]
module.eks.module.eks_managed_node_group["general"].data.aws_ssm_parameter.ami[0]: Read complete after 4s [id=/aws/service/eks/optimized-ami/1.36/amazon-linux-2023/x86_64/standard/recommended/release_version]
...
  # module.eks.aws_eks_cluster.this[0] will be created
  + resource "aws_eks_cluster" "this" {
      + arn                           = (known after apply)
      + bootstrap_self_managed_addons = false
      + certificate_authority         = (known after apply)
      + cluster_id                    = (known after apply)
      + created_at                    = (known after apply)
      + deletion_protection           = (known after apply)
      + enabled_cluster_log_types     = [
          + "api",
          + "audit",
          + "authenticator",
        ]
      + endpoint                      = (known after apply)
      + id                            = (known after apply)
      + identity                      = (known after apply)
      + name                          = "clinicdesk-eks"
      + platform_version              = (known after apply)
      + region                        = "ap-south-1"
      + role_arn                      = (known after apply)
      + status                        = (known after apply)
      + tags_all                      = {
          + "Environment" = "dev"
          + "ManagedBy"   = "terraform"
          + "Owner"       = "saptak-banerjee"
          + "Project"     = "clinicdesk"
        }
      + version                       = "1.36"
...
Plan: 61 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + cluster_endpoint  = (known after apply)
  + cluster_name      = "clinicdesk-eks"
  + cluster_version   = "1.36"
  + configure_kubectl = "aws eks update-kubeconfig --region ap-south-1 --name clinicdesk-eks"
  + nat_public_ip     = [
      + (known after apply),
    ]
  + node_group_names  = [
      + "general",
    ]
  + private_subnets   = [
      + (known after apply),
      + (known after apply),
    ]
  + public_subnets    = [
      + (known after apply),
      + (known after apply),
    ]
  + region            = "ap-south-1"
  + vpc_id            = (known after apply)

─────────────────────────────────────────────────────────────────────────────

Saved the plan to: tfplan

To perform exactly these actions, run the following command to apply:
    terraform apply "tfplan"
```

The plan talked to the real account (read-only): it resolved the two AZs and fetched the EKS-optimised AL2023 AMI for 1.36 from SSM, which proves the version exists for managed nodes in this region. Breakdown of the 61 resources:

```
$ terraform show -json tfplan | python3 -c 'import sys,json,collections; p=json.load(sys.stdin); c=collections.Counter(r["type"] for r in p["resource_changes"] if r["change"]["actions"]==["create"]); [print(f"{n:3} {t}") for t,n in c.most_common()]'
 12 aws_security_group_rule
  6 aws_iam_role_policy_attachment
  6 aws_eks_addon
  4 aws_route_table_association
  4 aws_subnet
  3 aws_iam_role
  2 aws_iam_policy
  2 aws_security_group
  2 aws_route
  2 aws_route_table
  1 aws_cloudwatch_log_group
  1 aws_eks_access_entry
  1 aws_eks_access_policy_association
  1 aws_eks_cluster
  1 aws_iam_openid_connect_provider
  1 time_sleep
  1 aws_default_network_acl
  1 aws_default_route_table
  1 aws_default_security_group
  1 aws_eip
  1 aws_internet_gateway
  1 aws_nat_gateway
  1 aws_vpc
  1 aws_eks_node_group
  1 aws_launch_template
  1 aws_kms_alias
  1 aws_kms_key
  1 null_resource

$ terraform show -json tfplan | python3 -c 'import sys,json; p=json.load(sys.stdin); [print(r["change"]["after"]["addon_name"]) for r in p["resource_changes"] if r["type"]=="aws_eks_addon"]'
eks-pod-identity-agent
vpc-cni
aws-ebs-csi-driver
coredns
kube-proxy
metrics-server

$ terraform show -json tfplan | python3 -c 'import sys,json; p=json.load(sys.stdin); [print(r["address"], r["change"]["after"].get("cidr_block"), r["change"]["after"].get("availability_zone")) for r in p["resource_changes"] if r["type"]=="aws_subnet"]'
module.vpc.aws_subnet.private[0] 10.42.10.0/24 ap-south-1a
module.vpc.aws_subnet.private[1] 10.42.11.0/24 ap-south-1b
module.vpc.aws_subnet.public[0] 10.42.0.0/24 ap-south-1a
module.vpc.aws_subnet.public[1] 10.42.1.0/24 ap-south-1b

$ terraform show -json tfplan | python3 -c 'import sys,json; p=json.load(sys.stdin); ng=[r for r in p["resource_changes"] if r["type"]=="aws_eks_node_group"][0]["change"]["after"]; print(ng["instance_types"], ng["capacity_type"], ng["ami_type"], ng["scaling_config"])'
['t3.medium'] ON_DEMAND AL2023_x86_64_STANDARD [{'desired_size': 2, 'max_size': 3, 'min_size': 1}]
```

**Screenshot:** ![terraform plan: 61 to add](./screenshots/11-terraform-plan.png)

Cost note: an EKS control plane, two t3.medium nodes and a NAT gateway cost money every hour, so `terraform apply` is run only for the evaluation window and followed by `terraform destroy`. `terraform apply`, the AWS console screenshots of the VPC and EKS cluster, `kubectl get nodes` and `terraform destroy`: _Phase 2 — pending_.

---

## 9. CI/CD pipeline

_Phase 2 — pending_

---

## 10. DevSecOps implementation

Local checks run in Phase 1 (the same gates move into CI in Phase 2):

**Container image scanning (Trivy), HIGH + CRITICAL, failing on findings:**

```
$ trivy --version | head -1
Version: 0.75.0

$ trivy image --severity HIGH,CRITICAL --exit-code 1 clinicdesk-backend:local; echo "exit code: $?"
2026-10-07T05:12:27+05:30	INFO	[vuln] Vulnerability scanning is enabled
2026-10-07T05:12:27+05:30	INFO	[secret] Secret scanning is enabled
2026-10-07T05:12:27+05:30	INFO	[secret] If your scanning is slow, please try '--scanners vuln' to disable secret scanning
2026-10-07T05:12:27+05:30	INFO	[secret] Please see https://trivy.dev/docs/v0.75/guide/scanner/secret#recommendation for faster secret detection
2026-10-07T05:12:28+05:30	INFO	Detected OS	family="alpine" version="3.24.2"
2026-10-07T05:12:28+05:30	INFO	[alpine] Detecting vulnerabilities...	os_version="3.24" repository="3.24" pkg_num=30
2026-10-07T05:12:28+05:30	INFO	Number of language-specific files	num=1
2026-10-07T05:12:28+05:30	INFO	[python-pkg] Detecting vulnerabilities...

Report Summary

┌──────────────────────────────────────────────────────────────────────────────────┬────────────┬─────────────────┬─────────┐
│                                      Target                                      │    Type    │ Vulnerabilities │ Secrets │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ clinicdesk-backend:local (alpine 3.24.2)                                         │   alpine   │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
...
│ opt/venv/lib/python3.14/site-packages/fastapi-0.142.2.dist-info/METADATA         │ python-pkg │        0        │    -    │
...
│ opt/venv/lib/python3.14/site-packages/psycopg_binary-3.3.6.dist-info/METADATA    │ python-pkg │        0        │    -    │
...
│ opt/venv/lib/python3.14/site-packages/sqlalchemy-2.1.3.dist-info/METADATA        │ python-pkg │        0        │    -    │
...
│ opt/venv/lib/python3.14/site-packages/uvloop-0.23.0.dist-info/METADATA           │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ opt/venv/lib/python3.14/site-packages/watchfiles-1.3.0.dist-info/METADATA        │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ opt/venv/lib/python3.14/site-packages/websockets-17.2.dist-info/METADATA         │ python-pkg │        0        │    -    │
└──────────────────────────────────────────────────────────────────────────────────┴────────────┴─────────────────┴─────────┘
Legend:
- '-': Not scanned
- '0': Clean (no security findings detected)

exit code: 0

$ trivy image --severity HIGH,CRITICAL --exit-code 1 clinicdesk-frontend:local; echo "exit code: $?"
2026-10-07T05:12:28+05:30	INFO	[vuln] Vulnerability scanning is enabled
2026-10-07T05:12:28+05:30	INFO	[secret] Secret scanning is enabled
2026-10-07T05:12:28+05:30	INFO	[secret] If your scanning is slow, please try '--scanners vuln' to disable secret scanning
2026-10-07T05:12:28+05:30	INFO	[secret] Please see https://trivy.dev/docs/v0.75/guide/scanner/secret#recommendation for faster secret detection
2026-10-07T05:12:28+05:30	INFO	Detected OS	family="alpine" version="3.24.2"
2026-10-07T05:12:28+05:30	INFO	[alpine] Detecting vulnerabilities...	os_version="3.24" repository="3.24" pkg_num=21
2026-10-07T05:12:28+05:30	INFO	Number of language-specific files	num=0

Report Summary

┌───────────────────────────────────────────┬────────┬─────────────────┬─────────┐
│                  Target                   │  Type  │ Vulnerabilities │ Secrets │
├───────────────────────────────────────────┼────────┼─────────────────┼─────────┤
│ clinicdesk-frontend:local (alpine 3.24.2) │ alpine │        0        │    -    │
└───────────────────────────────────────────┴────────┴─────────────────┴─────────┘
Legend:
- '-': Not scanned
- '0': Clean (no security findings detected)

exit code: 0
```

Both images: **0 HIGH/CRITICAL**, `--exit-code 1` returned 0, i.e. a CI gate would pass. Trivy checked the Alpine OS packages (30 in the backend, 21 in the frontend) and every Python package installed in `/opt/venv`, and also ran its secret scanner over the image layers.

How it got to zero: the first backend build used `python:3.14-slim` (Debian 13). Trivy then reported:

```
$ trivy image --quiet --severity HIGH,CRITICAL clinicdesk-backend:local
...
clinicdesk-backend:local (debian 13.7)
======================================
Total: 44 (HIGH: 44, CRITICAL: 0)
```

```
$ trivy image --quiet --severity HIGH,CRITICAL --format json clinicdesk-backend:local > trivy-backend.json
$ python3 -c "<count findings by package>" trivy-backend.json
Counter({('bsdutils', 'HIGH'): 4, ('libblkid1', 'HIGH'): 4, ('liblastlog2-2', 'HIGH'): 4, ('libmount1', 'HIGH'): 4, ('libsmartcols1', 'HIGH'): 4, ('libuuid1', 'HIGH'): 4, ('login', 'HIGH'): 4, ('mount', 'HIGH'): 4, ('util-linux', 'HIGH'): 4, ('libacl1', 'HIGH'): 1, ('libncursesw6', 'HIGH'): 1, ('libsystemd0', 'HIGH'): 1, ('libtinfo6', 'HIGH'): 1, ('libudev1', 'HIGH'): 1, ('ncurses-base', 'HIGH'): 1, ('ncurses-bin', 'HIGH'): 1, ('perl-base', 'HIGH'): 1})
```

All 44 were in base-OS packages the API never uses (util-linux, ncurses, systemd libraries, perl), and none had a fixed version yet (43 `affected`, 1 `fix_deferred`), so `--ignore-unfixed` would have hidden them rather than fixed them. Switching both stages to `python:3.14-alpine` removed them and cut the image from 346 MB to 212 MB.

**Dependency scanning (SCA):**

```
$ pip-audit --version
pip-audit 2.10.1

$ pip-audit --cache-dir <scratch>/s21/pipaudit-cache -r backend/requirements.txt
No known vulnerabilities found

$ pip-audit --cache-dir <scratch>/s21/pipaudit-cache -r backend/requirements-dev.txt
No known vulnerabilities found

$ cd frontend && npm audit; cd ..
found 0 vulnerabilities
```

**Manifest validation:** `kubeconform -strict` on the raw manifests and both Helm renders (section 6 and 7): all valid.

**Hardening already in the artefacts:** non-root users in both images; read-only root filesystems, `drop: [ALL]` capabilities, `allowPrivilegeEscalation: false`, `seccompProfile: RuntimeDefault` and `automountServiceAccountToken: false` on every pod; `restricted` Pod Security on the namespace; no Secret values in Git (template + `kubectl create secret`, or `existingSecret` in Helm); security headers + CSP from nginx; PostgreSQL not exposed outside its network; `.gitignore` covers `.env`, state files and real tfvars.

SAST, secret scanning of the Git history, IaC scanning and the pipeline security gates: _Phase 2 — pending_.

**Screenshot:** ![Trivy: 0 HIGH/CRITICAL on both images](./screenshots/09-trivy-clean.png)

---

## 11. Monitoring

The backend exposes Prometheus metrics at `/metrics` (`prometheus-fastapi-instrumentator`, grouped by handler template, method and status class; `/health`, `/ready` and `/metrics` are excluded so probes don't drown real traffic). Real output after the section 5 run:

```
$ curl -s localhost:8000/metrics | grep -E '^http_requests_total'
http_requests_total{handler="/api/doctors",method="GET",status="2xx"} 1.0
http_requests_total{handler="/api/appointments",method="POST",status="2xx"} 12.0
http_requests_total{handler="/api/appointments/{appointment_id}",method="GET",status="2xx"} 1.0
http_requests_total{handler="/api/appointments",method="POST",status="4xx"} 2.0
http_requests_total{handler="/api/appointments/{appointment_id}",method="PUT",status="2xx"} 2.0
http_requests_total{handler="/api/appointments/{appointment_id}/cancel",method="POST",status="2xx"} 1.0
http_requests_total{handler="/api/appointments/{appointment_id}/cancel",method="POST",status="4xx"} 1.0
http_requests_total{handler="/api/appointments/{appointment_id}",method="DELETE",status="2xx"} 1.0
http_requests_total{handler="/api/appointments/{appointment_id}",method="GET",status="4xx"} 1.0
http_requests_total{handler="/api/appointments",method="GET",status="2xx"} 1.0
http_requests_total{handler="/api/stats",method="GET",status="2xx"} 1.0

$ curl -s localhost:8000/metrics | grep -E '^http_request_duration_seconds_(count|sum)\{handler="/api/appointments",method="POST"'
http_request_duration_seconds_count{handler="/api/appointments",method="POST"} 14.0
http_request_duration_seconds_sum{handler="/api/appointments",method="POST"} 0.13406608499963113
```

**Screenshot:** ![/metrics output](./screenshots/08-metrics-endpoint.png)

Prometheus + Grafana (kube-prometheus-stack), the ServiceMonitor target showing `UP`, dashboards, logs: _Phase 2 — pending_.

---

## 12. GitOps

_Phase 2 — pending_

---

## 13. Troubleshooting

_Phase 2 — pending_

---

## 14. Screenshots

Images already captured from the running stack are in [`screenshots/`](./screenshots); terminal screenshots still to take are listed in [`screenshots/CAPTURE-LIST.md`](./screenshots/CAPTURE-LIST.md).

| File | Shows | Status |
| --- | --- | --- |
| `01-pytest-pass.png` | `pytest -v`, 23 passed | to capture |
| `02-compose-up.png` | `docker compose up --build -d` + `docker compose ps` | to capture |
| `03-app-dashboard.png` | ClinicDesk day board at `localhost:3000` | captured |
| `04-app-booking-conflict.png` | booking form showing the `409` clash message | captured |
| `05-app-mobile.png` | 390 px layout | captured |
| `06-swagger-docs.png` | Swagger UI at `localhost:8000/docs` | captured |
| `07-api-curl-crud.png` | curl CRUD sequence | to capture |
| `08-metrics-endpoint.png` | `curl localhost:8000/metrics` | to capture |
| `09-trivy-clean.png` | Trivy on both images | to capture |
| `10-helm-lint-template.png` | `helm lint` + kubeconform | to capture |
| `11-terraform-plan.png` | `terraform plan` summary | to capture |

Cluster, CI, monitoring, GitOps and troubleshooting screenshots: _Phase 2 — pending_.

---

## 15. Lessons learned

So far:

1. **"No fixable vulnerabilities" is not the same as "no vulnerabilities".** The Debian-slim image had 44 HIGH findings with no fix available. `--ignore-unfixed` would have turned the gate green while shipping them; changing the base image removed them.
2. **Liveness and readiness answer different questions.** If `/health` checked the database, a short PostgreSQL restart would make Kubernetes kill every healthy backend pod. Keeping the DB check in `/ready` only takes them out of rotation.
3. **Start-up migrations need a lock once you have replicas.** Two pods running `alembic upgrade head` at the same moment can both try `CREATE TABLE`; a PostgreSQL advisory lock in `env.py` makes the second one wait and then find nothing to do.
4. **Port and name drift between layers is the classic break.** The reference chart's Ingress points at port 8080 of a Service that listens on 8000, under a name the chart doesn't create. Here every Service port is referenced by name (`port: {name: http}`) and names come from one helper, and `kubeconform` + `helm template` catch schema mistakes before a cluster ever sees them.
5. **Charts that generate secrets must be GitOps-aware.** `lookup` keeps a generated password stable for `helm upgrade`, but Argo CD renders without cluster access, so the prod values switch to an externally created Secret.
6. **Tooling moves.** Starlette's TestClient now warns about `httpx` and wants `httpx2`; pinning current releases and running `pip-audit`/`npm audit` early kept the dependency set clean from the start.

---

## Cleanup

Done after Phase 1:

```bash
cd docker && docker compose down -v      # containers, network and the pgdata volume (output in 5.6)
```

No AWS resources exist: only `terraform plan` was run (read-only), never `apply`. The local `tfplan` file was deleted after the summary was taken. The `clinicdesk-backend:local` and `clinicdesk-frontend:local` images are kept for the Kubernetes phase.
