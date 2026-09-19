"""Step 12 - ModularRSI: two actor packs that differ in one module run a
benchmark-disjoint pool; `contrast` names the module; the meta pack patches it
in the losing pack under the pool's private gate; the patched module is then
checked on the eval table with two fake actors.

    FAKE_MODEL=1 python run.py
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402

A, B, META, VERIFIER = "actor-a", "actor-b", "modular-meta", "adult-income-verifier"
EVAL = "synth_shift_b"


def pool_tasks():
    return tasks.all_tasks(HERE / "pool")


def run_pool(model, work, run_dir, quiet=True):
    """Both actors on every pool task, arms named after the packs, then one meta visit with actor-a as the target."""
    a, b, meta = work
    for task in pool_tasks():
        for pack in (a, b):
            run = harness.boot(pack, task, arm=pack.name, run_dir=run_dir, quiet=quiet)
            harness.run(run, model)
    return curriculum.meta_visit(meta, a, pool_tasks()[-1], model, run_dir, quiet=quiet)


def transfer(pack, task, run_dir, styles=("default", "reverse")):
    """The pack on the eval table with each fake actor style: best val per style."""
    out = {}
    for style in styles:
        run = harness.boot(pack, task, arm=f"eval-{style}", run_dir=run_dir, quiet=True)
        harness.run(run, FakeModel(style))
        out[style] = max((r["val_score"] for r in run.fits if r["val_score"] is not None), default=None)
    return out


def main():
    model = harness.choose_model()
    work = steps.workspace(HERE, A, B, META)
    run_dir = steps.run_dir(HERE, "pool")
    eval_task = tasks.load_task(EVAL)
    before = transfer(work[0], eval_task, steps.run_dir(HERE, "eval_before"))
    visit = run_pool(model, work, run_dir, quiet=False)
    c = harness.TraceLog(run_dir / "traces.jsonl").rows("contrast")[-1]["info"]
    print(f"contrast: module {c['module']}, winner {c['winner']}, wins {json.dumps(c['wins'])}")
    for p in c["pairs"]:
        print(f"  {p['problem']}: success {p['success']} ({p['best'][p['success']]['val']}) vs failure {p['failure']} ({p['best'][p['failure']]['val']})")
    print(f"patch: {json.dumps(visit['patch'])}")
    after = transfer(work[0], eval_task, steps.run_dir(HERE, "eval_after"))
    print(f"actor-a on the eval table {EVAL} before the patch: {json.dumps(before)}; after: {json.dumps(after)}")
    print(f"modules of actor-a now equal to actor-b's: {packs.read_pack(work[0] / 'modules') == packs.read_pack(work[1] / 'modules')}")


if __name__ == "__main__":
    main()
