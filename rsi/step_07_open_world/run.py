"""Lab 07 - Harness^2: improve the harness during each task, with no grader, and learn how to edit."""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import agent, course, open_world, mle  # noqa: E402

course.banner("Lab 07 · the open world, without a verifier")

STREAM = mle.SPLITS["heldout"] + mle.SPLITS["ood"]   # arrive one at a time; the system never sees a grade
EDITOR = "gpt-5.4-mini"
OUT = course.RUNS / "07-open-world"

rows = []
for system, use_library in (("harness scaling (no library)", False), ("harness^2 (library)", True)):
    out = OUT / ("library" if use_library else "no-library")
    library = out / "EXPERIENCE.md"
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "done.json").exists():
        library.write_text("", encoding="utf-8")
        records = []
        for cid in STREAM:
            delivered, rec = open_world.step(course.H0, cid, library, out / cid, EDITOR, use_library=use_library)
            records.append(rec)
            print(f"{system:30s} {cid:44s} used {rec['use'] or 'reference'}  "
                  f"hidden beats {rec['delivered']['hidden_beats']:.2f}")
        (out / "done.json").write_text(json.dumps(records, indent=1), encoding="utf-8")
    for rec in json.loads((out / "done.json").read_text(encoding="utf-8")):
        rows.append([system, rec["competition"], f"{rec['reference']['hidden_beats']:.2f}",
                     f"{rec['delivered']['hidden_beats']:.2f}", ",".join(rec["use"]) or "kept reference"])

course.table(rows, ["system", "competition (in arrival order)", "reference beats", "delivered beats", "composer kept"])
print("The improvement library after the stream (what Harness^2 carries forward):\n")
print((OUT / "library" / "EXPERIENCE.md").read_text(encoding="utf-8") or "(empty)")
course.spend()
