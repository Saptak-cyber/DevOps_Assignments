# Kubernetes Fundamentals

**Author:** Saptak Banerjee
**Course:** SST DevOps & Cloud [SWE]
**Session:** 09 — Kubernetes Fundamentals (Lecture 9)
**Source material:** [`devops-heros/session9-k8s`](../../devops-heros/session9-k8s)
**Environment:** macOS (Darwin 26.5.1, arm64) · Docker Desktop 29.6.1 · minikube docker driver

---

## Task 1: Minikube & CLI Installation Verification

Verify that `minikube` and the Kubernetes CLI (`kubectl`) are installed and resolvable on the local system.

**Commands:**

```bash
minikube version
kubectl version --client
```

**Output:**

```
$ minikube version
minikube version: v1.39.0
commit: 7a9f6a841470a207de8cf4bafcccee0969d8ba10

$ kubectl version --client
Client Version: v1.37.0
Kustomize Version: v5.8.1
```

**Screenshot:**

![Minikube and Kubectl Version](./screenshots/01-version-check.png)

---

## Task 2: Starting the Minikube Kubernetes Cluster

Initialise the local single-node Kubernetes cluster. minikube auto-selects the Docker driver, pulls the `kicbase` node image, and bootstraps the control plane inside a Docker container.

**Command:**

```bash
minikube start
```

**Output:**

```
$ minikube start
* minikube v1.39.0 on Darwin 26.5.1 (arm64)
* Automatically selected the docker driver
* Using Docker Desktop driver with root privileges
* Starting "minikube" primary control-plane node in "minikube" cluster
* Pulling base image v0.0.51 ...
* Configuring CNI (Container Networking Interface) ...
* Verifying Kubernetes components...
  - Using image gcr.io/k8s-minikube/storage-provisioner:v5
* Enabled addons: storage-provisioner, default-storageclass
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

> **Note:** the `kicbase` image is ~470 MiB, so the first `minikube start` on a fresh machine is dominated by the image pull. Subsequent starts reuse the cached image and complete in seconds.

**Screenshot:**

![Minikube Start](./screenshots/02-minikube-start.png)

---

## Task 3: Verifying Cluster Status & Node Health

Inspect the control plane, kubelet, and API server status, confirm the node reaches `Ready`, and locate the API server / CoreDNS service endpoints.

**Commands:**

```bash
minikube status
kubectl get nodes -o wide
kubectl cluster-info
kubectl get pods -n kube-system
```

**Output:**

```
$ minikube status
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

$ kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION             CONTAINER-RUNTIME
minikube   Ready    control-plane   44s   v1.37.0   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.12.76-linuxkit (arm64)   containerd://2.3.4

$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:60716
CoreDNS is running at https://127.0.0.1:60716/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

$ kubectl get pods -n kube-system
NAME                               READY   STATUS    RESTARTS   AGE
coredns-559f6c778d-6jwzc           0/1     Running   0          36s
etcd-minikube                      1/1     Running   0          42s
kindnet-wf229                      1/1     Running   0          36s
kube-apiserver-minikube            1/1     Running   0          42s
kube-controller-manager-minikube   1/1     Running   0          42s
kube-proxy-2mvm2                   1/1     Running   0          36s
kube-scheduler-minikube            1/1     Running   0          42s
storage-provisioner                1/1     Running   0          41s
```

**Observations:**

- Immediately after `minikube start`, the node reports `NotReady` for ~10 seconds. This is expected: the kubelet registers the node before the CNI plugin (`kindnet`) has finished wiring up pod networking, and the `Ready` condition only flips once the network is usable.
- Because this is a single-node cluster, the one node carries the `control-plane` role **and** runs workload pods. In a real cluster the control plane would normally carry a `NoSchedule` taint.
- `kubectl get pods -n kube-system` is the practical proof of Task 5's theory — every control plane component from the architecture diagram below appears here as a real running pod (`etcd-minikube`, `kube-apiserver-minikube`, `kube-scheduler-minikube`, `kube-controller-manager-minikube`), alongside the per-node agents (`kube-proxy`, `kindnet`).

**Screenshot:**

![Minikube Status and Nodes](./screenshots/03-minikube-status.png)

---

## Task 4: Stopping the Minikube Cluster

Gracefully power down the cluster container to release CPU and memory back to the host.

**Commands:**

```bash
minikube stop
minikube status
```

**Output:**

```
$ minikube stop
* Stopping node "minikube"  ...
* Powering off "minikube" via SSH ...
* 1 node stopped.

