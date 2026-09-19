"""score_test - score one recipe on the locked test split: once, after FREEZE.

    python ../tools/score_test.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json \\
        --recipe '{"model": "hgb", "hyper": 0.1, "scale": "no", "encode": "ordinal", "class_weight": "none"}'

Refused while fits remain (FREEZE is the budget spent, or freeze.py forfeiting
the rest) and refused a second time. The lesson's Claude Code hook blocks the
call before it runs; the script refuses it again on its own.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, recipe  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, recipe="the recipe to score: JSON, k=v pairs, or @file"))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "score_test")
    rec = recipe.validate(cli.value(a.recipe))
    if not any(r["recipe"] == rec for r in run.arm_state["fits"]):
        raise ValueError("score_test takes a recipe this arm fitted")
    score = run.score_test_once(rec)
    run.log("score_test", recipe=rec, val_score=score, fits_used=run.arm_state["fits_used"], frozen=True)
    return {"test_score": score, "recipe": rec, "fits_used": run.arm_state["fits_used"], "metric": run.task["metric"]}


if __name__ == "__main__":
    cli.main(main)
