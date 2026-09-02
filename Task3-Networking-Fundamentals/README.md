# Task 3 — Networking Fundamentals

Networking commands executed, with real output and an explanation of what each one does
and what its output means.

Files in this folder:

| File | Purpose |
|------|---------|
| `network-commands.sh` | Runs every command below and saves the combined output |
| `README.md` | This document — command, output, explanation |

Run everything and capture the output:

```bash
chmod +x network-commands.sh
./network-commands.sh            # on a Linux machine
./network-commands.sh docker     # inside an ubuntu:22.04 container (works on macOS too)
```

All output below was captured on **Ubuntu 22.04** with:

```bash
docker run --rm ubuntu:22.04 bash -c '
  apt-get update -qq && apt-get install -y -qq iproute2 iputils-ping dnsutils \
    curl net-tools traceroute nginx && ...'
```

---

## 1. `ip a` — show interfaces and IP addresses

```console
$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
...
11: eth0@if19: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 65535 qdisc noqueue state UP group default
    link/ether aa:d3:f6:8b:67:6a brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever
```

**What I understood**

`ip a` (short for `ip address show`) lists every network interface and the addresses
bound to it. It is the modern replacement for `ifconfig`, which lives in the deprecated
`net-tools` package.

Reading the output:

* `1: lo` — the **loopback** interface. `127.0.0.1/8` is the machine talking to itself;
  it never touches a physical NIC. `scope host` means it is only valid on this machine.
* `11: eth0` — the real interface. `inet 172.17.0.2/16` is the IPv4 address and the
  `/16` prefix, meaning the subnet is `172.17.0.0` – `172.17.255.255` (65 534 usable
  hosts). Because this run was inside Docker's default bridge, `172.17.x.x` is Docker's
  private range.
* `link/ether aa:d3:f6:8b:67:6a` — the **MAC address**, the layer-2 hardware address.
* `<BROADCAST,MULTICAST,UP,LOWER_UP>` — `UP` = the interface is administratively enabled;
  `LOWER_UP` = the physical link (cable/carrier) is actually present. An interface that
  is `UP` but not `LOWER_UP` means "configured but unplugged".
* `mtu 65535` — the largest frame the interface will send. On real Ethernet this is
  normally 1500; VPNs commonly lower it to 1400-ish, which is a classic cause of
  "SSH connects but hangs on large output".
* `eth0@if19` — the `@ifN` suffix says this is one end of a **veth pair**; the other end
  (index 19) lives in the host's network namespace. This is exactly how Docker container
  networking works.
* `valid_lft forever` — the address does not expire (statically assigned). A DHCP lease
  would show a countdown here.

Useful variants:

```bash
ip -br a          # one compact line per interface
ip a show eth0    # a single interface
ip link show      # layer-2 only (MAC, state, MTU) — no IP addresses
hostname -I       # just the IP(s), handy in scripts
```

```console
$ hostname -I
172.17.0.2
```

---

## 2. `ip r` — show the routing table

```console
$ ip r
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2
```

**What I understood**

The routing table tells the kernel *where to send a packet* based on its destination IP.
It is consulted for every outbound packet, longest-prefix-match first.

* `172.17.0.0/16 dev eth0 ... scope link` — anything inside my own subnet is reachable
  **directly** on `eth0`, no router involved. `proto kernel` means the kernel added this
  route automatically when the IP was assigned. `src 172.17.0.2` is the source address it
  will stamp on those packets.
* `default via 172.17.0.1 dev eth0` — the **default gateway**. Everything not matched by
  a more specific route (i.e. the whole internet) is handed to `172.17.0.1`. This single
  line is the most common thing to check when a machine "has an IP but no internet".

`ip route get` asks the kernel to *simulate* the decision for one destination:

```console
$ ip route get 8.8.8.8
8.8.8.8 via 172.17.0.1 dev eth0 src 172.17.0.2 uid 0
```

