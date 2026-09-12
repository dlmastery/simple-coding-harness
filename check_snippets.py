"""Verify that every Python snippet quoted in a step README exists in that step's code.

Convention: a ```python block belongs to the last backticked path named above
it in the README, such as `agent.py` or `harness/tools.py`.
Every non-blank snippet line (except elisions starting with `...` or `# ...`)
must appear, whitespace-normalised, in that file. Illustrative pseudo-code
goes in ```text blocks, which are not checked.

    python check_snippets.py            # all steps
    python check_snippets.py 14 16      # a subset
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PATH_RE = re.compile(r"`([\w./-]+\.(?:py|js|toml|md|yml))`")


def snippets(readme):
    """Yield (path, block_lines, block_start_line) for each python fence."""
    lines = readme.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "```python":
            # the file a snippet belongs to is the last `path` named above it
            paths = [m for l in lines[:i] for m in PATH_RE.findall(l)]
            j = i + 1
            block = []
            while j < len(lines) and lines[j].strip() != "```":
                block.append(lines[j])
                j += 1
            yield (paths[-1] if paths else None, block, i + 1)
            i = j
        i += 1


def normalise(text):
    return " ".join(text.split())


def check_step(step):
    readme = step / "README.md"
    if not readme.exists():
        return []
    problems = []
    for path, block, line in snippets(readme):
        if path is None:
            problems.append(f"{readme}:{line}: python block has no `file.py` reference above it")
            continue
        candidates = [step / path, step / "harness" / path, step / "plugin" / "simple-harness-plugin" / path]
        source = next((c for c in candidates if c.exists()), None)
        if source is None:
            problems.append(f"{readme}:{line}: referenced file {path} not found in {step.name}")
            continue
        body = normalise(source.read_text(encoding="utf-8"))
        for offset, snippet_line in enumerate(block, 1):
            s = snippet_line.strip()
            if not s or s.startswith("...") or s.startswith("# ..."):
                continue
            if normalise(s) not in body:
                problems.append(f"{readme}:{line + offset}: not in {path}: {s[:80]}")
    return problems


def main():
    wanted = {int(a) for a in sys.argv[1:]} or None
    total, failures = 0, []
    if wanted is None:  # the root README quotes code by full path, e.g. `step_02_4_agent_loop/agent.py`
        found = check_step(ROOT)
        count = sum(1 for _ in snippets(ROOT / "README.md"))
        total += count
        print(f"{'README.md (root)':<36} {count:>2} snippets  {'ok' if not found else f'{len(found)} problems'}")
        failures += found
    for step in sorted(ROOT.glob("step_*/")):
        number = int(step.name.split("_")[1])
        if wanted and number not in wanted:
            continue
        found = check_step(step)
        count = sum(1 for _ in snippets(step / "README.md")) if (step / "README.md").exists() else 0
        total += count
        print(f"{step.name:<36} {count:>2} snippets  {'ok' if not found else f'{len(found)} problems'}")
        failures += found
    for f in failures:
        print("  " + f)
    print(f"{total} snippets checked, {len(failures)} problems")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
