from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "web" / "experiments" / "runs"
MANIFEST = ROOT / "web" / "experiments" / "exports" / "runs_manifest.csv"

OUT_CSV = ROOT / "paper_assets" / "tables" / "results_summary.csv"
OUT_XLSX = ROOT / "paper_assets" / "tables" / "results_summary.xlsx"

def read_json_safe(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def load_locust_stats(run_dir: Path):
    # Step 7 uses prefix "locust" -> locust_stats.csv
    p = run_dir / "locust_stats.csv"
    if not p.exists():
        # fallback: any *_stats.csv
        alt = list(run_dir.glob("*_stats.csv"))
        if alt:
            p = alt[0]
        else:
            return None

    df = pd.read_csv(p)
    return df

def pick_aggregated(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    name_series = df["Name"].astype(str).str.lower()
    for candidate in ["aggregated", "total"]:
        m = df[name_series == candidate]
        if not m.empty:
            return m.iloc[0]
    return None

def pick_by_patterns(df: pd.DataFrame, patterns, allow_aggregated=False):
    if df is None or df.empty:
        return None
    name_series = df["Name"].astype(str).str.lower()
    for pat in patterns:
        pat_l = str(pat).lower()
        m = df[name_series.str.contains(pat_l, na=False, regex=False)]
        if not m.empty:
            return m.iloc[0]
    if allow_aggregated:
        return pick_aggregated(df)
    return None

def get_percentile(row, key_candidates):
    for k in key_candidates:
        if k in row.index:
            try:
                return float(row[k])
            except Exception:
                pass
    return None

manifest = pd.read_csv(MANIFEST) if MANIFEST.exists() else pd.DataFrame(columns=["run_dir","scenario","defense","notes"])

records = []
per_endpoint = []

for _, m in manifest.iterrows():
    run_name = str(m["run_dir"])
    run_dir = RUNS_DIR / run_name
    if not run_dir.exists():
        continue

    stats_df = load_locust_stats(run_dir)
    if stats_df is None:
        continue
    # normalize columns
    stats_df.columns = [c.strip() for c in stats_df.columns]

    # pick summary rows for key endpoints
    agg = pick_aggregated(stats_df)
    pub = pick_by_patterns(
        stats_df,
        ["/api/state", "get /api/state", "/api/state/", "public_state"],
    )
    sec_ping = pick_by_patterns(
        stats_df,
        [
            "/api/secure/ping (valid)",
            "/api/secure/ping (invalid)",
            "/api/secure/ping",
            "secure_ping_valid",
            "secure_ping_invalid",
        ],
    )
    sec_state = pick_by_patterns(
        stats_df,
        [
            "/api/secure/state (valid)",
            "/api/secure/state (invalid)",
            "/api/secure/state",
            "secure_state_valid",
            "secure_state_invalid",
        ],
    )
    token = pick_by_patterns(
        stats_df,
        [
            "/api/auth/token",
            "post /api/auth/token",
            "/api/auth/token/",
            "auth_token",
            "auth_token_bad",
        ],
    )

    def row_to_summary(tag, row):
        if row is None:
            return None
        req = int(row.get("Request Count", row.get("RequestCount", 0)) or 0)
        fail = int(row.get("Failure Count", row.get("FailureCount", 0)) or 0)

        avg_rt = row.get("Average Response Time", row.get("AverageResponseTime", None))
        med_rt = row.get("Median Response Time", row.get("MedianResponseTime", None))

        p95 = get_percentile(row, ["95%", "95%ile", "95.0%"])
        p99 = get_percentile(row, ["99%", "99%ile", "99.0%"])

        rps = row.get("Requests/s", row.get("Requests/s", None))
        fps = row.get("Failures/s", row.get("Failures/s", None))

        return {
            "run_dir": run_name,
            "scenario": m.get("scenario",""),
            "defense": m.get("defense",""),
            "notes": m.get("notes",""),
            "endpoint_tag": tag,
            "endpoint_name": row.get("Name",""),
            "requests": req,
            "failures": fail,
            "failure_rate": (fail / req) if req else None,
            "rps": float(rps) if rps == rps else None,
            "failures_per_s": float(fps) if fps == fps else None,
            "avg_rt_ms": float(avg_rt) if avg_rt == avg_rt else None,
            "median_rt_ms": float(med_rt) if med_rt == med_rt else None,
            "p95_ms": p95,
            "p99_ms": p99,
        }

    for tag, row in [
        ("AGG", agg),
        ("PUBLIC_STATE", pub),
        ("SECURE_PING", sec_ping),
        ("SECURE_STATE", sec_state),
        ("AUTH_TOKEN", token),
    ]:
        s = row_to_summary(tag, row)
        if s:
            per_endpoint.append(s)

    # Prometheus snapshots (if present)
    prom_start = read_json_safe(run_dir / "prom_start.json")
    prom_end = read_json_safe(run_dir / "prom_end.json")

    # Git commit
    commit = ""
    p_commit = run_dir / "git_commit.txt"
    if p_commit.exists():
        commit = p_commit.read_text(encoding="utf-8").strip()

    # Meta
    meta = read_json_safe(run_dir / "meta.json")

    # One summary record per run (aggregate)
    if agg is not None:
        req = int(agg.get("Request Count", 0) or 0)
        fail = int(agg.get("Failure Count", 0) or 0)
        avg_rt = agg.get("Average Response Time", None)
        med_rt = agg.get("Median Response Time", None)
        p95 = get_percentile(agg, ["95%", "95%ile", "95.0%"])
        p99 = get_percentile(agg, ["99%", "99%ile", "99.0%"])

        records.append({
            "run_dir": run_name,
            "scenario": m.get("scenario",""),
            "defense": m.get("defense",""),
            "notes": m.get("notes",""),
            "users": meta.get("users",""),
            "spawn_rate": meta.get("spawn_rate",""),
            "run_time": meta.get("run_time",""),
            "git_commit": commit,
            "requests_total": req,
            "failures_total": fail,
            "failure_rate_total": (fail/req) if req else None,
            "avg_rt_ms_total": float(avg_rt) if avg_rt == avg_rt else None,
            "median_rt_ms_total": float(med_rt) if med_rt == med_rt else None,
            "p95_ms_total": p95,
            "p99_ms_total": p99,
            "prom_start_present": (run_dir / "prom_start.json").exists(),
            "prom_end_present": (run_dir / "prom_end.json").exists(),
        })
    else:
        records.append({
            "run_dir": run_name,
            "scenario": m.get("scenario",""),
            "defense": m.get("defense",""),
            "notes": m.get("notes",""),
            "users": meta.get("users",""),
            "spawn_rate": meta.get("spawn_rate",""),
            "run_time": meta.get("run_time",""),
            "git_commit": commit,
        })

df_runs = pd.DataFrame(records)
df_endpoints = pd.DataFrame(per_endpoint)

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
df_runs.to_csv(OUT_CSV, index=False)

with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xw:
    df_runs.to_excel(xw, sheet_name="Runs", index=False)
    df_endpoints.to_excel(xw, sheet_name="Endpoints", index=False)

print("Wrote:", OUT_CSV)
print("Wrote:", OUT_XLSX)
