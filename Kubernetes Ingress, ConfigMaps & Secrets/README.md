# Kubernetes Ingress, ConfigMaps & Secrets

Source material: [`devops-heros/session-12-ingress-configmaps-secrets`](../../devops-heros/session-12-ingress-configmaps-secrets)
— `lab.md`, the `01-configmap` / `02-secret` / `03-ingress` folders, the `04-full-demo`
application, and `troubleshooting/secret-base64-gotcha.md`. Manifests marked
*(course manifest)* are unchanged from that session.

Every console block is **real captured output** from the 3-node cluster built in
[Kubernetes Fundamentals](../Kubernetes%20Fundamentals/) (Kubernetes v1.37.0) with
ingress-nginx installed.

## Folder structure

```
Kubernetes Ingress, ConfigMaps & Secrets/
├── README.md
├── lab1-configmap/
│   ├── app-config.yaml              (course manifest)
│   └── configmap-as-volume.yaml     written here: volume vs subPath vs env var
├── lab2-secret/db-secret.yaml       (course manifest)
├── lab3-ingress/
│   ├── ingress-routes.yaml          (course manifest) path routing
│   └── ingress-tls.yaml             (course manifest) host routing + TLS
├── lab4-full-demo/                  (course manifests) configmap, secret,
│   │                                backend, frontend, ingress, run-demo.sh
│   └── cleanup.sh
└── troubleshooting/
    ├── secret-base64-gotcha.md      (course notes)
    └── newline-bug-demo.yaml        written here: the same bug, reproduced
```

> **One deviation from the session, needed to make Ingress work on this cluster.**
> The course runs on minikube with `minikube addons enable ingress`. On kind, the
> ingress-nginx controller uses `hostPort: 80/443`, so it is only reachable on the node whose
> host ports are mapped — the control plane, labelled `ingress-ready=true` by
> `cluster/kind-config.yaml`. The upstream manifest scheduled it onto a worker instead, so
> every request timed out until the controller was pinned:
>
> ```bash
> kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type=strategic -p '{
>   "spec": {"template": {"spec": {
>     "nodeSelector": {"kubernetes.io/os": "linux", "ingress-ready": "true"},
>     "tolerations": [
>       {"key": "node-role.kubernetes.io/control-plane", "operator": "Equal", "effect": "NoSchedule"}
>     ]}}}}'
> ```
>
> Tests then use `curl -H 'Host: …' http://localhost:8080` instead of editing `/etc/hosts`.


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

**MCQ 1.** Is data in a Kubernetes Secret encrypted?

- A. Yes, with AES-256 by default
- B. No — it is base64-**encoded**, which is not encryption
- C. Only if the Pod requests it
- D. Yes, but only in transit

**Answer: B** — base64 is a reversible transform with no key. Anyone who can read the Secret
object can read the password, demonstrated below in one command.

**MCQ 2.** Why must you use `echo -n` when base64-encoding a secret value by hand?

- A. It is faster
- B. `echo` without `-n` appends a newline, which becomes part of the secret
- C. `-n` enables encryption
- D. It is not required

**Answer: B** — the trailing `\n` is encoded into the value and injected into your app. Section
"Troubleshooting" reproduces the resulting auth failure.

**MCQ 3.** You edit a ConfigMap. A running Pod consumes it via `envFrom`. What happens?

- A. The env var updates within ~60s
- B. Nothing — env vars are fixed at container start; the Pod must restart
- C. The Pod restarts automatically
- D. The Deployment rolls out automatically

**Answer: B** — and a *mounted* ConfigMap behaves differently, which is the point of Lab 1.

**MCQ 4.** Both NodePort and LoadBalancer expose services externally. Why use an Ingress?

- A. It is cheaper
- B. One entry point can route many hostnames and paths by HTTP, and terminate TLS
- C. Ingress replaces Services
- D. Ingress is faster