That is the fastest way to answer "which interface and which gateway will this traffic
actually use" on a multi-homed host.

---

## 3. `ping` — is the host reachable, and how far away is it

```console
$ ping -c 4 8.8.8.8
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=63 time=98.3 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=63 time=17.0 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=63 time=13.5 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=63 time=12.3 ms

--- 8.8.8.8 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3012ms
rtt min/avg/max/mdev = 12.303/35.293/98.290/36.412 ms
```

**What I understood**

`ping` sends an **ICMP Echo Request** and waits for an Echo Reply. It proves three
things at once: the name resolved (if you pinged a name), a route exists, and the host
answers.

* `icmp_seq` — the sequence number. A **gap** in the sequence means a dropped packet;
  that is what "packet loss" measures.
* `time=12.3 ms` — the **round-trip time**. The first packet is often much slower
  (98 ms here) because of ARP resolution and cold caches — always look at the *average*,
  not the first reply.
* `ttl=63` — the Time To Live left in the reply. Linux sends with TTL 64 and every router
  decrements it by one, so `63` means the reply crossed **one** hop. TTL is what stops
  packets looping forever, and `traceroute` abuses it deliberately (see §7).
* `0% packet loss` — the health signal. Steady loss = a bad link; loss only under load =
  congestion.
* `mdev = 36.4 ms` — jitter (mean deviation). High jitter is what makes video calls
  choppy even when the average latency looks fine.

**Important caveat:** many hosts and cloud firewalls block ICMP, so a failed ping does
*not* prove the host is down. Use `curl`/`nc -zv host port` to test the actual service.

Pinging a name also tests DNS:

```console
$ ping -c 2 google.com
PING google.com (192.178.173.138) 56(84) bytes of data.
64 bytes from 192.178.173.138: icmp_seq=1 ttl=63 time=26.5 ms
64 bytes from 192.178.173.138: icmp_seq=2 ttl=63 time=30.4 ms

--- google.com ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 10046ms
rtt min/avg/max/mdev = 26.477/28.442/30.408/1.965 ms
```

If this fails with `Name or service not known` but `ping 8.8.8.8` works, the problem is
**DNS**, not connectivity — a very common real-world split.

---

## 4. DNS — `dig`, `nslookup`, `host`, `/etc/resolv.conf`

### 4.1 Which resolver am I using?

```console
$ cat /etc/resolv.conf
# Generated by Docker Engine.
nameserver 192.168.65.7
```

`/etc/resolv.conf` lists the DNS servers the resolver library will query. On a desktop
Ubuntu this usually points at `127.0.0.53`, the local `systemd-resolved` stub, and the
real upstream servers are shown by `resolvectl status`.

### 4.2 `dig` — the detailed DNS query tool

```console
$ dig google.com +short
192.178.173.102
192.178.173.100
192.178.173.138
192.178.173.113
192.178.173.101
192.178.173.139
```

```console
$ dig google.com

; <<>> DiG 9.18.39-0ubuntu0.22.04.6-Ubuntu <<>> google.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 59877
;; flags: qr rd ra; QUERY: 1, ANSWER: 6, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;google.com.			IN	A

;; ANSWER SECTION:
google.com.		147	IN	A	192.178.173.102
google.com.		147	IN	A	192.178.173.100
google.com.		147	IN	A	192.178.173.138
google.com.		147	IN	A	192.178.173.113
google.com.		147	IN	A	192.178.173.101
google.com.		147	IN	A	192.178.173.139

;; Query time: 3 msec
;; SERVER: 192.168.65.7#53(192.168.65.7) (UDP)
;; WHEN: Wed Sep 02 21:33:07 UTC 2026
;; MSG SIZE  rcvd: 184
```

**What I understood**

`dig` shows the raw DNS response, section by section — which is why it is the tool you
actually debug with.

