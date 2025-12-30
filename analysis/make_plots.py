from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "paper_assets" / "tables" / "results_summary.xlsx"
OUTDIR = ROOT / "paper_assets" / "figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

df_runs = pd.read_excel(XLSX, sheet_name="Runs")
df_ep = pd.read_excel(XLSX, sheet_name="Endpoints")

plt.rcParams.update(
    {
        "figure.dpi": 200,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
    }
)

defense_order = ["baseline", "attacked", "defended"]

# Helper: keep only labeled runs
df_runs = df_runs[df_runs["defense"].notna() & (df_runs["defense"].astype(str).str.len() > 0)]
df_ep = df_ep[df_ep["defense"].notna() & (df_ep["defense"].astype(str).str.len() > 0)]
df_runs["defense"] = pd.Categorical(df_runs["defense"], categories=defense_order, ordered=True)
df_ep["defense"] = pd.Categorical(df_ep["defense"], categories=defense_order, ordered=True)

def save_bar(df, x_col, y_col, title, filename, ylabel, rotation=20, ylim=None):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df[x_col], df[y_col], color="#4C78A8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=rotation)
    if ylim:
        ax.set_ylim(*ylim)
    fig.tight_layout()
    fig.savefig(OUTDIR / filename)
    plt.close(fig)

# Plot 1: p95 total latency by run (aggregate repeats)
df1 = df_runs.dropna(subset=["p95_ms_total"]).copy()
df1 = df1.groupby(["scenario", "defense"], as_index=False, observed=False)["p95_ms_total"].mean()
df1 = df1.sort_values(["scenario", "defense"])
df1["label"] = df1["scenario"].astype(str) + " | " + df1["defense"].astype(str)
save_bar(
    df1,
    "label",
    "p95_ms_total",
    "p95 latency (ms) by run (mean of repeats)",
    "p95_total_by_run.png",
    "p95 latency (ms)",
)

# Plot 2: failure rate total by run (aggregate repeats)
df2 = df_runs.dropna(subset=["failure_rate_total"]).copy()
df2 = df2.groupby(["scenario", "defense"], as_index=False, observed=False)["failure_rate_total"].mean()
df2 = df2.sort_values(["scenario", "defense"])
df2["label"] = df2["scenario"].astype(str) + " | " + df2["defense"].astype(str)
df2["failure_rate_pct"] = df2["failure_rate_total"] * 100
save_bar(
    df2,
    "label",
    "failure_rate_pct",
    "Blocked/Denied rate by run (mean of repeats)",
    "failure_rate_total_by_run.png",
    "rate (%)",
    ylim=(0, 100),
)

# Plot 3: Endpoint p95 comparison (PUBLIC_STATE vs SECURE vs AUTH_TOKEN)
df3 = df_ep[df_ep["endpoint_tag"].isin(["PUBLIC_STATE", "SECURE_PING", "SECURE_STATE", "AUTH_TOKEN"])].copy()
df3 = df3.dropna(subset=["p95_ms"])

# pivot: mean p95 per endpoint_tag and defense
pivot = df3.pivot_table(index="endpoint_tag", columns="defense", values="p95_ms", aggfunc="mean", observed=False)
pivot = pivot.reindex(index=["PUBLIC_STATE", "SECURE_PING", "SECURE_STATE", "AUTH_TOKEN"])
pivot = pivot.reindex(columns=defense_order)
fig, ax = plt.subplots(figsize=(8, 4))
pivot.plot(kind="bar", ax=ax)
ax.set_title("Mean p95 latency (ms) by endpoint and defense")
ax.set_xlabel("")
ax.set_ylabel("p95 latency (ms)")
ax.tick_params(axis="x", rotation=0)
fig.tight_layout()
fig.savefig(OUTDIR / "p95_by_endpoint_and_defense.png")
plt.close(fig)

print("Wrote plots to:", OUTDIR)
