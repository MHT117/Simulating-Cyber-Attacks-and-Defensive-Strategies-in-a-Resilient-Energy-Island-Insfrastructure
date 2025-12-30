#!/usr/bin/env python3
"""
Make plots from results_summary.csv produced by build_results.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def mean_of_repeats(df: pd.DataFrame, value_col: str, group_cols: list[str]) -> pd.DataFrame:
    out = df.groupby(group_cols, dropna=False)[value_col].mean().reset_index()
    return out


def bar_plot(df: pd.DataFrame, x: str, y: str, title: str, xlabel: str, ylabel: str, out_png: Path):
    plt.figure(figsize=(12, 6))
    plt.bar(df[x].astype(str), df[y].astype(float))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", required=True, type=Path)
    ap.add_argument("--out", dest="out_dir", required=True, type=Path)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    runs = pd.read_csv(args.in_csv)

    # p95 total by run (mean of repeats)
    runs["label"] = runs["scenario"].astype(str) + " | " + runs["condition"].astype(str)
    p95 = mean_of_repeats(runs, "p95_ms", ["label"]).sort_values("p95_ms")
    bar_plot(
        p95, "label", "p95_ms",
        "p95 latency (ms) by run (mean of repeats)",
        "scenario | condition", "p95 latency (ms)",
        args.out_dir / "p95_total_by_run.png"
    )

    # blocked rate by run
    br = mean_of_repeats(runs, "blocked_rate_401_403", ["label"]).sort_values("blocked_rate_401_403")
    br["blocked_rate_percent"] = br["blocked_rate_401_403"] * 100.0
    bar_plot(
        br, "label", "blocked_rate_percent",
        "Blocked/Denied rate by run (401+403) (mean of repeats)",
        "scenario | condition", "rate (%)",
        args.out_dir / "blocked_rate_by_run.png"
    )

    print(f"Wrote plots to: {args.out_dir}")

if __name__ == "__main__":
    main()
