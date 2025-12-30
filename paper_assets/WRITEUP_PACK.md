# WRITEUP PACK (Step 8 outputs)

## Tables (paper_assets/tables)
- results_summary.xlsx
  - Sheet: Runs -> overall p95/p99, failure rate, request totals per run
  - Sheet: Endpoints -> per-endpoint (PUBLIC/SECURE/AUTH) stats per run

## Figures (paper_assets/figures)
- p95_total_by_run.png
- failure_rate_total_by_run.png
- p95_by_endpoint_and_defense.png
- grafana_*.png (you capture in Grafana)

## Recommended Dissertation Figures
1) System architecture diagram (Unity WebGL -> Nginx -> Django/ASGI -> Redis -> Prometheus/Grafana)
2) Baseline vs defended p95 chart (generated)
3) Failure rate chart (generated)
4) Grafana time-series screenshot: RPS + 429s during flood
5) Grafana time-series screenshot: 401/403 during token abuse + blocks (if enabled)

## Recommended Dissertation Tables
1) Experiment scenarios table (users, spawn rate, runtime, mix)
2) Defense configuration table (Nginx zones, DRF throttle scopes, blocklist thresholds)
3) Results summary table (p95/p99, failure rate, throughput)

## Methodology Traceability
- Each run folder in research/runs has:
  - meta.json (parameters)
  - settings.py snapshot (configuration)
  - nginx.conf + prometheus.yml (infrastructure)
  - git_commit.txt + pip_freeze.txt (reproducibility)
