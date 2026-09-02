# DevOps Class Assignments

Solutions for the seven homework topics from the DevOps course, one folder per topic.
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

## Environment

| | |
|---|---|
| Host | macOS (Darwin 25.5.0, arm64) |
| Docker | Docker Desktop, engine 29.6.1 |
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
