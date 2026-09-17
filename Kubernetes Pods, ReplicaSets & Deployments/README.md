# Kubernetes Pods, ReplicaSets & Deployments

Source material: [`devops-heros/session10-k8s-core-objects`](../../devops-heros/session10-k8s-core-objects)
— the pod-lifecycle lab, the four deployment-strategy folders, the DaemonSet/StatefulSet
manifests and the two troubleshooting drills. Manifests marked *(course manifest)* are taken
from that session unchanged.

Every console block is **real captured output** from the 3-node cluster built in
[Kubernetes Fundamentals](../Kubernetes%20Fundamentals/) (Kubernetes v1.37.0).

## Folder structure

```
Kubernetes Pods, ReplicaSets & Deployments/
├── README.md
├── lab1-pod-lifecycle/           01..12-*.yaml   all 12 lifecycle states (course manifests)
├── lab2-replicaset/
│   ├── replicaset.yaml                           3 replicas, self-healing
│   └── adopted-pod.yaml                          bare Pod with a matching label
├── lab3-deployment-rollout/deployment.yaml       rollout, history, rollback
├── lab4-strategies/
│   ├── client-pod.yaml                           in-cluster curl client
│   ├── rolling/      v1, v2 (course) + v1/v2-prestop variants written for this task
│   ├── recreate/     v1, v2, service              (course manifests)
│   ├── blue-green/   blue, green, 2 services      (course manifests)
│   └── canary/       stable(9), canary(1), service (course manifests)
├── lab5-daemonset-statefulset/
│   ├── node-agent-ds.yaml                        (course manifest)
│   ├── statefulset.yaml                          (course manifest, MySQL — see note)
│   └── statefulset-web.yaml                      runnable StatefulSet + headless Service
└── troubleshooting/  broken-image.yaml, selector-mismatch.yaml (course manifests)
```


> **Run `kubectl` from inside this folder.** `kubectl -f` treats a comma as a
> separator between file paths, so any path containing a comma is split apart:
>
> ```console
> $ kubectl apply -f "Kubernetes Pods, ReplicaSets & Deployments/lab2-replicaset/replicaset.yaml"
> the path "Kubernetes Pods" does not exist
> the path " ReplicaSets & Deployments/lab2-replicaset/replicaset.yaml" does not exist
> ```
>
> `cd` into the task folder first and use the relative paths shown in each lab
> (`kubectl apply -f lab2-replicaset/replicaset.yaml`), which contain no comma.

---

## Part A — MCQs

**MCQ 1.** Which object does a Deployment directly manage?

- A. Pods
- B. ReplicaSets
- C. Nodes
- D. Services

**Answer: B. ReplicaSets** — the Deployment creates one ReplicaSet per revision of the Pod
template; that ReplicaSet creates the Pods. Proven by the `ownerReferences` output in Lab 3.

**MCQ 2.** How many official Pod **phases** are there?

- A. 3
- B. 5
- C. 8
- D. As many as `kubectl get pods` can print in STATUS

**Answer: B. 5** — `Pending`, `Running`, `Succeeded`, `Failed`, `Unknown`. `CrashLoopBackOff`
and `ImagePullBackOff` are *container waiting reasons*, not phases. Lab 1 shows a Pod whose
STATUS is `CrashLoopBackOff` while its phase is `Running`.

**MCQ 3.** A ReplicaSet has `replicas: 3` and three Pods running. You create a fourth bare Pod
carrying the same label as the ReplicaSet's selector. What happens?

- A. Nothing, the ReplicaSet ignores Pods it did not create
- B. The ReplicaSet scales up to 4
- C. The ReplicaSet deletes one Pod to get back to 3
- D. The API server rejects the Pod

**Answer: C** — a ReplicaSet reconciles against its **selector**, not against what it created.
It adopts the new Pod, counts 4, and deletes one. Real event log in Lab 2.

**MCQ 4.** Which strategy guarantees that two versions **never** serve traffic at the same time?

- A. RollingUpdate
- B. Recreate
- C. Canary
- D. Blue-green with a shared selector

**Answer: B. Recreate** — it terminates every old Pod before creating any new one, accepting
downtime to get that guarantee. Lab 4 measures both the guarantee and the outage.

**MCQ 5.** `kubectl rollout undo` works because:

- A. Kubernetes stores a backup of the image in etcd
- B. The old ReplicaSet is kept at 0 replicas and can be scaled back up
- C. The container runtime caches the previous container
- D. `kubectl` re-reads your local YAML file

**Answer: B** — old ReplicaSets are retained (`revisionHistoryLimit`, default 10) at 0 replicas.
Rollback is just scaling the old one up and the new one down. Lab 3 shows both ReplicaSets.

---

## Lab 1 — The Pod lifecycle, all 12 states at once

```console
$ kubectl apply -f lab1-pod-lifecycle/
pod/lifecycle-running created
pod/lifecycle-pending created
pod/lifecycle-succeeded created
pod/lifecycle-failed created
pod/lifecycle-crashloop created
pod/lifecycle-image-error created
pod/lifecycle-readiness created
pod/lifecycle-liveness created
pod/lifecycle-startup created
pod/lifecycle-init created
pod/lifecycle-multi-container created
pod/lifecycle-termination created
```

40 seconds later, every state in one table:

