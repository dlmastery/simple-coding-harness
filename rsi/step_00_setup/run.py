"""Lab 00 - check the workbench: Python packages, task data, model access, replay cache."""

import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import bench, course, llm  # noqa: E402

course.banner("Lab 00 · setup")

for pkg in ("pandas", "sklearn", "lightgbm", "openai"):
    try:
        importlib.import_module(pkg)
        print(f"  ok       {pkg}")
    except ImportError:
        print(f"  missing  {pkg}   -> see the README of this lab")

print(f"\ntask data directory: {bench.DATA}")
online = os.environ.get("RSI_LLM") != "replay"
for split, tasks in bench.SPLITS.items():
    for cid in tasks:
        if online and hasattr(bench, "prepare"):
            bench.prepare(cid)   # downloads from OpenML once, a few MB per task
        ready = (bench.DATA / cid / "private").exists()
        print(f"  {split:8s} {cid:16s} {'prepared' if ready else 'not prepared (replay still works)'}")

key = bool(os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY"))
rows = sum(1 for p in llm.CACHE_DIR.glob("*.jsonl") for _ in p.open(encoding="utf-8"))
print(f"\nmodel key present: {key}")
print(f"replay cache: {rows:,} recorded model answers and executions in {llm.CACHE_DIR}")
print("\nMode for the next labs:", os.environ.get("RSI_LLM", "auto"))
