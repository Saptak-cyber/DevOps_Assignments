# Screenshots — Kubernetes Ingress, ConfigMaps & Secrets

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-configmap.png` | ConfigMap Creation |
| `02-secret-decode.png` | Secret Decoding |
| `03-base64-gotcha.png` | Base64 Newline Gotcha |
| `04-volume-mount.png` | Config Volume Mount |
| `05-ingress-controller.png` | Ingress Controller |
| `06-ingress-routing.png` | Ingress Routing |
| `07-ingress-tls.png` | Ingress TLS |
| `09-ingress-no-controller.png` | Task 9 before: `kubectl get ingressclass` (none), Ingress with empty `ADDRESS`, curl exit 56 |
| `09-ingress-with-controller.png` | Task 9 after: ingress-nginx pods, Ingress `ADDRESS localhost`, curl `/api` and `/` through the controller |
| `10-troubleshooting-before.png` | Task 10 before: `password authentication failed` logs + `11 bytes` + `xxd` showing the trailing `0a` |
| `10-troubleshooting-after.png` | Task 10 after: fixed Secret, `rollout restart`, `od -c` without `\n`, `connected as yatri_admin` |

Every command needed is in the README, in the task that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).
