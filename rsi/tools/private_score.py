"""private_score - score one recipe on the private split the inner pack never sees. Twice per visit at most.

    python ../tools/private_score.py --pack .claude/skills/adult-income-meta --task ../tasks/02_breast_cancer.json \\
        --recipe @candidate.json

It is the gate's split: repeated evaluator access is how gates get gamed, so
the third call in a visit is refused. Never available to an actor pack.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, recipe, tasks  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, recipe="the recipe: JSON, k=v pairs, or @file",
                               visit={"type": "int", "default": 1, "help": "the visit number"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "private_score")
    used = [r for r in run.trace.rows("private_score", arm=run.arm, seed=run.seed) if (r["info"] or {}).get("visit") == a.visit]
    if len(used) >= 2:
        raise ValueError("private_score twice per visit at most; repeated evaluator access is how gates get gamed")
    rec = recipe.validate(cli.value(a.recipe))
    score = tasks.score_on(run.task, run.seed, rec, "private")
    run.log("private_score", recipe=rec, val_score=score, visit=a.visit)
    return {"private_score": score, "recipe": rec, "calls_this_visit": len(used) + 1}


if __name__ == "__main__":
    cli.main(main)
