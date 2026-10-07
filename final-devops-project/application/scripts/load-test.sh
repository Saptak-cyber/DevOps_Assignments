#!/usr/bin/env bash
# CPU load for the HPA demo: runs N parallel curl loops against the API for D seconds.
#   BASE_URL=http://<lb-host> CONCURRENCY=40 DURATION=240 ./load-test.sh
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:3000}"
CONCURRENCY="${CONCURRENCY:-30}"
DURATION="${DURATION:-180}"
end=$((SECONDS + DURATION))
worker() {
  while [ "$SECONDS" -lt "$end" ]; do
    curl -s -o /dev/null "$BASE_URL/api/stats" || true
    curl -s -o /dev/null "$BASE_URL/api/appointments?on=$(date +%F)" || true
  done
}
echo "load: $CONCURRENCY workers x ${DURATION}s against $BASE_URL"
for _ in $(seq 1 "$CONCURRENCY"); do worker & done
wait
echo "load test finished"
