"""Step 02 - the loop harness: boot skills/adult-income-loop on Adult; the model
runs loop.json over recipes.json and writes an audit log nothing reads back.

    FAKE_MODEL=1 python run.py      # the scripted fake, no key
    python run.py                   # the real model: BASE_URL / API_KEY / MODEL
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps  # noqa: E402

PACK = "adult-income-loop"


def main():
    task = steps.step_task(HERE)
    pack = steps.workspace(HERE, PACK)
    before = packs.checksums(pack)
    run = harness.boot(pack, task, run_dir=HERE / "runs" / PACK, arm="control")
    harness.run(run, harness.choose_model())
    print(run.messages[-1]["content"])
    print(steps.brief(curriculum.scorecard_for(run, [], [])))
    lines = (run.run_dir / "loop_log.jsonl").read_text(encoding="utf-8").splitlines()
    print(f"loop_log.jsonl: {len(lines)} lines, read back by: nobody; pack byte-identical after the run: {packs.checksums(pack) == before}")


if __name__ == "__main__":
    main()
