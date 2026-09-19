"""Step 03 - a meta skill generates the loop harness, under human approval:
boot skills/loop-writer, watch the proposal, answer y / n / edit, then run
the generated pack on Adult.

    FAKE_MODEL=1 python run.py                    # the fake writer; you answer at the prompt
    FAKE_MODEL=1 HUMAN=script:y python run.py     # a scripted yes
    python run.py                                 # the real model: BASE_URL / API_KEY / MODEL
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps  # noqa: E402

WRITER = "loop-writer"


def generate(model, out_dir, human=None, quiet=False, writer=WRITER, step=HERE):
    """Boot the writer on its own task.json with `out_dir` as the target; returns the writer's run."""
    task = steps.step_task(step / "skills" / writer)
    pack = steps.workspace(step, writer, into=Path(out_dir).parent / "work")
    run = harness.boot(pack, task, run_dir=Path(out_dir).parent / "writer", target=out_dir, human=human, quiet=quiet)
    harness.run(run, model)
    return run


def main(writer=WRITER, step=HERE, generated="adult-income-loop"):
    model = harness.choose_model()
    out = steps.run_dir(step, "generated") / generated
    run = generate(model, out, writer=writer, step=step)
    print(run.messages[-1]["content"])
    if not out.exists():
        print("nothing landed; the generated pack was not approved")
        return
    task = steps.step_task(step / "skills" / writer)
    print(f"lint of the landed pack: {packs.lint_pack(out, task) or 'ok'}")
    before = packs.checksums(out)
    inner = harness.boot(out, task, run_dir=step / "runs" / "generated", arm="control")
    harness.run(inner, model)
    print(steps.brief(curriculum.scorecard_for(inner, [], [])))
    print(f"generated pack byte-identical after its run: {packs.checksums(out) == before}")


if __name__ == "__main__":
    main()