$ minikube status
minikube
type: Control Plane
host: Stopped
kubelet: Stopped
apiserver: Stopped
kubeconfig: Stopped
```

`minikube stop` preserves cluster state on disk — a later `minikube start` resumes the same cluster with all objects intact. `minikube delete` is the destructive counterpart that discards it.

**Screenshot:**

![Minikube Stop](./screenshots/04-minikube-stop.png)

---

## Task 5: Kubernetes Cluster Architecture & Component Analysis

A Kubernetes cluster splits into a **Control Plane** (decides what should run) and a set of **Worker Nodes** (actually run it). Every component talks to the API server; nothing else touches `etcd` directly.

```
+-------------------------------------------------------------------------------+
|                               CONTROL PLANE (MASTER)                          |
|                                                                               |
|   +-------------------+       +--------------------+       +--------------+   |
|   |       etcd        |<----->|  kube-apiserver    |<----->|kube-scheduler|   |
|   | (State Database)  |       |    (Front Door)    |       +--------------+   |
|   +-------------------+       +---------+----------+                          |
|                                         |                                     |
|                                         v                                     |
|                             +------------------------+                        |
|                             | kube-controller-manager|                        |
|                             +------------------------+                        |
+-----------------------------------------+-------------------------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
+------------------------------------+ +------------------------------------+
|          WORKER NODE 1             | |          WORKER NODE 2             |
|   +------------+  +------------+   | |   +------------+  +------------+   |
|   |  kubelet   |  | kube-proxy |   | |   |  kubelet   |  | kube-proxy |   |
|   +-----+------+  +-----+------+   | |   +-----+------+  +-----+------+   |
|         |               |          | |         |               |          |
|         v               v          | |         v               v          |
|   +----------------------------+   | |   +----------------------------+   |
|   | CRI (containerd runtime)   |   | |   | CRI (containerd runtime)   |   |
|   +----------------------------+   | |   +----------------------------+   |
|         |                          | |         |                          |
|         v                          | |         v                          |
|   +------------+  +------------+   | |   +------------+  +------------+   |
|   |   Pod 1    |  |   Pod 2    |   | |   |   Pod 3    |  |   Pod 4    |   |
|   | [Container]|  | [Container]|   | |   | [Container]|  | [Container]|   |
|   +------------+  +------------+   | |   +------------+  +------------+   |
+------------------------------------+ +------------------------------------+
```

### 1. Control Plane Components

| Component | Role | Seen in this cluster as |
| --- | --- | --- |
| `kube-apiserver` | The single front door. Exposes the REST API, authenticates/authorises every request, and is the **only** component that reads and writes `etcd`. `kubectl`, controllers, and kubelets all go through it. | `kube-apiserver-minikube` |
| `etcd` | Distributed, consistent key-value store holding the entire declarative cluster state — every object spec, status, and Secret. Losing `etcd` means losing the cluster. | `etcd-minikube` |
| `kube-scheduler` | Watches for Pods with no `nodeName` assigned and picks the best node using resource requests, node affinity/anti-affinity, taints and tolerations. It only *decides* placement; it never starts containers. | `kube-scheduler-minikube` |
| `kube-controller-manager` | Runs the reconciliation loops that drive **current state → desired state**. Bundles the Node controller (eviction on node failure), ReplicaSet controller (maintains replica count), EndpointSlice controller (binds Services to live Pod IPs), and others. | `kube-controller-manager-minikube` |

### 2. Worker Node Components

| Component | Role | Seen in this cluster as |
| --- | --- | --- |
| `kubelet` | The per-node agent. Receives `PodSpec`s from the API server, instructs the container runtime to pull images and start containers, runs liveness/readiness probes, and reports node + pod status back. Runs as a host process, not a pod. | host process on the `minikube` node |
| `kube-proxy` | Programs `iptables`/IPVS rules on each node so that Service virtual IPs load-balance to the correct backing Pod IPs. | `kube-proxy-2mvm2` (DaemonSet) |
| **CRI runtime** | The software that actually runs containers. Modern clusters use `containerd` or `CRI-O` via the Container Runtime Interface; the old Docker shim was removed in Kubernetes 1.24. | `containerd://2.3.4` (from `kubectl get nodes -o wide`) |
| **CNI plugin** | Assigns each Pod an IP and wires up pod-to-pod routing across nodes. | `kindnet-wf229` (DaemonSet) |
| **Pod** | Smallest deployable unit. One or more tightly-coupled containers sharing a network namespace (one IP, one port space) and volumes. Most pods run one app container plus optional init/sidecar containers. | every workload pod |

### 3. How a `kubectl apply` actually flows

1. `kubectl apply -f pod.yml` → HTTP POST to **kube-apiserver**.
2. API server authenticates, validates the object, and persists it to **etcd**. The Pod now exists as an API object with `nodeName: ""`.
3. **kube-scheduler** notices the unscheduled Pod, chooses a node, and writes the binding back through the API server.
4. The **kubelet** on that node sees a Pod bound to itself, calls the **CRI runtime** to pull the image and start containers, and the **CNI plugin** assigns the Pod IP.
5. kubelet reports status back to the API server → `kubectl get pods` shows `1/1 Running`.

> This is why a Pod referencing a non-existent image still gets *created* successfully: steps 1–3 all succeed and the object is safely in `etcd`. Only step 4 fails, which surfaces as `ErrImagePull` / `ImagePullBackOff` in the Pod's **status**, not as an error from `kubectl apply`.

**Screenshot:**

![Kubernetes Architecture Components](./screenshots/05-architecture-components.png)

---

## Resources

- https://kubernetes.io/docs/concepts/architecture/
- https://kubernetes.io/docs/tutorials/kubernetes-basics/
- https://minikube.sigs.k8s.io/docs/start/?arch=%2Fmacos%2Farm64%2Fstable%2Fbinary+download
- https://github.com/Nency-Ravaliya/Kubernetes
