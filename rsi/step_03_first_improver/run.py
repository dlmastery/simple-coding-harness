"""Lab 03 - the first improver: propose edits, evaluate on evolve, keep anything that scores higher."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import course, improve, mle, report  # noqa: E402

course.banner("Lab 03 · a greedy harness improver")

RUN = course.RUNS / "03-greedy"
policy = improve.load_policy(course.I0)          # greedy acceptance, no critic, no pruner
improve.evolve(RUN, course.H0, mle.SPLITS["evolve"], rounds=3, p=policy)

print("\nThe lineage of the final harness:")
report.lineage_table(RUN)
print("Decisions:", report.decisions(RUN), "\n")

harness, best = report.product(RUN)
report.splits_table({f"greedy {best}": harness})
course.spend()