**Answer: B** — a Service is layer 4 (IP and port). It cannot read a URL path or a `Host`
header, so exposing 20 microservices means 20 load balancers. An Ingress is layer 7: one
address, one certificate, routing rules. It still sends traffic *to* Services.

**MCQ 5.** What does an Ingress resource do without an Ingress controller running?

- A. Nothing — the rules are just stored data
- B. Kubernetes routes traffic using built-in defaults
- C. It fails to be created
- D. It behaves like a NodePort

**Answer: A** — an Ingress is only a set of rules. Something must read them and act: nginx,
Traefik, HAProxy, or a cloud ALB controller. No controller means a stored object and no routing.

---

## Lab 1 — ConfigMap

### Plain-text config, out of the image

```console
$ kubectl apply -f lab1-configmap/app-config.yaml
configmap/yatri-app-config created

$ kubectl get configmap yatri-app-config
NAME               DATA   AGE
yatri-app-config   5      0s

$ kubectl describe configmap yatri-app-config
Name:         yatri-app-config
Namespace:    default
Labels:       app=yatri-backend

Data
====
DEFAULT_CURRENCY:
----
INR

ENVIRONMENT:
----
production

LOG_LEVEL:
----
INFO

MAX_BOOKING_DAYS:
----
30

PORT:
----
5000
```

`DATA 5` counts keys. Note `describe` prints ConfigMap values in full — unlike Secrets, there is
nothing to hide.

```console
$ kubectl get configmap yatri-app-config -o jsonpath='{.data.ENVIRONMENT}'
production
```

### Three ways to consume one, and how they differ on update

The course manifests use `envFrom`. `configmap-as-volume.yaml` wires up the same ConfigMap three
ways in one Pod: a **plain volume mount**, a **`subPath` mount**, and an **env var**.

```console
$ kubectl exec config-volume-demo -- ls -l /config
total 0
lrwxrwxrwx    1 root     root            15 Sep 17 18:50 GREETING -> ..data/GREETING
lrwxrwxrwx    1 root     root            17 Sep 17 18:50 index.html -> ..data/index.html

$ kubectl exec config-volume-demo -- cat /config/GREETING
hello from the original ConfigMap

$ kubectl exec config-volume-demo -- env | grep GREETING_ENV
GREETING_ENV=hello from the original ConfigMap

$ kubectl exec config-volume-demo -- curl -s localhost/
<html><body>
<h1>Served from a ConfigMap volume</h1>
<p>version: ORIGINAL</p>
</body></html>
```

Those are **symlinks**, not files, and the reason matters — see the `..data` indirection below.

Now edit the ConfigMap with the Pod left running:

```bash
kubectl patch configmap nginx-site-config --type=merge -p '{"data":{"GREETING":"UPDATED value, edited at runtime", ...}}'
```

```console
$ kubectl get configmap nginx-site-config -o jsonpath='{.data.GREETING}'
UPDATED value, edited at runtime
```

After ~90 seconds, the three consumers disagree:

```console
--- 1. plain volume mount /config/GREETING ---
$ kubectl exec config-volume-demo -- cat /config/GREETING
UPDATED value, edited at runtime

--- 2. subPath mount (index.html) ---
$ kubectl exec config-volume-demo -- curl -s localhost/
<html><body>
<h1>Served from a ConfigMap volume</h1>
<p>version: ORIGINAL</p>
</body></html>

--- 3. env var ---
$ kubectl exec config-volume-demo -- env | grep GREETING_ENV
GREETING_ENV=hello from the original ConfigMap
```

| Consumption mode | Updates in a running Pod? |
|---|---|
| Volume mount (whole ConfigMap into a directory) | **yes**, on the kubelet sync period |
| Volume mount with `subPath` | **no**, never |
| `env` / `envFrom` | **no**, never |

The `subPath` case is the trap: it looks like a file mount and behaves like an env var. `subPath`
resolves to a single file at mount time and is not part of the volume's refresh.