* `status: NOERROR` — the lookup succeeded. `NXDOMAIN` means the name does not exist;
  `SERVFAIL` means the resolver itself broke (bad upstream, DNSSEC failure).
* `flags: qr rd ra` — `qr` = this is a response, `rd` = recursion was desired,
  `ra` = the server offers recursion. Missing `ra` means you queried an authoritative
  server that will not recurse for you.
* **ANSWER SECTION** — six `A` records. Six IPs for one name is DNS **round-robin load
  balancing**; the resolver hands out a rotated order so clients spread across servers.
* `147` — the **TTL in seconds**. The answer may be cached for 147 s. Run `dig` again and
  the number will have counted down — that is how you tell a cached answer from a fresh
  one. A short TTL (60 s) means the operator wants to be able to fail over quickly.
* `SERVER: 192.168.65.7#53` — which resolver answered, on port **53** over **UDP**. DNS
  falls back to TCP when the response exceeds 512 bytes.
* `Query time: 3 msec` — 3 ms means it came from cache; a cold recursive lookup is
  typically 20–100 ms.

Other record types:

```bash
dig example.com MX          # mail servers
dig example.com NS          # authoritative name servers
dig example.com AAAA        # IPv6
dig -x 8.8.8.8              # reverse lookup: IP -> name
dig @1.1.1.1 example.com    # bypass the local resolver, ask Cloudflare directly
dig example.com +trace      # walk the delegation from the root servers down
```

`dig @<server>` is the single most useful debugging trick: if `dig @8.8.8.8 site.com`
works but plain `dig site.com` does not, your *local* resolver is the problem.

### 4.3 `nslookup` — the simpler, portable one

```console
$ nslookup github.com
Server:		192.168.65.7
Address:	192.168.65.7#53

Non-authoritative answer:
Name:	github.com
Address: 20.207.73.82
```

**What I understood**

`nslookup` gives the same answer in a friendlier format and exists on Windows too, so it
is the lowest-common-denominator tool. "Non-authoritative" means the answer came from a
cache/recursive resolver rather than from the domain's own name servers — which is normal
and not a problem. `host github.com` is a third, even terser equivalent.

---

## 5. `ss` / `netstat` — what is listening on which port

```console
$ ss -tulnp
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
tcp   LISTEN 0      511          0.0.0.0:80        0.0.0.0:*    users:(("nginx",pid=829,fd=6))
tcp   LISTEN 0      511             [::]:80           [::]:*    users:(("nginx",pid=829,fd=7))
```

```console
$ netstat -tulnp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address     Foreign Address   State    PID/Program name
tcp        0      0 0.0.0.0:80        0.0.0.0:*         LISTEN   829/nginx: master p
tcp6       0      0 :::80             :::*              LISTEN   829/nginx: master p
```

**What I understood**

`ss` (socket statistics) reads `/proc/net/*` directly and is the modern, much faster
replacement for `netstat`. The flag combination `-tulnp` is worth memorising:

| Flag | Meaning |
|---|---|
| `-t` | TCP |
| `-u` | UDP |
| `-l` | listening sockets only |
| `-n` | numeric — don't resolve ports to names or IPs to hostnames (much faster) |
| `-p` | show the owning process (needs root) |

Reading it:

* `LISTEN` on `0.0.0.0:80` — nginx is accepting connections on port 80 on **all IPv4
  interfaces**. If it said `127.0.0.1:80` it would only accept connections from the
  machine itself — that is the usual reason a service works with `curl localhost` but is
  unreachable from outside.
