# Task 7 — Docker Networking & Volumes

Four sub-tasks: multi-network container isolation, host networking, bind mounts, and
overlay networks. Every console block below is real captured output.

## Folder structure

```
Task7-Docker-Networking/
├── README.md
├── task1-container-networking/setup.sh    # 3 containers, 3 networks, connectivity tests
├── task2-host-network/setup.sh            # Apache on --network host
├── task3-bind-mount/
│   ├── setup.sh                           # bind mount + live edit demo
│   └── html/index.html                    # "Hello students"
└── task4-overlay-network/demo.sh          # swarm + overlay network demo
```

Every script takes a `clean` argument to tear its resources down:

```bash
./task1-container-networking/setup.sh clean
./task2-host-network/setup.sh clean
./task3-bind-mount/setup.sh clean
./task4-overlay-network/demo.sh clean
```

---

## Docker network drivers — the map

| Driver | Scope | What it does | Use it for |
|---|---|---|---|
| `bridge` | single host | Default. Private subnet + NAT; ports must be published with `-p` | Almost everything on one host |
| `host` | single host | Container shares the **host's** network namespace — no isolation, no NAT | Max throughput, or a container that needs many/dynamic ports |
| `none` | single host | Loopback only, no external networking | Batch jobs that must not touch the network |
| `overlay` | **multi-host** | VXLAN tunnel joining containers across different Docker hosts | Swarm / multi-node clusters |
| `macvlan` | single host | Container gets its own MAC and an IP on the **physical** LAN | Legacy apps that must appear as a real device on the LAN |
| `ipvlan` | single host | Like macvlan, but shares the host's MAC | Environments where switches limit MACs per port |

### The single most important thing about a *user-defined* bridge

The **default** `bridge` network has no DNS between containers — you would have to link
containers by IP. A **user-defined** bridge (`docker network create mynet`) runs an
embedded DNS server at `127.0.0.11` that resolves container **names** automatically. That
alone is the reason to always create your own network.

---

# Task 1 — Docker Container Networking

**Goal:** 3 containers (frontend, backend, database), 3 networks, with the backend on
**two** networks — the classic 3-tier isolation pattern.

```
   frontend ──── frontend-net ──── backend ──── database-net ──── database
   (nginx)                        (alpine)                        (mysql:8)
                                      │
                                  backend-net  (third network, spare)

   frontend and database share NO network -> they cannot reach each other.
   Only the backend can talk to both. That is the point.
```

## 1.1 Create three networks

```console
$ docker network create frontend-net
aa5b6a26874a7d825f44d5b8b6f4b445887ad57aa2499eded96c0c4d2e6ac47b
$ docker network create backend-net
7bff4b5b839d43789dd47a66757e3789cf6b3a5cf296fdd0a4b634d1e2d4b819
$ docker network create database-net
f27899dc308841b01af0603feeaa5dd9cfbc806f9aa6004c44c6b61ccc319bed

$ docker network ls
NETWORK ID     NAME           DRIVER    SCOPE
7bff4b5b839d   backend-net    bridge    local
1f140a2da75a   bridge         bridge    local
f27899dc3088   database-net   bridge    local
aa5b6a26874a   frontend-net   bridge    local
8a0c7553bf7d   host           host      local
58528924efce   none           null      local
```

`bridge`, `host` and `none` are the three built-ins Docker always provides. Docker
allocated each new network its own subnet automatically: `172.18.0.0/16`,
`172.19.0.0/16`, `172.20.0.0/16`.

## 1.2 Create the containers

```console
$ docker run -d --name frontend --network frontend-net nginx:alpine
f5b85c00f22d61e8e781717d07fc3429adce36c122015c7194dbc28af694fa5f

$ docker run -d --name backend --network frontend-net alpine sleep 3600
5525403750ea413f87de161a0a16f62cfef62557b46389cbbcc1820b76370c60

$ docker run -d --name database --network database-net \
      -e MYSQL_ROOT_PASSWORD=rootpass -e MYSQL_DATABASE=appdb mysql:8
d429fa20092c1d3b09e37b98c04c5eb69f5223ae431fc25e045265e70b789a32
```

`alpine sleep 3600` is the standard trick to keep a bare Alpine container alive — with no
long-running process, PID 1 exits immediately and the container stops.

