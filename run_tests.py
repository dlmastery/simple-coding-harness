"""Run every step's offline test suite. No API key needed.

    python run_tests.py            # all steps, root and genui/
    python run_tests.py 13 14      # just these root steps (2 selects every 2.x stage)
    python run_tests.py genui/02   # every step under genui/02_*
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
numbers = {int(a) for a in sys.argv[1:] if a.isdigit()}
prefixes = [a.rstrip("/") for a in sys.argv[1:] if not a.isdigit()]

steps = []
for step in sorted(ROOT.glob("step_*/")):
    if prefixes and not numbers:
        continue
    if numbers and int(step.name.split("_")[1]) not in numbers:
        continue
    steps.append(step)
for step in sorted(ROOT.glob("genui/*/step_*/")):
    rel = step.relative_to(ROOT).as_posix()
    if numbers and not prefixes:
        continue
    if prefixes and not any(rel.startswith(p) for p in prefixes):
        continue
    steps.append(step)

failed = []
for step in steps:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_step.py"],
        cwd=step, capture_output=True, text=True,
    )
    verdict = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr.strip()[-200:]
    label = step.relative_to(ROOT).as_posix()
    print(f"{label:<44} {verdict}")
    if result.returncode:
        failed.append(label)
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-40:])
        print("\n".join("    " + line for line in tail.splitlines()))

sys.exit(1 if failed else 0)