```console
$ kubectl get pods -o wide
NAME                        READY   STATUS             RESTARTS      AGE   IP            NODE                 NOMINATED NODE   READINESS GATES
lifecycle-crashloop         0/1     Error              1 (16s ago)   41s   10.244.1.7    devops-k8s-worker2   <none>           <none>
lifecycle-failed            0/1     Error              0             41s   10.244.1.6    devops-k8s-worker2   <none>           <none>
lifecycle-image-error       0/1     ImagePullBackOff   0             41s   10.244.2.6    devops-k8s-worker    <none>           <none>
lifecycle-init              1/1     Running            0             40s   10.244.1.9    devops-k8s-worker2   <none>           <none>
lifecycle-liveness          1/1     Running            0             41s   10.244.1.8    devops-k8s-worker2   <none>           <none>
lifecycle-multi-container   2/2     Running            0             40s   10.244.2.9    devops-k8s-worker    <none>           <none>
lifecycle-pending           0/1     Pending            0             41s   <none>        <none>               <none>           <none>
lifecycle-readiness         1/1     Running            0             41s   10.244.2.7    devops-k8s-worker    <none>           <none>
lifecycle-running           1/1     Running            0             41s   10.244.1.5    devops-k8s-worker2   <none>           <none>
lifecycle-startup           0/1     Running            0             41s   10.244.2.8    devops-k8s-worker    <none>           <none>
lifecycle-succeeded         0/1     Completed          0             41s   10.244.2.5    devops-k8s-worker    <none>           <none>
lifecycle-termination       1/1     Running            0             40s   10.244.1.10   devops-k8s-worker2   <none>           <none>
```

### The distinction the STATUS column hides

`STATUS` is a **blend** of the Pod phase and the first container's waiting/terminated reason.
Ask for the phase separately and they disagree:

```console
$ kubectl get pods -o custom-columns='NAME:.metadata.name,PHASE:.status.phase,STATUS_COL:.status.containerStatuses[0].state'
NAME                        PHASE       STATUS_COL
lifecycle-crashloop         Running     map[terminated:map[... exitCode:1 ... reason:Error ...]]
lifecycle-failed            Failed      map[terminated:map[... exitCode:1 ... reason:Error ...]]
lifecycle-image-error       Pending     map[waiting:map[message:failed to pull and unpack image "docker.io/library/jakwehrgkaejw:kahsdfgkhj": ... reason:ErrImagePull]]
lifecycle-init              Running     map[running:map[startedAt:2026-09-17T18:16:01Z]]
lifecycle-pending           Pending     <none>
lifecycle-succeeded         Succeeded   map[terminated:map[... exitCode:0 ... reason:Completed ...]]
```

Two results worth memorising:

| Pod | `STATUS` column | Actual **phase** | Why |
|---|---|---|---|
| `lifecycle-crashloop` | `CrashLoopBackOff` | **`Running`** | The Pod is alive and its `restartPolicy` is working. The *container* keeps dying; the Pod has not failed. |
| `lifecycle-image-error` | `ImagePullBackOff` | **`Pending`** | No container ever started, so the Pod never reached `Running`. |

Confirmed directly:

```console
$ kubectl get pod lifecycle-crashloop
NAME                  READY   STATUS             RESTARTS      AGE
lifecycle-crashloop   0/1     CrashLoopBackOff   4 (76s ago)   3m30s

$ kubectl get pod lifecycle-crashloop -o jsonpath='phase={.status.phase} waitingReason={.status.containerStatuses[0].state.waiting.reason} restarts={.status.containerStatuses[0].restartCount}'
phase=Running waitingReason=CrashLoopBackOff restarts=4
```

`RESTARTS 4` after 3m30s, not 20 — the kubelet backs off exponentially (10s, 20s, 40s, 80s,
capped at 5min). That is why a crashing Pod's `RESTARTS` count climbs slowly, and why
`CrashLoopBackOff` is a *waiting* state: the container is not running, the kubelet is sleeping
before the next attempt.

### Why `Pending` is almost always a scheduling problem

`02-pending.yaml` requests `memory: 9Gi` on nodes that have ~8Gi:

```console
$ kubectl describe pod lifecycle-pending | grep -A5 'Events:'
Events:
  Type     Reason            Age                From               Message
  ----     ------            ----               ----               -------
  Warning  FailedScheduling  19s (x3 over 50s)  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint(s), 2 Insufficient memory. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.
```

The scheduler reports *per-node* reasons: 1 node rejected on a **taint** (the control plane),
2 on **insufficient memory**. `NODE` is `<none>` and the IP is `<none>` — an unscheduled Pod has
no node and no network identity at all.

### `Succeeded` vs `Failed` — the exit code decides

```console
$ kubectl logs lifecycle-succeeded
Task started
Task completed successfully

$ kubectl get pod lifecycle-failed -o jsonpath='phase={.status.phase} exitCode={.status.containerStatuses[0].state.terminated.exitCode} reason={.status.containerStatuses[0].state.terminated.reason}'
phase=Failed exitCode=1 reason=Error
```

Exit `0` → phase `Succeeded`, STATUS prints `Completed`. Any non-zero exit → phase `Failed`,
STATUS prints `Error`. Both have `restartPolicy: Never`; with the default `Always` the failed
one would have become the `CrashLoopBackOff` above.

### ImagePullBackOff — read the message, it names the fix

