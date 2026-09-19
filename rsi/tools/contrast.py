"""contrast - ModularRSI: pair a success and a failure of two actor packs on every pool task both ran, and name
the one module file whose text differs between them.

    python ../tools/contrast.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json \\
        --a .claude/skills/actor-a --b .claude/skills/actor-b --tasks pool

For each task under --tasks (or the one --task) that both actors ran on the
memory arm: the actor with the higher best val is the success, the other the
failure. `modules_differing` lists the modules/*.md files whose text differs
between the two packs; `module` is the one file when exactly one differs
(the bug is localised), else null. `winner` is the actor with more
successes, or null at a tie. Zero fits.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, tasks  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, a={"required": True, "help": "the first actor pack"}, b={"required": True, "help": "the second actor pack"},
                               tasks="a directory of pool task files (default: only --task)"))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "contrast")
    pa, pb = packs.read_pack(a.a), packs.read_pack(a.b)
    if not pa or not pb:
        raise ValueError("both actor packs must exist")
    na, nb = Path(a.a).name, Path(a.b).name
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
    task_paths = sorted(Path(a.tasks).glob("*.json")) if a.tasks else [Path(a.task)]
    pairs = []
    for tp in task_paths:
        best = {}
        for name, pack in ((na, a.a), (nb, a.b)):
            r = Run(pack, tp, "memory", a.seed, a.run)
            rows = [x for x in r.fit_rows() if x["val_score"] is not None]
            top = max(rows, key=lambda x: x["val_score"]) if rows else None
            best[name] = {"val": top["val_score"] if top else None, "recipe": top["recipe"] if top else None, "fits": len(r.fit_rows())}
        if best[na]["val"] is None or best[nb]["val"] is None:
            pairs.append({"problem": tasks.load_task(tp)["name"], "skipped": "an actor has no memory-arm fits here", "best": best})
            continue
        if best[na]["val"] == best[nb]["val"]:
            pairs.append({"problem": tasks.load_task(tp)["name"], "skipped": "tie", "best": best})
            continue
        success, failure = (na, nb) if best[na]["val"] > best[nb]["val"] else (nb, na)
        pairs.append({"problem": tasks.load_task(tp)["name"], "success": success, "failure": failure, "best": best})
    decided = [p for p in pairs if "success" in p]
    wins = {na: sum(1 for p in decided if p["success"] == na), nb: sum(1 for p in decided if p["success"] == nb)}
    winner = max((na, nb), key=lambda n: wins[n]) if decided and wins[na] != wins[nb] else None
    module = differing[0] if len(differing) == 1 else None
    result = {"pairs": pairs, "modules_differing": differing, "module": module, "winner": winner, "wins": wins,
              "texts": {na: pa.get(module), nb: pb.get(module)} if module else {}, "fits_spent": 0}
    run.log("contrast", module=module, winner=winner, wins=wins, differing=differing)
    return result


if __name__ == "__main__":
    cli.main(main)
