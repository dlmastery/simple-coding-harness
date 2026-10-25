"""Lab 06 - one harness is not enough: a Pareto front of cost and score, and a model swap."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import agent, course, evaluate, improve, mle, pareto  # noqa: E402

course.banner("Lab 06 · Pareto harnesses and model transfer")

# Every evaluated candidate from labs 03-05 is a point (evolve score, cost).
points = []
for run in ("03-greedy", "04-scores-only", "05-rrsi"):
    for c in improve.candidates(course.RUNS / run):
        if "result" in c:
            points.append((f"{run[:2]}/{c['id']}", c["result"]["score"], c["result"]["cost"]))
front = pareto.front(points)
print(f"{len(points)} evaluated harnesses, {len(front)} on the Pareto front:")
course.table([[i, f"{s:.3f}", f"{c:,.0f}"] for i, s, c in front], ["harness", "evolve beats", "cost/attempt"])

chosen = pareto.profiles(points)
rows = []
for name, (pid, s, c) in chosen.items():
    run, cid = pid.split("/")
    run_dir = next(course.RUNS.glob(f"{run}-*"))
    res = evaluate.evaluate(run_dir / cid / "harness", mle.SPLITS["heldout"], (0, 1))
    rows.append([name, pid, f"{s:.3f}", f"{res.score:.3f}", f"{res.cost:,.0f}"])
course.table(rows, ["profile", "harness", "evolve beats", "heldout beats", "heldout cost"])

# Model as data: does the evolved harness still help a different frozen model?
OTHER = "gpt-5.4-mini"
best = chosen["heavy"][0]
run, cid = best.split("/")
evolved = next(course.RUNS.glob(f"{run}-*")) / cid / "harness"
rows = []
for model in (agent.load_harness(course.H0)["config"]["model"], OTHER):
    for label, hdir in (("h0", course.H0), (f"evolved {best}", evolved)):
        h = agent.load_harness(hdir)
        h["config"] = {**h["config"], "model": model}
        res = evaluate.evaluate(h, mle.SPLITS["evolve"] + mle.SPLITS["heldout"], (0, 1))
        rows.append([model, label, f"{res.score:.3f}", f"{res.tokens:,.0f}"])
course.table(rows, ["frozen model", "harness", "beats (evolve + heldout)", "tokens/attempt"])
course.spend()