```console
$ kubectl describe pod lifecycle-image-error | grep -A8 'Events:' | tail -6
  Normal   Scheduled  51s                default-scheduler  Successfully assigned default/lifecycle-image-error to devops-k8s-worker
  Normal   Pulling    30s (x2 over 50s)  kubelet            spec.containers{broken-image}: Pulling image "jakwehrgkaejw:kahsdfgkhj"
  Warning  Failed     19s (x2 over 43s)  kubelet            spec.containers{broken-image}: Failed to pull image "jakwehrgkaejw:kahsdfgkhj": failed to pull and unpack image "docker.io/library/jakwehrgkaejw:kahsdfgkhj": failed to resolve reference "docker.io/library/jakwehrgkaejw:kahsdfgkhj": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
  Warning  Failed     19s (x2 over 43s)  kubelet            spec.containers{broken-image}: Error: ErrImagePull
  Normal   BackOff    5s (x2 over 42s)   kubelet            spec.containers{broken-image}: Back-off pulling image "jakwehrgkaejw:kahsdfgkhj"
  Warning  Failed     5s (x2 over 42s)   kubelet            spec.containers{broken-image}: Error: ImagePullBackOff
```

Note the progression `ErrImagePull` → **`ImagePullBackOff`**: the first is the failed attempt,
the second is the kubelet giving up for a while. Also note `docker.io/library/` was prepended —
an unqualified image name always resolves to Docker Hub's official-images namespace, which is
why typos read as "repository does not exist **or may require authorization**".

### Probes: readiness gates traffic, liveness restarts, startup protects slow boots

```console
$ kubectl get pod lifecycle-readiness -o jsonpath='ready={.status.containerStatuses[0].ready} conditionsReady={.status.conditions[?(@.type=="Ready")].status}'
ready=true conditionsReady=True
```

`lifecycle-startup` was the interesting one in the big table:

```
lifecycle-startup   0/1   Running   0   41s
```

Phase `Running`, `READY 0/1`. The container is up but its **startup probe** has not passed yet,
so it is not Ready and would receive **no Service traffic**. That is the whole point:

| Probe | On failure | Use it for |
|---|---|---|
| `readinessProbe` | Pod removed from Service endpoints, **not** restarted | "I am alive but can't serve yet" (warming cache, waiting on DB) |
| `livenessProbe` | Container **restarted** | Deadlocks — a process that is up but wedged |
| `startupProbe` | Container restarted, but **disables the other probes until it passes** | Slow-booting apps (JVM) that would otherwise be killed by liveness before they finish starting |

### Init containers and multi-container Pods

```console
$ kubectl get pod lifecycle-init
NAME             READY   STATUS    RESTARTS   AGE
lifecycle-init   1/1     Running   0          40s
```

The init container ran `sleep 10` to completion *before* nginx started. Init containers run
sequentially, to completion, and only then does the app container start — the standard way to
wait for a dependency or fetch config without baking it into the app image.

```console
$ kubectl logs lifecycle-multi-container -c sidecar --tail=3
Sidecar is running
Sidecar is running
Sidecar is running
```

`READY 2/2` in the table: two containers, one Pod, one IP, one lifecycle. `-c <name>` is
mandatory once a Pod has more than one container.

### Graceful termination — SIGTERM, then the grace period

`12-termination.yaml` traps `SIGTERM`, sleeps 10s, and has
`terminationGracePeriodSeconds: 20`. Streaming the logs while deleting it:

```console
$ kubectl logs -f lifecycle-termination
Application running
SIGTERM received; cleaning up...
Cleanup complete
```

And the delete itself blocked for the length of the cleanup:

```console
$ date +%T
23:46:40
$ kubectl delete pod lifecycle-termination
pod "lifecycle-termination" deleted from default namespace
$ date +%T
23:46:51
```

11 seconds — the 10s handler plus overhead, **not** the full 20s grace period. The sequence is:
Pod marked `Terminating` and removed from Service endpoints → `SIGTERM` → your handler gets up
to `terminationGracePeriodSeconds` → `SIGKILL` if it is still alive. An app that ignores
SIGTERM gets the full 20s wait and then dies hard, dropping in-flight requests.

```bash
kubectl delete -f lab1-pod-lifecycle/     # cleanup
```

---

## Lab 2 — ReplicaSet: the reconcile loop you can watch

```console
$ kubectl apply -f lab2-replicaset/replicaset.yaml
replicaset.apps/web-rs created

$ kubectl get rs web-rs
NAME     DESIRED   CURRENT   READY   AGE
web-rs   3         3         3       15s

$ kubectl get pods -l app=web-rs
NAME           READY   STATUS    RESTARTS   AGE
web-rs-8ln6l   1/1     Running   0          15s
web-rs-9sl4h   1/1     Running   0          15s
web-rs-jjj87   1/1     Running   0          15s
```

### Self-healing

```console
$ kubectl delete pod web-rs-8ln6l
pod "web-rs-8ln6l" deleted from default namespace

$ kubectl get pods -l app=web-rs
NAME           READY   STATUS              RESTARTS   AGE
web-rs-22kln   0/1     ContainerCreating   0          0s
web-rs-9sl4h   1/1     Running             0          26s
web-rs-jjj87   1/1     Running             0          26s
```

The replacement (`web-rs-22kln`) is already `ContainerCreating` at **age 0s** — the controller
reacted to the deletion within the same second. Twelve seconds later the count is restored:

