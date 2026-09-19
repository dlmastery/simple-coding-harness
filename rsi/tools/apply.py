"""apply - land a proposal the user approved, with their exact words. Refused without them.

    python ../tools/apply.py --pack .claude/skills/loop-writer --task ../tasks/01_adult_income.json \\
        --proposal p1 --approved "yes, looks good"
    python ../tools/apply.py --pack ... --task ... --proposal p1 --approved "edit" --edited @their_version.json
    python ../tools/apply.py --pack ... --task ... --proposal p1 --approved "no"       # records the rejection; nothing lands

The first word decides: y / yes / approve / ok lands the proposal; edit lands
the user's version from --edited (an edited pack is linted again first);
n / no / reject, or anything unclear, records a rejection and lands nothing.
The trace records who approved (the human) and the words. A proposal is
applied at most once. The lesson's hook blocks apply.py without --approved
before it runs; the script refuses it again on its own.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, proposals  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402
from propose import lint_payload  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, proposal={"required": True, "help": "the proposal id from propose.py"},
                               approved={"default": None, "help": "the user's exact words"},
                               edited={"default": None, "help": "the user's version of the payload (JSON or @file), with --approved edit"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "apply")
    if a.approved is None or not a.approved.strip():
        raise ValueError('apply needs --approved "<the user\'s exact words>": ask them first; nothing lands without an answer')
    path, record = proposals.load(run.root, a.proposal)
    if record["applied"]:
        raise ValueError(f"proposal {a.proposal} was applied already")
    if record["decision"] == "n":
        raise ValueError(f"proposal {a.proposal} was rejected already; propose again if you have something new")
    decision = proposals.classify(a.approved)
    record["decision"], record["words"], record["approved_by"] = decision, a.approved, "human"
    target = Path(record["target"])
    if decision == "n":
        proposals.save(path, record)
        run.log("reject", proposal=a.proposal, words=a.approved, by="human")
        return {"id": a.proposal, "decision": "n", "landed": False, "words": a.approved}
    payload = record["payload"]
    if decision == "edit":
        if a.edited is None:
            raise ValueError("--approved edit needs --edited <the user's version>; nothing lands")
        payload = cli.value(a.edited)
        if record["kind"] == "pack":
            problems = lint_payload(payload, run.task)
            if problems:
                raise ValueError(f"the edited pack does not lint: {problems}; nothing lands")
        else:
            current = packs.read_pack(target) if target.exists() else {}
            payload["files"] = {n: {"before": current.get(n), "after": c.get("after")} for n, c in payload["files"].items()}
        record["payload"] = payload         # the user's version is what lands
    if record["kind"] == "pack":
        checksums = proposals.land_pack(target, payload)
        version = None
    else:
        version = proposals.land_patch(target, run.versions_dir, payload)
        checksums = packs.checksums(target)
    record["applied"] = True
    proposals.save(path, record)
    run.log("apply", proposal=a.proposal, decision=decision, words=a.approved, by="human", version=version, checksums=checksums)
    return {"id": a.proposal, "decision": decision, "landed": True, "target": str(target), "version": version,
            "files": sorted(payload if record["kind"] == "pack" else payload["files"]), "approved_by": "human", "words": a.approved}


if __name__ == "__main__":
    cli.main(main)
