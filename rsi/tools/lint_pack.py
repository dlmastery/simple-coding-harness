"""lint_pack - every reason a pack (on disk, or a proposed {path: text}) may not run for a task.

    python ../tools/lint_pack.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
    python ../tools/lint_pack.py --files @proposal.json --task ../tasks/01_adult_income.json

Checks: SKILL.md front matter (name, description, metadata type / version /
rsi), tools.md with an Allowed section, schema.json's budget / test rule /
metric / models against the task (a pack may not widen the task), every
recipe in the schema, loop.json (counted_while, N = budget, errors count,
exit FREEZE -> score_test), graph.json + paths.json (no cycle, one scale /
encode / model per path, score_test a freeze-only sink, every path legal),
a verifier pack's contract line and memory.schema.json, an AIDE pack's guard
line in every operator. `{"ok": true}` or `{"ok": false, "problems": [...]}`.
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, tasks  # noqa: E402

PARSER = cli.parser(__doc__, pack="a pack directory (or a directory of packs)", files="a proposed pack as {path: text} (JSON or @file)",
                    task={"required": True, "help": "the task.json the pack is for"})


def main(argv=None):
    a = PARSER.parse_args(argv)
    task = tasks.load_task(a.task)
    if a.files:
        files = cli.value(a.files)
        if not isinstance(files, dict) or not all(isinstance(v, str) for v in files.values()):
            raise ValueError("--files is {path: text}")
        tmp = Path(tempfile.mkdtemp(prefix="lint_"))
        try:
            packs.write_pack(tmp, files)
            problems = packs.lint_pack(tmp, task)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        what = "proposal"
    elif a.pack:
        problems = packs.lint_pack(a.pack, task)
        what = str(a.pack)
    else:
        raise ValueError("give --pack or --files")
    return {"ok": not problems, "problems": problems, "pack": what, "task": task["name"]}


if __name__ == "__main__":
    cli.main(main)