```console
$ kubectl get pods -l app=web-rs
NAME           READY   STATUS    RESTARTS   AGE
web-rs-22kln   1/1     Running   0          12s
web-rs-9sl4h   1/1     Running   0          38s
web-rs-jjj87   1/1     Running   0          38s
```

A replacement, not a resurrection: new name, new IP, no memory of the old Pod. This is why Pods
are called cattle, and why anything stateful needs a StatefulSet (Lab 5).

```console
$ kubectl get pods -l app=web-rs -o jsonpath='{.items[0].metadata.ownerReferences[0].kind}/{.items[0].metadata.ownerReferences[0].name}'
ReplicaSet/web-rs
```

### Selectors, not parentage — the MCQ 3 proof

`adopted-pod.yaml` is a plain Pod that just happens to carry `app: web-rs`:

```console
$ kubectl apply -f lab2-replicaset/adopted-pod.yaml
pod/orphan-with-matching-label created

$ kubectl get pods -l app=web-rs
NAME           READY   STATUS    RESTARTS   AGE
web-rs-22kln   1/1     Running   0          23s
web-rs-9sl4h   1/1     Running   0          49s
web-rs-jjj87   1/1     Running   0          49s

$ kubectl get pod orphan-with-matching-label
Error from server (NotFound): pods "orphan-with-matching-label" not found
```

It was created, then *executed*. The ReplicaSet's own event log names the killer:

```console
$ kubectl describe rs web-rs | grep -A10 'Events:'
Events:
  Type    Reason            Age   From                   Message
  ----    ------            ----  ----                   -------
  Normal  SuccessfulCreate  57s   replicaset-controller  Created pod: web-rs-8ln6l
  Normal  SuccessfulCreate  57s   replicaset-controller  Created pod: web-rs-jjj87
  Normal  SuccessfulCreate  57s   replicaset-controller  Created pod: web-rs-9sl4h
  Normal  SuccessfulCreate  31s   replicaset-controller  Created pod: web-rs-22kln
  Normal  SuccessfulDelete  18s   replicaset-controller  Deleted pod: orphan-with-matching-label
```

`SuccessfulDelete … orphan-with-matching-label` by the `replicaset-controller`. It adopted a Pod
it never created, counted 4 against a desired 3, and deleted one. **Overlapping selectors
between two controllers is therefore a real outage mechanism** — two ReplicaSets that select the
same labels will fight, each deleting the other's Pods forever.

---

## Lab 3 — Deployment: rollout, history, rollback

### The three-layer ownership chain

```console
$ kubectl get deploy,rs,pods -l app=web-deploy
NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web-deploy   3/3     3            3           43s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/web-deploy-7c8f89fd6b   3         3         3       43s

NAME                              READY   STATUS    RESTARTS   AGE
pod/web-deploy-7c8f89fd6b-9cg95   1/1     Running   0          43s
pod/web-deploy-7c8f89fd6b-l2mqn   1/1     Running   0          43s
pod/web-deploy-7c8f89fd6b-l9mk7   1/1     Running   0          43s

$ kubectl get pods -l app=web-deploy -o jsonpath='{.items[0].metadata.ownerReferences[0].kind}/{.items[0].metadata.ownerReferences[0].name}'
ReplicaSet/web-deploy-7c8f89fd6b
```

`Deployment → ReplicaSet → Pod`. `7c8f89fd6b` is a hash of the **Pod template**, which is the
mechanism behind everything below: change the template, get a new hash, get a new ReplicaSet.

### Rolling out v2

```console
$ kubectl set image deployment/web-deploy web=nginx:1.25-alpine
deployment.apps/web-deploy image updated

$ kubectl rollout status deployment/web-deploy --timeout=120s
Waiting for deployment "web-deploy" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "web-deploy" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "web-deploy" rollout to finish: 1 old replicas are pending termination...
deployment "web-deploy" successfully rolled out

$ kubectl get rs -l app=web-deploy
NAME                    DESIRED   CURRENT   READY   AGE
web-deploy-7c8f89fd6b   0         0         0       64s
web-deploy-b77ffc5df    3         3         3       13s
```

**The old ReplicaSet is still there, scaled to 0.** That is the rollback mechanism, sitting in
plain sight — it is not a backup, it is the previous generation kept ready to scale back up.

```console
$ kubectl rollout history deployment/web-deploy
deployment.apps/web-deploy
REVISION  CHANGE-CAUSE
1         <none>
2         upgrade nginx 1.24 -> 1.25
```

`CHANGE-CAUSE` comes from the `kubernetes.io/change-cause` annotation. It is `<none>` for
revision 1 because nothing set it — `--record` is deprecated, so annotate explicitly:

```bash
kubectl annotate deployment/web-deploy kubernetes.io/change-cause='upgrade nginx 1.24 -> 1.25' --overwrite
```

### Rollback

```console
$ kubectl rollout undo deployment/web-deploy
deployment.apps/web-deploy rolled back

$ kubectl get deploy web-deploy -o jsonpath='image={.spec.template.spec.containers[0].image}'
image=nginx:1.24-alpine

$ kubectl get rs -l app=web-deploy
NAME                    DESIRED   CURRENT   READY   AGE
web-deploy-7c8f89fd6b   3         3         3       85s
web-deploy-b77ffc5df    0         0         0       34s
```

