"""Run every step's offline test suite. No API key needed.

    python run_tests.py            # all steps
    python run_tests.py 13 14      # just these (2 selects every 2.x stage)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
steps = sorted(ROOT.glob("step_*/"))
wanted = {int(a) for a in sys.argv[1:]} or None

failed = []
for step in steps:
    number = int(step.name.split("_")[1])
    if wanted and number not in wanted:
        continue
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_step.py"],
        cwd=step, capture_output=True, text=True,
    )
    verdict = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr.strip()[-200:]
    print(f"{step.name:<36} {verdict}")
    if result.returncode:
        failed.append(step.name)
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-40:])
        print("\n".join("    " + line for line in tail.splitlines()))

sys.exit(1 if failed else 0)
