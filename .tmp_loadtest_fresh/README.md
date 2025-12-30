# Load-test suite (Locust) – Energy Island API

This folder is a **clean, reproducible** way to run your experiments and generate the “right” results without manual troubleshooting.

## 0) Prereqs

- Your Django/Daphne API is running at: `http://127.0.0.1:8000`
- Endpoints:
  - Token: `/api/auth/token/`
  - Secure ping: `/api/secure/ping/`
  - Secure state: `/api/secure/state/`
  - Public state (default assumed): `/api/public/state/`  
    (If yours differs, set `PUBLIC_STATE_PATH` env var.)

- Locust installed:
  - `pip install locust`

## 1) Set credentials (PowerShell)

```powershell
$env:LOCUST_USER = "YOUR_USERNAME"
$env:LOCUST_PASS = "YOUR_PASSWORD"
$env:LOCUST_HOST = "http://127.0.0.1:8000"
```

## 2) Run one scenario (headless)

Example: baseline public endpoint, 10 users, 2 spawn/s, 2 minutes

```powershell
.\scripts\run_one.ps1 -Scenario baseline_public_state -Condition baseline -Users 10 -SpawnRate 2 -Duration "2m"
```

## 3) Run the full suite (baseline + attacked + defended)

You run the suite in **two phases**:

### Phase A: baseline + attacked (defenses OFF)
```powershell
.\scripts\run_suite.ps1 -Repeats 3
```

### Phase B: defended (defenses ON)
Turn your defenses ON in the backend (however you do it), then:

```powershell
.\scripts\run_suite_defended.ps1 -Repeats 3
```

All raw CSV outputs go into:

`.\runs\<run_id>\`

Each run also includes a `meta.json` so analysis never produces NaNs.

## 4) Build summary + plots

```powershell
python .\analysis\build_results.py --runs-dir .\runs --out .\exports
python .\analysis\make_plots.py --in .\exports\results_summary.csv --out .\exports
```

Outputs:
- `exports/results_summary.xlsx`
- `exports/results_summary.csv`
- `exports/p95_total_by_run.png`
- `exports/p95_by_endpoint_and_condition.png`
- `exports/blocked_rate_by_run.png`

## 5) Grafana screenshots (optional but recommended)

For each run window, take screenshots of:
- Total RPS: `sum(rate(django_http_responses_total_by_status_total[1m]))`
- HTTP 200 rate: `sum(rate(django_http_responses_total_by_status_total{status="200"}[1m]))`
- HTTP 401 rate: `sum(rate(django_http_responses_total_by_status_total{status="401"}[1m]))`
- HTTP 403 rate: `sum(rate(django_http_responses_total_by_status_total{status="403"}[1m]))`
- p95 latency (seconds):
  `histogram_quantile(0.95, sum(rate(django_http_requests_latency_including_middlewares_seconds_bucket[1m])) by (le))`

Tip: set Grafana time range to “Last 15 minutes” before each run, then screenshot right after.
