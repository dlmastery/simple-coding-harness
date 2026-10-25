"""Lab 08 - recursion: revise the improver from its own run, then test the revised improver fairly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import course, edits, evaluate, mle, recursive, report  # noqa: E402

course.banner("Lab 08 · improve the improver")

I1 = course.RSI / "improvers" / "i1"
RUN0 = course.RUNS / "03-greedy"          # the improver i0 at work (lab 03)
RUN1 = course.RUNS / "08-i1"

# 1. The meta-improver reads i0's whole run and how its product did on heldout competitions.
product0, best0 = report.product(RUN0)
_, transfer = recursive.transfer_report(product0, mle.SPLITS["heldout"])
if not (I1 / "policy.json").exists():
    diagnosis, refused = recursive.meta_step(course.I0, RUN0, I1, transfer)
    print("refused meta-edits:", refused or "none")
print("Diagnosis of i0:\n ", (I1 / "DIAGNOSIS.md").read_text(encoding="utf-8").strip()[:1200], "\n")
print("What changed in the improver:\n")
print(edits.diff(course.I0, I1) or "(no change)", "\n")

# 2. The revised improver does the same job under the same budget: from h0, on the evolve set.
product1 = recursive.run_improver(I1, RUN1, course.H0, rounds=3)
_, best1 = report.product(RUN1)

# 3. Fair comparison. Heldout was seen by the meta-improver, so only OOD is untouched by every level.
report.splits_table({f"i0 product {best0}": product0, f"i1 product {best1}": product1})
d = evaluate.paired_diff(evaluate.evaluate(product1, mle.SPLITS["ood"], (0, 1)),
                         evaluate.evaluate(product0, mle.SPLITS["ood"], (0, 1)))
print("i1 versus i0 on OOD, the only split no level has seen:\n  ", evaluate.fmt_diff(d))
course.spend()
