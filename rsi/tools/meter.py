"""meter - AIDE2's budget meter and outer-loop rule: the cost so far per arm, and keep-if-better across the set.

    python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --of v1
    python ../tools/meter.py --pack ... --task ... --target ... --decide --proposal g1 --before v1 --after v2 --tasks ../tasks

The cost of an arm is what the log holds: fits (the budget) and script calls
(every trace row the arm wrote); there is no token count here because no
Python harness sees the agent's transcript, and the README says so. `--decide`
is the outer rule: per curriculum problem, the `after` arm's best val minus
the `before` arm's; the statistical layer discards a per-problem gain more
than 3 MADs above the median (one lucky problem cannot carry the decision);
the rewrite is kept only if the remaining total gain is positive and it
loses on at most half the problems - otherwise the proposal's version is
rolled back. Both arms must have run every problem under the same budget;
a missing arm is a refusal, not a guess.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, proposals, tasks  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, target={"required": True, "help": "the inner (actor) pack"},
                               of={"default": "", "help": "the arm to meter (default: all arms)"},
                               decide={"action": "store_true", "help": "the outer rule: keep-if-better across --tasks"},
                               proposal="with --decide: the operators proposal (patch_pack stage 1, approval: metered)",
                               before="with --decide: the arm that ran the previous operators", after="with --decide: the arm that ran the rewrite",
                               tasks="with --decide: the curriculum directory", mad_k={"type": float, "default": 3.0, "help": "the outlier threshold in MADs"}))


def aide_keep(before, after, mad_k=3.0):
    """AIDE2's outer rule as one function. Returns (keep, detail)."""
    problems = sorted(set(before) & set(after))
    gains = {p: round(after[p] - before[p], 4) for p in problems}
    values = sorted(gains.values())
    median = values[len(values) // 2] if values else 0.0
    mad = max(sorted(abs(v - median) for v in values)[len(values) // 2] if values else 0.0, 0.01)   # a floor of one AUC point: rounding is not spread
    outliers = [p for p, g in gains.items() if g - median > mad_k * mad]
    kept = {p: g for p, g in gains.items() if p not in outliers}
    total = round(sum(kept.values()), 4)
    keep = bool(kept) and total > 0 and sum(1 for g in kept.values() if g < 0) <= len(kept) // 2
    return keep, {"gains": gains, "outliers_discarded": outliers, "total_gain": total, "wins": sum(1 for g in kept.values() if g > 0),
                  "losses": sum(1 for g in kept.values() if g < 0), "median": median, "mad": round(mad, 4)}


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "meter")
    target = Run(a.target, a.task, "memory", a.seed, a.run)
    from _lib.trace import TraceLog

    rows = []
    for path in sorted(target.root.parent.glob("*/traces.jsonl")):
        rows += TraceLog(path).rows()
    if a.of:
        rows = [r for r in rows if r["arm"] == a.of]
    fits = [r for r in rows if r["event"] == "fit"]
    out = {"arm": a.of or "all", "fits": len(fits), "calls": len(rows), "problems": sorted({r["problem"] for r in fits}),
           "note": "cost = fits (the budget) + script calls (trace rows); no token count: no harness sees the agent's transcript"}
    if not a.decide:
        run.log("meter", **{k: v for k, v in out.items() if k != "note"})
        return out
    if not (a.proposal and a.before and a.after and a.tasks):
        raise ValueError("--decide needs --proposal, --before, --after and --tasks")
    curriculum = [tasks.load_task(p) for p in sorted(Path(a.tasks).glob("*.json"))]
    curriculum = [t for t in curriculum if t["role"] == "curriculum"]
    best = {arm: {} for arm in (a.before, a.after)}
    budget = {}
    for t in curriculum:
        for arm in (a.before, a.after):
            r = Run(a.target, next(p for p in sorted(Path(a.tasks).glob("*.json")) if tasks.load_task(p)["name"] == t["name"]), arm, a.seed, a.run)
            if not r.opened or not r.arm_state["frozen"]:
                raise ValueError(f"arm {arm!r} has not run {t['name']} to FREEZE; the rule needs every problem under the same budget")
            scored = [f for f in r.arm_state["fits"] if f["val_score"] is not None]
            best[arm][t["name"]] = max((f["val_score"] for f in scored), default=0.0)
            budget[arm] = budget.get(arm, 0) + r.arm_state["fits_used"]
    if budget[a.before] != budget[a.after]:
        raise ValueError(f"the budgets differ: {a.before} spent {budget[a.before]} fits, {a.after} {budget[a.after]}; not comparable")
    keep, detail = aide_keep(best[a.before], best[a.after], a.mad_k)
    path, record = proposals.load(run.root, a.proposal)
    label = record.get("version")
    if record.get("decision") is not None:
        raise ValueError(f"proposal {a.proposal} is already decided ({record['decision']})")
    if keep:
        record.update(decision="y", approved_by="metered", applied=True)
    else:
        packs.rollback(target.pack_dir, target.versions_dir, label)
        record.update(decision="n", approved_by="metered", applied=False)
        run.log("rollback", proposal=a.proposal, version=label, by="metered", checksums=packs.checksums(target.pack_dir))
    record["evaluation"] = {"before": a.before, "after": a.after, "budget": budget, **detail}
    proposals.save(path, record)
    run.log("decide", proposal=a.proposal, keep=keep, by="metered", budget=budget, **detail)
    return {"proposal": a.proposal, "keep": keep, "decision": record["decision"], "version": label, "budget": budget,
            "best_before": best[a.before], "best_after": best[a.after], **detail}


if __name__ == "__main__":
    cli.main(main)
