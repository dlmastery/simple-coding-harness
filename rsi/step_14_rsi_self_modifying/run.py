"""Step 14 - the Darwin Goedel Machine lineage: after every problem the current
variant runs a fixed held-out benchmark, the meta pack archives it with that
score, chooses the parent from the archive, and proposes a rewrite of the
actor's SKILL.md and loop.json from the parent, behind the private gate and
the human.

    FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps, tasks  # noqa: E402
from common.tools import archive_index  # noqa: E402

ACTOR, VERIFIER, META = "adult-income", "adult-income-verifier", "dgm-meta"


def held_out():
    return tasks.all_tasks(HERE / "skills" / META / "held-out")


def run_generations(model, problems, run_dir, human=None, into=None, quiet=True):
    """Lesson 09's sequence, plus: before each meta visit the current variant runs the held-out benchmark under an
    arm named for the generation, and the control arm runs it once, so the archive can score the variant."""
    actor, verifier, meta = steps.workspace(HERE, ACTOR, VERIFIER, META, into=into)
    for task in held_out():
        curriculum.run_problem(actor, task, model, run_dir, arm="control", memory_off=True, quiet=quiet)

    def visit(task, i):
        arm = f"heldout-{i}"
        for bench in held_out():
            curriculum.run_problem(actor, bench, model, run_dir, arm=arm, quiet=quiet)
        return curriculum.meta_visit(meta, actor, task, model, run_dir, human=human, quiet=quiet, user=f"Begin. Follow the procedure in your instructions.\nHeld-out arm: {arm}")

    curve = curriculum.run_curriculum(actor, verifier, problems, model, run_dir, human=human, meta=visit, quiet=quiet)
    return curve, actor, run_dir


def main():
    model = harness.choose_model()
    run_dir = steps.run_dir(HERE, "curriculum")
    curve, actor, _ = run_generations(model, tasks.curriculum(), run_dir, quiet=False)
    curriculum.print_curve(curve)
    meta_run = harness.boot(HERE / "skills" / META, tasks.curriculum()[0], run_dir=run_dir, target=actor, arm="meta", quiet=True)
    print("archive (variant, problem it ran, held-out gain over the static walk on the fixed benchmark):")
    for e in archive_index(meta_run):
        print(f"  {e['label']:<34} {e['problem']:<16} {e['held_out']:+.4f}")
    for row in curve:
        print(f"  after problem {row['index']}: {json.dumps(row['meta']['patch'])}")
    versions = sorted(p.name for p in (run_dir / "versions").glob("gen_*"))
    patched = sorted({f for a in harness.TraceLog(run_dir / "traces.jsonl").rows("apply") for f in a["info"]["files"]})
    variants = [packs.read_pack(run_dir / "archive" / e["label"]) for e in archive_index(meta_run)]
    differing = sorted({n for v in variants for n in v if n != "CHECKSUMS.json" and v[n] != variants[0].get(n)})
    print(f"versions {versions}; files the meta pack ever rewrote: {patched}; files that differ across the archive: {differing}")
    print("policy line now: " + next(l.strip() for l in (actor / "SKILL.md").read_text(encoding="utf-8").splitlines() if l.strip().startswith("Search policy:")))


if __name__ == "__main__":
    main()
