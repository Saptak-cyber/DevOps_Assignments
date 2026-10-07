# Screenshots — Kubernetes Troubleshooting

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-commands.png` | Task 1: `kubectl get pods -o wide`, `kubectl describe pod describe-demo` (Events), `kubectl logs logs-demo`, `kubectl exec exec-demo -- curl localhost`, `kubectl events --for pod/events-demo`, `kubectl top pods` |
| `02-crashloopbackoff.png` | `kubectl get pod crash-demo -w` cycling Error/CrashLoopBackOff, `kubectl logs crash-demo`, then `1/1 Running` after the fix |
| `03-imagepullbackoff.png` | `kubectl describe pod image-demo` Events (`not found`), then `1/1 Running` after `kubectl apply -f fixed-pod.yaml` |
| `04-errimagepull.png` | `ErrImagePull` status + `pull access denied, repository does not exist` event + the two `crictl pull` results |
| `05-pending.png` | `FailedScheduling` events for both pending pods (selector and `Insufficient cpu/memory`) and the fixed pods Running |
| `06-containercreating.png` | `ContainerCreating` with `FailedMount ... not found` events, then Running after `kubectl apply -f fix-missing-objects.yaml` |
| `07-service-connectivity.png` | `kubectl get endpoints web-service` = `<none>`, `kubectl describe svc` selector, then endpoints + `HTTP 200` |
| `08-dns.png` | `nslookup` NXDOMAIN for the wrong name vs success for `postgres-db.production...`, and the CoreDNS-at-0 timeout |
| `09-pod-networking.png` | curl timeout (exit 28), `kubectl describe networkpolicy web-deny-all-ingress`, then `HTTP 200` after the allow policy |
| `10-configuration.png` | `[FATAL ERROR]: DATABASE_URL ... MISSING!` log and `CreateContainerConfigError` event, then the fixed pods |
| `11-mini-broken-pod.png` | Mini project: `kubectl get pod project-broken-pod` (ImagePullBackOff) and `kubectl describe` Events |
| `12-mini-service-selector.png` | Mini project: endpoints `<none>`, `--show-labels` vs `Selector: app=wrong-app`, then endpoints restored |

Every command needed is in the README, in the section that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).