The two ReplicaSets simply swapped replica counts — `7c8f89fd6b` is the *same* ReplicaSet from
revision 1, reused because the Pod template hash is identical. Nothing was rebuilt.

```console
$ kubectl rollout history deployment/web-deploy
REVISION  CHANGE-CAUSE
2         upgrade nginx 1.24 -> 1.25
3         <none>
```

Revision 1 is gone and 3 has appeared: a rollback is recorded as a **new revision**, not as a
rewind. History is append-only, so you can roll back a rollback.

`kubectl rollout undo` also warns, correctly:

```
Warning: resource deployments/web-deploy was previously managed with 'kubectl apply'. Rolling back will not update the kubectl.kubernetes.io/last-applied-configuration annotation, which may cause unexpected behavior on future 'kubectl apply' operations.
```

Your YAML in git now disagrees with the cluster. `undo` is the emergency lever; the durable fix
is to revert the commit and `apply`.

### What a *failed* rollout does — and does not — break

```console
$ kubectl set image deployment/web-deploy web=nginx:does-not-exist-9.9
deployment.apps/web-deploy image updated

$ kubectl get pods -l app=web-deploy
NAME                          READY   STATUS             RESTARTS   AGE
web-deploy-7c8f89fd6b-g9fsz   1/1     Running            0          33s
web-deploy-7c8f89fd6b-hh4ww   1/1     Running            0          37s
web-deploy-7c8f89fd6b-zvqzx   1/1     Running            0          29s
web-deploy-868969c467-p6wvk   0/1     ImagePullBackOff   0          25s

$ kubectl rollout status deployment/web-deploy --timeout=20s
Waiting for deployment "web-deploy" rollout to finish: 1 out of 3 new replicas have been updated...
error: timed out waiting for the condition
```

This is the single most reassuring output in the whole task. **All 3 old Pods are still
`Running` and serving.** The rollout created exactly one new Pod, it failed to pull, and the
Deployment refused to proceed:

```console
$ kubectl get deploy web-deploy -o jsonpath='{range .status.conditions[*]}{.type}={.status} reason={.reason}{"|"}{end}'
Available=True reason=MinimumReplicasAvailable|Progressing=True reason=ReplicaSetUpdated|
```

`Available=True` **during a broken deploy**. `maxUnavailable` (default 25%) is what buys this:
the Deployment may not remove an old Pod until a new one is Ready, and the new one never became
Ready, so nothing was removed. A bad image is a stalled rollout, not an outage — provided your
readiness probe is honest.

```console
$ kubectl rollout undo deployment/web-deploy
$ kubectl rollout status deployment/web-deploy --timeout=90s | tail -2
deployment "web-deploy" successfully rolled out
```

---

## Lab 4 — The four deployment strategies, measured

