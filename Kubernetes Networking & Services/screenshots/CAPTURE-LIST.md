# Screenshot capture checklist — Kubernetes Networking & Services

The README references these filenames. Capture each one from your terminal and save it here
with the exact name, and the images in the README will render on GitHub.

| File | What to capture |
| --- | --- |
| `01-port-architecture.png` | Port Architecture |
| `02-clusterip-access.png` | ClusterIP Internal Access |
| `02-clusterip-endpoints.png` | ClusterIP Service and Endpoints |
| `03-nodeport-access.png` | NodePort 200 OK |
| `03-nodeport-service.png` | NodePort Service |
| `04-loadbalancer-access.png` | LoadBalancer Access |
| `04-loadbalancer-externalip.png` | LoadBalancer External IP |
| `05-externalname-cname.png` | ExternalName CNAME |
| `06-headless-dns.png` | Headless Service DNS |
| `07-no-selector-endpoints.png` | Services Without Selectors |
| `08-fqdn-coredns.png` | FQDN and CoreDNS |
| `09-pod-identity.png` | Pod Identity Invariance |
| `12-tunnel-gotcha.png` | NodePort Tunnel Gotcha |
| `13-deployment-vs-replicaset.png` | Task 13.1: `kubectl get rs -o wide` + pod images after `set image` on both (Deployment rolled, bare ReplicaSet did not) |
| `13-replicaset-vs-service.png` | Task 13.3: EndpointSlice before/after deleting a `web-rs` pod, curl still `200` on the same ClusterIP |
| `13-fqdn-namespace-dns.png` | `fqdn/README.md` §4: `curl http://api` fails, `api.team-a` / FQDN succeed from the `default` namespace |
| `14-coredns-query-log.png` | `coredns/README.md` §4: CoreDNS `log` output showing the search-list walk for `github.com` |
| `14-coredns-outage-drill.png` | `coredns/README.md` §6: CoreDNS at 0 replicas → name fails, ClusterIP works, empty `kube-dns` endpoints → fixed |

Every command needed is in the README (or the `fqdn/` / `coredns/` sub-README), in the task that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).
