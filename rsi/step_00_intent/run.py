"""Step 00 - the intent: validate task.json against common/task.schema.json,
check that acceptance.md names exactly the scorecard fields, and show that
lint_pack refuses a pack that widens the intent.

    python run.py
"""

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import packs, tasks  # noqa: E402
from common.scorecard import SCORECARD_FIELDS  # noqa: E402

FIELD_LINE = re.compile(r"^- ([a-z_]+)$", re.M)


def acceptance_fields(path=HERE / "acceptance.md"):
    """The `- field` bullets under `## The scorecard`: the contract every later scorecard meets."""
    text = path.read_text(encoding="utf-8")
    section = text.split("## The scorecard")[1].split("## ")[0]
    return tuple(FIELD_LINE.findall(section))


def widened(pack_dir, **changes):
    """A copy of a pack with schema.json fields changed: what a pack that tries to widen the intent looks like."""
    tmp = Path(tempfile.mkdtemp(prefix="widen_"))
    shutil.copytree(pack_dir, tmp / "pack")
    schema_path = tmp / "pack" / "schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema.update(changes)
    with open(schema_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(schema, f, indent=1)
    return tmp / "pack"


def main():
    task = tasks.load_task(HERE / "task.json")
    print(f"task.json valid: {task['name']} - {task['title']}; metric {task['metric']}; budget {task['budget']['n_fits']} fits per arm")
    fields = acceptance_fields()
    print(f"acceptance.md names {len(fields)} scorecard fields; matches common/scorecard.py: {fields == SCORECARD_FIELDS}")
    regular = HERE.parent / "step_01_regular_harness" / "skills" / "adult-income-regular"
    if regular.exists():
        print(f"lint_pack on step 01's pack: {packs.lint_pack(regular, task) or 'ok'}")
        print(f"lint_pack on a pack with n_fits 48: {packs.lint_pack(widened(regular, n_fits=48), task)}")
        print(f"lint_pack on a pack with two test scores: {packs.lint_pack(widened(regular, test_rule={'scores': 2, 'after': 'FREEZE'}), task)}")


if __name__ == "__main__":
    main()
