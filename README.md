# DevOps Class Assignments

Solutions for all 21 sessions of the DevOps course homework (sessions 1 and 2 share one folder),
one folder per topic.
Each folder contains a `README.md` with the write-up, real captured command output, and
runnable code where applicable.

| # | Folder | Topic | Code included |
|---|---|---|---|
| 1 | [Task1-Linux-Fundamentals](Task1-Linux-Fundamentals/) | Soft/hard links, `adduser` vs `useradd`, `journalctl`, command cheat sheet | `link-demo.sh` |
| 2 | [Task2-Shell-Scripting](Task2-Shell-Scripting/) | System information script | `system-info.sh` |
| 3 | [Task3-Networking-Fundamentals](Task3-Networking-Fundamentals/) | `ip`, `ping`, `dig`, `ss`, `curl`, `traceroute` with explanations | `network-commands.sh` |
| 4 | [Task4-Git-GitHub](Task4-Git-GitHub/) | `git commit -a -m` vs `-m`; cherry-pick | `git-cherry-pick-demo.sh` |
| 5 | [Task5-Docker-Fundamentals](Task5-Docker-Fundamentals/) | Six Hello World apps: Node, Python, Java, Apache, React, Nginx | 6 apps + Dockerfiles, `build-and-run-all.sh` |
| 6 | [Task6-Dockerfiles-And-Images](Task6-Dockerfiles-And-Images/) | Multi-stage build on port 8080 + 3 deployed applications | `multi-stage-app/`, `deployments/` |
| 7 | [Task7-Docker-Networking](Task7-Docker-Networking/) | 3-network isolation, host network, bind mount, overlay network | 4 setup scripts |
| 8 | [Kubernetes Fundamentals](Kubernetes%20Fundamentals/) | Minikube + kubectl install, cluster lifecycle (start/status/stop), control-plane & worker architecture, basic objects, Kubernetes Basics tutorial (modules 1–6) | CLI + architecture |
| 9 | [Kubernetes Pods, ReplicaSets & Deployments](Kubernetes%20Pods,%20ReplicaSets%20&%20Deployments/) | 14 tasks: all 12 Pod lifecycle states, ReplicaSet self-healing, StatefulSet, DaemonSet, rollout/rollback, 4 deployment strategies measured, troubleshooting drills | 45+ manifests |
| 10 | [Kubernetes Networking & Services](Kubernetes%20Networking%20&%20Services/) | 12 tasks: the 4 ports, all 5 Service types, CoreDNS/FQDN with `ndots` cost measured, no-selector Services, Deployment vs StatefulSet identity, LB cost analysis, object comparisons; [`fqdn/`](Kubernetes%20Networking%20&%20Services/fqdn/) and [`coredns/`](Kubernetes%20Networking%20&%20Services/coredns/) READMEs | 25+ manifests |
| 11 | [Kubernetes Ingress, ConfigMaps & Secrets](Kubernetes%20Ingress,%20ConfigMaps%20&%20Secrets/) | 8 tasks: ConfigMaps, Secrets and the base64 newline bug, env vs volume live-update, ingress-nginx host/path routing, TLS termination, Ingress vs Ingress Controller, Secret troubleshooting before/after | 15+ manifests |
| 12 | [Kubernetes Storage, HPA & Probes](Kubernetes%20Storage,%20HPA%20&%20Probes/) | Session 13: emptyDir/hostPath/PV/PVC/StorageClass/dynamic provisioning, HPA scale-out and scale-down under load, mini project (PVC + HPA + probes) incl. bonus challenges | volume manifests, HPA + load generator, `mini-project/` |
| 13 | [Kubernetes Troubleshooting](Kubernetes%20Troubleshooting/) | Session 14: the 8 core `kubectl` commands; 9 failure types each broken → investigated → root cause → fixed → verified; mini project with questions and table | 40+ broken/fixed manifests |
| 14 | [Helm](Helm/) | Session 15: every listed `helm` command, install → upgrade → upgrade → rollback workflow, notes-chart mini project | 3 charts |
| 15 | [CI-CD & GitHub Actions](CI-CD%20&%20GitHub%20Actions/) | Session 16: CI/CD demo — matrix test, artifacts, GHCR push, deploy to kind in the runner; green and deliberately red runs | app, Dockerfile, [`s16-cicd.yml`](.github/workflows/s16-cicd.yml) |
| 16 | [Complete CI-CD & DevSecOps](Complete%20CI-CD%20&%20DevSecOps/) | Session 17: Build → Test → SAST → SCA → secret scan → image build → image scan → security gate → push → deploy; gate shown blocking a vulnerable dependency | app, scanner configs, gate policy, [`s17-devsecops.yml`](.github/workflows/s17-devsecops.yml) |
| 17 | [Terraform & Infrastructure as Code](Terraform%20&%20Infrastructure%20as%20Code/) | Session 18: S3 bucket on real AWS (init → destroy), research READMEs for IAM, EC2, S3, VPC, DynamoDB & RDS | `terraform-s3-demo/`, `aws-services/` |
| 18 | [Cloud & Terraform in Action](Cloud%20&%20Terraform%20in%20Action/) | Session 19: VPC + subnet + IGW + SG + EC2 (nginx) + S3 on real AWS, dependencies, state, plan/apply/destroy | Terraform project |
| 19 | [Monitoring, Observability & GitOps](Monitoring,%20Observability%20&%20GitOps/) | Session 20: kube-prometheus-stack metrics/alerts/Grafana, Jaeger trace demo, Argo CD GitOps mini project (Git change → sync, self-heal) | monitoring values, alert rules, `gitops/` |
| 20 | [final-devops-project](final-devops-project/) | Session 21: ClinicDesk (FastAPI + React + PostgreSQL) through CI, DevSecOps, GHCR, Terraform-provisioned EKS, Helm, Ingress, HPA, Prometheus/Grafana, Argo CD GitOps, troubleshooting challenge | full project, [`final-devops-project.yml`](.github/workflows/final-devops-project.yml) |

