# Screenshot list — Docker Networking & Volumes (Session 8)

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-connectivity-tests.png` | Task 1.4: backend → frontend and backend → database succeed, frontend → database fails, DNS resolution, MySQL port check |
| `02-network-membership.png` | Task 1.5: `docker network inspect` membership, the backend on two networks |
| `03-bind-mount-before.png` | Task 3.3: browser at `http://localhost:8090` showing **Hello students** from the bind-mounted folder |
| `04-bind-mount-after-edit.png` | Task 3.4: the same page after `index.html` was edited on the host, with no container restart |
| `05-host-network-verify.png` | Task 2.3: Apache started with `--network host` and checked over HTTP |
| `06-host-network-namespace.png` | Task 2.4: proof the container shares the host's network namespace |
| `07-overlay-swarm-demo.png` | Task 4.3: overlay network on a real single-node swarm, VIP vs `tasks.<service>` DNS |

## How these screenshots were produced

`03` and `04` are live browser captures (Playwright) of the bind-mount demo re-run on 2026-10-07:
the page was captured, `index.html` was edited on the host, and the page was reloaded; the
container's `StartedAt` time was identical before and after. The others are renderings of the
real command output already captured in this README.
