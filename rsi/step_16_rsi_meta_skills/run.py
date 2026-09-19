"""Step 16 - MetaSkill-Evolve: two timescales on one frozen model. The task
skills (the actor's cards and policy line) evolve after every problem under
the private gate; the meta-skills (the meta pack's own five role files) evolve
every k problems by the same pipeline, and only with the human's y.

    FAKE_MODEL=1 HUMAN=script:y,y python run.py       # k = 3: two slow-clock visits over six problems
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps, tasks  # noqa: E402

ACTOR, VERIFIER, META, EVOLVER = "adult-income", "adult-income-verifier", "task-skills-meta", "meta-evolver"
K = 3   # the slow clock: meta-skills may change every k problems


def run_two_clocks(model, problems, run_dir, human=None, into=None, k=K, quiet=True):
    """The curriculum: a fast visit (task skills, gate) after every problem; a slow visit (meta-skills, human)
    every k problems. The slow loop's log and versions live under run_dir/meta."""
    actor, verifier, meta, evolver = steps.workspace(HERE, ACTOR, VERIFIER, META, EVOLVER, into=into)
    slow_dir = run_dir / "meta"
    slow_dir.mkdir(parents=True, exist_ok=True)

    def visit(task, i):
        fast = curriculum.meta_visit(meta, actor, task, model, run_dir, human=human, quiet=quiet)
        slow = None
        if i % k == 0:
            # the slow loop reads the same log: the fast run_dir's trace is copied as its evidence
            (slow_dir / "traces.jsonl").write_text((run_dir / "traces.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
            slow = curriculum.meta_visit(evolver, meta, task, model, slow_dir, human=human, quiet=quiet)
        return {"fast": fast, "slow": slow}

    curve = curriculum.run_curriculum(actor, verifier, problems, model, run_dir, human=human, meta=visit, quiet=quiet)
    return curve, actor, meta, run_dir


def main():
    model = harness.choose_model()
    run_dir = steps.run_dir(HERE, "curriculum")
    curve, actor, meta, _ = run_two_clocks(model, tasks.curriculum(), run_dir, quiet=False)
    curriculum.print_curve(curve)
    for row in curve:
        fast, slow = row["meta"]["fast"], row["meta"]["slow"]
        print(f"  after problem {row['index']}: task skills {'changed' if fast['changed'] else 'unchanged'} "
              f"({json.dumps((fast['patch'] or {}).get('files'))}); "
              + ("meta-skills: not this clock" if slow is None else f"meta-skills {'changed' if slow['changed'] else 'unchanged'} ({json.dumps(slow['patch'])})"))
    slow_versions = sorted(p.name for p in (run_dir / "meta" / "versions").glob("gen_*")) if (run_dir / "meta" / "versions").exists() else []
    print(f"meta pack versions: {slow_versions}")
    for v in slow_versions:
        before = packs.read_pack(run_dir / "meta" / "versions" / v)
        for name in sorted(n for n in before if n.startswith("roles/") and before[n] != packs.read_pack(meta).get(n)):
            print(f"  {v}/{name} -> now: " + packs.diff({name: before[name]}, {name: packs.read_pack(meta)[name]}).replace("\n", " | "))
    for name in ("roles/allocator.md", "roles/proposer.md"):
        print(f"{name}: " + " / ".join(l for l in (meta / name).read_text(encoding="utf-8").splitlines() if ":" in l and l[0].isupper()))


if __name__ == "__main__":
    main()
