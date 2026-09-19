"""fit_recipe - fit one recipe (or a list) on train, score it on val, count the budget.

    python ../tools/fit_recipe.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json \\
        --recipe '{"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}'
    python ../tools/fit_recipe.py --pack ... --task ... --recipe model=rf,hyper=16,scale=no,encode=ordinal,class_weight=balanced
    python ../tools/fit_recipe.py --pack ... --task ... --recipes @recipes.json      # a list, in order, one budget count each
    python ../tools/fit_recipe.py --pack ... --task ... --recipes @.claude/skills/adult-income-regular/schema.json   # the static list
    python ../tools/fit_recipe.py --pack ... --task ... --recipes @.claude/skills/adult-income-loop/recipes.json --range 6:12   # t = 6..11

Every fit counts, an error too. The 25th is refused. A recipe outside
schema.json, a model the task does not allow, a recipe a forbid card rules
out, or one the schema's `forbid` list names, is refused and costs no fit.
The result of the last fit says FREEZE when the budget is spent.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory, recipe, tasks  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, recipe="one recipe: JSON, k=v pairs, or @file",
                               recipes="a JSON list of recipes (or @file): fitted in order, one budget count each",
                               range="with --recipes: the slice t0:t1 of the list to fit (0-based, t1 excluded), e.g. 0:6"))


def check(run, rec, schema):
    """Every reason this recipe may not be fitted, before any budget is spent."""
    rec = recipe.validate(rec)
    if rec["model"] not in run.task["allowed_models"]:
        raise ValueError(f"model {rec['model']} is not allowed by the task")
    if rec["model"] not in schema.get("models", recipe.SCHEMA["model"]):
        raise ValueError(f"model {rec['model']} is not in schema.json -> models")
    fields = schema.get("fields", recipe.SCHEMA)
    for f in ("scale", "encode", "class_weight"):
        if rec[f] not in fields.get(f, recipe.SCHEMA[f]):
            raise ValueError(f"{f}={rec[f]!r} is not in schema.json -> fields")
    if rec["hyper"] not in fields.get("hyper", recipe.SCHEMA["hyper"]).get(rec["model"], []):
        raise ValueError(f"hyper={rec['hyper']!r} is not in schema.json -> fields -> hyper -> {rec['model']}")
    for rule in schema.get("forbid", []):                      # the schema's own forbids (a meta patch)
        if rec.get(rule["field"]) == rule["value"]:
            raise ValueError(f"schema.json forbids {rule['field']}={rule['value']!r} (no fit spent)")
    cards = [] if run.memory_off else memory.load(run.memory_path)
    card = memory.forbidden(rec, cards, run.profile)
    if card is not None:
        raise ValueError(f"a forbid card rules this recipe out: {json.dumps(card['then'])} (no fit spent)")
    return rec


def fit_one(run, rec, error=None):
    """Count one fit, run it (or record the error), append the trace row and the state row."""
    n = run.spend()
    t0 = time.time()
    if error is None:
        fitted = tasks.fit_for(run.task, run.seed, rec)
        val, error = fitted["val_score"], fitted["error"]
    else:
        val = None
    row = {"n": n, "recipe": rec, "val_score": val, "error": error}
    run.arm_state["fits"].append(row)
    run.log("fit", recipe=rec, val_score=val, error=error, seconds=round(time.time() - t0, 3), n=n)
    out = {**row, "fits_left": run.left}
    if run.arm_state["frozen"]:
        out["FREEZE"] = True
    return out


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "fit_recipe")
    if not run.opened:
        raise ValueError("this arm is not open: run load_splits.py first")
    if "schema.json" not in run.files:
        raise ValueError("this pack has no schema.json: it may not fit")
    schema = json.loads(run.files["schema.json"])
    todo = [cli.value(a.recipe)] if a.recipe else cli.value(a.recipes) if a.recipes else None
    if isinstance(todo, dict) and "recipes" in todo:          # --recipes @schema.json: the pack's static list
        todo = todo["recipes"]
    if not todo or not isinstance(todo, list):
        raise ValueError("give --recipe (one) or --recipes (a JSON list, or @schema.json for its recipes)")
    t0 = 0
    if a.range:
        t0, t1 = (int(x) for x in a.range.split(":"))
        todo = todo[t0:t1]
    results = []
    for rec in todo:
        try:
            rec = check(run, rec, schema)
        except ValueError as e:
            results.append({"t": t0 + len(results), "recipe": rec, "error": str(e), "refused": True})
            continue
        try:
            results.append({"t": t0 + len(results), **fit_one(run, rec)})
        except ValueError as e:                      # the budget: every recipe after the 24th is refused
            results.append({"t": t0 + len(results), "recipe": rec, "error": str(e), "refused": True})
        finally:
            run.save()
    run.save()
    s = run.arm_state
    if len(results) == 1:
        return {**results[0], "fits_used": s["fits_used"], "n_fits": s["n_fits"]}
    return {"results": results, "fits_used": s["fits_used"], "n_fits": s["n_fits"], "fits_left": run.left, **({"FREEZE": True} if s["frozen"] else {})}


if __name__ == "__main__":
    cli.main(main)
