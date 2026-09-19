"""Step 06 - the RSI harness: the actor pack (skills/adult-income) proposes one
recipe at a time shaped by memory.json; the verifier pack turns the log into
cards. Run it on two curriculum problems in a row and compare each with the
MEMORY_OFF arm at the same budget.

    FAKE_MODEL=1 python run.py                       # problems 1 and 2 of the curriculum, both arms
    FAKE_MODEL=1 python run.py breast_cancer wine    # any problems by name, in order
    MEMORY_OFF=1 FAKE_MODEL=1 python run.py          # the off switch: same 24 fits, no cards
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, memory, steps, tasks  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"


def main(names):
    model = harness.choose_model()
    actor, verifier = steps.workspace(HERE, ACTOR, VERIFIER)
    run_dir = HERE / "runs" / "curriculum"
    problems = [tasks.load_task(n) for n in names] or tasks.curriculum()[:2]
    if harness.memory_off_env():
        for task in problems:
            card, _, _ = curriculum.run_problem(actor, task, model, run_dir, arm="control", memory_off=True)
            print(steps.brief(card))
        return
    curve = curriculum.run_curriculum(actor, verifier, problems, model, run_dir)
    curriculum.print_curve(curve)
    cards = memory.load(actor / "memory.json")
    print(f"memory.json after {len(problems)} problems: {len(cards)} cards, {sum(memory.active(c) for c in cards)} active")
    for c in cards:
        if memory.active(c):
            print("  " + json.dumps(c))


if __name__ == "__main__":
    main(sys.argv[1:])