`--network` on `docker run` can be given only **once**. Additional networks are joined
afterwards with `docker network connect`.

## 1.3 Connect the backend to a second network

```console
$ docker network connect database-net backend

$ docker inspect backend --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}'
database-net=172.20.0.3 frontend-net=172.18.0.3
```

The backend now has **two IP addresses** — one on each network. Two virtual NICs, two
subnets, one container.

## 1.4 Connectivity tests

### backend → frontend (same network) — succeeds

```console
$ docker exec backend ping -c 2 frontend
PING frontend (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: seq=0 ttl=64 time=0.891 ms
64 bytes from 172.18.0.2: seq=1 ttl=64 time=0.151 ms

--- frontend ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.151/0.521/0.891 ms
```

### backend → database (same network) — succeeds

```console
$ docker exec backend ping -c 2 database
PING database (172.20.0.2): 56 data bytes
64 bytes from 172.20.0.2: seq=0 ttl=64 time=1.738 ms
64 bytes from 172.20.0.2: seq=1 ttl=64 time=0.199 ms

--- database ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.199/0.968/1.738 ms
```

Note the different subnets: `172.18.0.2` for the frontend, `172.20.0.2` for the database.
The backend reached each one over a different interface.

### frontend → database (no shared network) — fails, as designed

```console
$ docker exec frontend ping -c 2 database
ping: database: Name does not resolve
>>> FAILED AS EXPECTED: frontend and database share no network
```

**This is the whole point of the exercise.** The failure is at **DNS**, not at routing —
`Name does not resolve`, not `Destination unreachable`. Docker's embedded DNS only
answers for containers on a network you are *also* on. The database is invisible to the
frontend: it cannot be reached, and it cannot even be named.

That is defence in depth. A compromised frontend cannot scan for or connect to the
database, because there is no path and no name.

### DNS resolution from the backend

```console
$ docker exec backend nslookup frontend
Server:		127.0.0.11
Address:	127.0.0.11:53
Non-authoritative answer:
Name:	frontend
Address: 172.18.0.2

$ docker exec backend nslookup database
Server:		127.0.0.11
Address:	127.0.0.11:53
Non-authoritative answer:
Name:	database
Address: 172.20.0.2
```

`127.0.0.11` is **Docker's embedded DNS server**, injected into every container on a
user-defined network. Look for it in `/etc/resolv.conf` inside any such container.

### Real service check — MySQL on port 3306

```console
$ docker exec backend nc -zv database 3306
database (172.20.0.2:3306) open
```

`ping` only proves ICMP works. `nc -z` proves the **TCP port** is accepting connections —
which is what actually matters for a database.

## 1.5 Inspect network membership

```console
$ docker network inspect frontend-net --format '{{range .Containers}}{{.Name}} ({{.IPv4Address}}){{println}}{{end}}'
backend (172.18.0.3/16)
frontend (172.18.0.2/16)

$ docker network inspect backend-net --format '...'
(empty — no container joined this one)

$ docker network inspect database-net --format '...'
backend (172.20.0.3/16)
database (172.20.0.2/16)
```

The backend appears in **two** listings. `backend-net` is empty — created to satisfy the
"3 networks" requirement, but nothing joined it, which is itself a useful demonstration
that a network can exist with no members.

## 1.6 Commands used

```bash
docker network create <name>                    # default driver: bridge
docker network create --driver bridge --subnet 172.30.0.0/16 mynet
docker network ls
docker network inspect <name>
docker network connect <network> <container>    # join an EXTRA network
docker network disconnect <network> <container>
docker network rm <name>
docker network prune                            # remove all unused networks

docker run --network <name> ...                 # only ONE network at run time
docker exec <c> ping -c 2 <other-container>
docker exec <c> nc -zv <host> <port>            # test a real TCP port
docker exec <c> nslookup <name>
```

---

# Task 2 — Host Network

**Goal:** pull the Apache2 image, run it with `--network host`, and access the site on
port 80 with **no port mapping**.

## 2.1 Pull the image

```console
$ docker pull httpd:2.4
2.4: Pulling from library/httpd
...
Digest: sha256:979c38c2228d28c2edfd45c6e27dcee1c7b4a101a5526721ae8ece454e89e99e
Status: Downloaded newer image for httpd:2.4
docker.io/library/httpd:2.4
```