All traffic tests run from `curl-client`, a Pod inside the cluster, so they work the same on
kind, minikube or EKS (the course's `nodePort` values were removed for the same reason).

Each strategy was measured the same way: hammer the Service twice a second through the switch
and tally what came back.

| Strategy | Requests | Result | Downtime | Versions mixed? |
|---|---|---|---|---|
| RollingUpdate | 130 | 38× v1, 90× v2, **2 failed** | ~1s | **Yes** |
| RollingUpdate + `preStop` | 130 | 41× v1, 89× v2, **0 failed** | none | Yes |
| Recreate | 100 | 6× v1, 92× v2, **2 failed** | ~1s hard cut | **No** |
| Blue-green | 40 | 12× blue, 16× green, 12× blue, **0 failed** | none | No |
| Canary | 200 | 179× stable, 21× canary | none | Yes, **by design** |

### 4.1 RollingUpdate — gradual, and briefly serving both versions

`maxSurge: 1`, `maxUnavailable: 0` (course manifest), 4 replicas:

```console
$ kubectl rollout status deployment/app-rolling
Waiting for deployment "app-rolling" rollout to finish: 1 out of 4 new replicas have been updated...
Waiting for deployment "app-rolling" rollout to finish: 2 out of 4 new replicas have been updated...
Waiting for deployment "app-rolling" rollout to finish: 3 out of 4 new replicas have been updated...
Waiting for deployment "app-rolling" rollout to finish: 1 old replicas are pending termination...
deployment "app-rolling" successfully rolled out
```

The request log through the switch:

```text
26 VERSION: v1
27 VERSION: v1
28 VERSION: v2     <-- first v2 response
29 VERSION: v2
30 VERSION: v1     <-- still v1 too
31 VERSION: v1
32 VERSION: v2
33 VERSION: v1
34 VERSION: v1
```

```text
  2 REQUEST FAILED
 38 VERSION: v1
 90 VERSION: v2
```

The interleaving is the defining property of a rolling update: for the length of the rollout
**both versions serve live traffic from the same Service**. Any change that is not backwards
compatible — a renamed API field, a breaking DB migration — will break requests in this window.

### 4.2 The 2 failed requests, and how to actually get to zero

`maxUnavailable: 0` promises no capacity loss, yet 2 of 130 requests failed at the moment the
first old Pod was terminated. The cause is not capacity, it is **propagation**: when a Pod is
deleted it is removed from the Service's endpoints, but each node's iptables/IPVS rules are
updated a moment later. In that gap a client can still be routed to a Pod that has already
started shutting down.

The fix is to make the Pod outlive its own removal from the endpoint list. `deployment-v1-prestop.yaml`
and `deployment-v2-prestop.yaml` add:

```yaml
          lifecycle:
            preStop:
              exec:
                # Keep serving for 5s AFTER the Pod leaves Endpoints, so in-flight
                # requests and not-yet-updated iptables rules still find a live server.
                command: ["sh", "-c", "sleep 5"]
```

Same 130-request test, same rollout, only the hook added:

```text
  41 VERSION: v1
  89 VERSION: v2
```

**Zero failures.** 2 → 0 from five seconds of sleep. `preStop` does not delay `SIGTERM` to your
app for nothing — it holds the container open while the cluster finishes forgetting about it.
This is the difference between "zero-downtime deploy" on the slide and in production.

### 4.3 Recreate — downtime bought in exchange for a guarantee

```yaml
  strategy:
    type: Recreate
```

```text
 5 VERSION: v1
 6 VERSION: v1
 7 VERSION: v1
 8 REQUEST FAILED
 9 VERSION: v2
10 VERSION: v2
```

A hard cut: v1, a gap, v2. Compare with the rolling log above — **no request ever saw a mix**.
The tally was `6× v1, 2 failed, 92× v2`, and a pod sample during the cut caught the dip
(`ready=1 total=3`) as all old Pods went down together before the new ones came up.

The outage here was ~1s only because the v2 image was already cached on both nodes. On a cold
image pull this same strategy is a 30-60s outage. Choose it only when two versions **must not**
coexist: a breaking schema migration, a `ReadWriteOnce` volume that a second Pod cannot mount,
or a licence-locked legacy app.

### 4.4 Blue-green — two full stacks, one label flip

Both versions run at full size; the Service selector decides which one is live.

```console
$ kubectl get pods -l app=myapp -L slot
NAME                        READY   STATUS    RESTARTS   AGE   SLOT
app-blue-5c69d7785c-fp9s8   1/1     Running   0          10s   blue
app-blue-5c69d7785c-rnqgn   1/1     Running   0          10s   blue
app-blue-5c69d7785c-rwdjr   1/1     Running   0          10s   blue
app-green-84df7f978-qvm4g   1/1     Running   0          10s   green
app-green-84df7f978-x2dpm   1/1     Running   0          10s   green
app-green-84df7f978-xqjhg   1/1     Running   0          10s   green

$ kubectl get svc myapp-service -o jsonpath='selector={.spec.selector}'
selector={"app":"myapp","slot":"blue"}
```

Six Pods running, but only the three blue ones are in the Service:

```console
$ kubectl get endpointslice -l kubernetes.io/service-name=myapp-service -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{" "}{end}'
10.244.2.33 10.244.1.42 10.244.2.32

$ kubectl exec curl-client -- curl -s http://myapp-service | grep -o '[A-Z]* ENVIRONMENT'
BLUE ENVIRONMENT
```

The switch is one patch of one label:

```console
$ kubectl patch service myapp-service -p '{"spec":{"selector":{"app":"myapp","slot":"green"}}}'
service/myapp-service patched
```

The full request log across a switch **and** a rollback:

```text
 1 BLUE ENVIRONMENT      ...   12 BLUE ENVIRONMENT
13 GREEN ENVIRONMENT     <-- the switch
14 GREEN ENVIRONMENT     ...   28 GREEN ENVIRONMENT
29 BLUE ENVIRONMENT      <-- the rollback
30 BLUE ENVIRONMENT      ...   40 BLUE ENVIRONMENT
```

Zero failures, zero mixing, and the cut lands between two consecutive requests 500ms apart. The
rollback is as fast as the deploy because blue was never touched — it was sitting there,
warm, the whole time. That is what you pay for: **double the resources** for the duration.

### 4.5 Canary — a real traffic split, measured

One Service selects on the shared label `app: myapp-canary`, so its endpoint list is
`stable + canary` Pods and the split is just the **Pod ratio**.

Before the canary exists:

```console
$ kubectl exec curl-client -- sh -c 'for i in $(seq 1 30); do curl -s http://myapp-canary-service | grep -o "STABLE v1\|CANARY v2"; done' | sort | uniq -c
  30 STABLE v1
```

Add 1 canary Pod next to 9 stable ones — 10 endpoints, 10% canary:

```console
$ kubectl get deploy -l app=myapp-canary
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
app-canary   1/1     1            1           7s
app-stable   9/9     9            9           22s

$ kubectl exec curl-client -- sh -c 'for i in $(seq 1 200); do curl -s http://myapp-canary-service | grep -o "STABLE v1\|CANARY v2"; done' | sort | uniq -c
  21 CANARY v2
 179 STABLE v1
```

**21/200 = 10.5%** against a predicted 10.0%. Shift to 3 canary / 7 stable:

```console
  66 CANARY v2
 134 STABLE v1
```

**66/200 = 33%** against a predicted 30%. Promote to 10 canary / 0 stable:

```console
$ kubectl get deploy -l app=myapp-canary
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
app-canary   10/10   10           10          52s
app-stable   0/0     0            0           67s

$ kubectl exec curl-client -- sh -c 'for i in $(seq 1 60); do curl -s http://myapp-canary-service | grep -o "STABLE v1\|CANARY v2"; done' | sort | uniq -c
  60 CANARY v2
```

Measured progression: **0% → 10.5% → 33% → 100%**, each step one `kubectl scale`. Rollback is
`kubectl scale deployment app-canary --replicas=0` — instant, because stable never went away.

The limitation is visible in those numbers: 10.5% and 33% are *approximately* the target,
because `kube-proxy` load-balances per connection with no notion of weight. You cannot ask for
1% with 10 Pods — that needs 100 Pods, or an Ingress/service mesh that splits by weight instead
of by Pod count.

### Choosing

| | Rolling | Recreate | Blue-green | Canary |
|---|---|---|---|---|
| Downtime | none* | **yes** | none | none |
| Extra resources | +`maxSurge` | none | **2×** | +canary |
| Two versions live | yes | **never** | no | yes, on purpose |
| Rollback speed | a rollout | a rollout | **instant** | instant |
| Real-user testing | no | no | no | **yes** |
| Default? | **yes** | when forced | high-stakes releases | risky releases |

\* only with a `preStop` hook — see 4.2.

---

## Lab 5 — DaemonSet and StatefulSet

### DaemonSet: one Pod per node, except where it isn't

```console
$ kubectl get daemonset node-logging-agent
NAME                 DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
node-logging-agent   2         2         2       2            2           <none>          20s

$ kubectl get pods -l app=node-logging-agent -o wide --no-headers | awk '{print $1, $7}'
node-logging-agent-6qbjw devops-k8s-worker2
node-logging-agent-mzvlk devops-k8s-worker
```

`DESIRED 2` on a **3-node** cluster. A DaemonSet has no `replicas` field — it derives the count
from eligible nodes, and the control plane is not eligible:

```console
$ kubectl get nodes -o custom-columns='NODE:.metadata.name,TAINTS:.spec.taints[*].key'
NODE                       TAINTS
devops-k8s-control-plane   node-role.kubernetes.io/control-plane
devops-k8s-worker          <none>
devops-k8s-worker2         <none>
```

Compare with `kube-proxy`, which genuinely must run everywhere:

```console
$ kubectl get ds kube-proxy -n kube-system
NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
kube-proxy   3         3         3       3            3           kubernetes.io/os=linux   22m

$ kubectl get ds kube-proxy -n kube-system -o jsonpath='{range .spec.template.spec.tolerations[*]}{.key}{" op="}{.operator}{" effect="}{.effect}{"\n"}{end}'
 op=Exists effect=
```

An empty key with `operator: Exists` and no effect is the **tolerate-everything** wildcard, so
`kube-proxy` gets 3/3. If a monitoring or logging agent is silently missing from your control
plane nodes, this is why — and the one-line fix is that toleration.

```console
$ kubectl logs -l app=node-logging-agent --tail=1 --prefix
[pod/node-logging-agent-6qbjw/fluent-logger] [Thu Sep 17 18:33:00 UTC 2026] Collecting host system metrics on node-logging-agent-6qbjw
[pod/node-logging-agent-mzvlk/fluent-logger] [Thu Sep 17 18:33:00 UTC 2026] Collecting host system metrics on node-logging-agent-mzvlk
```

### StatefulSet: names, order and volumes that stick

> The course manifest `statefulset.yaml` (MySQL 5.7) is kept for reference but is not runnable
> here: `mysql:5.7` publishes no arm64 image, and the manifest's `serviceName: mysql` has no
> matching headless Service in the session folder. `statefulset-web.yaml` demonstrates the same
> three guarantees on nginx, with the required headless Service included.

**Ordered creation**, sampled every 3s:

```text
--- t+3s
  web-0 1/1 Running
  web-1 0/1 Pending
--- t+6s
  web-0 1/1 Running
  web-1 1/1 Running
  web-2 0/1 Pending
--- t+9s
  web-0 1/1 Running
  web-1 1/1 Running
  web-2 1/1 Running
```

`web-1` is `Pending` while `web-0` is already `Running`, and `web-2` does not appear until
`web-1` is Ready. Strictly sequential — a Deployment would have started all three at once.

**Stable identity and a volume per Pod:**

```console
$ kubectl get pods -l app=web-sts -o wide --no-headers | awk '{print $1, $6, $7}'
web-0 10.244.2.46 devops-k8s-worker
web-1 10.244.1.56 devops-k8s-worker2
web-2 10.244.2.48 devops-k8s-worker

$ kubectl get pvc -l app=web-sts
NAME         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-web-0   Bound    pvc-5717745f-264b-4c75-9402-4be0ec86138d   128Mi      RWO            standard       62s
data-web-1   Bound    pvc-18344d22-3b4a-42c9-9197-d88a5ff555a8   128Mi      RWO            standard       58s
data-web-2   Bound    pvc-5e4b27c2-27d2-42e5-bb69-b9a82b5d4fe7   128Mi      RWO            standard       53s
```

Ordinal names — `web-0`, not `web-7c8f89fd6b-x2k9p` — and one PVC per Pod named after it, all
created by the single `volumeClaimTemplates` block. Each Pod is individually addressable by DNS
through the headless Service:

```console
$ kubectl exec curl-client -- sh -c 'for h in web-0 web-1 web-2; do echo -n "$h -> "; curl -s http://$h.web-headless; done'
web-0 -> served by web-0
web-1 -> served by web-1
web-2 -> served by web-2
```

**The volume survives the Pod.** Write a file, destroy the Pod, read it back:

```console
$ kubectl exec web-1 -- sh -c 'echo "durable marker written at $(date -u +%H:%M:%S)" > /usr/share/nginx/html/marker.txt'

$ kubectl exec curl-client -- curl -s http://web-1.web-headless/marker.txt
durable marker written at 18:34:52

$ kubectl delete pod web-1
pod "web-1" deleted from default namespace

$ kubectl get pod web-1 --no-headers
web-1   1/1   Running   0   20s

$ kubectl exec curl-client -- curl -s http://web-1.web-headless/marker.txt
durable marker written at 18:34:52

$ kubectl get pvc data-web-1 -o jsonpath='pvc={.metadata.name} volume={.spec.volumeName} created={.metadata.creationTimestamp}'
pvc=data-web-1 volume=pvc-18344d22-3b4a-42c9-9197-d88a5ff555a8 created=2026-09-17T18:33:23Z
```

Same timestamp in the file, same `volumeName`, same PVC creation time — the Pod was rebuilt, the
volume was not. Contrast with Lab 2, where the ReplicaSet's replacement Pod got a new name, a
new IP and nothing of its predecessor.

> Caution when reading this lab: `index.html` is rewritten by a `postStart` hook on every
> container start, so a marker written *into `index.html`* correctly disappears after a restart.
> That is the hook overwriting the file, not the volume losing data. `marker.txt` is untouched by
> the hook, which is why it is the honest test.

| | Deployment | StatefulSet | DaemonSet |
|---|---|---|---|
| Pod names | random hash | **ordinal**, `web-0`… | per node |
| Start order | all at once | **sequential** | per node, as nodes appear |
| Storage | shared or none | **one PVC per Pod** | usually host paths |
| Replica count | you set it | you set it | **derived from nodes** |
| Scale down | random Pod | **highest ordinal first** | drain the node |

---

## Troubleshooting drills

### Drill 1 — selector does not match the Pod template

```console
$ kubectl apply -f troubleshooting/selector-mismatch.yaml
The Deployment "selector-error-demo" is invalid: spec.template.metadata.labels: Invalid value: {"app":"wrong-app-name"}: `selector` does not match template `labels`
```

Rejected at **admission** — nothing was created, there is no Pod to debug. A Deployment whose
selector cannot match its own template would own zero Pods forever, so the API server refuses it
outright. Fast failures are the good kind.

### Drill 2 — an image tag that does not exist

```console
$ kubectl apply -f troubleshooting/broken-image.yaml
deployment.apps/yatri-backend created

$ kubectl get deploy yatri-backend
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
yatri-backend   0/3     3            0           25s

$ kubectl get pods -l app=yatri-backend
NAME                             READY   STATUS             RESTARTS   AGE
yatri-backend-77dbb657cd-npbbk   0/1     ErrImagePull       0          25s
yatri-backend-77dbb657cd-qd7nd   0/1     ErrImagePull       0          25s
yatri-backend-77dbb657cd-xk4cw   0/1     ImagePullBackOff   0          25s
```

Accepted at admission, failed at **runtime**. `UP-TO-DATE 3` but `AVAILABLE 0`: the manifest is
valid, the world disagrees with it. Note this deployment had no previous version to fall back
on, so unlike Lab 3 there is nothing serving — `0/3` really is down.

```console
$ kubectl set image deployment/yatri-backend backend=nginx:1.25-alpine
deployment.apps/yatri-backend image updated
$ kubectl rollout status deployment/yatri-backend --timeout=120s | tail -1
deployment "yatri-backend" successfully rolled out
```

The two drills together are the rule: **schema errors fail at `apply`, reality errors fail at
`get pods`.** If `apply` succeeded, stop re-reading your YAML and go read the events.

### Drill 3 — the selector is immutable

```console
$ kubectl patch deployment yatri-backend --type=merge -p '{"spec":{"selector":{"matchLabels":{"app":"renamed"}}}}'
The Deployment "yatri-backend" is invalid:
* spec.template.metadata.labels: Invalid value: {"app":"yatri-backend","version":"broken-v3"}: `selector` does not match template `labels`
* spec.selector: Invalid value: {"matchLabels":{"app":"renamed"}}: field is immutable
```

`field is immutable`. Changing a selector would orphan every existing Pod — the old ReplicaSet
would no longer be recognised, and the Pods would be left running with nothing managing them.
Kubernetes forbids it, so **renaming labels means deleting and recreating the Deployment**. Plan
label schemes before the first `apply`.

---

## Cleanup

```bash
kubectl delete -f lab1-pod-lifecycle/
kubectl delete -f lab2-replicaset/replicaset.yaml
kubectl delete -f lab3-deployment-rollout/deployment.yaml
kubectl delete deploy app-rolling app-rolling-safe app-recreate app-blue app-green app-stable app-canary
kubectl delete svc  app-rolling-service app-rolling-safe-service app-recreate-service myapp-service myapp-canary-service
kubectl delete -f lab5-daemonset-statefulset/node-agent-ds.yaml
kubectl delete -f lab5-daemonset-statefulset/statefulset-web.yaml
kubectl delete pvc -l app=web-sts      # StatefulSet PVCs are NOT deleted with the StatefulSet
kubectl delete pod curl-client
kubectl delete deploy yatri-backend
```

That `kubectl delete pvc` line is not housekeeping pedantry — deleting a StatefulSet
deliberately leaves its PersistentVolumeClaims behind so you can rebuild the set over the same
data. They bill until you remove them.
