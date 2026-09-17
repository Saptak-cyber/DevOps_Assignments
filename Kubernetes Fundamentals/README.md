# Kubernetes Fundamentals

Source material: [`devops-heros/session9-k8s`](../../devops-heros/session9-k8s) — the
Kubernetes Basics tutorial, the cluster-architecture docs and the minikube quick-start
linked in that session's `Readme.md`.

Every console block below is **real captured output** from a live 3-node cluster
(Kubernetes **v1.37.0**, containerd 2.3.4, kind v0.33.0). Nothing is illustrative.

## Folder structure

```
Kubernetes Fundamentals/
├── README.md
├── cluster/kind-config.yaml              # the 3-node cluster used for all 4 K8s tasks
├── lab1-first-pod/nginx-pod.yaml         # smallest deployable unit
├── lab2-namespaces/
│   ├── namespaces.yaml                   # dev + production namespaces
│   └── pods-in-namespaces.yaml           # same Pod name in both namespaces
└── lab3-architecture-tour/tour.sh        # read-only walk over the control plane
```

---

## Part A — MCQs

**MCQ 1.** Which control-plane component decides *which node* a new Pod runs on?

- A. `kubelet`
- B. `kube-scheduler`
- C. `kube-controller-manager`
- D. `etcd`

**Answer: B. `kube-scheduler`** — it watches for Pods with an empty `spec.nodeName`, filters
nodes that *can* run the Pod, scores the survivors, and writes the winner back. It never
starts a container itself; it only makes the decision.

**MCQ 2.** What is the smallest object you can deploy in Kubernetes?

- A. A container
- B. A Deployment
- C. A Pod
- D. A node

**Answer: C. A Pod** — Kubernetes has no API for "run one container". The Pod is the atomic
scheduling unit; a container only ever exists inside one.

**MCQ 3.** Which component runs on **every** node and actually starts the containers?

- A. `kube-apiserver`
- B. `kube-proxy`
- C. `kubelet`
- D. CoreDNS

**Answer: C. `kubelet`** — it takes the PodSpecs assigned to its node and drives the container
runtime (containerd here) to make reality match them, then reports status back.

**MCQ 4.** Where is all cluster state stored?

- A. In `kubelet`'s local cache on each node
- B. In `etcd`
- C. In the `kube-controller-manager`'s memory
- D. In the container images

**Answer: B. `etcd`** — a consistent key-value store. It is the single source of truth; losing
`etcd` without a backup means losing the cluster's entire state.

**MCQ 5.** Which command shows you which node a Pod landed on?

- A. `kubectl get pods`
- B. `kubectl get pods -o wide`
- C. `kubectl logs <pod>`
- D. `kubectl api-resources`

**Answer: B. `kubectl get pods -o wide`** — the default output omits the `IP` and `NODE`
columns. Proof is in Lab 1 below.

---

## Part B — Cluster architecture, verified against a live cluster

### The two planes

```
        ┌──────────────────── CONTROL PLANE (the brain) ─────────────────────┐
        │                                                                    │
        │   kube-apiserver  ←── the ONLY component that talks to etcd        │
        │        │  (REST + auth + admission; everything goes through here)  │
        │        ├── etcd                     consistent state store         │
        │        ├── kube-scheduler           picks a node for each Pod      │
        │        └── kube-controller-manager  drives actual → desired state  │
        └────────────────────────────┬───────────────────────────────────────┘
                                     │  (watch / report)
        ┌────────────────────────────┴───────────────────────────────────────┐
        │                     WORKER NODES (the muscle)                      │
        │   kubelet        starts + supervises containers on this node       │
        │   kube-proxy     programs iptables so Service VIPs work            │
        │   containerd     the container runtime that pulls and runs images  │
        └────────────────────────────────────────────────────────────────────┘
              + add-ons: CoreDNS (cluster DNS), CNI plugin (Pod networking)
```

### Step B.1 — Who is in the cluster

