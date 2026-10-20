# Demo: slides and walkthrough video

| File | What it is |
| --- | --- |
| [`clinicdesk-presentation.pptx`](./clinicdesk-presentation.pptx) | 14-slide deck: overview, tech stack, architecture diagram, app and tests, containers, CI/CD flow, DevSecOps, Terraform, Kubernetes and Helm, GitOps, observability, key learnings. Speaker notes on every slide. |
| [`clinicdesk-presentation.pdf`](./clinicdesk-presentation.pdf) | The same deck as a PDF |
| [`clinicdesk-walkthrough.mp4`](./clinicdesk-walkthrough.mp4) | Recorded presentation and live walkthrough (23 min, 1080p): slides, codebase, a live push of ClinicDesk 1.2.0 through the pipeline, Terraform plan and AWS console, Argo CD rolling it out, Kubernetes, Prometheus and Grafana |

The video follows the order in `SUBMISSION.md`: slides first, then a live walkthrough of the codebase, CI/CD, Terraform, Argo CD, Kubernetes, Prometheus and Grafana.

---

## Recording runbook

The EKS cluster is not left running (cost), so it is rebuilt for the recording and destroyed afterwards. Every command below was already run once for the main [README](../README.md); section numbers point to the captured output.

### 0. Before recording (about 25 minutes, off camera)

Run from `final-devops-project/`. AWS credentials come from the environment and are never committed.

```bash
export AWS_REGION=ap-south-1            # plus AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY

# Record clip T1 now: a non-empty plan only exists before apply
cd terraform
terraform init -input=false
terraform plan -input=false -out=tfplan          # README 8.1
terraform apply -input=false tfplan              # about 14 min, README 8.2
cd ..

aws eks update-kubeconfig --region ap-south-1 --name clinicdesk-eks --kubeconfig ~/.kube/clinicdesk-eks
export KUBECONFIG=~/.kube/clinicdesk-eks
kubectl get nodes

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

GF_PASS="$(openssl rand -base64 18)"; echo "$GF_PASS" > ~/.clinicdesk-grafana-pass   # outside the repo
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.0.0 \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml \
  --set grafana.adminPassword="$GF_PASS" --wait --timeout 10m
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version 4.15.1 \
  -n ingress-nginx --create-namespace -f kubernetes/addons/ingress-nginx-values.yaml --wait --timeout 10m
helm upgrade --install argocd argo/argo-cd --version 10.9.6 \
  -n argocd --create-namespace -f gitops/argocd/argocd-values.yaml --wait --timeout 10m

# Bootstrap (README 12.2)
kubectl apply -f kubernetes/00-namespace.yaml
kubectl -n clinicdesk create secret generic clinicdesk-db \
  --from-literal=username=clinicdesk --from-literal=password="$(openssl rand -base64 24)"
kubectl apply -f monitoring/grafana-dashboard-clinicdesk.yaml
kubectl apply -f gitops/argocd/clinicdesk-application.yaml

# Wait for Synced / Healthy, then seed a demo day through the load balancer
kubectl -n argocd get application clinicdesk -w
LB=$(kubectl -n ingress-nginx get svc ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
BASE_URL=http://$LB application/scripts/seed-demo.sh "$(TZ=Asia/Kolkata date +%F)"
```

UIs for the recording (one terminal tab each):

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443                         # http://localhost:8080 (server.insecure)
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090  # http://localhost:9090/targets
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80       # http://localhost:3001 (admin / $GF_PASS)
```

### 1. Slides (about 5 minutes)

Present `clinicdesk-presentation.pptx`. The speaker notes hold the talking points.

### 2. Codebase

Show the repository layout (README section 1), then:

- `application/backend/app/routers/appointments.py`: booking and the 409 clash check
- `application/backend/alembic/versions/0001_clinic_schema.py` and `tests/conftest.py` (SQLite test database)
- `application/backend/Dockerfile` and `application/frontend/Dockerfile`: multi-stage, non-root
- `helm/clinicdesk/`, `terraform/main.tf`, `gitops/values-eks.yaml`, `.github/workflows/final-devops-project.yml`

### 3. CI/CD: trigger a push

Make a small visible change (for example the footer text in `application/frontend/src/App.jsx`, or the version in `application/backend/app/config.py`), then:

```bash
git add -A && git commit -m "ClinicDesk: <describe the visible change>" && git push
```

Open the Actions tab and follow the run through the security gate to the push to GHCR and the GitOps promote commit. Show the new `:<sha>` tags on the GHCR package page.

### 4. Terraform

Play clip T1 (the `terraform plan` recorded before apply). Then show the AWS console in Mumbai (`ap-south-1`): **VPC → Your VPCs** (`clinicdesk` VPC, 2 public + 2 private subnets) and **EKS → Clusters → clinicdesk-eks** (Active, node group `general`).

### 5. Argo CD

At `http://localhost:8080`: the `clinicdesk` application is Synced and Healthy. Within about a minute of the promote commit from step 3, the revision changes and the Deployments roll to the new SHA:

```bash
kubectl -n argocd get application clinicdesk -o wide
kubectl -n clinicdesk get deploy -o custom-columns='DEPLOYMENT:.metadata.name,IMAGE:.spec.template.spec.containers[0].image'
```

Reload the app through the load balancer to show the change is live.

### 6. Kubernetes

```bash
kubectl -n clinicdesk get pods -o wide
kubectl -n clinicdesk get svc,ingress,hpa
helm list -A
```

### 7. Prometheus

`http://localhost:9090/targets`, filter `clinicdesk`: backend targets `UP`. Start load first so the next step has data:

```bash
BASE_URL=http://$LB CONCURRENCY=30 DURATION=240 application/scripts/load-test.sh
```

### 8. Grafana

`http://localhost:3001` → dashboard **ClinicDesk API**: requests per second, latency, and HPA replicas climbing under the load test.

### Screenshots to save while the cluster is up

GRADING.md M7 and M8 ask for these as images. The README already has the same output as text. Save them into `../screenshots/`:

| File | Capture |
| --- | --- |
| `22-kubectl-get-pods.png` | `kubectl -n clinicdesk get pods -o wide`, all `Running` |
| `23-kubectl-get-svc.png` | `kubectl -n clinicdesk get svc,ingress` |
| `24-helm-list.png` | `helm list -A` |
| `25-aws-console-vpc.png` | VPC console: the `clinicdesk` VPC and its four subnets |

### 9. After recording: tear down (README "Cleanup")

```bash
kubectl -n argocd delete application clinicdesk --wait=true --timeout=180s
kubectl -n clinicdesk delete pvc --all --wait=true --timeout=180s
helm uninstall ingress-nginx -n ingress-nginx --wait --timeout 5m
helm uninstall argocd -n argocd --wait --timeout 5m
helm uninstall kube-prometheus-stack -n monitoring --wait --timeout 5m
kubectl delete namespace clinicdesk ingress-nginx argocd monitoring --wait=true --timeout=300s
cd terraform && terraform destroy -input=false -auto-approve
aws eks list-clusters --region ap-south-1
```

### Exporting the video

GitHub rejects files over 100 MB. Compress before committing:

```bash
ffmpeg -i recording.mov -vf scale=-2:1080 -c:v libx264 -crf 28 -preset slow -c:a aac -b:a 96k demo/clinicdesk-walkthrough.mp4
```

If it is still over 100 MB, attach it to a GitHub release instead (assets up to 2 GB) and link it from this file. GRADING.md allows either.
