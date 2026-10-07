# Screenshots — Linux Fundamentals

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-adduser-real-run.png` | Sub-task 2.4 real run: `adduser devopsuser` in `ubuntu:22.04`, then `id`, `grep /etc/passwd`, `ls -la /home/devopsuser`, and the `useradd testraw` contrast |
| `01-journalctl-real-run.png` | Sub-task 3.3 real run: `journalctl -u demo-app`, and `systemctl status broken-app` + `journalctl -xeu broken-app` showing the failure reason |

Every command needed is in the README, in the sub-task that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).
