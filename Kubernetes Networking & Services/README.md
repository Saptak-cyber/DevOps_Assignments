# Kubernetes Networking & Services

Source material: [`devops-heros/session-11-kubernetes-services`](../../devops-heros/session-11-kubernetes-services)
— `service.md` (the five service types, the four ports, services without selectors) and
`fqdn.md` (CoreDNS, FQDN anatomy, cross-namespace resolution), plus the `01-`…`05-` manifest
folders and the endpoint-triage drill. Manifests marked *(course manifest)* are unchanged from
that session.

Every console block is **real captured output** from the 3-node cluster built in
[Kubernetes Fundamentals](../Kubernetes%20Fundamentals/) (Kubernetes v1.37.0).

## Folder structure

```
Kubernetes Networking & Services/
├── README.md
├── lab1-clusterip/     app-deployment.yaml, service.yaml   (course manifests)
│                       echo-deployment.yaml                 written here: Pods that
│                                                            serve their own hostname
├── lab2-nodeport/      app-deployment.yaml, service.yaml   (course manifests)
├── lab3-loadbalancer/  app-deployment.yaml, service.yaml   (course manifests)
├── lab4-externalname/  service.yaml, client-pod.yaml       (course manifests)
├── lab5-headless/      service.yaml, app-statefulset.yaml  (course manifests)
├── lab6-dns-fqdn/      curl-test-pod.yaml                  (course manifest)
│                       cross-namespace.yaml                 written here: same Service
│                                                            name in two namespaces
├── lab7-no-selector/   manual-endpoints.yaml                written here
│                       apply.sh                             substitutes a live IP
│                                                            and applies it
└── troubleshooting/    empty-endpoints.yaml                (course manifest)
                        unready-endpoints.yaml               written here
```

> One change to the course manifests: the hardcoded `nodePort` values were removed from the
> blue-green/canary services in the previous task, and traffic tests here run from a Pod
> **inside** the cluster where possible, so they behave identically on kind, minikube or EKS.
> `lab2-nodeport` keeps `nodePort: 30080` because the cluster config maps that port to the host.

---

## Part A — MCQs

**MCQ 1.** What is the default Service type if you do not specify one?

- A. NodePort
- B. ClusterIP
- C. LoadBalancer
- D. Headless

**Answer: B. ClusterIP** — internal-only. This is why a freshly created Service is unreachable
from your laptop and everyone assumes it is broken.

**MCQ 2.** In a Service, what does `targetPort` refer to?

- A. The port clients connect to on the Service
- B. The port on the **Pod/container** that traffic is forwarded to
- C. The port opened on every node
- D. The port CoreDNS listens on

**Answer: B** — `port` is what the Service listens on, `targetPort` is the container's port.
Lab 1 uses `port: 8080 → targetPort: 80` and shows port 80 on the *Service* failing.

**MCQ 3.** A Service's `Endpoints` list is empty, but `kubectl get pods` shows the Pods
`Running`. What are the two likely causes?

- A. The cluster is out of IPs
- B. A selector/label mismatch, **or** the Pods are not `Ready`
- C. CoreDNS has crashed
- D. The Service needs to be recreated

**Answer: B** — both are reproduced in the troubleshooting section. Only **ready** Pods are
listed as endpoints.

**MCQ 4.** Which Service type has **no** ClusterIP?

- A. NodePort
- B. LoadBalancer
- C. ExternalName and Headless
- D. All of them have one

**Answer: C** — ExternalName is a pure DNS CNAME, and a Headless Service sets
`clusterIP: None` deliberately so DNS returns Pod IPs instead of a VIP. Both are shown below.

**MCQ 5.** What is the default NodePort range?

- A. 1–1024
- B. 8000–9000
- C. 30000–32767
- D. Any free port

