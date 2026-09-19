"""write_plan - RSIAgent's curriculum: write the next phase's experiments into the actor pack's plan.json.

    python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json \\
        --target .claude/skills/adult-income-actor --plan '{"phase": "broad", "c": 2.0, "experiments": [ ...recipes... ]}'
    python ../tools/write_plan.py --pack ... --task ... --target ... --plan @plan.json
    python ../tools/write_plan.py --pack ... --task ... --target ... --uncertainty            # the numbers, no write

A plan is {phase: broad | deep, c: number, experiments: [recipes]}; the actor
fits the experiments in order (`fit_recipe.py --recipes @<actor>/plan.json`).
`--uncertainty` prints, per model family, n (fits so far on this problem),
success ((wins + 1) / (n + 2), a win = a val_score at least the first fit's)
and u = (1 - success) + c / (n + 1) for the given --c, so the planner can
check its arithmetic; plan.json is per-run scratch and not part of the pack's
versioned text.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, recipe  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, target={"required": True, "help": "the actor pack that will run the plan"},
                               plan="the plan: JSON or @file", uncertainty={"action": "store_true", "help": "print the per-family numbers instead of writing"},
                               c={"type": float, "default": 2.0, "help": "the exploration weight for --uncertainty"}))


def uncertainty(rows, c, models):
    """Per family: n, wins, success, u - the numbers the planner ranks families by."""
    baseline = next((r["val_score"] for r in rows if r["val_score"] is not None), None)
    out = {}
    for m in models:
        mine = [r for r in rows if r["recipe"]["model"] == m]
        n = len(mine)
        wins = sum(1 for r in mine if r["val_score"] is not None and baseline is not None and r["val_score"] >= baseline)
        faults = sum(1 for r in mine if r["val_score"] is None or (baseline is not None and r["val_score"] < baseline))
        success = (wins + 1) / (n + 2)
        out[m] = {"n": n, "wins": wins, "faults": faults, "success": round(success, 4), "u": round((1 - success) + c / (n + 1), 4)}
    return out


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "write_plan")
    target = Run(a.target, a.task, a.arm, a.seed, a.run)
    rows = target.fit_rows()
    models = json.loads(target.files["schema.json"]).get("models", recipe.SCHEMA["model"])
    if a.uncertainty or not a.plan:
        return {"phase": "broad" if not rows else "deep", "c": a.c, "fits_so_far": len(rows), "families": uncertainty(rows, a.c, models),
                "tried": [r["recipe"] for r in rows]}
    plan = cli.value(a.plan)
    if not isinstance(plan, dict) or plan.get("phase") not in ("broad", "deep") or not isinstance(plan.get("experiments"), list):
        raise ValueError("a plan is {phase: broad | deep, c: number, experiments: [recipes]}")
    experiments = [recipe.validate(r) for r in plan["experiments"]]
    if not experiments:
        raise ValueError("a plan needs at least one experiment")
    plan = {"phase": plan["phase"], "c": float(plan.get("c", 0)), "experiments": experiments}
    with open(target.pack_dir / "plan.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    run.log("plan", phase=plan["phase"], c=plan["c"], families=[r["model"] for r in experiments], n=len(experiments))
    return {"written": str(target.pack_dir / "plan.json"), "phase": plan["phase"], "c": plan["c"], "experiments": len(experiments),
            "families": [r["model"] for r in experiments]}


if __name__ == "__main__":
    cli.main(main)
