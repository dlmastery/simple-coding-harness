"""save_model - pickle the fitted pipeline of a recipe this arm fitted into the run directory.

    python ../tools/save_model.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --recipe @best.json

Not a search fit: it refits the same recipe on the same split (deterministic)
and counts nothing. Refused for a recipe this arm never fitted.
"""
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, recipe, tasks  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, recipe="the recipe to save: JSON, k=v pairs, or @file"))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "save_model")
    rec = recipe.validate(cli.value(a.recipe))
    if not any(r["recipe"] == rec for r in run.arm_state["fits"]):
        raise ValueError("save_model takes a recipe this arm fitted")
    fitted = tasks.fit_for(run.task, run.seed, rec)
    if fitted["pipeline"] is None:
        raise ValueError(f"that recipe did not fit: {fitted['error']}")
    path = run.root / f"model_{run.arm}_{run.seed}.pkl"
    with open(path, "wb") as f:
        pickle.dump(fitted["pipeline"], f)
    run.log("save_model", recipe=rec, path=path.name)
    return {"saved": str(path), "recipe": rec}


if __name__ == "__main__":
    cli.main(main)