## Verification status

Everything documented here was actually executed. Highlights:

* **Task 1** — link demo run; inode numbers and link counts in the README are from the
  real run.
* **Task 2** — script executed inside `ubuntu:22.04` so the captured output is genuine
  Linux output, not macOS.
* **Task 3** — every networking command run inside `ubuntu:22.04` with `iproute2`,
  `dnsutils`, `net-tools`, `traceroute` and `nginx` installed.
* **Task 4** — the full git history, branch, cherry-pick and resulting commit graph are
  from a real repository.
* **Task 5** — all six images built; all six containers ran and returned HTTP 200 with
  the Hello World content, and each page is shown rendered in a browser screenshot.
* **Task 6** — multi-stage image built (286 MB) and compared against the single-stage
  equivalent (555 MB); the absence of `javac` and of the source in the final image was
  verified by inspecting both images. All three deployment apps built, ran and answered
  their API endpoints.
* **Task 7** — three networks and three containers created with connectivity tests
  (including the expected failure); Apache run on `--network host`; bind mount edited live
  without a restart; a real single-node swarm created with an overlay network showing VIP
  vs `tasks.<service>` DNS.
* **Kubernetes Fundamentals** — minikube v1.39.0 installed and the full cluster lifecycle
  captured live: `minikube version`, `start`, `status`, `kubectl get nodes -o wide`,
  `cluster-info`, `stop`. The control-plane components in the architecture write-up are
  cross-checked against the real `kube-system` Pods on the running cluster.
* **Pods, ReplicaSets & Deployments** — all 12 lifecycle manifests executed; CrashLoopBackOff
  backoff growth captured at 4s → 12s → 29s; a liveness probe restart observed; ReplicaSet
  self-healing timed at ~1s; StatefulSet ordinal startup and PVC re-attachment verified; and
  each deployment strategy **measured** — rolling 119/120 requests served, canary 14% at a 9:1
  pod ratio and 27% at 7:3, Recreate producing 13 consecutive failed requests.
* **Networking & Services** — all five Service types deployed; ClusterIP load balancing
  confirmed from per-Pod access logs; a NodePort answered from both nodes including the one
  running no Pod; `LoadBalancer` captured moving from `<pending>` to an external IP under
  `minikube tunnel`; headless DNS returning all three Pod IPs; and the `ndots:5` search-domain
  cost measured at CoreDNS as **120 queries vs 40** for 20 lookups.
