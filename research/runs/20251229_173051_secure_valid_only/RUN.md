# Run: secure_valid_only

- Timestamp: 20251229_173051
- Host: http://127.0.0.1:8000
- Locust file: loadtests\locust_secure_valid_only.py
- Users: 20
- Spawn rate: 2
- Duration: 2m
- Markers used: True
- Defenses ON: False

## What to paste into dissertation
- Put p50/p95/p99 from: locust_stats.csv
- Error breakdown from: locust_failures.csv (and Prometheus snapshots if available)
- Attach Grafana screenshots taken during run:
  - RPS
  - p95 latency
  - 401/403/429 rates
  - Nginx connections
  - Redis memory/health

## Notes
- Record whether defenses were ON (nginx zones + DRF scopes + abuse blocklist).
