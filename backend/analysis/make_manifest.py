from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "web" / "experiments" / "runs"
OUT = ROOT / "web" / "experiments" / "exports" / "runs_manifest.csv"

rows = []
for run_dir in sorted(RUNS_DIR.glob("*")):
    if not run_dir.is_dir():
        continue
    meta = {}
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    parts = run_dir.name.split("__")
    scenario = meta.get("name", "")
    defense = ""
    notes = ""
    if len(parts) >= 2 and not scenario:
        scenario = parts[1]
    if len(parts) >= 3:
        defense = parts[2]
    if len(parts) >= 4:
        notes = parts[3]

    rows.append({
        "run_dir": run_dir.name,
        "scenario": scenario,                    # derived from folder naming
        "defense": defense,                      # baseline / attacked / defended
        "notes": notes,                          # rep info or defense notes
        "users": meta.get("users", ""),
        "spawn_rate": meta.get("spawn_rate", ""),
        "run_time": meta.get("run_time", ""),
        "host": meta.get("host", ""),
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
        "run_dir","scenario","defense","notes","users","spawn_rate","run_time","host"
    ])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print("Wrote:", OUT)
print("Next: open runs_manifest.csv and fill any missing values if needed.")