```console
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:50268
CoreDNS is running at https://127.0.0.1:50268/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

$ kubectl get nodes
NAME                       STATUS   ROLES           AGE    VERSION
devops-k8s-control-plane   Ready    control-plane   115s   v1.37.0
devops-k8s-worker          Ready    <none>          105s   v1.37.0
devops-k8s-worker2         Ready    <none>          105s   v1.37.0
```

Three nodes: one control plane, two workers. `ROLES` is `<none>` for workers — a "worker" is
simply a node with no control-plane role label, not a separate kind of thing.

### Step B.2 — See the control plane running as Pods

```console
$ kubectl get pods -n kube-system
NAME                                               READY   STATUS    RESTARTS   AGE
coredns-559f6c778d-9vm79                           1/1     Running   0          2m6s
coredns-559f6c778d-ptz29                           1/1     Running   0          2m6s
etcd-devops-k8s-control-plane                      1/1     Running   0          2m13s
kindnet-jwxl6                                      1/1     Running   0          2m6s
kindnet-kqvhv                                      1/1     Running   0          2m5s
kindnet-ld564                                      1/1     Running   0          2m5s
kube-apiserver-devops-k8s-control-plane            1/1     Running   0          2m14s
kube-controller-manager-devops-k8s-control-plane   1/1     Running   0          2m13s
kube-proxy-pvgst                                   1/1     Running   0          2m5s
kube-proxy-t6gph                                   1/1     Running   0          2m5s
kube-proxy-tpv8s                                   1/1     Running   0          2m6s
kube-scheduler-devops-k8s-control-plane            1/1     Running   0          2m13s
```

Every architecture diagram box above is a real Pod in `kube-system`. Note the counts, they
are the whole lesson:

| Component | Pods | Why that number |
|---|---|---|
| `etcd`, `kube-apiserver`, `kube-scheduler`, `kube-controller-manager` | **1 each** | Control plane — single control-plane node here (3+ in production for HA) |
| `kube-proxy`, `kindnet` (CNI) | **3 each** | One per node, every node needs networking — a **DaemonSet** |
| `coredns` | **2** | A Deployment, replicated for availability, not per-node |

Which node each one sits on:

```console
$ kubectl get pods -n kube-system -o wide --no-headers | awk '{print $1, $7}'
coredns-559f6c778d-9vm79 devops-k8s-control-plane
coredns-559f6c778d-ptz29 devops-k8s-control-plane
etcd-devops-k8s-control-plane devops-k8s-control-plane
kindnet-jwxl6 devops-k8s-control-plane
kindnet-kqvhv devops-k8s-worker2
kindnet-ld564 devops-k8s-worker
kube-apiserver-devops-k8s-control-plane devops-k8s-control-plane
kube-controller-manager-devops-k8s-control-plane devops-k8s-control-plane
kube-proxy-pvgst devops-k8s-worker2
kube-proxy-t6gph devops-k8s-worker
kube-proxy-tpv8s devops-k8s-control-plane
kube-scheduler-devops-k8s-control-plane devops-k8s-control-plane
```

The four control-plane components are **only** on `devops-k8s-control-plane`. `kube-proxy` and
`kindnet` appear once per node, exactly as the table predicts.

---

## Lab 1 — Your first Pod, and the lifecycle trace that proves the architecture

`lab1-first-pod/nginx-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-first-pod
  labels:
    app: my-first-pod
    course: devops-heros
spec:
  containers:
    - name: nginx
      image: nginx:1.25-alpine
      ports:
        - containerPort: 80
      resources:
        requests:
          cpu: "50m"
          memory: "64Mi"
        limits:
          cpu: "200m"
          memory: "128Mi"
```

```console
$ kubectl apply -f lab1-first-pod/nginx-pod.yaml
pod/my-first-pod created

$ kubectl get pod my-first-pod -o wide
NAME           READY   STATUS    RESTARTS   AGE   IP           NODE                 NOMINATED NODE   READINESS GATES
my-first-pod   1/1     Running   0          12s   10.244.1.3   devops-k8s-worker2   <none>           <none>
```

`READY 1/1` = one of one container passing. The Pod got IP `10.244.1.3` from the CNI and was
placed on `devops-k8s-worker2` — a decision **I never made**, the scheduler did.