* **Ingress, ConfigMaps & Secrets** — ingress-nginx v1.15.1 enabled; ConfigMap/Secret injection
  verified inside a running Pod; the env-var vs volume live-update difference measured across a
  kubelet sync (env stayed `INFO`, the mounted file became `DEBUG`); Secrets shown mounted on
  **tmpfs**; the trailing-newline base64 bug reproduced down to the `0a` byte in a hexdump; and
  host + path routing plus TLS termination verified end to end.
* **Storage, HPA & Probes** — PV/PVC binding gotchas on minikube found and fixed
  (`storageClassName: ""`, provisioner RBAC); HPA scaled 1 → 5 under load and back to 1 exactly
  after the 5-minute stabilization window; mini-project data survived Pod deletion.
* **Kubernetes Troubleshooting** — nine failure types reproduced and fixed with before/after
  output; the class `dnsutils:1.3` image turned out to no longer exist and was replaced.
* **Helm** — Helm v4.3.0; every listed command run, including install from the real bitnami repo;
  the mini-project's bad upgrade shown silently resetting prod values until rolled back.
* **CI/CD & DevSecOps** — both pipelines green on GitHub Actions, images pushed to GHCR with
  commit-SHA tags and deployed to kind inside the runner; the security gate shown blocking a
  run with a vulnerable `cryptography` pin (push and deploy skipped).
* **Terraform (Sessions 18–19)** — applied on a real AWS account in `ap-south-1`, verified with the
  AWS CLI (and `curl` to the EC2 nginx page), then destroyed; a final CLI sweep found nothing left.
* **Monitoring, Observability & GitOps** — PromQL CPU/memory queries, four custom alerts driven to
  *firing*, Grafana API queries, a Jaeger HotROD trace; Argo CD synced a Git change of
  replicas 2 → 3 and reverted a manual `kubectl scale` (self-heal).
* **Final project (ClinicDesk)** — 10-job pipeline (tests, SAST, SCA, secret scan, image scan,
  security gate, GHCR push, kind smoke test, GitOps tag bump) green on GitHub; Terraform-provisioned
  EKS (61 resources, ~70 min uptime) running the Helm chart behind an NLB, HPA scaling 2 → 5,
  Prometheus/Grafana scraping the backend, Argo CD rolling commit `dbbdd49` onto the cluster;
  seven troubleshooting issues fixed on EKS; then fully destroyed.

## Environment

| | |
|---|---|
| Host | macOS (Darwin 25.5.0, arm64) |
| Docker | Docker Desktop, engine 29.6.1 |
| Kubernetes | minikube v1.39.0 (docker driver), Kubernetes v1.37.0, containerd 2.3.4, 2 nodes |
| Ingress | ingress-nginx v1.15.1 (`minikube addons enable ingress`) |
| Linux outputs | captured inside `ubuntu:22.04` containers |
| Git | 2.x |
| Helm / Terraform | Helm v4.3.0, Terraform 1.16, AWS provider 6.x |
| Cloud | AWS `ap-south-1` (Sessions 18, 19, 21) — all resources destroyed after verification |
| CI | GitHub Actions on this repository; workflows in [`.github/workflows/`](.github/workflows/) |

