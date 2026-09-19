"""Step 13 - Recuris: memory as a skill package. The actor names its situation
in working.md and gets the cards that fit it; after each problem the meta
agent turns the evidence into one localised, validated card update. Gains
are reported by horizon: the gap per number of problems seen.

    FAKE_MODEL=1 python run.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, steps, tasks  # noqa: E402
from common.tools import skill_cards  # noqa: E402

ACTOR, META = "adult-income-skills", "skill-memory-meta"


def skills_problem(model, actor, meta, task, run_dir, *, bar=None, seed=0, quiet=True):
    """One problem: the actor (working memory + selected cards), then one meta visit that may update one card."""
    card, run, _ = curriculum.run_problem(actor, task, model, run_dir, seed=seed, arm="memory", bar=bar, quiet=quiet)
    visit = curriculum.meta_visit(meta, actor, task, model, run_dir, seed=seed, quiet=quiet)
    card = dict(card, skill_cards=len(skill_cards(actor)), horizon=max((c.get("horizon", 0) for c in skill_cards(actor)), default=0),
                update=visit["changed"])
    return card, run


def main(problems=None):
    model = harness.choose_model()
    actor, meta = steps.workspace(HERE, ACTOR, META)
    run_dir = steps.run_dir(HERE, "curriculum")
    problems = problems or tasks.curriculum()
    curve = curriculum.run_curriculum(actor, None, problems, model, run_dir,
                                      memory_arm=lambda task, bar: skills_problem(model, actor, meta, task, run_dir, bar=bar))
    curriculum.print_curve(curve)
    print("gain by horizon (problems seen so far -> val gap, cards in the package, highest card horizon, working memory):")
    trace = harness.TraceLog(run_dir / "traces.jsonl")
    for row in curve:
        w = trace.rows("working", problem=row["problem"])[-1]["info"]
        m = row["memory"]
        print(f"  horizon {row['index']}: gap {row['gap_val']:+.4f}, cards {m['skill_cards']}, max horizon {m['horizon']}, "
              f"need {w['need']}, applied {w['cards']}, updated this problem: {m['update']}")
    return curve


if __name__ == "__main__":
    main()