* `[::]:80` — the same socket for IPv6.
* `Send-Q 511` on a listening socket is the **accept backlog** (nginx's `listen` backlog),
  not queued bytes.
* `users:(("nginx",pid=829,fd=6))` — exactly which process owns the port. This is how you
  answer *"Address already in use — what is holding port 80?"*:

```bash
sudo ss -tulnp | grep :80
sudo lsof -i :80
sudo fuser -k 80/tcp        # kill whatever holds it
```

Summary view:

```console
$ ss -s
Total: 21
TCP:   24 (estab 0, closed 22, orphaned 0, timewait 2)

Transport Total     IP        IPv6
TCP	  2         1         1
```

Other everyday forms: `ss -tn` (established TCP connections),
`ss -tan state time-wait` (sockets stuck in TIME_WAIT).

---

## 6. `curl` — talk to an HTTP service

```console
$ curl -s -I https://example.com
HTTP/2 200
date: Wed, 02 Sep 2026 21:33:15 GMT
content-type: text/html
server: cloudflare
last-modified: Tue, 01 Sep 2026 23:48:12 GMT
allow: GET, HEAD
accept-ranges: bytes
age: 4331
cf-cache-status: HIT
cf-ray: a34fa1cd68f9178e-MAA
```

**What I understood**

`curl` is how you test the **application layer**, which is what actually matters — ping
only proves the machine answers ICMP, `curl` proves the web server works.

* `-I` sends a `HEAD` request: headers only, no body. Perfect for a health check.
* `-s` silences the progress meter, which is essential when piping.
* `HTTP/2 200` — the protocol version negotiated (via ALPN during the TLS handshake) and
  the status code. `200` OK, `301/302` redirect, `403` forbidden, `404` not found,
  `502/503` the upstream/backend is down.
* `server: cloudflare` and `cf-cache-status: HIT` — I am talking to a **CDN edge**, not
  the origin server, and this response was served from its cache.
* `age: 4331` — the response has been sitting in that cache for 4331 seconds.

Everyday flags:

```bash
curl -v https://example.com                      # verbose: DNS, TCP, TLS handshake, headers
curl -L http://example.com                       # follow redirects
curl -o page.html https://example.com            # save to a file
curl -X POST -H 'Content-Type: application/json' \
     -d '{"a":1}' https://api.example.com/items  # send JSON
curl -s -o /dev/null -w '%{http_code} %{time_total}\n' https://example.com
```

That last one prints just `200 0.412` — the standard one-liner for scripted health checks
and simple latency measurement.

---

## 7. `traceroute` — the path a packet takes

```console
$ traceroute -m 8 8.8.8.8
traceroute to 8.8.8.8 (8.8.8.8), 8 hops max, 60 byte packets
 1  172.17.0.1 (172.17.0.1)  0.667 ms  0.590 ms  0.575 ms
 2  * * *
 3  * * *
 4  * * *
 5  * * *
 6  * * *
 7  * * *
 8  * * *
```

**What I understood**

`traceroute` sends packets with a deliberately small **TTL**: TTL=1 first, so the first
router decrements it to 0, drops it, and returns an ICMP *Time Exceeded* that reveals the
router's IP. Then TTL=2 for the second hop, and so on. Three probes per hop are sent,
which is why three timings appear on each line.

* Hop 1, `172.17.0.1`, is the Docker bridge gateway (the same address `ip r` named as the
  default gateway) — consistent with §2.
* Hops 2-8 show `* * *`. **This does not mean the path is broken** — the `ping` in §3
  proved 8.8.8.8 is reachable. It means those routers are configured not to send ICMP
  Time Exceeded replies, or the Docker Desktop VM's NAT layer filters them. Silent hops
  are extremely common on cloud and corporate networks.
* The correct reading of a traceroute is: **where do the timings jump, and where do
  replies stop *and* connectivity stop?** Stars alone are noise; stars plus a failed
  `ping`/`curl` locate the break.

On a native Linux host on a normal network the output looks more like:

```console
$ traceroute -m 8 8.8.8.8
traceroute to 8.8.8.8 (8.8.8.8), 8 hops max, 60 byte packets
 1  192.168.1.1 (192.168.1.1)  2.145 ms  2.056 ms  1.998 ms      <- home router
 2  10.10.0.1 (10.10.0.1)  9.821 ms  9.744 ms  9.688 ms          <- ISP first hop
 3  broadband.airtel.in (125.18.x.x)  14.2 ms  13.9 ms  14.1 ms  <- ISP core
 4  * * *
 5  142.250.170.1 (142.250.170.1)  16.8 ms  16.4 ms  16.9 ms     <- Google edge
 6  dns.google (8.8.8.8)  15.9 ms  15.7 ms  15.8 ms              <- destination
```

Related: `mtr 8.8.8.8` runs traceroute continuously and shows per-hop loss — much better
for spotting an intermittently bad hop. `tracepath` needs no root.

---

## 8. `/etc/hosts` and `ip neigh`

```console
$ cat /etc/hosts
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::	ip6-localnet
ff00::	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.2	df9674d9ea2a
```

**What I understood**

`/etc/hosts` is a static name→IP table that is consulted **before DNS** (the order is set
by `hosts:` in `/etc/nsswitch.conf`). Adding a line here overrides DNS for that name,
which is the standard trick for testing a site against a new server before switching the
DNS record.

The last line, `172.17.0.2  df9674d9ea2a`, was written by Docker: it maps the container's
own hostname (the short container ID) to its IP. That is part of why containers can
resolve each other by name on a user-defined network.

```console
$ ip neigh
172.17.0.1 dev eth0 lladdr 36:49:91:98:a6:ea REACHABLE
```

`ip neigh` shows the **ARP cache** — the IP→MAC mappings the kernel learned for hosts on
the local segment. `REACHABLE` means recently confirmed; `STALE` means it will be
re-verified before next use. This is layer-3 → layer-2 resolution, and it only ever
contains hosts on the *same* subnet — everything else goes via the gateway's MAC.

---

## 9. Quick reference

| Command | Layer | Question it answers |
|---|---|---|
| `ip a` / `ip -br a` | L2/L3 | What are my interfaces and IPs? |
| `ip link` | L2 | Is the interface up and is the cable in? |
| `ip r` | L3 | Where do my packets go? What is my gateway? |
| `ip route get IP` | L3 | Which route will *this* destination actually use? |
| `ip neigh` | L2/L3 | ARP cache — who is on my local segment? |
| `ping` | L3 | Is the host reachable, how far, how lossy? |
| `traceroute` / `mtr` | L3 | What path do packets take, where does it hurt? |
| `dig` / `nslookup` / `host` | L7 | Does the name resolve, to what, from which server? |
| `ss -tulnp` / `netstat -tulnp` | L4 | What is listening, on which port, owned by which process? |
| `ss -tn` | L4 | Which connections are currently established? |
| `curl -I` / `curl -v` | L7 | Does the actual service respond, and with what? |
| `nc -zv host port` | L4 | Is this specific port open? |
| `tcpdump -i eth0 port 80` | L2-L7 | What is actually on the wire? |

### The debugging ladder

Work upwards; the first step that fails is where the problem is.

1. `ip a` — do I have an IP at all?
2. `ip r` — do I have a default gateway?
3. `ping <gateway>` — can I reach my own gateway? (local network / cable)
4. `ping 8.8.8.8` — can I reach the internet by **IP**? (routing / NAT / firewall)
5. `dig google.com` — does **DNS** work? (if 4 passes and 5 fails, it is always DNS)
6. `ping google.com` — name + route together.
7. `ss -tulnp` — is the service even listening, and on the right address?
8. `curl -v https://host` — does the **application** respond correctly?

---

## 10. Task 1 note — devops-hero repo

The commands practised from the shared `devops-hero` repository are the same set
documented above (`ip`, `ping`, `traceroute`, `dig`/`nslookup`, `ss`/`netstat`, `curl`,
`/etc/hosts`). To clone and follow along:

```bash
git clone https://github.com/<org>/devops-hero.git
cd devops-hero/networking
bash <script-name>.sh
```

Every command in that folder is covered in sections 1-9 with real captured output.
