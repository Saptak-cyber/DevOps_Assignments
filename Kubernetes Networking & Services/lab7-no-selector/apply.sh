#!/usr/bin/env bash
# manual-endpoints.yaml carries PLACEHOLDER_IP rather than a hardcoded address,
# because a Pod IP is only valid on the cluster that issued it. This substitutes
# a live IP and applies the result.
#
#   ./apply.sh              -> target an echo-app Pod IP (lab1)
#   ./apply.sh 10.0.0.42    -> target an address you supply
set -euo pipefail
cd "$(dirname "$0")"

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  TARGET=$(kubectl get pods -l app=echo-app -o jsonpath='{.items[0].status.podIP}' 2>/dev/null || true)
  if [ -z "$TARGET" ]; then
    echo "No echo-app Pod found. Apply ../lab1-clusterip/echo-deployment.yaml first," >&2
    echo "or pass an address explicitly:  ./apply.sh <ip>" >&2
    exit 1
  fi
  echo "Targeting echo-app Pod IP: $TARGET"
fi

sed "s/PLACEHOLDER_IP/$TARGET/" manual-endpoints.yaml | kubectl apply -f -
echo
kubectl describe svc legacy-db | grep -E 'Selector:|Endpoints:'
