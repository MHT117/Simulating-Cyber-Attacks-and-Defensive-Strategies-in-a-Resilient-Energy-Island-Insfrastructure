# Run: baseline_public_state

- Timestamp: 20251229_154631
- Host: http://localhost:8080
- Locust file: perf\locustfile.py
- Users: 50
- Spawn rate: 5
- Duration: 2m
- Markers used: True

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
