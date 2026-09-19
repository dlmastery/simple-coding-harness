"""exam - the held-out problem: the frozen pack's memory arm vs the control arm over several seeds.

    python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4

Reads both arms' scorecards per seed (the agent ran them; both arms were
opened with --freeze-memory so no card landed), counts the wins (a higher
test score, or the same score reached with fewer wasted fits), names every
applicable card that did not transfer (its preferred value is not in the
memory arm's best recipe on most seeds), and checks the pack's checksums
against the ones its first exam boot recorded. Writes runs/<pack>/exam.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory, packs  # noqa: E402
from _lib.state import Run  # noqa: E402
from scorecard import card_for  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, seeds={"default": "0,1,2,3,4", "help": "the seeds, comma-separated"}), arm=False)


def main(argv=None):
    a = PARSER.parse_args(argv)
    seeds = [int(s) for s in a.seeds.split(",") if s.strip()]
    results, missing = [], []
    first_boot = None
    for seed in seeds:
        cards = {}
        for arm in ("memory", "control"):
            run = Run(a.pack, a.task, arm, seed, a.run)
            if not run.opened:
                missing.append(f"{arm}/{seed}")
                continue
            cards[arm] = card_for(run)
            boots = run.trace.rows("boot", arm=arm, seed=seed)
            if boots and first_boot is None:
                first_boot = boots[0]["info"]["checksums"]
        if len(cards) < 2:
            continue
        m, c = cards["memory"], cards["control"]
        gap = None if m["test_score"] is None or c["test_score"] is None else round(m["test_score"] - c["test_score"], 4)
        win = gap is not None and (gap > 0 or (gap == 0 and m["wasted_fits"] < c["wasted_fits"]))
        results.append({"seed": seed, "memory": m, "control": c, "gap_test": gap,
                        "gap_val": None if m["best_val_score"] is None or c["best_val_score"] is None else round(m["best_val_score"] - c["best_val_score"], 4),
                        "win": win})
    run = Run(a.pack, a.task, "memory", seeds[0], a.run)
    cards_now = memory.load(run.memory_path)
    applicable = memory.applicable(cards_now, run.profile)
    best = [r["memory"]["best_recipe"] for r in results]
    did_not_transfer = [c for c in applicable if "prefer" in c["then"]
                        and sum(1 for b in best if b and b[c["then"]["field"]] == c["then"]["prefer"]) <= len(best) // 2]
    now = packs.checksums(run.pack_dir)
    report = {"problem": run.problem, "seeds": seeds, "results": results, "missing": missing,
              "wins": sum(1 for r in results if r["win"]), "wins_on_score": sum(1 for r in results if (r["gap_test"] or 0) > 0),
              "ties": sum(1 for r in results if r["gap_test"] == 0),
              "mean_gap_test": round(sum(r["gap_test"] or 0 for r in results) / len(results), 4) if results else None,
              "cards_applicable": applicable, "did_not_transfer": did_not_transfer,
              "pack_unchanged": first_boot is not None and {k: v for k, v in now.items() if k != "plan.json"} == {k: v for k, v in first_boot.items() if k != "plan.json"},
              "no_card_written": not any(run.trace.rows("card"))}
    out_path = run.root.parent / "exam.json"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    lines = [f"exam {report['problem']}: memory arm beats control on {report['wins']} of {len(results)} seeds "
             f"({report['wins_on_score']} on test score, {report['ties']} same score; a tie won by fewer wasted fits), "
             f"mean test gap {report['mean_gap_test']}; pack unchanged: {report['pack_unchanged']}; no card written: {report['no_card_written']}"]
    for r in results:
        lines.append(f"  seed {r['seed']}: memory test {r['memory']['test_score']} val {r['memory']['best_val_score']} wasted {r['memory']['wasted_fits']} | "
                     f"control test {r['control']['test_score']} val {r['control']['best_val_score']} wasted {r['control']['wasted_fits']} | "
                     f"gap {r['gap_test']} {'win' if r['win'] else 'loss'}")
    for c in did_not_transfer:
        lines.append(f"  did not transfer: {json.dumps(c['if'])} -> {json.dumps(c['then'])} (evidence {c['evidence']}, counter {c['counter']})")
    return {**report, "table": "\n".join(lines), "path": str(out_path)}


if __name__ == "__main__":
    cli.main(main)