Where a command is Linux-only (`journalctl`, `adduser`, `useradd`, and `--network host`
reaching the laptop's own `localhost`), the README says so explicitly. `adduser`/`useradd` were
run in `ubuntu:22.04` and `journalctl` on a systemd node, so those outputs are real as well.

## Note on commit SHAs

On 2026-10-07 the commit history was rewritten to edit commit messages only; every file is
byte-for-byte unchanged. That gave the affected commits new SHAs. The READMEs, the GitHub
Actions runs and the GHCR image tags (which are the commit SHA a pipeline ran on) still show
the **original** SHAs. This table maps each original SHA cited in this repository to its
current commit on `main`:

| Original SHA (as cited) | Current commit | Commit |
|---|---|---|
| `709944b` | [`c27eced`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/c27eced51476eb3b49969b403b9947e383157619) | Session 16: add CI/CD demo project and GitHub Actions workflow |
| `82b3858` | [`0dd4be0`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/0dd4be02dcd0c12f85ac481440695c6c7c2edf52) | Session 17: add DevSecOps demo project and pipeline |
| `eca9956` | [`1a689c6`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/1a689c6a7c7da43f7084896cad57ec045d9427a1) | Session 16: bump pytest to 9.1.1, skip pipeline on docs-only changes |
| `1bbe4d1` | [`841e763`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/841e7636323eb60662ce25a107148ad9c59d8638) | Session 17: skip the DevSecOps pipeline on docs-only changes |
| `79c12eb` | [`b76feab`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/b76feab303593a0479ce66eed971c7f1103f4f8a) | Session 16: skip reverse-DNS in HTTP server bind (35 s macOS test stall) |
| `e664e8a` | [`8403600`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/8403600dde7ab7a39e63b84ebcc24a544b477d10) | Final project README (Phase 1 evidence) and UI screenshots |
| `1c0ef7b` | [`9a95e74`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/9a95e74744658ae4bae56bb8879df202850423b9) | Helm/Argo CD: make the Postgres StatefulSet compare equal so the app reports Synced |
| `b7d8743` | [`2f78678`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/2f786783e2a895c2ea446898766cfcef25a56c28) | gitops(clinicdesk): promote 1c0ef7b to EKS [skip ci] |
| `dbbdd49` | [`e8f9059`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/e8f9059b0166755f1a62327b27eaba6f5d25c059) | ClinicDesk 1.1.0: show front-desk opening hours in the footer |
| `2f649de` | [`ecf3097`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/ecf3097122d3f9c1d5a84b2761fd65b1148daf12) | gitops(clinicdesk): promote dbbdd49 to EKS [skip ci] |
| `7a58acc` | [`77a1ea0`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/77a1ea060c6eb8eef9282e27e4e443c788859ffe) | Session 20: GitOps source manifests for the Argo CD mini project |
| `25ac5d3` | [`facfa35`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/facfa35866419dc7b78cb990b636ef1454267455) | Session 20 mini project: scale application to three replicas |
| `b1bc8d3` | [`6ccd527`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/6ccd527e27d34f8ae177eb78b99077b198ec4ea6) | Final project README: EKS deployment, CI/CD, DevSecOps, monitoring, GitOps demo and troubleshooting evidence |
| `8d6553a` | [`bbcfc97`](https://github.com/Saptak-cyber/DevOps_Assignments/commit/bbcfc97f553f497ac2e220302d60ed3759eac732) | Security: allowlist a reviewed gitleaks false positive in README history |

## Running everything

```bash
# Task 1
bash Task1-Linux-Fundamentals/link-demo.sh

# Task 2
bash Task2-Shell-Scripting/system-info.sh

# Task 3
bash Task3-Networking-Fundamentals/network-commands.sh docker

# Task 4
bash Task4-Git-GitHub/git-cherry-pick-demo.sh

# Task 5
cd Task5-Docker-Fundamentals && ./build-and-run-all.sh && cd ..

# Task 6
cd Task6-Dockerfiles-And-Images/multi-stage-app
docker build -t multistage-app . && docker run -d --name multistage-container -p 8080:8080 multistage-app
cd ../deployments && docker compose up -d --build && cd ../..

# Task 7
cd Task7-Docker-Networking
./task1-container-networking/setup.sh
./task2-host-network/setup.sh
./task3-bind-mount/setup.sh
./task4-overlay-network/demo.sh
cd ..
```

Each Docker task's script accepts a `clean` argument to tear its resources down.

### The four Kubernetes tasks

They share one cluster, so build it once. A second node is added on purpose — the DaemonSet
task needs more than one node to show *one Pod per node*:

```bash
minikube start
minikube node add
kubectl wait --for=condition=Ready nodes --all --timeout=180s
```

Only "Kubernetes Ingress, ConfigMaps & Secrets" needs the ingress controller:

```bash
minikube addons enable ingress
kubectl wait -n ingress-nginx --for=condition=ready pod \
  -l app.kubernetes.io/component=controller --timeout=300s
```

Then work through each task's README; every lab is `kubectl apply -f <folder>` and each README
ends with its own cleanup block.

> **On macOS/Windows with the Docker driver, `curl $(minikube ip):<nodePort>` will time out.**
> That is a host-to-container routing limitation, not a broken manifest — use
> `minikube service <svc> --url` instead. Explained in full in
> [Kubernetes Networking & Services](Kubernetes%20Networking%20&%20Services/) Task 12.

To remove everything at once:

```bash
minikube delete
```
