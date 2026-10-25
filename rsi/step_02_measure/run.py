"""Lab 02 - honest measurement: three splits, replicas, a noise band, and an A/A test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import course, evaluate, mle  # noqa: E402

course.banner("Lab 02 · measure before you improve")

results = {}
for split, comps in mle.SPLITS.items():
    results[split] = evaluate.evaluate(course.H0, comps, replicas=(0, 1, 2, 3),
                                       save_to=course.RUNS / "02-h0" / split)

rows = []
for split, res in results.items():
    for cid, v in res.per_competition().items():
        rows.append([split, cid, f"{v:.3f}"])
course.table(rows, ["split", "competition", "beats (mean of 4 replicas)"])

course.table([[s, f"{r.score:.3f}", f"{evaluate.noise_band(r):.3f}", f"{r.above_median:.2f}", f"{r.valid:.2f}",
               f"{r.tokens:,.0f}", f"{r.exec_seconds:.0f}"] for s, r in results.items()],
             ["split", "beats", "noise band (2 SE)", "above median", "valid", "tokens/attempt", "train s/attempt"])

# A/A test: the same harness against itself. Replicas 0-1 play "old", 2-3 play "new".
ev = results["evolve"]
rename = lambda res, pair: evaluate.Result({k.replace(f"/r{a}", f"/s{i}"): v for k, v in res.cells.items()
                                            for i, a in enumerate(pair) if k.endswith(f"/r{a}")},
                                           res.tokens, res.exec_seconds, res.above_median, res.valid)
d = evaluate.paired_diff(rename(ev, (2, 3)), rename(ev, (0, 1)))
print("A/A test on evolve (identical harness, different draws):")
print("  ", evaluate.fmt_diff(d))
course.spend()