### The event trace — the whole architecture in five lines

```console
$ kubectl get events --field-selector involvedObject.name=my-first-pod --sort-by=.lastTimestamp
LAST SEEN   TYPE     REASON      OBJECT             MESSAGE
20s         Normal   Scheduled   pod/my-first-pod   Successfully assigned default/my-first-pod to devops-k8s-worker2
20s         Normal   Pulling     pod/my-first-pod   Pulling image "nginx:1.25-alpine"
9s          Normal   Pulled      pod/my-first-pod   Successfully pulled image "nginx:1.25-alpine" in 11.212s (11.212s including waiting). Image size: 20193659 bytes.
9s          Normal   Created     pod/my-first-pod   Container created
9s          Normal   Started     pod/my-first-pod   Container started
```

Read it as a handover, because that is exactly what it is:

1. `Scheduled` — **kube-scheduler** chose `worker2` and wrote `spec.nodeName` back through the
   API server.
2. `Pulling` / `Pulled` — **kubelet on worker2** noticed a Pod assigned to it and told
   **containerd** to fetch the image. It took 11.2s; that gap is why a fresh Pod sits in
   `ContainerCreating`.
3. `Created` / `Started` — containerd created and started the container; kubelet reported
   `Running` back to the API server.

Nobody in that chain talked to `etcd` except the API server. That is the rule.

### Pod phase vs. what `get pods` prints

```console
$ kubectl get pod my-first-pod -o jsonpath='{.status.phase}'
Running
```

The five official **phases** are `Pending`, `Running`, `Succeeded`, `Failed`, `Unknown`. The
`STATUS` column lies slightly for convenience — it also prints reasons like
`ContainerCreating`, `CrashLoopBackOff` and `Completed`, which are *not* phases. (This is
explored in depth in [Kubernetes Pods, ReplicaSets & Deployments](../Kubernetes%20Pods,%20ReplicaSets%20&%20Deployments/).)

```console
$ kubectl describe pod my-first-pod | sed -n '1,20p'
Name:             my-first-pod
Namespace:        default
Priority:         0
Service Account:  default
Node:             devops-k8s-worker2/172.18.0.2
Start Time:       Thu, 17 Sep 2026 23:42:22 +0530
Labels:           app=my-first-pod
                  course=devops-heros
Annotations:      <none>
Status:           Running
IP:               10.244.1.3
IPs:
  IP:  10.244.1.3
Containers:
  nginx:
    Container ID:   containerd://4a1305b0beef0de0765e7d26c4af742a77443ade50b6dd626684c76d5fa9c606
    Image:          nginx:1.25-alpine
    Image ID:       docker.io/library/nginx@sha256:516475cc129da42866742567714ddc681e5eed7b9ee0b9e9c015e464b4221a00
    Port:           80/TCP
    Host Port:      0/TCP
```

`Container ID: containerd://…` is the proof that Kubernetes is not a container runtime — it
*delegates* to one via the CRI.

---

## Lab 2 — Namespaces: the scope for object names

```console
$ kubectl apply -f lab2-namespaces/namespaces.yaml
namespace/dev created
namespace/production created

$ kubectl apply -f lab2-namespaces/pods-in-namespaces.yaml
pod/web created
pod/web created
```

Two `pod/web created` lines from one file — the **same name twice**, which would be illegal in
a single namespace:

```console
$ kubectl get pods --all-namespaces -l app=web
NAMESPACE    NAME   READY   STATUS    RESTARTS   AGE
dev          web    1/1     Running   0          21s
production   web    1/1     Running   0          20s
```

```console
$ kubectl get namespaces
NAME                 STATUS   AGE
default              Active   2m33s
dev                  Active   11s
ingress-nginx        Active   2m6s
kube-node-lease      Active   2m33s
kube-public          Active   2m33s
kube-system          Active   2m33s
local-path-storage   Active   2m29s
production           Active   11s
```

`default`, `kube-system`, `kube-public` and `kube-node-lease` are the four built-ins.