**Answer: C. 30000–32767** (configurable with the API server's `--service-node-port-range`).
Lab 3 shows the auto-allocated `30355` landing inside it.

---

## Part B — The four ports you must not confuse

| Field | Lives on | Who connects to it | In Lab 1 |
|---|---|---|---|
| `containerPort` | the Pod spec | documentation, mostly | `80` |
| `targetPort` | the Service | the Service, forwarding inward | `80` |
| `port` | the Service | **other Pods in the cluster** | `8080` |
| `nodePort` | the Service | **anything that can reach a node's IP** | `30080` (Lab 2) |

```console
$ kubectl get svc echo-service -o jsonpath='servicePort={.spec.ports[0].port} targetPort={.spec.ports[0].targetPort} clusterIP={.spec.clusterIP}'
servicePort=8080 targetPort=80 clusterIP=10.96.12.142

$ kubectl get deploy echo-app -o jsonpath='containerPort={.spec.template.spec.containers[0].ports[0].containerPort}'
containerPort=80
```

They are not interchangeable, and the failure is silent rather than loud:

```console
$ kubectl exec curl-test-pod -- curl -s -o /dev/null -w 'via service port 8080 -> %{http_code}' http://echo-service:8080
via service port 8080 -> 200

$ kubectl exec curl-test-pod -- curl -s -o /dev/null -w 'wrong port 80 -> %{http_code}' --max-time 4 http://echo-service:80
wrong port 80 -> 000command terminated with exit code 28
```

Exit 28 is a **timeout**, not a refusal. Nothing listens on 80 on that ClusterIP, so packets are
dropped rather than rejected — which is exactly why "it just hangs" is the classic symptom of a
wrong `port`.

---

## Lab 1 — ClusterIP: the stable identity Pods do not have

```console
$ kubectl get svc web-service-clusterip
NAME                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
web-service-clusterip   ClusterIP   10.96.106.108   <none>        8080/TCP   8s

$ kubectl describe svc web-service-clusterip | grep -E 'Selector:|^IP:|Port:|TargetPort:|Endpoints:'
Selector:                 app=web-clusterip
IP:                       10.96.106.108
Port:                     http  8080/TCP
TargetPort:               80/TCP
Endpoints:                10.244.1.62:80,10.244.2.53:80,10.244.1.63:80
```

The Service is a **selector plus a VIP**. It found three Pods matching `app=web-clusterip` and
listed them as endpoints. Nothing about this is hardcoded.

### The problem ClusterIP exists to solve

Delete all three Pods and let the Deployment rebuild them:

```console
$ kubectl delete pods -l app=web-clusterip
pod "web-app-clusterip-66865d4855-j5z9h" deleted from default namespace
pod "web-app-clusterip-66865d4855-sdtc9" deleted from default namespace
pod "web-app-clusterip-66865d4855-slnnk" deleted from default namespace

$ kubectl get pods -l app=web-clusterip -o wide --no-headers | awk '{print $1, $6}'
web-app-clusterip-66865d4855-62mcp 10.244.1.65
web-app-clusterip-66865d4855-cbn94 10.244.1.64
web-app-clusterip-66865d4855-r7dpk 10.244.2.54
```

Every Pod name changed and **every Pod IP changed** (`1.62, 2.53, 1.63` → `1.65, 1.64, 2.54`).
Meanwhile:

```console
$ kubectl get svc web-service-clusterip
NAME                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
web-service-clusterip   ClusterIP   10.96.106.108   <none>        8080/TCP   26s

$ kubectl get endpointslice -l kubernetes.io/service-name=web-service-clusterip -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{" "}{end}'
10.244.2.54 10.244.1.65 10.244.1.64

$ kubectl exec curl-test-pod -- curl -s -o /dev/null -w 'status=%{http_code}' http://web-service-clusterip:8080
status=200
```

Same ClusterIP `10.96.106.108`, endpoints silently rewritten to the three new IPs, and the client
never noticed. **That** is the service abstraction: a name and an IP that outlive the Pods behind
them. Hardcoding a Pod IP in a config file is a bug with a delayed fuse.

### Load balancing, measured

`echo-deployment.yaml` makes each Pod serve its own hostname:

```console
$ kubectl exec curl-test-pod -- sh -c 'for i in $(seq 1 90); do curl -s http://echo-service:8080; done' | sort | uniq -c
  33 POD: echo-app-5f9849999b-gnnn2
  28 POD: echo-app-5f9849999b-k6zlq
  29 POD: echo-app-5f9849999b-qjvq9
```

33/28/29 out of 90 — near-even but **not** round-robin. `kube-proxy` in iptables mode picks a
backend at *random per new connection*, so the split converges with volume rather than
alternating. Two consequences that matter:

- A single long-lived connection (an HTTP keep-alive session, a gRPC channel, a DB pool) is
  pinned to **one** Pod for its lifetime. Scaling up does not rebalance existing connections.
- Per-request balancing needs something that speaks HTTP — an Ingress or a service mesh — not a
  Service.

---

## Lab 2 — NodePort: the same port on every node

```console
$ kubectl get svc web-service-nodeport
NAME                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
web-service-nodeport   NodePort   10.96.224.248   <none>        80:30080/TCP   1s
```

`80:30080/TCP` — the Service port *and* the node port. The cluster config maps container port
30080 to host port 30080, so this is reachable from the Mac running the cluster:

```console
$ curl -4 -s -o /dev/null -w 'localhost:30080 -> %{http_code}' http://localhost:30080
localhost:30080 -> 200
```

> Use `curl -4`. Without it, curl resolves `localhost` to `::1` first, gets
> `connection refused` on IPv6, and reports `000` before silently retrying IPv4 — a confusing
> 30 seconds if you are not expecting it.

### The part people get wrong

Only two Pods exist, both on workers:

```console
$ kubectl get pods -l app=web-nodeport -o wide --no-headers | awk '{print $1, $7}'
web-app-nodeport-6c8f48bd-4dp9t devops-k8s-worker
web-app-nodeport-6c8f48bd-rghgb devops-k8s-worker2
```

Yet all **three** nodes answer on 30080:

```console
$ for n in devops-k8s-control-plane devops-k8s-worker devops-k8s-worker2; do echo -n "$n:30080 -> "; docker exec $n curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:30080; echo; done
devops-k8s-control-plane:30080 -> 200
devops-k8s-worker:30080 -> 200
devops-k8s-worker2:30080 -> 200
```

The control-plane node runs **no Pod of this app** and still returns 200. `kube-proxy` opened
port 30080 on every node in the cluster and forwards to a Pod wherever it lives — one extra
network hop. This is why you can point an external load balancer at any node and why
`externalTrafficPolicy: Local` exists (it disables that hop, preserving the client IP, at the
cost of nodes with no local Pod refusing traffic).

A NodePort Service is **a superset of ClusterIP** — it keeps its VIP:

```console
$ kubectl exec curl-test-pod -- curl -s -o /dev/null -w 'ClusterIP path -> %{http_code}' http://web-service-nodeport:80
ClusterIP path -> 200

$ kubectl get svc web-service-nodeport -o jsonpath='type={.spec.type} clusterIP={.spec.clusterIP} port={.spec.ports[0].port} targetPort={.spec.ports[0].targetPort} nodePort={.spec.ports[0].nodePort}'
type=NodePort clusterIP=10.96.224.248 port=80 targetPort=80 nodePort=30080
```

---

## Lab 3 — LoadBalancer: what happens with no cloud provider

```console
$ kubectl get svc web-service-loadbalancer
NAME                       TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
web-service-loadbalancer   LoadBalancer   10.96.56.20   <pending>     80:30355/TCP   21s
```

`EXTERNAL-IP` is **`<pending>`**, and it will stay pending forever. This is the most useful thing
this lab can show, because it is the exact symptom people hit on a bare-metal or local cluster.

```console
$ kubectl get svc web-service-loadbalancer -o jsonpath='type={.spec.type} clusterIP={.spec.clusterIP} nodePort={.spec.ports[0].nodePort} ingressStatus={.status.loadBalancer}'
type=LoadBalancer clusterIP=10.96.56.20 nodePort=30355 ingressStatus={}

$ kubectl describe svc web-service-loadbalancer | grep -A5 'Events:'
Events:                   <none>
```

`status.loadBalancer` is an empty object and there are **no events at all** — nothing failed,
because nothing tried. `type: LoadBalancer` is a *request* that a cloud-controller-manager is
supposed to see and act on by provisioning a real load balancer (an AWS ELB, a GCP forwarding
rule) and writing its address back into `status`. kind has no such controller, so the request is
simply never picked up. On bare metal, MetalLB is what fills that role.

Note what it *did* get: a ClusterIP **and** an auto-allocated `nodePort: 30355`. The three types
are layered, not parallel:

```
LoadBalancer  =  NodePort   +  a cloud LB pointed at those node ports
NodePort      =  ClusterIP  +  a port opened on every node
ClusterIP     =  a VIP      +  a selector-driven endpoint list
```

Which is why the Service still works perfectly from inside:

```console
$ kubectl exec curl-test-pod -- curl -s -o /dev/null -w 'via ClusterIP -> %{http_code}' http://web-service-loadbalancer
via ClusterIP -> 200
```

"`EXTERNAL-IP` pending" never means the app is broken. It means nobody is listening to your
request for a load balancer.

---

## Lab 4 — ExternalName: a DNS alias, and nothing else

```console
$ kubectl get svc external-database-service
NAME                        TYPE           CLUSTER-IP   EXTERNAL-IP        PORT(S)   AGE
external-database-service   ExternalName   <none>       nencyravaliya.me   <none>    0s

$ kubectl get svc external-database-service -o jsonpath='type={.spec.type} externalName={.spec.externalName} clusterIP={.spec.clusterIP}'
type=ExternalName externalName=nencyravaliya.me clusterIP=
```

No ClusterIP. No ports. No endpoints:

```console
$ kubectl get endpointslice -l kubernetes.io/service-name=external-database-service
No resources found in default namespace.
```

All it does is make CoreDNS answer with a CNAME:

```console
$ kubectl exec curl-test-pod -- nslookup external-database-service.default.svc.cluster.local
Server:		10.96.0.10
Address:	10.96.0.10:53

external-database-service.default.svc.cluster.local	canonical name = nencyravaliya.me
```

The value of this is that your app config says `external-database-service` in every environment,
and the *Service* decides whether that means an RDS hostname in production or a staging box in
dev — no config change, no redeploy.

The caveats are the reason it is not used more:

- It is **DNS only**. No proxying, no load balancing, no health checks; `kube-proxy` is not
  involved at all.
- Port remapping is impossible — the client must use the real port, since the Service has none.
- TLS breaks if the external host validates SNI/Host against the name the client used.
- It cannot alias a raw IP. For that you need a Service with no selector (Lab 7).

---

## Lab 5 — Headless Service: DNS that returns every Pod

```console
$ kubectl get svc web-service-headless
NAME                   TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
web-service-headless   ClusterIP   None         <none>        80/TCP    2s
```

`CLUSTER-IP: None` — set explicitly with `clusterIP: None`. That single field changes what DNS
returns.

```console
$ kubectl get pods -l app=web-headless -o wide --no-headers | awk '{print $1, $6}'
web-stateful-0 10.244.2.58
web-stateful-1 10.244.1.71
web-stateful-2 10.244.1.72

$ kubectl exec curl-test-pod -- nslookup web-service-headless.default.svc.cluster.local
Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	web-service-headless.default.svc.cluster.local
Address: 10.244.1.71
Name:	web-service-headless.default.svc.cluster.local
Address: 10.244.2.58
Name:	web-service-headless.default.svc.cluster.local
Address: 10.244.1.72
```

**Three A records, one per Pod** — the actual Pod IPs, not a VIP. A normal ClusterIP Service
returns exactly one address (its VIP) and hides the Pods behind iptables. Here the client gets
the full membership list and chooses for itself.

And because the StatefulSet's `serviceName` points at this Service, each Pod also gets its own
resolvable name:

```console
$ kubectl exec curl-test-pod -- nslookup web-stateful-0.web-service-headless.default.svc.cluster.local
Name:	web-stateful-0.web-service-headless.default.svc.cluster.local
Address: 10.244.2.58
```

`10.244.2.58` is exactly `web-stateful-0`'s IP from the table above. That is what clustered
software needs and a ClusterIP cannot provide: a MongoDB replica set has to know *which* member
is the primary, Kafka clients must reach a *specific* broker that owns a partition, and a
Postgres client must send writes to the leader and reads to a replica. "Any healthy backend" is
the wrong answer to all three.

| | ClusterIP | Headless |
|---|---|---|
| `clusterIP` | a VIP | `None` |
| DNS returns | 1 address (the VIP) | **every ready Pod IP** |
| Load balancing | kube-proxy, per connection | **the client's problem** |
| Per-Pod DNS | no | yes, with a StatefulSet |
| Use for | stateless apps | StatefulSets, clustered databases, service discovery |

---

## Lab 6 — CoreDNS and FQDN

### Where DNS comes from

```console
$ kubectl exec curl-test-pod -- cat /etc/resolv.conf
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

Three lines, injected by the kubelet into every Pod:

- **`nameserver 10.96.0.10`** — CoreDNS, reached through an ordinary ClusterIP Service:

  ```console
  $ kubectl get svc kube-dns -n kube-system
  NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
  kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   32m

  $ kubectl get pods -n kube-system -l k8s-app=kube-dns
  NAME                       READY   STATUS    RESTARTS   AGE
  coredns-559f6c778d-9vm79   1/1     Running   0          32m
  coredns-559f6c778d-ptz29   1/1     Running   0          32m
  ```

  Cluster DNS is itself just two Pods behind a Service. The Service name is `kube-dns` for
  backwards compatibility even though the software is CoreDNS.

- **`search default.svc.cluster.local …`** — why `curl http://echo-service` works without a
  domain. The resolver appends each suffix in turn until one resolves.
- **`options ndots:5`** — any name with fewer than 5 dots gets the search suffixes tried
  **first**. `echo-service` (0 dots) is tried as `echo-service.default.svc.cluster.local` before
  ever being tried as a public name. This is also a known latency trap: an external lookup like
  `api.github.com` (2 dots) wastes three failed queries before succeeding, which is why
  performance-sensitive apps use a trailing dot (`api.github.com.`) or a custom `dnsConfig`.

### FQDN anatomy

```
web-service-headless   .   default    .  svc  .  cluster.local
└─ Service name ──┘        └─ ns ─┘      └┬┘     └─ cluster domain ─┘
                                      resource type
```

### The same short name means different things to different clients

`cross-namespace.yaml` creates a Service called `api` in **both** `team-a` and `team-b`, each
serving a different page, plus a client Pod in `team-a`:

```console
$ kubectl exec client -n team-a -- curl -s http://api
I am the API in namespace team-a

$ kubectl exec client -n team-a -- curl -s http://api.team-b
I am the API in namespace team-b

$ kubectl exec client -n team-a -- curl -s http://api.team-b.svc.cluster.local
I am the API in namespace team-b
```

The short name `api` resolved to the **local** namespace's Service, because of that client's own
search path:

```console
$ kubectl exec client -n team-a -- cat /etc/resolv.conf
search team-a.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

`team-a.svc.cluster.local` is first. The identical URL from a Pod in `default` resolves to
nothing at all:

```console
$ kubectl exec curl-test-pod -- curl -s --max-time 5 http://api
command terminated with exit code 6
(no api Service in default namespace)
```

curl exit code **6 is "could not resolve host"** — a DNS failure, not a connection failure.
Worth knowing by heart: exit 6 = DNS, exit 7 = connection refused, exit 28 = timeout. Those
three distinguish "wrong name" from "no endpoints" from "wrong port" without any further
digging.

The lesson for config files: `api` is ambiguous and moves with whatever namespace the caller
happens to run in. Use `api.team-b` for cross-namespace calls, or the full FQDN when you want
zero ambiguity.

---

## Lab 7 — A Service with no selector

From `service.md` section 6, and a common interview question: a Service does not *have* to have
a selector. Without one, the endpoint controller leaves it alone and you write the endpoints
yourself.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: legacy-db
spec:
  # No selector at all. Nothing will ever be auto-populated here.
  ports:
    - name: http
      port: 80
      targetPort: 80
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: legacy-db-manual
  labels:
    kubernetes.io/service-name: legacy-db    # this label is the link to the Service
addressType: IPv4
ports:
  - name: http
    port: 80
    protocol: TCP
endpoints:
  - addresses: ["10.244.1.67"]
    conditions:
      ready: true
```

The manifest ships `PLACEHOLDER_IP` rather than a hardcoded address, since a Pod IP is only
valid on the cluster that issued it. `apply.sh` substitutes a live one:

```console
$ ./lab7-no-selector/apply.sh
Targeting echo-app Pod IP: 10.244.2.65
service/legacy-db created
endpointslice.discovery.k8s.io/legacy-db-manual configured

Selector:                 <none>
Endpoints:                10.244.2.65:80
```

```console
$ kubectl get svc legacy-db -o jsonpath='selector={.spec.selector} clusterIP={.spec.clusterIP}'
selector= clusterIP=10.96.189.129

$ kubectl describe svc legacy-db | grep -E 'Selector:|Endpoints:'
Selector:                 <none>
Endpoints:                10.244.1.67:80

$ kubectl exec curl-test-pod -- curl -s --max-time 5 http://legacy-db
POD: echo-app-5f9849999b-gnnn2
```

`Selector: <none>` and yet it has a working endpoint and a ClusterIP that load-balances to it.
Unlike ExternalName, this **does** go through kube-proxy, which means it works with raw IPs, can
remap ports, and does not depend on the client resolving an external hostname. It is the right
tool for putting a cluster-internal DNS name and VIP in front of an on-prem database or a legacy
VM during a migration.

---

## Troubleshooting — a Service with no endpoints

Two distinct causes, identical symptom. Both are worth being able to tell apart in seconds.

### Cause 1 — the selector matches nothing

```console
$ kubectl apply -f troubleshooting/empty-endpoints.yaml
service/broken-backend-service created

$ kubectl get svc broken-backend-service
NAME                     TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
broken-backend-service   ClusterIP   10.96.23.76   <none>        80/TCP    5s
```

The Service looks completely healthy — it has a ClusterIP and an age. But:

```console
$ kubectl describe svc broken-backend-service | grep -E 'Selector:|Endpoints:'
Selector:                 app=wrong-backend-name
Endpoints:

$ kubectl exec curl-test-pod -- curl -s --max-time 5 -o /dev/null -w 'status=%{http_code}' http://broken-backend-service
status=000command terminated with exit code 7
```

Exit **7**, connection refused: the name resolved (the Service exists) but there is nothing
behind it. Triage is three commands:

```console
$ kubectl get svc broken-backend-service -o jsonpath='selector={.spec.selector}'
selector={"app":"wrong-backend-name"}

$ kubectl get pods -l app=wrong-backend-name
No resources found in default namespace.

$ kubectl get pods -l app=echo-app --show-labels --no-headers | head -2
echo-app-5f9849999b-gnnn2   1/1   Running   0   3m   app=echo-app,pod-template-hash=5f9849999b
echo-app-5f9849999b-k6zlq   1/1   Running   0   3m   app=echo-app,pod-template-hash=5f9849999b
```

Ask the Service what it selects, then ask the cluster whether anything carries that label. Here
nothing does. Fix the selector and endpoints appear within seconds:

```console
$ kubectl patch svc broken-backend-service -p '{"spec":{"selector":{"app":"echo-app"},"ports":[{"name":"http","port":80,"targetPort":80}]}}'
service/broken-backend-service patched

$ kubectl describe svc broken-backend-service | grep -E 'Selector:|Endpoints:'
Selector:                 app=echo-app
Endpoints:                10.244.1.66:80,10.244.1.67:80,10.244.2.55:80

$ kubectl exec curl-test-pod -- curl -s --max-time 5 http://broken-backend-service
POD: echo-app-5f9849999b-qjvq9
```

### Cause 2 — the selector is right and the Pods are not Ready

This is the one that wastes afternoons, because the selector *checks out*.
`unready-endpoints.yaml` has a correct selector and a readiness probe pointed at a path nginx
does not serve:

```console
$ kubectl get pods -l app=unready-app
NAME                          READY   STATUS    RESTARTS   AGE
unready-app-686b5dc86-h4z75   0/1     Running   0          25s
unready-app-686b5dc86-zs24m   0/1     Running   0          25s

$ kubectl describe svc unready-service | grep -E 'Selector:|Endpoints:'
Selector:                 app=unready-app
Endpoints:
```

`STATUS: Running`, selector matches, endpoints empty. The giveaway is **`READY 0/1`**, and the
EndpointSlice spells it out — the addresses *are* there, flagged unusable:

```console
$ kubectl get endpointslice -l kubernetes.io/service-name=unready-service -o jsonpath='{range .items[*].endpoints[*]}addr={.addresses[0]} ready={.conditions.ready}{"\n"}{end}'
addr=10.244.1.74 ready=false
addr=10.244.2.61 ready=false
```

```console
$ kubectl describe pod unready-app-686b5dc86-h4z75 | grep -E 'Warning.*Unhealthy'
  Warning  Unhealthy  43s                kubelet            spec.containers{web}: Readiness probe failed: Get "http://10.244.1.74:80/healthz-that-does-not-exist": dial tcp 10.244.1.74:80: connect: connection refused
  Warning  Unhealthy  0s (x15 over 42s)  kubelet            spec.containers{web}: Readiness probe failed: HTTP probe failed with statuscode: 404
```

The probe's own history in two lines: first `connection refused` while nginx was still starting,
then a steady `statuscode: 404` once it was up — the app is fine, the probe's path is wrong.

This is the readiness contract doing its job: a Pod that is not Ready receives **no Service
traffic**. It is what makes rolling updates safe (previous task, Lab 3) and it is why a broken
health check takes an entire Deployment out of service while every Pod reports `Running`.

### The triage order

```
kubectl get svc <svc>            # does it exist, does it have a ClusterIP?
kubectl describe svc <svc>       # Selector + Endpoints — the two lines that matter
   Endpoints empty?
     -> kubectl get pods -l <the selector>
          nothing returned?      -> selector/label mismatch          (cause 1)
          returned but 0/1 READY -> readiness probe failing          (cause 2)
   Endpoints present but requests fail?
     -> compare port / targetPort / containerPort   (curl exit 28, timeout)
```

And by curl exit code: **6** = DNS, wrong name or namespace. **7** = resolved, no endpoints.
**28** = timeout, usually the wrong port.

---

## Cleanup

```bash
kubectl delete -f lab1-clusterip/ -f lab2-nodeport/ -f lab3-loadbalancer/
kubectl delete -f lab4-externalname/service.yaml
kubectl delete -f lab5-headless/
kubectl delete pvc -l app=web-headless          # if the StatefulSet declared any
kubectl delete svc legacy-db && kubectl delete endpointslice legacy-db-manual
kubectl delete -f troubleshooting/
kubectl delete -f lab6-dns-fqdn/cross-namespace.yaml    # deletes namespaces team-a, team-b
kubectl delete pod curl-test-pod
```
