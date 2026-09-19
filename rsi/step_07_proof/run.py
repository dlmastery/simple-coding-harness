"""Step 07 - the proof: the learning curve over problems 1..6 and the exam on
problem 7, memory arm vs MEMORY_OFF arm at the same budget.

    FAKE_MODEL=1 python run.py --curriculum    # problems 1..6 in order, the pack carried forward
    FAKE_MODEL=1 python run.py --exam          # the frozen pack on problem 7, five seeds
    FAKE_MODEL=1 python run.py                 # both
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, memory, steps, tasks  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"


def main(args):
    model = harness.choose_model()
    do_curve = "--curriculum" in args or "--exam" not in args
    do_exam = "--exam" in args or "--curriculum" not in args
    work = HERE / "runs" / "work"
    if do_curve or not (work / ACTOR).exists():
        actor, verifier = steps.workspace(HERE, ACTOR, VERIFIER)
        run_dir = steps.run_dir(HERE, "curriculum")
        curve = curriculum.run_curriculum(actor, verifier, tasks.curriculum(), model, run_dir)
        print("learning curve (memory arm - MEMORY_OFF arm, same budget, same seed):")
        curriculum.print_curve(curve)
        cards = memory.load(actor / "memory.json")
        print(f"cards after problem 6: {len(cards)}, active {sum(memory.active(c) for c in cards)}")
    if do_exam:
        actor = work / ACTOR
        report = curriculum.run_exam(actor, tasks.exam(), model, steps.run_dir(HERE, "exam"))
        curriculum.print_exam(report)


if __name__ == "__main__":
    main(sys.argv[1:])
