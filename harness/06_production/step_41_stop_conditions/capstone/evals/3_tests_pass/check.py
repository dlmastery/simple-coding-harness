"""Step 38 - check 3: the workspace's own pytest suite passes and collects at least one test."""

import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import fail, ok  # noqa: E402

tests = sorted(p.name for p in Path.cwd().glob("test_*.py")) + sorted(p.name for p in Path.cwd().glob("*_test.py"))
if not tests:
    fail("no test_*.py file in the workspace")

completed = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
    capture_output=True, text=True, timeout=240,
)
output = (completed.stdout + completed.stderr).strip()
lines = output.splitlines()
last = next((line for line in reversed(lines) if re.search(r"\d+ (passed|failed|error)", line)), lines[-1] if lines else "(no output)")
if completed.returncode == 5:
    fail("pytest collected no tests")
if completed.returncode != 0:
    print("\n".join(output.splitlines()[-15:]))
    fail(f"pytest exited {completed.returncode}: {last}")
if " passed" not in last:
    fail(f"pytest reported no passing test: {last}")
ok(f"{', '.join(tests)}: {last}")
