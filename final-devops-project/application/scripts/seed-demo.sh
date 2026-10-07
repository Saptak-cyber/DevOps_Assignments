#!/usr/bin/env bash
# Book a realistic demo day through the public API (works against Compose, a
# port-forward or the Ingress). Usage: BASE_URL=http://localhost:3000 ./seed-demo.sh [YYYY-MM-DD]
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
DAY="${1:-$(date +%F)}"

book() { # doctor_id time minutes name phone reason
  curl -sS -o /dev/null -w "%{http_code} $2 $4\n" -X POST "$BASE_URL/api/appointments" \
    -H 'Content-Type: application/json' \
    -d "{\"doctor_id\":$1,\"scheduled_at\":\"${DAY}T$2\",\"duration_minutes\":$3,\"reason\":\"$6\",\"patient\":{\"full_name\":\"$4\",\"phone\":\"$5\"}}"
}

book 1 09:00 30 "Meera Krishnan"   "+91 98450 11201" "Fever for three days"
book 1 09:30 15 "Imran Qureshi"    "+91 98450 11202" "BP review"
book 1 10:15 30 "Lakshmi Pillai"   "+91 98450 11203" "Diabetes follow-up"
book 1 11:30 45 "Sanjay Kulkarni"  "+91 98450 11204" "Annual health check"
book 2 09:15 30 "Aarav Sharma"     "+91 98450 11205" "Vaccination, 18 months"
book 2 10:00 20 "Diya Banerjee"    "+91 98450 11206" "Ear pain"
book 2 14:00 30 "Kabir Malhotra"   "+91 98450 11207" "Growth check"
book 3 10:00 30 "Nisha Verma"      "+91 98450 11208" "Eczema flare-up"
book 3 12:00 20 "Tanvi Deshpande"  "+91 98450 11209" "Acne review"
book 4 09:30 45 "Harish Gowda"     "+91 98450 11210" "Knee pain after fall"
book 4 15:30 30 "Fatima Sheikh"    "+91 98450 11211" "Post-op shoulder review"
