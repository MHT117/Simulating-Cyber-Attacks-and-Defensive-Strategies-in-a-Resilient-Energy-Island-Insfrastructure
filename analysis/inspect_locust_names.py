from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "research" / "runs"

for run_dir in sorted(RUNS.glob("*")):
    p = run_dir / "locust_stats.csv"
    if not p.exists():
        alt = list(run_dir.glob("*_stats.csv"))
        if alt:
            p = alt[0]
        else:
            continue
    df = pd.read_csv(p)
    if "Name" not in df.columns:
        continue
    names = sorted(set(df["Name"].astype(str).tolist()))
    print("\n=== ", run_dir.name, " ===")
    for n in names[:80]:
        print(n)
    if len(names) > 80:
        print(f"... ({len(names)} total)")
