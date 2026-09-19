"""scorecard - the numbers a claim is made of, for one arm of one pack on one task; the fields of acceptance.md.

    python ../tools/scorecard.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
    python ../tools/scorecard.py --pack ... --task ... --arm control

Read from state.json and traces.jsonl, never from the agent's story: fits
used, wasted fits (fits before the first recipe within 0.005 of the control
arm's best on the same problem and seed, plus every fit that errored), best
val, the one test score, whether the test was touched before FREEZE, and the
cards this problem added / demoted / left active. Written to
runs/<pack>/<task>/scorecard_<arm>_<seed>.json.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory, scorecard  # noqa: E402
from _lib.state import Run  # noqa: E402

PARSER = cli.common(cli.parser(__doc__))


def card_for(run):
    s = run.arm_state
    fits = s["fits"]
    best_val, best_recipe = scorecard.best_of(fits)
    control = run.all_state["arms"].get(f"control/{run.seed}")
    bar = scorecard.best_of(control["fits"])[0] if control and control is not s else None
    test_rows = run.trace.rows("score_test", problem=run.problem, arm=run.arm, seed=run.seed)
    card_rows = [r for r in run.trace.rows("card", problem=run.problem, seed=run.seed) if r["arm"] == run.arm]
    cards = [] if run.memory_off else memory.load(run.memory_path)
    return scorecard.make_scorecard(
        problem=run.problem, arm=run.arm, seed=run.seed, n_fits=s["n_fits"], fits_used=s["fits_used"],
        wasted_fits=scorecard.wasted_fits(fits, bar), best_val_score=best_val, best_recipe=best_recipe,
        test_score=s["test_score"], test_scored_once=len(test_rows) == 1 and s["test_scored"],
        test_touched_before_freeze=any(not (r["info"] or {}).get("frozen") for r in test_rows),
        cards_active=sum(1 for c in cards if memory.active(c)),
        cards_added=sum(1 for r in card_rows if (r["info"] or {}).get("added")),
        cards_demoted=sum(1 for r in card_rows if (r["info"] or {}).get("demoted")),
    )


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    card = card_for(run)
    path = run.root / f"scorecard_{run.arm}_{run.seed}.json"
    scorecard.write_scorecard(path, card)
    return {**card, "path": str(path)}


if __name__ == "__main__":
    cli.main(main)
