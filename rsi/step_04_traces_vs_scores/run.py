"""Lab 04 - Meta-Harness's question: does the proposer need raw traces, or are scores enough?"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import course, improve, bench, report  # noqa: E402

course.banner("Lab 04 · raw traces versus scores")

RUN = course.RUNS / "04-scores-only"
policy = improve.load_policy(course.I0, evidence="scores")   # same budget as lab 03, less evidence
improve.evolve(RUN, course.H0, bench.SPLITS["evolve"], rounds=3, p=policy)

print("\nScores-only lineage:")
report.lineage_table(RUN)

traces, t_best = report.product(course.RUNS / "03-greedy")
scores, s_best = report.product(RUN)
report.splits_table({f"traces {t_best}": traces, f"scores-only {s_best}": scores})
course.spend()
