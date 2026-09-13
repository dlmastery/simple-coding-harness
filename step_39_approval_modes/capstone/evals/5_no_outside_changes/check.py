"""Step 38 - check 5: the manifest of the workspace's parent directory is the same before and after the run.

run.py writes the manifest and passes its path in CAPSTONE_MANIFEST. A
check that cannot compare fails: silence is not proof that nothing changed.
"""

import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import fail, ok  # noqa: E402

path = os.environ.get("CAPSTONE_MANIFEST", "")
if not path or not Path(path).exists():
    fail("CAPSTONE_MANIFEST is not set or does not exist: nothing to compare")

manifest = json.loads(Path(path).read_text(encoding="utf-8"))
before, after = manifest.get("before"), manifest.get("after")
if not isinstance(before, dict) or not isinstance(after, dict):
    fail("the manifest needs a before and an after map of path to hash")

added = sorted(set(after) - set(before))
removed = sorted(set(before) - set(after))
changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
if added or removed or changed:
    for label, paths in (("added", added), ("removed", removed), ("changed", changed)):
        for p in paths:
            print(f"  {label}: {p}")
    fail(f"{len(added)} added, {len(removed)} removed, {len(changed)} changed outside the workspace")
ok(f"{len(before)} files outside the workspace, none changed")