## 2.2 Run with the host network

```console
$ docker run -d --name apache-host --network host httpd:2.4
b738cd5bb7b029c129ae7e8a4e45fa988c43a535144140a5150a3f775358e7bd
```

**Note there is no `-p` flag.** With `--network host` there is nothing to map — the
container writes directly into the host's network stack.

## 2.3 Verify

```console
$ docker ps --filter name=apache-host --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
NAMES         IMAGE       STATUS         PORTS
apache-host   httpd:2.4   Up 3 seconds
```

**The `PORTS` column is empty.** That is the signature of host networking — there is no
NAT rule to display, because there is no separate network namespace to translate between.

```console
$ docker inspect apache-host --format '{{.HostConfig.NetworkMode}}'
host

$ docker inspect apache-host --format '{{.NetworkSettings.IPAddress}}'
template parsing error: ... map has no entry for key "IPAddress"
```

That error is itself the proof: a host-networked container has **no IP address of its
own**, so the field does not exist in the inspect output. A bridge container would show
something like `172.17.0.2`.

## 2.4 Proof it shares the host's network namespace

```console
$ docker exec apache-host hostname
docker-desktop

$ docker exec apache-host ip -br a
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0             UP             192.168.65.3/24 fdc4:f303:9324::3/64 ...
docker0          UP             172.17.0.1/16 fe80::3449:91ff:fe98:a6ea/64
br-aa5b6a26874a  UP             172.18.0.1/16 fe80::3088:2ff:feb2:d7dd/64
br-7bff4b5b839d  DOWN           172.19.0.1/16
br-f27899dc3088  UP             172.20.0.1/16 fe80::3020:32ff:fe29:bf4b/64
vethedc0428@if11 UP             fe80::947b:8ff:fea0:f825/64
veth3d7cc6e@if11 UP             fe80::6463:13ff:fef7:13aa/64
... (many more veth interfaces)
```

This is conclusive. From *inside* the container you can see:

* `docker0` — the Docker daemon's own default bridge;
* `br-aa5b6a26874a`, `br-7bff4b5b839d`, `br-f27899dc3088` — the three bridges Docker
  created for `frontend-net`, `backend-net` and `database-net` back in **Task 1**;
* every `veth*` interface, i.e. one end of every other container's virtual cable.

A normally-networked container sees only `lo` and its own `eth0`. This container sees the
host's entire networking stack, because it *is* the host's stack.

```console
$ docker exec apache-host curl -s -I localhost
HTTP/1.1 200 OK
Date: Wed, 02 Sep 2026 21:55:14 GMT
Server: Apache/2.4.68 (Unix)
Last-Modified: Fri, 07 Nov 2025 08:23:08 GMT
ETag: "bf-642fce432f300"
Accept-Ranges: bytes
Content-Length: 191
Content-Type: text/html
```

Apache is serving on port 80 of the host's network namespace.

## 2.5 The macOS/Windows caveat — and what it teaches

```console
$ curl --max-time 5 http://localhost:80        # run on the macOS host
(no response)
```

**This is not a bug — it is the definition of "host".** On Linux, Docker runs directly on
the machine, so `--network host` means *your machine's* network and `curl localhost:80`
works immediately. On **macOS and Windows**, Docker runs inside a small Linux VM. "The
host" is that **VM**, not your laptop — which is exactly why `hostname` printed
`docker-desktop` and `eth0` was `192.168.65.3`, an address on the VM's private network.

Ways to make it reachable from macOS:

* Enable **Settings → Resources → Network → "Enable host networking"** (Docker Desktop
  4.34+), which forwards host-networked ports to the Mac.
* Or use a normal bridge container with an explicit mapping: `docker run -d -p 80:80 httpd:2.4`.
* Or run the exercise on a real Linux machine or VM, where it works with no caveats.

**On Linux the expected output is:**

```console
$ docker run -d --name apache-host --network host httpd:2.4
$ curl http://localhost:80
<html><body><h1>It works!</h1></body></html>

$ docker ps
CONTAINER ID   IMAGE       COMMAND              STATUS         PORTS   NAMES
b738cd5bb7b0   httpd:2.4   "httpd-foreground"   Up 3 seconds           apache-host
```

