# Flattens a Jaeger /api/v3/traces/<id> (OTLP JSON) response into one line per span,
# ordered by start time: offset from trace start, duration, service, span name.
[ .result.resourceSpans[]
  | (.resource.attributes[] | select(.key == "service.name") | .value.stringValue) as $svc
  | .scopeSpans[].spans[]
  | { svc: $svc, name, start: (.startTimeUnixNano | tonumber), end: (.endTimeUnixNano | tonumber) } ]
| (map(.start) | min) as $t0
| sort_by(.start)
| ("offset_ms  duration_ms  service       span", "---------  -----------  ------------  ----"),
  (.[] | "\((((.start - $t0) / 1e6) | floor) | tostring | " " * (9 - length) + .)  \((((.end - .start) / 1e6) | floor) | tostring | " " * (11 - length) + .)  \(.svc + " " * (12 - (.svc | length)))  \(.name)")