Deleting just the Pod (leaving the ConfigMap edited) picks everything up:

```console
$ kubectl exec config-volume-demo -- env | grep GREETING_ENV
GREETING_ENV=UPDATED value, edited at runtime

$ kubectl exec config-volume-demo -- curl -s localhost/
<html><body>
<h1>Served from a ConfigMap volume</h1>
<p>version: UPDATED</p>
</body></html>
```

Which is why production does not rely on live reload at all — it changes the ConfigMap *and*
triggers a rollout (`kubectl rollout restart deployment/...`, or a checksum annotation on the Pod
template so the change itself forces a new revision).

### Why those symlinks exist

```console
$ kubectl exec config-volume-demo -- ls -la /config
total 12
drwxrwxrwx    3 root     root          4096 Sep 17 18:52 .
drwxr-xr-x    1 root     root          4096 Sep 17 18:50 ..
drwxr-xr-x    2 root     root          4096 Sep 17 18:52 ..2026_09_17_18_52_20.2843357114
lrwxrwxrwx    1 root     root            32 Sep 17 18:52 ..data -> ..2026_09_17_18_52_20.2843357114
lrwxrwxrwx    1 root     root            15 Sep 17 18:50 GREETING -> ..data/GREETING
lrwxrwxrwx    1 root     root            17 Sep 17 18:50 index.html -> ..data/index.html
```

The kubelet writes each new version into a fresh timestamped directory, then **atomically
repoints the `..data` symlink**. An app never sees a half-written config file — it sees the old
version or the new one. This is also why `subPath` cannot update: it bypasses `..data` and binds
the underlying file directly.

> A caught mistake worth recording: re-running `kubectl apply -f configmap-as-volume.yaml` to
> recreate the Pod also reverted the ConfigMap to the file's original values (`configmap/
> nginx-site-config configured`), silently undoing the runtime patch. `apply` reconciles
> *everything* in the file. Recreate only the Pod when you want to keep a live edit.

---

## Lab 2 — Secret

### The rule, and the byte that proves it

```console
$ echo 'secretpassword' | base64
c2VjcmV0cGFzc3dvcmQK

$ echo -n 'secretpassword' | base64
c2VjcmV0cGFzc3dvcmQ=
```

Different output for the same password. Decode both and look at the actual bytes:

```console
$ echo 'secretpassword' | base64 | base64 -d | xxd
00000000: 7365 6372 6574 7061 7373 776f 7264 0a    secretpassword.

$ echo -n 'secretpassword' | base64 | base64 -d | xxd
00000000: 7365 6372 6574 7061 7373 776f 7264       secretpassword
```

The trailing **`0a`** — a newline — is the whole bug. `echo` adds it, `echo -n` does not, and
base64 faithfully encodes it as part of your password.

### Applying and inspecting

```console
$ kubectl apply -f lab2-secret/db-secret.yaml
secret/yatri-db-secret created

$ kubectl get secret yatri-db-secret
NAME              TYPE     DATA   AGE
yatri-db-secret   Opaque   3      0s

$ kubectl describe secret yatri-db-secret
Type:  Opaque

Data
====
POSTGRES_DB:        19 bytes
POSTGRES_PASSWORD:  14 bytes
POSTGRES_USER:      11 bytes
```

`describe` prints **byte counts instead of values** — the one place Kubernetes tries to protect
you, so a secret does not end up in a terminal recording or a CI log.

### That protection is a courtesy, not a security boundary

```console
$ kubectl get secret yatri-db-secret -o jsonpath='{.data.POSTGRES_PASSWORD}'
c2VjcmV0cGFzc3dvcmQ=

$ kubectl get secret yatri-db-secret -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
secretpassword

