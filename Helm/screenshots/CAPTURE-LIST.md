# Screenshots — Helm

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-helm-commands.png` | Task 1: `helm install demo ./my-chart`, `helm list`, `helm status demo`, `helm history demo` after the upgrades and `helm rollback demo 1` |
| `02-helm-repo-search.png` | Task 1: `helm repo add bitnami ...`, `helm repo list`, `helm search repo bitnami/nginx`, `helm search hub nginx` |
| `03-helm-rollback.png` | Task 2: `helm history rollback-demo` after the rollback (revisions 1–4) and the 3 `nginx:1.24` pods |
| `04-helm-auto-rollback.png` | Task 2 extra: the `--rollback-on-failure` error and `helm history` showing `failed` + `Rollback to 4` |
| `05-notes-install.png` | Mini project: `helm install notes-dev notes-chart` + `kubectl get pods,svc,cm` |
| `06-notes-bad-upgrade.png` | Mini project: `ImagePullBackOff` pod while `helm status` says `deployed` |
| `07-notes-rollback.png` | Mini project: `helm rollback notes-dev 2`, `helm history notes-dev`, three Running pods |

Every command needed is in the README, in the section that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).