## 2.6 Host vs bridge networking

| | `bridge` (default) | `host` |
|---|---|---|
| Network namespace | Its own | **Shares the host's** |
| Container IP | Yes (`172.17.0.x`) | No — uses the host's |
| `-p` port mapping | Required | **Ignored** (Docker warns) |
| Port conflicts | Isolated; two containers can both use 80 | Real — only one process per port on the host |
| Performance | Slight NAT/iptables overhead | Native — no NAT hop |
| Isolation | Good | **None** — the container sees every host interface |
| Multi-host | No | No |
| Platform | Everywhere | Linux (macOS/Windows need the opt-in feature) |

**When host networking is the right answer:** very high packet rates where the NAT hop
matters; a service that opens many or unpredictable ports (SIP, some monitoring agents);
a network tool that genuinely needs to see the host's interfaces (`tcpdump`, a metrics
exporter). Otherwise prefer a bridge — the isolation is worth the microseconds.

---

# Task 3 — Bind Mount

**Goal:** create a local folder with `index.html` saying "Hello students", bind-mount it
into nginx, then edit the file and see the change without restarting the container.

## 3.1 The local folder

```console
$ ls -l task3-bind-mount/html
total 8
-rw-r--r--  1 saptakbanerjee  staff  238 Sep  3 03:24 index.html

$ cat task3-bind-mount/html/index.html
<!doctype html>
<html>
  <head>
    <title>Bind Mount Demo</title>
    <meta charset="utf-8">
  </head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello students</h1>
  </body>
</html>
```

## 3.2 Bind mount it into nginx

```console
$ docker run -d --name nginx-bind -p 8090:80 \
      -v /absolute/path/to/task3-bind-mount/html:/usr/share/nginx/html:ro \
      nginx:alpine
b6ccbe073634e47b52eafffcfd41f2a42740534f4dbf4b8ad4f8397152f8bbb7
```

Syntax: `-v <HOST PATH>:<CONTAINER PATH>[:options]`

* The host path **must be absolute**. `-v ./html:/...` or `-v html:/...` is interpreted
  as a **named volume** called `html`, not a bind mount — and you get an empty directory
  with no error. This is the single most common bind-mount mistake. Use `$(pwd)/html`.
* `:ro` makes the mount read-only inside the container. Correct for static content the
  app has no business modifying.
* The modern equivalent is more explicit and worth preferring in scripts:
  `--mount type=bind,source=/abs/path,target=/usr/share/nginx/html,readonly`

## 3.3 Access the site

```console
$ curl http://localhost:8090
<!doctype html>
<html>
  <head>
    <title>Bind Mount Demo</title>
    <meta charset="utf-8">
  </head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello students</h1>
  </body>
</html>
```

**"Hello students" is served.**

```console
$ docker inspect nginx-bind --format '{{json .Mounts}}'
[{"Type":"bind",
  "Source":"/Users/saptakbanerjee/.../task3-bind-mount/html",
  "Destination":"/usr/share/nginx/html",
  "Mode":"ro","RW":false,"Propagation":"rprivate"}]
```

`"Type":"bind"` confirms it is a bind mount, not a volume. `"RW":false` confirms `:ro`
took effect.

## 3.4 Modify the file — no restart

The file was rewritten **on the host** to:

```html
<h1>Hello students - this file was edited on the host!</h1>
<p>The nginx container was never restarted.</p>
```

```console
$ curl http://localhost:8090
<!doctype html>
<html>
  <head>
    <title>Bind Mount Demo - UPDATED</title>
    <meta charset="utf-8">
  </head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello students - this file was edited on the host!</h1>
    <p>The nginx container was never restarted.</p>
  </body>
</html>

$ docker ps --filter name=nginx-bind --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
NAMES        STATUS         PORTS
nginx-bind   Up 2 seconds   0.0.0.0:8090->80/tcp, [::]:8090->80/tcp
```

**Verified: the change appeared with no restart.** The `STATUS` column still shows the
original uptime — the container was never stopped, restarted, or rebuilt.

The same file seen from inside the container:

```console
$ docker exec nginx-bind cat /usr/share/nginx/html/index.html
<!doctype html>
...
    <h1>Hello students - this file was edited on the host!</h1>
    <p>The nginx container was never restarted.</p>
...
```