$ kubectl get secret yatri-db-secret -o yaml | grep -A4 '^data:'
data:
  POSTGRES_DB: eWF0cmlfcHJvZHVjdGlvbl9kYg==
  POSTGRES_PASSWORD: c2VjcmV0cGFzc3dvcmQ=
  POSTGRES_USER: eWF0cmlfYWRtaW4=
```

One pipe to `base64 -d` and the password is in plain text. What a Secret *does* buy you, versus
hardcoding:

- it keeps credentials out of the container image and out of git (if the YAML is not committed);
- it is a separate RBAC-able object, so `get secrets` can be denied to people who can `get pods`;
- the kubelet mounts it into a `tmpfs`, so it is not written to the node's disk;
- it can be encrypted **at rest in etcd** — but only if the cluster admin configured
  `EncryptionConfiguration`. Without that, etcd holds the same base64 shown above.

Real secret management (Vault, Sealed Secrets, External Secrets, cloud KMS) exists because of
that list, not in spite of it.

---

## Lab 3 + Lab 4 — Ingress, with the full application behind it

### The whole chain deployed

```console
$ kubectl apply -f lab4-full-demo/configmap.yaml -f lab4-full-demo/secret.yaml -f lab4-full-demo/backend.yaml -f lab4-full-demo/frontend.yaml
configmap/yatri-app-config configured
secret/yatri-db-secret configured
deployment.apps/yatri-backend created
service/yatri-backend-service created
deployment.apps/yatri-frontend created
service/yatri-frontend-service created

$ kubectl get pods -l 'app in (yatri-backend,yatri-frontend)'
NAME                             READY   STATUS    RESTARTS   AGE
yatri-backend-6c58cb99c7-7jw5r   1/1     Running   0          15s
yatri-backend-6c58cb99c7-pw5kz   1/1     Running   0          15s
yatri-frontend-ddcfc4b5f-4zxt7   1/1     Running   0          15s
yatri-frontend-ddcfc4b5f-pmjs4   1/1     Running   0          15s
```

The backend injects the ConfigMap with `envFrom` and each Secret key with `secretKeyRef`.
Verified inside the container:

```console
$ kubectl exec yatri-backend-6c58cb99c7-7jw5r -- env | grep -E 'ENVIRONMENT|LOG_LEVEL|DEFAULT_CURRENCY|MAX_BOOKING_DAYS|APP_PORT|POSTGRES' | sort
APP_PORT=5000
DEFAULT_CURRENCY=INR
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_BOOKING_DAYS=30
POSTGRES_DB=yatri_production_db
POSTGRES_PASSWORD=secretpassword
POSTGRES_USER=yatri_admin
```

Five values from the ConfigMap and three from the Secret, arriving as ordinary environment
variables. **The application cannot tell them apart** — which is the design goal. Config and
credentials are separate *objects*, with separate RBAC and separate change processes, but one
uniform interface to the code.

### Path-based routing

`ingress-routes.yaml` puts both services on one host:

```console
$ kubectl get ingress
NAME            CLASS   HOSTS         ADDRESS     PORTS   AGE
yatri-ingress   nginx   yatri.local   localhost   80      87s

$ kubectl describe ingress yatri-ingress | grep -A8 'Rules:'
Rules:
  Host         Path  Backends
  ----         ----  --------
  yatri.local
               /api(/|$)(.*)   yatri-backend-service:80 (10.244.1.75:5000,10.244.2.62:5000)
               /               yatri-frontend-service:80 (10.244.1.76:80,10.244.2.63:80)
Annotations:   nginx.ingress.kubernetes.io/rewrite-target: /$2
               nginx.ingress.kubernetes.io/ssl-redirect: false
               nginx.ingress.kubernetes.io/use-regex: true
```

`describe ingress` resolves each rule all the way down to **Pod IP and container port** — the
fastest way to confirm an Ingress is wired to something real. An empty backend list here means
the Service behind it has no endpoints (previous task's triage applies).

Both paths, one address, one port:

```console
$ curl -4 -s -H 'Host: yatri.local' http://localhost:8080/ | head -12
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
...
<h1>Welcome to nginx!</h1>

