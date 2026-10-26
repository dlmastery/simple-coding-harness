"""Lab 09 - audit every lineage, then write the claim your evidence supports."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import course, improve, bench  # noqa: E402

course.banner("Lab 09 · audit and defend")

terms = improve.leakage_terms(bench.SPLITS["evolve"])
rows = []
for run_dir in sorted(p for p in course.RUNS.iterdir() if (p / "BEST").exists()):
    best = (run_dir / "BEST").read_text(encoding="utf-8").strip()
    lineage = improve.lineage(run_dir, best)
    kept = [e for c in lineage[1:] for e in c["meta"].get("edits", [])]
    refused = [r for c in improve.candidates(run_dir) for r in c["meta"].get("refused", [])]
    leaks = improve.critic(kept, {}, terms)
    files = sorted({e["file"] for e in kept})
    rows.append([run_dir.name, best, len(lineage) - 1, len(kept), len(leaks), len(refused), ", ".join(files)[:60]])
course.table(rows, ["run", "final", "accepted steps", "kept edits", "leak hits", "refused (integrity)", "files touched"])

print("Refused edits are integrity events: the proposer tried to change something it may not.")
for run_dir in sorted(p for p in course.RUNS.iterdir() if (p / "BEST").exists()):
    for c in improve.candidates(run_dir):
        for r in c["meta"].get("refused", []):
            print(f"  {run_dir.name}/{c['id']}: {r['file']} -> {r['refused']}")
course.spend()
