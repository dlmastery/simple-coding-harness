"""propose - write a proposal (a whole pack, or a patch) for the user to approve. Nothing lands.

    python ../tools/propose.py --pack .claude/skills/loop-writer --task ../tasks/01_adult_income.json \\
        --target .claude/skills/adult-income-loop --kind pack --payload @proposal.json --summary "loop pack for adult_income"
    python ../tools/propose.py --pack ... --task ... --target ... --kind patch --payload @patch.json --summary "..."

A `pack` payload is {path: text}; it is linted against the task first and a
pack that does not lint is refused before the user sees it. A `patch`
payload is {"files": {path: {"after": text}}, "recipe": {...}}. The result
holds the proposal id and the diff: show the diff to the user, ask
"approve / edit / reject", and only then run apply.py with their words.
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, proposals  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, target={"required": True, "help": "the pack directory the proposal is for (created or patched on apply)"},
                               kind={"required": True, "choices": ["pack", "patch"]},
                               payload={"required": True, "help": "the payload: JSON or @file"},
                               summary={"default": "", "help": "one line for the user"}))


def lint_payload(files, task):
    tmp = Path(tempfile.mkdtemp(prefix="lint_"))
    try:
        packs.write_pack(tmp, files)
        return packs.lint_pack(tmp, task)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "propose")
    payload = cli.value(a.payload)
    target = Path(a.target)
    if a.kind == "pack":
        if not isinstance(payload, dict) or not all(isinstance(v, str) for v in payload.values()):
            raise ValueError("a pack payload is {path: text}")
        problems = lint_payload(payload, run.task)
        if problems:
            raise ValueError(f"lint_pack refuses this pack before the user sees it: {problems}")
    else:
        if not isinstance(payload, dict) or "files" not in payload:
            raise ValueError("a patch payload is {files: {path: {after: text}}, recipe: {...}}")
        current = packs.read_pack(target) if target.exists() else {}
        payload["files"] = {n: {"before": current.get(n), "after": c.get("after")} for n, c in payload["files"].items()}
    record, diff = proposals.write(run.root, a.kind, payload, a.summary, target)
    run.log("propose", proposal=record["id"], kind=a.kind, summary=a.summary, files=sorted(payload if a.kind == "pack" else payload["files"]))
    return {"id": record["id"], "kind": a.kind, "target": str(target), "summary": a.summary, "diff": diff,
            "file": str(run.root / "proposals" / f"{record['id']}.json"),
            "next": f"Show the diff to the user. Ask: approve / edit / reject. Then: python ../tools/apply.py --pack {a.pack} "
                    f"--task {a.task} --proposal {record['id']} --approved \"<the user's exact words>\" [--edited @their_version.json]"}


if __name__ == "__main__":
    cli.main(main)