$ curl -4 -s -H 'Host: yatri.local' http://localhost:8080/api/
Yatri Backend API
=================
ENVIRONMENT     : production
LOG_LEVEL       : INFO
DEFAULT_CURRENCY: INR
POSTGRES_USER   : yatri_admin
POSTGRES_DB     : yatri_production_db
```

That second response is the entire task in one place: an HTTP request from **outside** the
cluster, routed by path through the Ingress to a Service to a Pod, and the body is the
application reading values that came from a **ConfigMap** and a **Secret**.

The `rewrite-target: /$2` annotation with the `(/|$)(.*)` capture group is what strips `/api`
before proxying — the backend sees `/`, not `/api/`. Without it the backend would 404 on a path
it never implemented.

### Routing is by `Host` header, not by IP

```console
$ curl -4 -s -o /dev/null -w 'Host: wrong.local -> %{http_code}' http://localhost:8080/
Host: wrong.local -> 404
```

Same IP, same port, no `Host` match → the controller's default backend answers **404**. This is
how one load balancer serves many domains, and also why "it works with the Host header but not
in my browser" always comes down to DNS or `/etc/hosts`.

### TLS termination

```console
$ openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout tls.key -out tls.crt \
    -subj '/CN=portal.campus.local/O=devops-class' \
    -addext 'subjectAltName=DNS:portal.campus.local,DNS:api.campus.local'

$ kubectl create secret tls campus-tls-cert --cert=tls.crt --key=tls.key
secret/campus-tls-cert created

$ kubectl get secret campus-tls-cert
NAME              TYPE                DATA   AGE
campus-tls-cert   kubernetes.io/tls   2      0s

$ kubectl describe secret campus-tls-cert
Type:  kubernetes.io/tls

Data
====
tls.crt:  1273 bytes
tls.key:  1704 bytes
```

Type `kubernetes.io/tls`, not `Opaque` — a typed Secret that **must** contain exactly the keys
`tls.crt` and `tls.key`. `kubectl create secret tls` enforces that, which is why it is preferable
to hand-writing the YAML.

```console
$ kubectl apply -f lab3-ingress/ingress-tls.yaml
ingress.networking.k8s.io/campus-ingress-tls created

$ kubectl get ingress campus-ingress-tls
NAME                 CLASS   HOSTS                                  ADDRESS   PORTS     AGE
campus-ingress-tls   nginx   portal.campus.local,api.campus.local             80, 443   10s
```

`PORTS 80, 443` — the 443 appears only because a `tls:` block references the Secret.

Two hostnames, one certificate, two different backends:

```console
$ curl -4 -sk --resolve portal.campus.local:8443:127.0.0.1 https://portal.campus.local:8443/ | head -4
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>

