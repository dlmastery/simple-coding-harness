"""Step 01 - the regular harness: boot skills/adult-income-regular on Adult and
let the model walk the 24-recipe list. Same text every run, same waste.

    FAKE_MODEL=1 python run.py      # the scripted fake, no key
    python run.py                   # the real model: BASE_URL / API_KEY / MODEL
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, steps  # noqa: E402

PACK = "adult-income-regular"


def main():
    task = steps.step_task(HERE)
    pack = steps.workspace(HERE, PACK)
    run = harness.boot(pack, task, run_dir=HERE / "runs" / PACK, arm="control")
    harness.run(run, harness.choose_model())
    print(run.messages[-1]["content"])
    card = curriculum.scorecard_for(run, [], [])
    print(steps.brief(card))
    print(f"model calls {run.calls}; trace {run.trace.path}")


if __name__ == "__main__":
    main()
