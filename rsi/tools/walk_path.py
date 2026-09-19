"""walk_path - walk one path of graph.json by id: fit the recipe it binds. An illegal path is skipped and counted.

    python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --path p01
    python ../tools/walk_path.py --pack ... --task ... --paths p01,p02,p03        # several, in order

A path that is not in paths.json is refused: the loop walks the paths it has,
it does not invent one. A path that breaks a graph rule (a missing edge, two
models, reaching score_test) costs its fit and lands in the log as an error.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, graph  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402
from fit_recipe import fit_one  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, path="one path id", paths="path ids, comma-separated, walked in order"))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "walk_path")
    if "graph.json" not in run.files or "paths.json" not in run.files:
        raise ValueError("this pack has no graph.json / paths.json")
    g = json.loads(run.files["graph.json"])
    paths = {p["id"]: p for p in json.loads(run.files["paths.json"])}
    ids = [a.path] if a.path else [p.strip() for p in (a.paths or "").split(",") if p.strip()]
    if not ids:
        raise ValueError("give --path or --paths")
    results = []
    for pid in ids:
        if pid not in paths:
            results.append({"path": pid, "error": f"no path {pid!r} in paths.json; the loop walks the paths it has, it does not invent one", "refused": True})
            continue
        reason = graph.why_illegal(g, paths[pid])
        try:
            if reason:
                results.append({"path": pid, **fit_one(run, graph.path_recipe(paths[pid]) or paths[pid].get("bindings"), error=f"illegal path: {reason}")})
            else:
                results.append({"path": pid, **fit_one(run, graph.path_recipe(paths[pid]))})
        except ValueError as e:
            results.append({"path": pid, "error": str(e), "refused": True})
        finally:
            run.save()
    s = run.arm_state
    if len(results) == 1:
        return {**results[0], "fits_used": s["fits_used"], "n_fits": s["n_fits"]}
    return {"results": results, "fits_used": s["fits_used"], "n_fits": s["n_fits"], "fits_left": run.left, **({"FREEZE": True} if s["frozen"] else {})}


if __name__ == "__main__":
    cli.main(main)
