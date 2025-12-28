# Run: metrics_step6

- Date: 2025-12-27
- Metrics stack:
  - Prometheus: http://localhost:9090
  - Grafana: http://localhost:3000 (admin/admin)
  - Scrape targets: django (host.docker.internal:8000), nginx_exporter, redis_exporter
- Django metrics:
  - /metrics available at http://127.0.0.1:8000/metrics
  - Daphne bound to 0.0.0.0:8000 so Prometheus can scrape
- Nginx metrics:
  - /nginx_status (restricted) for exporter
- Marker events:
  - step6_public_start / step6_public_end
  - step6_mixed_start / step6_mixed_end
  - step6_auth_start / step6_auth_end
- Screenshots:
  - Not captured by Codex (no GUI access)

## Locust runs (defenses enabled)

### Public flood (step6_public_state)
- Users: 50
- Spawn rate: 5 / second
- Duration: 2 minutes
- Aggregated results (from stats.csv):
  - Requests: 16979
  - Failures: 15780
  - Avg latency: 33.42 ms
  - Median: 1 ms
  - p95: 7 ms
  - p99: 8 ms
  - RPS: 142.15

### JWT mixed 80/20 (step6_secure_mixed_80_20)
- Users: 80
- Spawn rate: 8 / second
- Duration: 3 minutes
- Aggregated results (from stats.csv):
  - Requests: 4152
  - Failures: 4126
  - Avg latency: 530.76 ms
  - Median: 5 ms
  - p95: 59 ms
  - p99: 32000 ms
  - RPS: 23.17

### Auth login storm (step6_auth_login_storm)
- Users: 40
- Spawn rate: 10 / second
- Duration: 2 minutes
- Aggregated results (from stats.csv):
  - Requests: 44360
  - Failures: 44360
  - Avg latency: 4.00 ms
  - Median: 1 ms
  - p95: 26 ms
  - p99: 43 ms
  - RPS: 371.81

## Dashboard panels to capture
- API request rate: rate(django_http_responses_total[1m])
- p95 latency: histogram_quantile(0.95, sum(rate(django_http_requests_latency_seconds_bucket[1m])) by (le))
- Error rates: 401/403/429 response rates
- Nginx: connections + requests (from exporter)
- Redis: redis_up, redis_memory_used_bytes
