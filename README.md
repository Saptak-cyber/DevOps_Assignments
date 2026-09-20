# DevOps Class Assignments

Solutions for the eleven homework topics from the DevOps course, one folder per topic.
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
| 8 | [Kubernetes Fundamentals](Kubernetes%20Fundamentals/) | Minikube + kubectl install, cluster lifecycle (start/status/stop), control-plane & worker architecture | no manifests (CLI + architecture) |
| 9 | [Kubernetes Pods, ReplicaSets & Deployments](Kubernetes%20Pods,%20ReplicaSets%20&%20Deployments/) | 14 tasks: all 12 Pod lifecycle states, ReplicaSet self-healing, StatefulSet, DaemonSet, rollout/rollback, 4 deployment strategies measured, troubleshooting drills | 45+ manifests |
| 10 | [Kubernetes Networking & Services](Kubernetes%20Networking%20&%20Services/) | 12 tasks: the 4 ports, all 5 Service types, CoreDNS/FQDN with `ndots` cost measured, no-selector Services, Deployment vs StatefulSet identity, LB cost analysis | 25+ manifests |
| 11 | [Kubernetes Ingress, ConfigMaps & Secrets](Kubernetes%20Ingress,%20ConfigMaps%20&%20Secrets/) | 8 tasks: ConfigMaps, Secrets and the base64 newline bug, env vs volume live-update, ingress-nginx host/path routing, TLS termination | 15+ manifests |

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
  the Hello World content. React verified with a browser screenshot.
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

## Environment

| | |
|---|---|
| Host | macOS (Darwin 25.5.0, arm64) |
| Docker | Docker Desktop, engine 29.6.1 |
| Kubernetes | minikube v1.39.0 (docker driver), Kubernetes v1.37.0, containerd 2.3.4, 2 nodes |
| Ingress | ingress-nginx v1.15.1 (`minikube addons enable ingress`) |
| Linux outputs | captured inside `ubuntu:22.04` containers |
| Git | 2.x |

Where a command is Linux-only (`journalctl`, `adduser`, `useradd`, and `--network host`
reaching the laptop's own `localhost`), the README says so explicitly and shows the
expected Ubuntu output alongside a note on how to reproduce it.

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
