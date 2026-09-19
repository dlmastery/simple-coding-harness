"""validate_intent - lesson 00: task.json against the task schema, acceptance.md against the scorecard fields.

    python ../tools/validate_intent.py --task task.json --acceptance acceptance.md

The intent is the one file every later pack, writer and verifier reads and
none may widen: the budget (at most 24 fits), the locked-test rule (scored
once, after FREEZE), the metric, the allowed models, the profile keys. The
acceptance page must name every scorecard field, so what counts as success
is written before any pack exists.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, tasks  # noqa: E402
from _lib.scorecard import SCORECARD_FIELDS  # noqa: E402

PARSER = cli.parser(__doc__, task={"required": True, "help": "the task.json"}, acceptance="the acceptance.md")


def main(argv=None):
    a = PARSER.parse_args(argv)
    problems = []
    try:
        task = tasks.load_task(a.task)
    except Exception as e:
        return {"ok": False, "problems": [f"task.json: {str(e).splitlines()[0]}"]}
    missing = []
    if a.acceptance:
        text = Path(a.acceptance).read_text(encoding="utf-8")
        missing = [f for f in SCORECARD_FIELDS if f"`{f}`" not in text and not re.search(rf"^- {f}$", text, re.M)]
        if missing:
            problems.append(f"acceptance.md lacks the scorecard fields {missing}")
        if "once" not in text or "FREEZE" not in text:
            problems.append("acceptance.md must state the locked-test rule: scored once, after FREEZE")
    return {"ok": not problems, "problems": problems, "task": task["name"], "index": task["index"], "role": task["role"],
            "title": task["title"], "budget": task["budget"], "metric": task["metric"],
            "test_rule": task["test_rule"], "allowed_models": task["allowed_models"], "profile_keys": task["profile_keys"],
            "scorecard_fields": list(SCORECARD_FIELDS)}


if __name__ == "__main__":
    cli.main(main)
