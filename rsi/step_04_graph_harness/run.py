"""Step 04 - the graph harness: boot skills/adult-income-graph on Adult; the
model walks the 24 paths of paths.json through graph.json.

    FAKE_MODEL=1 python run.py      # the scripted fake, no key
    python run.py                   # the real model: BASE_URL / API_KEY / MODEL
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps  # noqa: E402

PACK = "adult-income-graph"


def main():
    task = steps.step_task(HERE)
    pack = steps.workspace(HERE, PACK)
    before = packs.checksums(pack)
    run = harness.boot(pack, task, run_dir=HERE / "runs" / PACK, arm="control")
    harness.run(run, harness.choose_model())
    print(run.messages[-1]["content"])
    print(steps.brief(curriculum.scorecard_for(run, [], [])))
    illegal = [r for r in run.fits if r["error"] and r["error"].startswith("illegal path")]
    print(f"paths walked {len(run.fits)}, illegal (skipped and counted) {len(illegal)}; "
          f"graph.json and paths.json byte-identical after the run: {packs.checksums(pack) == before}")


if __name__ == "__main__":
    main()
