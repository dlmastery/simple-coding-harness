"""write_loop_log - append audit lines to loop_log.jsonl. Nothing reads it back: there is no tool that does.

    python ../tools/write_loop_log.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json \
        --entry '{"t": 1, "val_score": 0.9}'
    python ../tools/write_loop_log.py --pack ... --task ... --entries '[{"t": 0, "val_score": 0.91}, {"t": 1, "val_score": 0.9}]'
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, entry="one audit entry: JSON, k=v pairs, or @file", entries="a JSON list of entries (or @file)"))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "write_loop_log")
    entries = [cli.value(a.entry)] if a.entry else cli.value(a.entries) if a.entries else None
    if not entries or not all(isinstance(e, dict) for e in entries):
        raise ValueError("an entry is a JSON object (--entry), or --entries a JSON list of them")
    path = run.root / "loop_log.jsonl"
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for entry in entries:
            f.write(json.dumps({"problem": run.problem, "arm": run.arm, **entry}) + "\n")
    return {"logged": len(entries), "path": str(path)}


if __name__ == "__main__":
    cli.main(main)