### The mistake everyone makes once

```console
$ kubectl get pod web -n dev
NAME   READY   STATUS    RESTARTS   AGE
web    1/1     Running   0          21s

$ kubectl get pod web
Error from server (NotFound): pods "web" not found
```

Identical command, one flag apart. Without `-n`, `kubectl` looks in `default`, where no `web`
Pod exists. `NotFound` almost always means *wrong namespace*, not *missing object*.

### Namespaced vs. cluster-scoped

```console
$ kubectl api-resources --namespaced=true -o name | head -12
bindings
configmaps
endpoints
events
limitranges
persistentvolumeclaims
pods
podtemplates
replicationcontrollers
resourcequotas
secrets
serviceaccounts

$ kubectl api-resources --namespaced=false -o name | head -8
componentstatuses
namespaces
nodes
persistentvolumes
mutatingadmissionpolicies.admissionregistration.k8s.io
mutatingadmissionpolicybindings.admissionregistration.k8s.io
mutatingwebhookconfigurations.admissionregistration.k8s.io
validatingadmissionpolicies.admissionregistration.k8s.io
```

Nodes and PersistentVolumes are **cluster-scoped** — physical-ish resources shared by
everyone. Pods, ConfigMaps and Secrets are namespaced. This is also the boundary RBAC and
ResourceQuotas work on.

---

## Lab 3 — The kubectl tour

Run `./lab3-architecture-tour/tour.sh` to replay all of this read-only.

### `kubectl explain` — the API reference offline

```console
$ kubectl explain pod.spec.containers.image
KIND:       Pod
VERSION:    v1

FIELD: image <string>

DESCRIPTION:
    Container image name. More info:
    https://kubernetes.io/docs/concepts/containers/images This field is optional
    to allow higher level config management to default or override container
    images in workload controllers like Deployments and StatefulSets.
```

`kubectl explain` beats guessing YAML field names — it reads the live cluster's own schema, so
it is never out of date with your version.

### Logs and exec

```console
$ kubectl logs my-first-pod | tail -4
2026/09/17 18:12:33 [notice] 1#1: start worker process 38
2026/09/17 18:12:33 [notice] 1#1: start worker process 39
2026/09/17 18:12:33 [notice] 1#1: start worker process 40
2026/09/17 18:12:33 [notice] 1#1: start worker process 41

$ kubectl exec my-first-pod -- nginx -v
nginx version: nginx/1.25.5

$ kubectl exec my-first-pod -- curl -s -o /dev/null -w '%{http_code}\n' localhost:80
200
```

The Pod serves HTTP 200 on its own port 80 — but only *inside* the cluster. Nothing outside
can reach `10.244.1.3` yet; that is what Services exist for, and is the subject of
[Kubernetes Networking & Services](../Kubernetes%20Networking%20&%20Services/).

### Imperative vs. declarative

| | Imperative | Declarative |
|---|---|---|
| Command | `kubectl run my-first-pod --image=nginx:1.25-alpine` | `kubectl apply -f nginx-pod.yaml` |
| State lives | in your shell history | in a file you can commit and review |
| Re-running it | errors — `AlreadyExists` | fine — converges, prints `unchanged` |
| Use it for | throwaway debug Pods | everything real |

`apply` is idempotent, which is the entire reason GitOps is possible. `create` is not.

---

## Cleanup

```bash
kubectl delete -f lab1-first-pod/nginx-pod.yaml
kubectl delete -f lab2-namespaces/pods-in-namespaces.yaml
kubectl delete -f lab2-namespaces/namespaces.yaml
```

Deleting a namespace deletes everything inside it — which is the fastest way to clean up a lab,
and the fastest way to lose production.

## Reproducing the cluster

```bash
kind create cluster --config cluster/kind-config.yaml
kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml
```

The config gives 3 nodes (so DaemonSets and NodePort are meaningful), labels the control plane
`ingress-ready=true`, and maps host ports `8080`/`8443` → container `80`/`443` plus NodePorts
`30080`/`30081`. The same cluster serves all four Kubernetes tasks.
