# Screenshots — Final DevOps Project (ClinicDesk)

The README references these filenames, and every one of them is in this folder.

| File | What it shows | README section | Status |
| --- | --- | --- | --- |
| `01-pytest-pass.png` | `cd application/backend && pytest -v` showing `23 passed` | 4.1 | rendered from the README output |
| `02-compose-up.png` | `cd docker && docker compose up --build -d` then `docker compose ps` (all healthy) | 5.2 | rendered from the README output |
| `03-app-dashboard.png` | ClinicDesk day board at `http://localhost:3000` | 4.4 | captured |
| `04-app-booking-conflict.png` | Booking form showing the double-booking (`409`) message | 4.4 | captured |
| `05-app-mobile.png` | App at phone width (390 px) | 4.4 | captured |
| `06-swagger-docs.png` | Swagger UI at `http://localhost:8000/docs` | 4.4 | captured |
| `07-api-curl-crud.png` | curl create / update / cancel / delete against `/api/appointments` | 5.4 | rendered from the README output |
| `08-metrics-endpoint.png` | `curl -s localhost:8000/metrics \| grep ^http_requests_total` | 11.1 | rendered from the README output |
| `09-trivy-clean.png` | "7. Security gate" job log of a green run (all checks PASS) | 10 | captured live |
| `10-helm-lint-template.png` | `helm lint` (dev + prod) and the kubeconform summaries | 7.1 | rendered from the README output |
| `11-terraform-plan.png` | End of `terraform plan`: `Plan: 61 to add, 0 to change, 0 to destroy.` | 8.1 | rendered from the README output |
| `12-eks-app-via-ingress.png` | The app on EKS through the ingress-nginx NLB | 6.2 | captured |
| `13-aws-console-eks.png` | AWS console (ap-south-1): VPC `clinicdesk-dev-vpc` and EKS cluster `clinicdesk-eks` Active | 8.3 | captured live (re-apply on 2026-10-07; account ID masked) |
| `14-prometheus-targets.png` | Prometheus Status → Target health, `clinicdesk-backend` targets UP | 11.2 | captured |
| `15-grafana-dashboard.png` | Grafana "ClinicDesk API" dashboard with live data | 11.2 | captured |
| `16-argocd-app.png` | Argo CD application `clinicdesk`: Synced + Healthy | 12.3 | captured |
| `17-gitops-new-version-footer.png` | The 1.1.0 footer served from EKS after the GitOps rollout | 12.3 | captured |
| `18-ci-pipeline-green.png` | GitHub Actions run 37552961415: all 10 jobs green (graph view) | 9 | captured live |
| `19-ghcr-sha-tags.png` | GHCR package page for `clinicdesk-backend` showing the commit-SHA tags | 9 | captured live |
| `20-terraform-destroy.png` | `Destroy complete! Resources: 61 destroyed.` | 8.4 / Cleanup | rendered from the README output |

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line). GitHub Actions and GHCR screenshots are live browser captures of the actual runs and packages (Playwright, signed in as Saptak-cyber). Browser screenshots of Grafana, Prometheus, Argo CD and the app were taken live while the clusters were running.
