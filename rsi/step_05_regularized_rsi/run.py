"""Lab 05 - RRSI: budget, critic, pruner and a noise floor; then two overfitting probes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import course, edits, evaluate, improve, mle, report  # noqa: E402

course.banner("Lab 05 · regularized recursive self-improvement")

RUN = course.RUNS / "05-rrsi"
policy = improve.load_policy(course.I0, critic=True, prune=True, accept="rrsi", budget_max=4, budget_min=1)
improve.evolve(RUN, course.H0, mle.SPLITS["evolve"], rounds=3, p=policy)

print("\nRRSI lineage:")
report.lineage_table(RUN)
print("Decisions:", report.decisions(RUN), "\n")

greedy, g_best = report.product(course.RUNS / "03-greedy")
rrsi, r_best = report.product(RUN)
report.splits_table({f"greedy {g_best}": greedy, f"rrsi {r_best}": rrsi})

# Probe 1 - the critic, after the fact: would it have rejected anything the greedy run kept?
terms = improve.leakage_terms(mle.SPLITS["evolve"])
print("Critic applied to the greedy lineage:")
for c in improve.lineage(course.RUNS / "03-greedy", g_best)[1:]:
    hits = improve.critic(c["meta"].get("edits", []), {}, terms)
    print(f"  {c['id']}: {hits or 'clean'}")

# Probe 2 - a counterfactual protocol (CHASE): same competitions, descriptions without their names.
print("\nCounterfactual: MLE-bench's obfuscated descriptions (same task, competition name removed)")
rows = []
base = evaluate.evaluate(course.H0, mle.SPLITS["evolve"], (0, 1))
base_cf = evaluate.evaluate(course.H0, mle.SPLITS["evolve"], (0, 1), obfuscate=True)
for label, h in [(f"greedy {g_best}", greedy), (f"rrsi {r_best}", rrsi)]:
    orig = evaluate.evaluate(h, mle.SPLITS["evolve"], (0, 1)).score - base.score
    cf = evaluate.evaluate(h, mle.SPLITS["evolve"], (0, 1), obfuscate=True).score - base_cf.score
    kept = cf / orig if orig > 0 else float("nan")
    rows.append([label, f"{orig:+.3f}", f"{cf:+.3f}", f"{kept:.0%}" if orig > 0 else "-"])
course.table(rows, ["harness", "gain, original protocol", "gain, obfuscated", "gain kept"])
course.spend()
