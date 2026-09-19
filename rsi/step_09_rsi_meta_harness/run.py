"""Step 09 - the RSI meta harness: inner (problem n) -> verifier -> meta ->
inner (problem n+1) across the curriculum, one generation per problem, under
human approval or under the private gate; versions/ and rollback.

    FAKE_MODEL=1 python run.py --approval human   # you answer at every generation (HUMAN=script:y,y,... to script)
    FAKE_MODEL=1 python run.py --approval gate    # the private split decides keep-or-rollback; you only see the log
    META_OFF=1 FAKE_MODEL=1 python run.py         # the off switch: no meta visit, the pack stays byte-identical
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps, tasks  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"
META = {"human": "adult-income-meta", "gate": "adult-income-meta-gate"}


def run_generations(model, approval, problems, run_dir, human=None, meta_off=False, into=None, quiet=True):
    """The curriculum with a meta visit after every problem. Returns (curve, actor dir, versions dir)."""
    actor, verifier, meta = steps.workspace(HERE, ACTOR, VERIFIER, META[approval], into=into)

    def visit(task, i):
        if meta_off:
            return {"pack": None, "patch": None, "changed": False, "off": True}
        return curriculum.meta_visit(meta, actor, task, model, run_dir, human=human, quiet=quiet)

    curve = curriculum.run_curriculum(actor, verifier, problems, model, run_dir, human=human, meta=visit, quiet=quiet)
    return curve, actor, run_dir / "versions"


def main(args):
    approval = args[args.index("--approval") + 1] if "--approval" in args else "human"
    meta_off = os.environ.get("META_OFF", "") in ("1", "true", "yes")
    model = harness.choose_model()
    run_dir = steps.run_dir(HERE, f"curriculum_{approval}")
    problems = tasks.curriculum()
    before = packs.checksums(HERE / "skills" / ACTOR)
    curve, actor, versions = run_generations(model, approval, problems, run_dir, meta_off=meta_off, quiet=False)
    curriculum.print_curve(curve)
    for row in curve:
        m = row["meta"]
        print(f"  after problem {row['index']}: " + ("META_OFF" if m.get("off") else f"{m['pack']} -> {json.dumps(m['patch'])}"))
    gens = sorted(p.name for p in versions.glob("gen_*")) if versions.exists() else []
    print(f"versions: {gens or 'none'}; actor pack byte-identical to skills/: {packs.checksums(actor) == before}")
    boots = [b for b in curriculum.harness.TraceLog(run_dir / "traces.jsonl").rows("boot", arm="memory") if b["info"]["pack"] == ACTOR]
    print("actor boots (checksums of SKILL.md / schema.json / memory.json per generation):")
    for b in boots:
        c = b["info"]["checksums"]
        print(f"  {b['problem']:<16} {c['SKILL.md']} {c['schema.json']} {c['memory.json']}")


if __name__ == "__main__":
    main(sys.argv[1:])
