# Screenshot capture checklist — Monitoring, Observability & GitOps

The README references these filenames. The browser screenshots (marked **captured**) were taken during the run with headless
Chromium and are already in this folder. The terminal ones still need capturing: re-run the commands from the README section
that references each file and save the screenshot here with the exact name, and the images will render on GitHub.

| File | Status | What to capture |
| --- | --- | --- |
| `01-kps-pods.png` | to capture | Task 1.1: `helm list -n monitoring` and `kubectl get pods -n monitoring` (all 6 kube-prometheus-stack pods Running) |
| `02-promql-cpu-memory.png` | to capture | Task 1.3: the `up` query and the node/pod CPU and memory `q '...'` queries |
| `03-grafana-node-exporter.png` | **captured** | Task 1.7: Grafana *Node Exporter / Nodes* dashboard (node CPU, load, memory 42.3 %, disk) |
| `04-grafana-namespace-pods.png` | **captured** | Task 1.7: Grafana *Kubernetes / Compute Resources / Namespace (Pods)* for `default`, with `cpu-burner` at 0.5 cores and `memory-hog` at 54.8 MiB |
| `05-prometheus-alerts-firing.png` | **captured** | Task 1.5: Prometheus *Alerts* page filtered on `Session20`, all four rules FIRING |
| `06-alertmanager-alerts.png` | **captured** | Task 1.5: Alertmanager UI, `namespace="default"` group with 5 active alerts |
| `07-logs-and-health.png` | to capture | Task 1.4/1.6: `kubectl logs deployment/session20-demo`, the probe lines from `kubectl describe pod`, and the `up` / `kube_pod_status_ready` queries |
| `08-jaeger-hotrod-trace.png` | **captured** | Task 2: Jaeger trace view of HotROD `GET /dispatch` (789 ms, 6 services, 40 spans, 3 failed Redis spans) |
| `09-argocd-synced-2-replicas.png` | **captured** | Mini Project Step 5: Argo CD UI, `session20-mini` Synced + Healthy with 2 Pods |
| `10-argocd-synced-3-replicas.png` | **captured** | Mini Project Step 7: Argo CD UI, Synced to `25ac5d3` with 3 Pods |
| `11-gitops-rollout-terminal.png` | to capture | Mini Project Step 7: `git push` of the replicas change and `kubectl get deployment -n session20 -w` reaching `3/3` |
| `12-selfheal-terminal.png` | to capture | Mini Project Step 8: `kubectl scale ... --replicas=1` followed by `kubectl get deployment -n session20` back at `3/3` |
| `13-argocd-diff-terminal.png` | to capture | Mini Project Extra: `kubectl get application` showing `OutOfSync` and `argocd app diff session20-mini` (`replicas: 1` vs `3`) |

The kind cluster was deleted after the run. To recapture the terminal shots, recreate it with Step 1/1.1, reinstall with the
values file and the manifests in `monitoring/` and `gitops/`, and re-run the commands.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line). Browser screenshots of Grafana, Prometheus, Argo CD and the app were taken live while the clusters were running.
