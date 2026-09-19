"""Step 08 - a meta skill generates the RSI harness (actor + verifier), under
human approval; then the generated packs run two curriculum problems.

    FAKE_MODEL=1 python run.py                    # the fake writer; you answer at the prompt
    FAKE_MODEL=1 HUMAN=script:y python run.py     # a scripted yes
    python run.py                                 # the real model: BASE_URL / API_KEY / MODEL
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps, tasks  # noqa: E402

WRITER = "rsi-writer"
PROBLEMS = ("breast_cancer", "synth_shift_b")


def step03():
    spec = importlib.util.spec_from_file_location("step03_run", HERE.parent / "step_03_meta_generates_loop" / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_rsi(model, out_dir, human=None, quiet=False):
    """The writer's target is a directory holding both packs: actor/ and verifier/."""
    return step03().generate(model, out_dir, human=human, quiet=quiet, writer=WRITER, step=HERE)


def main():
    model = harness.choose_model()
    out = steps.run_dir(HERE, "generated") / "rsi"
    run = generate_rsi(model, out)
    print(run.messages[-1]["content"])
    if not out.exists():
        print("nothing landed; the generated packs were not approved")
        return
    task = steps.step_task(HERE / "skills" / WRITER)
    print(f"lint of the landed packs: {packs.lint_pack(out, task) or 'ok'}")
    curve = curriculum.run_curriculum(out / "actor", out / "verifier", [tasks.load_task(n) for n in PROBLEMS], model, HERE / "runs" / "generated")
    curriculum.print_curve(curve)


if __name__ == "__main__":
    main()
