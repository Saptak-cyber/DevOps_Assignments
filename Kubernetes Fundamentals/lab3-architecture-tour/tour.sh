#!/usr/bin/env bash
# Read-only walk over a live cluster's architecture. Changes nothing.
set -u

h() { printf '\n=== %s ===\n' "$1"; }
r() { printf '$ %s\n' "$1"; eval "$1" 2>&1; }

h "1. Who is the control plane, and where"
r "kubectl cluster-info"
r "kubectl get nodes"

h "2. Control-plane components, running as Pods"
r "kubectl get pods -n kube-system"

h "3. One kube-proxy + one CNI pod per node (DaemonSets)"
r "kubectl get pods -n kube-system -o wide --no-headers | awk '{print \$1, \$7}'"

h "4. Namespaced vs cluster-scoped resources"
r "kubectl api-resources --namespaced=true  -o name | head -12"
r "kubectl api-resources --namespaced=false -o name | head -8"

h "5. The API schema, offline"
r "kubectl explain pod.spec.containers.image"

h "6. Node capacity the scheduler reasons about"
r "kubectl describe node \$(kubectl get nodes -o jsonpath='{.items[1].metadata.name}') | sed -n '/^Capacity:/,/^System Info:/p'"

printf '\nTour complete. Nothing was created or deleted.\n'