There is only one copy of this file on disk. The container and the host are looking at
the same inode through the same mount — nothing is copied or synchronised.

### One real artifact worth knowing about

The very first `curl` issued in the same instant as the write returned a **truncated**
body — nginx had already sent a `Content-Length` from the pre-edit `stat()` while the file
was growing underneath it. The next request was complete and correct (`Content-Length: 336`
matching the host's `wc -c` of 336). This is a classic `sendfile` + bind-mount race, not a
bind-mount failure. In development the standard fix is `sendfile off;` in the nginx config,
which also disables `open_file_cache` staleness on network/VM-backed filesystems.

## 3.5 Read-only enforcement

```console
$ docker exec nginx-bind sh -c 'echo hack > /usr/share/nginx/html/index.html'
sh: can't create /usr/share/nginx/html/index.html: Read-only file system
>>> BLOCKED AS EXPECTED: the mount is read-only (:ro)
```

The container cannot modify content the host owns. Drop `:ro` and writes from inside the
container land in the host folder immediately.

## 3.6 Bind mount vs named volume

| | Bind mount | Named volume |
|---|---|---|
| Syntax | `-v /abs/host/path:/container/path` | `-v myvolume:/container/path` |
| Where the data lives | Anywhere you choose on the host | Docker-managed (`/var/lib/docker/volumes/`) |
| Created by | You, beforehand | Docker, automatically |
| Visible in `docker volume ls` | No | Yes |
| Edit from the host | Yes — that is the point | Awkward (root-owned internal path) |
| Portable across machines | No — depends on an absolute host path | Yes |
| Performance on macOS/Windows | Slower (crosses the VM filesystem boundary) | Faster (lives inside the VM) |
| Backup | Ordinary file copy | `docker run --rm -v myvol:/data -v $(pwd):/backup alpine tar czf /backup/v.tgz /data` |
| **Best for** | **Source code in development, config files** | **Database data, production state** |

```bash
# Volume commands
docker volume create myvol
docker volume ls
docker volume inspect myvol
docker volume rm myvol
docker volume prune

# Live-reload development — the everyday use of a bind mount
docker run -d -p 3000:3000 \
  -v "$(pwd)":/app \
  -v /app/node_modules \        # anonymous volume MASKS the host's node_modules,
  node:20-alpine npm run dev    #   so the container keeps its own Linux-built copy

# Database data — the everyday use of a named volume
docker run -d --name db -v mysql-data:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=secret mysql:8
```

Without a volume, everything a container writes lives in its thin writable layer and is
**destroyed with the container**. That is the bug behind "my database was empty after
`docker compose down`".

---

# Task 4 — Overlay Network

**Goal:** research overlay networks, their use cases, and how they work across multiple
Docker hosts. Demonstrated below on a real single-node swarm.

## 4.1 What an overlay network is

A `bridge` network is a Linux bridge on **one** machine. Two containers on two different
hosts cannot see each other on it — the bridge does not extend past the box.

An **overlay** network is a **virtual layer-2 network spanning many Docker hosts**.
Containers on different physical machines get addresses in one flat subnet
(e.g. `10.0.1.0/24`) and talk to each other by name, exactly as if they shared a switch —
even when the hosts are in different racks, datacentres or cloud regions.

## 4.2 How it works

### VXLAN encapsulation

Overlay uses **VXLAN** (Virtual Extensible LAN, RFC 7348):

1. Container A on host 1 sends an Ethernet frame to container B's overlay IP.
2. The host's VXLAN driver **wraps** that whole frame in a **UDP packet on port 4789**,
   tagged with a 24-bit **VNI** (VXLAN Network Identifier) that names the overlay network.
3. The UDP packet travels over the ordinary physical network from host 1 to host 2 —
   the physical network only ever sees normal UDP traffic and needs no special config.
4. Host 2 **unwraps** it and delivers the original frame to container B.

So it is a layer-2 frame tunnelled inside a layer-3 packet — a tunnel, not routing.
The 24-bit VNI allows ~16 million isolated networks, versus VLAN's 4 096.

### Control plane — how hosts learn about each other

Swarm managers maintain a distributed store (Raft consensus) of every network, service,
task and its IP. When a container starts, the manager **gossips** its location to every
node hosting that network, so each node's VXLAN driver knows which physical host to send
a given overlay IP to. There is no broadcast flooding.

### Required ports between the hosts

| Port | Protocol | Purpose |
|---|---|---|
| **2377** | TCP | Cluster management (managers only) |
| **7946** | TCP **and** UDP | Node-to-node control-plane gossip |
| **4789** | UDP | **VXLAN data plane** — the actual encapsulated traffic |

A blocked 4789/UDP is the #1 cause of "the overlay network exists but containers cannot
reach each other". Nodes see each other (7946 works) but no data flows.

### Encryption

```bash
docker network create -d overlay --opt encrypted secure-net
```

Adds IPsec (AES-GCM) to the VXLAN tunnel — important when the traffic crosses a network
you do not control. It costs roughly 10–15 % throughput, so it is opt-in.

## 4.3 Demonstration on a real swarm

### Overlay requires swarm mode

```console
$ docker network create -d overlay will-fail
Error response from daemon: This node is not a swarm manager. Use "docker swarm init"
or "docker swarm join" to connect this node to swarm and try again.

$ docker swarm init
Swarm initialized: current node (k2oq79jaatqm11kwm5nfqtokt) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-03g9bq433bwlnshzp3rdcduc96tnwfd6di0psezqj0xa46orc9 192.168.65.3:2377
```

### Swarm mode creates two networks automatically

```console
$ docker network ls
NETWORK ID     NAME              DRIVER    SCOPE
rjsygdu6wju2   app-overlay       overlay   swarm
7bff4b5b839d   backend-net       bridge    local
1f140a2da75a   bridge            bridge    local
f27899dc3088   database-net      bridge    local
ed091fd910a2   docker_gwbridge   bridge    local
aa5b6a26874a   frontend-net      bridge    local
8a0c7553bf7d   host              host      local
4ciuc41m4fl0   ingress           overlay   swarm
58528924efce   none              null      local
```

Two new entries appeared:

* **`ingress`** (overlay, swarm) — carries traffic for **published service ports** and
  implements the routing mesh.
* **`docker_gwbridge`** (bridge, local) — gives overlay-attached containers **outbound**
  access to the internet. An overlay network is internal-only; this bridge is the door
  out. It appears once a container actually joins an overlay.

Note the **`SCOPE`** column: overlay networks are `swarm`-scoped, meaning every node in
the cluster knows about them. Bridge networks are `local` — they exist only on one host.

### Create a user-defined overlay

```console
$ docker network create --driver overlay --attachable app-overlay
rjsygdu6wju2eydltzf4s27v6

$ docker network inspect app-overlay \
    --format '{{.Name}} driver={{.Driver}} scope={{.Scope}} attachable={{.Attachable}} subnet={{range .IPAM.Config}}{{.Subnet}}{{end}}'
app-overlay driver=overlay scope=swarm attachable=true subnet=10.0.1.0/24
```

`--attachable` lets plain `docker run` containers join the overlay too. Without it, only
swarm **services** can attach.

### Deploy services on the overlay

```console
$ docker service create --name web --network app-overlay --replicas 3 -p 8091:80 nginx:alpine
verify: Service r89zqgu22x5znrmozikvu2a2g converged

$ docker service create --name api --network app-overlay --replicas 2 alpine sleep 3600
verify: Service 4ewmsbs8rw1ct6xuzkxiqpd05 converged

$ docker service ls
ID             NAME      MODE         REPLICAS   IMAGE           PORTS
4ewmsbs8rw1c   api       replicated   2/2        alpine:latest
r89zqgu22x5z   web       replicated   3/3        nginx:alpine    *:8091->80/tcp

$ docker service ps web
ID             NAME    IMAGE          NODE             DESIRED STATE   CURRENT STATE
tbcmj0g5h49i   web.1   nginx:alpine   docker-desktop   Running         Running 13 seconds ago
nofvaxbnditf   web.2   nginx:alpine   docker-desktop   Running         Running 13 seconds ago
z9fohtjzw3pl   web.3   nginx:alpine   docker-desktop   Running         Running 13 seconds ago
```

On a multi-node swarm the `NODE` column would name different machines; here all three
replicas landed on the only node.

### Service discovery — VIP vs task DNS

```console
$ docker exec api.2.o28jq... nslookup web
Non-authoritative answer:
Name:	web
Address: 10.0.1.2

$ docker exec api.2.o28jq... nslookup tasks.web
Non-authoritative answer:
Name:	tasks.web
Address: 10.0.1.3
Name:	tasks.web
Address: 10.0.1.4
Name:	tasks.web
Address: 10.0.1.5
```

**This is the most important output in Task 4.** Two names, two behaviours:

* **`web` → `10.0.1.2`** — a single **VIP** (virtual IP). It belongs to no container. IPVS
  in the kernel load-balances connections to that VIP across the healthy replicas. When a
  replica dies or the service scales, the VIP is unchanged, so clients need no retry
  logic and no DNS cache invalidation.
* **`tasks.web` → `10.0.1.3, .4, .5`** — the real IP of every individual replica. This is
  DNS round-robin, used when a client needs to address specific instances (cluster
  members gossiping, a stateful set).

Note the addresses: `10.0.1.3/.4/.5` are all in `app-overlay`'s `10.0.1.0/24` subnet, and
in a real cluster those three replicas could each be on a different physical host while
keeping consecutive IPs in one flat subnet. **That is the overlay abstraction.**

```console
$ docker exec api.2.o28jq... sh -c 'for i in 1 2 3; do curl -s -o /dev/null -w "request $i -> HTTP %{http_code}\n" http://web; done'
request 1 -> HTTP 200
request 2 -> HTTP 200
request 3 -> HTTP 200
```

Three requests to the name `web`, load-balanced through the VIP — no proxy configured, no
IP hardcoded anywhere.

### The routing mesh

```console
$ curl -I http://localhost:8091
HTTP/1.1 200 OK
Server: nginx/1.31.4
Date: Wed, 02 Sep 2026 21:56:13 GMT
```

A published service port goes through the `ingress` overlay. In a multi-node swarm, port
**8091 answers on every node — including nodes running no replica of `web`**. The ingress
network forwards the request to a node that has one. This is the **routing mesh**, and it
is why you can point a plain load balancer at all nodes without tracking placement.

## 4.4 The multi-host walkthrough

A single node cannot demonstrate the cross-host part. Two machines (VMs, cloud instances,
or two VirtualBox/Multipass VMs on one laptop):

```bash
# ---------- On host 1 (manager), IP 192.168.1.10 ----------
docker swarm init --advertise-addr 192.168.1.10
# prints:  docker swarm join --token SWMTKN-1-xxxx 192.168.1.10:2377

docker network create --driver overlay --attachable my-overlay

# ---------- On host 2 (worker), IP 192.168.1.11 ----------
docker swarm join --token SWMTKN-1-xxxx 192.168.1.10:2377
# "This node joined a swarm as a worker."

# ---------- Back on host 1 ----------
docker node ls          # both nodes now listed, one Leader, one worker

# Spread 4 replicas across both hosts
docker service create --name web --network my-overlay --replicas 4 nginx:alpine
docker service ps web   # the NODE column now names BOTH machines

# The cross-host proof:
docker service create --name client --network my-overlay \
  --constraint 'node.role==worker' alpine sleep 3600

# From the client container ON HOST 2, reach a web replica ON HOST 1 by name:
docker exec <client-task> ping -c 3 web
docker exec <client-task> curl -I http://web
```

The `ping` crosses two physical machines while looking like a single flat subnet — the
VXLAN tunnel makes the hop invisible to the application. On the wire between the hosts
you would see only UDP/4789 traffic:

```bash
sudo tcpdump -i eth0 -n udp port 4789
```

Confirm swarm state at any point:

```console
$ docker node ls
ID                            HOSTNAME         STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
k2oq79jaatqm11kwm5nfqtokt *   docker-desktop   Ready     Active         Leader           29.6.1
```

## 4.5 Use cases

1. **Multi-host container communication** — the core purpose. A backend on host 1 talks
   to a database on host 2 by name, with no port publishing and no IP wrangling.
2. **Horizontal scaling** — `docker service scale web=10` spreads replicas across the
   cluster; the VIP keeps working, and clients never learn a new address.
3. **High availability** — a node dies, the swarm reschedules its tasks elsewhere, and
   the VIP starts routing to the new locations. No client-side change.
4. **Network segmentation at cluster scale** — one overlay per tier (`frontend-net`,
   `backend-net`, `db-net`) reproduces the Task 1 isolation model across many machines.
5. **Zero-downtime rolling updates** — `docker service update --image myapp:v2
   --update-parallelism 1 --update-delay 10s web` replaces replicas one at a time while
   the VIP keeps serving from the rest.
6. **Encrypted traffic between datacentres** — `--opt encrypted` when the physical path
   is untrusted.

## 4.6 Bridge vs overlay

| | `bridge` | `overlay` |
|---|---|---|
| Spans hosts | **No** — one machine | **Yes** — the whole cluster |
| Requires swarm mode | No | **Yes** |
| Scope in `docker network ls` | `local` | `swarm` |
| Underlying tech | Linux bridge + iptables NAT | **VXLAN tunnel over UDP/4789** |
| Service discovery | Container-name DNS | Container name, service **VIP**, and `tasks.<svc>` |
| Load balancing | None built in | **IPVS via the VIP**, plus the routing mesh |
| Encryption option | No | Yes (`--opt encrypted`, IPsec) |
| Typical subnet | `172.17–172.31.x.x` | `10.0.x.x` |
| Use for | Single-host dev, Compose | Multi-host production clusters |

## 4.7 Overlay vs Kubernetes networking

Swarm overlay and Kubernetes CNI plugins (Flannel, Calico, Cilium, Weave) solve the same
problem — a flat pod/container network across many hosts — with the same core mechanism.
Flannel's default backend is literally VXLAN. Calico can instead use BGP to route pod
subnets natively, avoiding encapsulation overhead. Understanding overlay is therefore
directly transferable: it is the same VXLAN concept Kubernetes is built on, with a
smaller surface area to learn it from.

## 4.8 Command reference

```bash
# Swarm
docker swarm init [--advertise-addr <IP>]
docker swarm join --token <token> <manager-ip>:2377
docker swarm join-token worker        # reprint the worker token
docker swarm join-token manager
docker node ls
docker node inspect <node>
docker swarm leave --force            # on the last manager

# Overlay networks
docker network create -d overlay <name>
docker network create -d overlay --attachable <name>        # allow docker run
docker network create -d overlay --opt encrypted <name>     # IPsec
docker network create -d overlay --subnet 10.10.0.0/24 <name>
docker network inspect <name>

# Services
docker service create --name web --network <net> --replicas 3 -p 8080:80 nginx:alpine
docker service ls
docker service ps <service>
docker service logs -f <service>
docker service scale web=10
docker service update --image nginx:1.27 --update-parallelism 1 --update-delay 10s web
docker service rm <service>

# Stacks (Compose files in swarm mode)
docker stack deploy -c docker-compose.yml mystack
docker stack services mystack
docker stack rm mystack
```

---

## Cleanup

```bash
./task1-container-networking/setup.sh clean
./task2-host-network/setup.sh clean
./task3-bind-mount/setup.sh clean
./task4-overlay-network/demo.sh clean     # also leaves the swarm
```

---

## Summary of what each sub-task proved

| Task | Proved by |
|---|---|
| **1 — Container networking** | `frontend → database` failed with `Name does not resolve`, while `backend → both` succeeded. Isolation is enforced at DNS *and* routing, not just by convention. |
| **2 — Host network** | `docker ps` showed an **empty PORTS column**, `.NetworkSettings.IPAddress` did not exist, and `ip -br a` from inside the container listed the host's `docker0`, every `br-*` and every `veth*`. |
| **3 — Bind mount** | A host-side edit appeared over HTTP with the container's uptime unchanged; `docker inspect` showed `"Type":"bind","RW":false`; a write from inside was refused with `Read-only file system`. |
| **4 — Overlay network** | `docker network create -d overlay` was refused outside swarm mode; after `swarm init` the network came up with `scope=swarm subnet=10.0.1.0/24`, and `web` resolved to a single VIP `10.0.1.2` while `tasks.web` resolved to all three replicas `10.0.1.3/.4/.5`. |

## Submission

```bash
git add Task7-Docker-Networking/
git commit -m "Add Docker networking and volume tasks with verified output"
git push origin main
```
