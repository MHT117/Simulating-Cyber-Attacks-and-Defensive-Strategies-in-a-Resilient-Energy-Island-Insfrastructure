#!/usr/bin/env python3
"""
Build a clean results summary from Locust CSV outputs.

Inputs:
  --runs-dir  directory containing run folders, each with:
              - meta.json
              - locust_stats.csv
              - locust_failures.csv (may be missing if no failures)
Outputs (to --out):
  - results_summary.csv
  - results_summary.xlsx
  - runs_manifest.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class RunMeta:
    run_id: str
    scenario: str
    condition: str
    repeat: int
    host: str
    users: int
    spawn_rate: int
    duration: str
    started_at: str

    @staticmethod
    def load(p: Path) -> "RunMeta":
        d = json.loads(p.read_text(encoding="utf-8"))
        return RunMeta(
            run_id=d["run_id"],
            scenario=d["scenario"],
            condition=d["condition"],
            repeat=int(d.get("repeat", 1)),
            host=d.get("host", ""),
            users=int(d.get("users", 0)),
            spawn_rate=int(d.get("spawn_rate", 0)),
            duration=str(d.get("duration", "")),
            started_at=str(d.get("started_at", "")),
        )


def find_file(run_dir: Path, suffix: str) -> Optional[Path]:
    # Expected: locust_stats.csv, locust_failures.csv, etc.
    p = run_dir / f"locust_{suffix}.csv"
    return p if p.exists() else None


def parse_stats(stats_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(stats_csv)
    # Locust versions vary: some use "Name", some "name"
    if "Name" not in df.columns and "name" in df.columns:
        df = df.rename(columns={"name": "Name"})
    return df


def parse_failures(fail_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(fail_csv)
    # Columns often: Method, Name, Error, Occurrences
    if "Occurrences" not in df.columns and "occurrences" in df.columns:
        df = df.rename(columns={"occurrences": "Occurrences"})
    if "Error" not in df.columns and "error" in df.columns:
        df = df.rename(columns={"error": "Error"})
    if "Name" not in df.columns and "name" in df.columns:
        df = df.rename(columns={"name": "Name"})
    return df


def blocked_counts(fails: pd.DataFrame) -> Dict[str, int]:
    """
    Return counts of blocked/denied by status code, based on failure "Error" strings.
    We look for "HTTP 401", "HTTP 403", "HTTP 429".
    """
    out = {"401": 0, "403": 0, "429": 0, "other": 0}
    if fails is None or fails.empty:
        return out

    for _, row in fails.iterrows():
        err = str(row.get("Error", ""))
        occ = int(row.get("Occurrences", 0))
        if "HTTP 401" in err:
            out["401"] += occ
        elif "HTTP 403" in err:
            out["403"] += occ
        elif "HTTP 429" in err:
            out["429"] += occ
        else:
            out["other"] += occ
    return out


def pick_total_row(stats: pd.DataFrame) -> pd.Series:
    # Prefer Aggregated / Total row, else sum
    for key in ("Aggregated", "Total"):
        m = stats["Name"].astype(str).str.lower().eq(key.lower())
        if m.any():
            return stats[m].iloc[0]
    # Fallback: sum numeric columns
    numeric = stats.select_dtypes(include="number")
    summed = numeric.sum(numeric_only=True)
    # attach minimal
    s = pd.Series({"Name": "Summed"})
    return s._append(summed)


def safe_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def build(runs_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    run_rows: List[dict] = []
    endpoint_rows: List[dict] = []

    for meta_path in sorted(runs_dir.rglob("meta.json")):
        run_dir = meta_path.parent
        stats_path = find_file(run_dir, "stats")
        if not stats_path:
            continue

        meta = RunMeta.load(meta_path)
        stats = parse_stats(stats_path)
        fails_path = find_file(run_dir, "failures")
        fails = parse_failures(fails_path) if fails_path and fails_path.exists() else None

        totals = pick_total_row(stats)
        totals_requests = int(totals.get("Request Count", totals.get("num_requests", totals.get("Requests", 0))) or 0)
        totals_failures = int(totals.get("Failure Count", totals.get("num_failures", totals.get("Failures", 0))) or 0)

        # p95 column name varies: "95%" or "95%" string or "95% (ms)"
        p95 = None
        for col in stats.columns:
            if str(col).strip().startswith("95"):
                p95 = col
                break
        total_p95_ms = safe_float(totals.get(p95, float("nan"))) if p95 else float("nan")

        # Requests/s column varies
        rps = None
        for col in stats.columns:
            if str(col).lower().replace(" ", "") in ("requests/s", "rps", "requestspersecond"):
                rps = col
                break
        total_rps = safe_float(totals.get(rps, float("nan"))) if rps else float("nan")

        bc = blocked_counts(fails)
        blocked_total = bc["401"] + bc["403"]  # ignore 429 by default
        blocked_rate = (blocked_total / totals_requests) if totals_requests else float("nan")

        run_rows.append({
            "run_id": meta.run_id,
            "scenario": meta.scenario,
            "condition": meta.condition,
            "repeat": meta.repeat,
            "host": meta.host,
            "users": meta.users,
            "spawn_rate": meta.spawn_rate,
            "duration": meta.duration,
            "started_at": meta.started_at,
            "total_requests": totals_requests,
            "total_failures": totals_failures,
            "failure_rate": (totals_failures / totals_requests) if totals_requests else float("nan"),
            "blocked_401": bc["401"],
            "blocked_403": bc["403"],
            "blocked_429": bc["429"],
            "blocked_other": bc["other"],
            "blocked_total_401_403": blocked_total,
            "blocked_rate_401_403": blocked_rate,
            "p95_ms": total_p95_ms,
            "rps": total_rps,
        })

        # endpoint-level rows (exclude Aggregated/Total)
        for _, row in stats.iterrows():
            name = str(row.get("Name", ""))
            if name.lower() in ("aggregated", "total"):
                continue
            if name.strip() == "":
                continue

            req = int(row.get("Request Count", row.get("num_requests", 0)) or 0)
            fail = int(row.get("Failure Count", row.get("num_failures", 0)) or 0)
            ep_p95 = safe_float(row.get(p95, float("nan"))) if p95 else float("nan")
            ep_rps = safe_float(row.get(rps, float("nan"))) if rps else float("nan")

            endpoint_rows.append({
                "run_id": meta.run_id,
                "scenario": meta.scenario,
                "condition": meta.condition,
                "repeat": meta.repeat,
                "endpoint_tag": name,
                "requests": req,
                "failures": fail,
                "failure_rate": (fail / req) if req else float("nan"),
                "p95_ms": ep_p95,
                "rps": ep_rps,
            })

    return pd.DataFrame(run_rows), pd.DataFrame(endpoint_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    runs_df, endpoints_df = build(args.runs_dir)

    # Manifest
    manifest_cols = ["run_id", "scenario", "condition", "repeat", "host", "users", "spawn_rate", "duration", "started_at"]
    manifest = runs_df[manifest_cols].copy() if not runs_df.empty else pd.DataFrame(columns=manifest_cols)
    manifest.to_csv(args.out / "runs_manifest.csv", index=False)

    # Save summary CSV + XLSX
    runs_df.to_csv(args.out / "results_summary.csv", index=False)

    xlsx_path = args.out / "results_summary.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
        runs_df.to_excel(w, sheet_name="Runs", index=False)
        endpoints_df.to_excel(w, sheet_name="Endpoints", index=False)

    print(f"Wrote: {xlsx_path}")
    print(f"Wrote: {args.out / 'results_summary.csv'}")
    print(f"Wrote: {args.out / 'runs_manifest.csv'}")


if __name__ == "__main__":
    main()
