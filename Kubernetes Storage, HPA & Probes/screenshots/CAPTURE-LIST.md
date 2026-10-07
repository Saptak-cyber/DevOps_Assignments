# Screenshots — Kubernetes Storage, HPA & Probes

The README references these filenames, and every one of them is in this folder.

| File | Referenced in | What it shows |
| --- | --- | --- |
| `01-emptydir.png` | `01-kubernetes-volumes/README.md` §1 | emptyDir: file survives `kill 1` (RESTARTS 1) but is gone after Pod delete/recreate |
| `02-hostpath.png` | `01-kubernetes-volumes/README.md` §2 | hostPath: `minikube ssh -- cat /tmp/hostpath-data/host.txt` and the file surviving Pod deletion |
| `03-static-pv-pvc.png` | `01-kubernetes-volumes/README.md` §3 | `kubectl get pv,pvc` showing the default-class gotcha, then `student-pvc Bound student-pv`, then `Released` |
| `04-storageclass.png` | `01-kubernetes-volumes/README.md` §4 | `kubectl get sc` with both classes + the `ProvisioningFailed ... nodes is forbidden` event and the Bound result after the RBAC fix |
| `05-dynamic-provisioning.png` | `01-kubernetes-volumes/README.md` §5 | `kubectl get pvc,pv` after applying `dynamic-pvc.yaml` (auto-created `pvc-<uid>` PV) |
| `06-hpa-created.png` | `README.md` Task 2 | `kubectl get hpa` showing `cpu: 1%/50%` and `kubectl describe hpa hpa-demo` |
| `07-hpa-scale-out.png` | `README.md` Task 2 | `kubectl get hpa` at 5 replicas + `kubectl top pods` + `kubectl get pods` under load |
| `08-hpa-scale-down.png` | `README.md` Task 2 | `kubectl get hpa` back at 1 replica + `SuccessfulRescale ... New size: 1` event |
| `09-mini-deploy.png` | `README.md` Task 3 | `kubectl get all -n production-webapp` and `kubectl get pvc -n production-webapp` |
| `10-mini-storage.png` | `README.md` Task 3 | `cat /data/student.txt` from a new Pod after delete / scale-to-zero |
| `11-mini-service.png` | `README.md` Task 3 | port-forward + `curl http://localhost:8080` returning the nginx page |
| `12-mini-hpa.png` | `README.md` Task 3 | `kubectl get hpa -n production-webapp -w` going 2 → 5 and back to 2 |
| `13-mini-bonus-probes.png` | `README.md` Task 3 | bonus: `0/1 Running` with empty endpoints (readiness) and `CrashLoopBackOff` restarts (liveness) |

Every command needed is in the README that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).
