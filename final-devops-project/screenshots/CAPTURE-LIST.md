# Screenshot capture checklist — Final DevOps Project (ClinicDesk)

The README references these filenames. Files marked **captured** are already in this folder
(taken from the running Docker Compose stack). For the rest, run the command from the README
section shown, capture the terminal, and save it here with the exact name so the README renders on GitHub.

| File | What to capture | README section | Status |
| --- | --- | --- | --- |
| `01-pytest-pass.png` | `cd application/backend && pytest -v` showing `23 passed` | 4.1 | to capture |
| `02-compose-up.png` | `cd docker && docker compose up --build -d` followed by `docker compose ps` (all three healthy) | 5.2 | to capture |
| `03-app-dashboard.png` | ClinicDesk day board at `http://localhost:3000` with seeded appointments | 4.4 | captured |
| `04-app-booking-conflict.png` | Booking form showing the double-booking (`409`) message | 4.4 | captured |
| `05-app-mobile.png` | App at phone width (390 px) | 4.4 | captured |
| `06-swagger-docs.png` | Swagger UI at `http://localhost:8000/docs` | 4.4 | captured |
| `07-api-curl-crud.png` | curl create / update / cancel / delete sequence against `/api/appointments` | 5.4 | to capture |
| `08-metrics-endpoint.png` | `curl -s localhost:8000/metrics \| grep ^http_requests_total` | 11 | to capture |
| `09-trivy-clean.png` | `trivy image --severity HIGH,CRITICAL --exit-code 1` on both images (0 findings) | 10 | to capture |
| `10-helm-lint-template.png` | `helm lint` (dev + prod) and the kubeconform summaries | 7 | to capture |
| `11-terraform-plan.png` | End of `terraform plan`: `Plan: 61 to add, 0 to change, 0 to destroy.` and the outputs | 8 | to capture |

Cluster, CI/CD, monitoring, GitOps and troubleshooting screenshots will be added to this list in Phase 2.