$ curl -4 -sk --resolve api.campus.local:8443:127.0.0.1 https://api.campus.local:8443/api/
Yatri Backend API
=================
ENVIRONMENT     : production
LOG_LEVEL       : INFO
DEFAULT_CURRENCY: INR
POSTGRES_USER   : yatri_admin
POSTGRES_DB     : yatri_production_db
```

The handshake, and proof it is our certificate:

```console
$ curl -4 -skv --resolve portal.campus.local:8443:127.0.0.1 https://portal.campus.local:8443/ 2>&1 | grep -E 'subject:|issuer:|SSL connection|ALPN: server'
* SSL connection using TLSv1.3 / AEAD-AES256-GCM-SHA384
* ALPN: server accepted h2
*  subject: CN=portal.campus.local; O=devops-class
*  issuer: CN=portal.campus.local; O=devops-class
```

`subject == issuer` is the definition of self-signed. TLS 1.3 and HTTP/2 (`h2`) came from the
controller's defaults, not from anything in the manifest.

```console
$ curl -4 -s -o /dev/null --resolve portal.campus.local:8443:127.0.0.1 https://portal.campus.local:8443/
exit=000  <- curl refused to trust it
```

Without `-k`, curl **correctly rejects** it: no CA signed this certificate. In production
cert-manager issues real Let's Encrypt certificates into exactly this kind of Secret, and
nothing else about the Ingress changes.

Note that TLS terminates **at the Ingress**. The hop from controller to backend Pod was plain
HTTP on `targetPort: 5000`. That is standard, and it is also the thing to be explicit about in a
security review — inside-the-cluster traffic is unencrypted unless you add a mesh or
backend-protocol annotations.

---

## Troubleshooting — the trailing-newline Secret bug

`troubleshooting/secret-base64-gotcha.md` describes this failure. `newline-bug-demo.yaml`
reproduces it: two Secrets that both *intend* to hold `mypassword`, one encoded with `echo` and
one with `echo -n`, injected into a Pod that compares them against the expected value.

```console
$ kubectl logs newline-bug-demo
expected length : 10
PW_BROKEN length: 11
PW_GOOD   length: 10

pw-broken: AUTH FAILED  <- password mismatch
pw-good:   AUTH OK

hexdump of the broken value:
00000000  6d 79 70 61 73 73 77 6f  72 64 0a                 |mypassword.|
0000000b
hexdump of the good value:
00000000  6d 79 70 61 73 73 77 6f  72 64                    |mypassword|
0000000a
```

`AUTH FAILED` against `AUTH OK`, from a one-character difference in the command that generated
the value. A real database returns `password authentication failed for user`, which sends people
hunting for a wrong username, a network policy or a firewall rule.

### Why it is hard to see

```console
$ kubectl get secret pw-broken pw-good
NAME        TYPE     DATA   AGE
pw-broken   Opaque   1      15s
pw-good     Opaque   1      15s

$ kubectl describe secret pw-broken | grep -A3 'Data'
Data
====
PASSWORD:  11 bytes
```

Identical in `get`. The **only** visible clue anywhere in `kubectl` is `11 bytes` where the
password is 10 characters long. That byte count is the fastest check there is:

```bash
# Is the length what you expect?
kubectl get secret pw-broken -o jsonpath='{.data.PASSWORD}' | base64 -d | wc -c   # 11, should be 10

# Is there a trailing newline?
kubectl get secret pw-broken -o jsonpath='{.data.PASSWORD}' | base64 -d | xxd | tail -1
```

### Avoiding it entirely

```bash
# Let kubectl do the encoding — no echo, no newline, no base64 by hand.
kubectl create secret generic pw-good --from-literal=PASSWORD='mypassword'
```

`--from-literal` takes the raw string and encodes it correctly. Hand-written base64 in a YAML
file is the only way to hit this bug, and `kubectl create secret generic --dry-run=client -o yaml`
generates the manifest for you when you do need the file.

---

## One-command run and cleanup

The session ships automation for the full demo (course scripts, kept as-is):

```bash
./lab4-full-demo/run-demo.sh      # applies configmap, secret, backend, frontend, ingress
./lab4-full-demo/cleanup.sh       # removes them
```

Note `run-demo.sh` assumes minikube (`minikube addons enable ingress`, `minikube ip` for
`/etc/hosts`). On the kind cluster used here, apply the manifests directly and test with a `Host`
header as shown above.

```bash
kubectl delete -f lab4-full-demo/ingress.yaml -f lab4-full-demo/frontend.yaml \
               -f lab4-full-demo/backend.yaml -f lab4-full-demo/secret.yaml \
               -f lab4-full-demo/configmap.yaml
kubectl delete -f lab3-ingress/ingress-tls.yaml
kubectl delete secret campus-tls-cert
kubectl delete -f lab1-configmap/configmap-as-volume.yaml
kubectl delete -f troubleshooting/newline-bug-demo.yaml
```
