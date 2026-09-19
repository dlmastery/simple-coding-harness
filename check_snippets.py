"""Verify that every code snippet quoted in a step README exists in that step's code.

Convention: a ```python (or ```ts, ```tsx, ```js, ```jsx, ```html, ```css)
block belongs to the last backticked path named above it in the README, such
as `agent.py` or `harness/tools.py`.
Every non-blank snippet line (except elisions starting with `...` or `# ...`)
must appear, whitespace-normalised, in that file. Illustrative pseudo-code
goes in ```text blocks, which are not checked.

    python check_snippets.py            # all steps, root and genui/
    python check_snippets.py 14 16      # a subset of the root steps
    python check_snippets.py genui/03   # every step under genui/03_*
    python check_snippets.py rsi        # every step of the rsi/ series
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PATH_RE = re.compile(r"`([\w./-]+\.(?:py|js|mjs|cjs|jsx|ts|tsx|toml|md|yml|yaml|html|css|json))`")
FENCES = {"```python", "```ts", "```tsx", "```js", "```jsx", "```html", "```css"}


def snippets(readme):
    """Yield (path, block_lines, block_start_line) for each python fence."""
    lines = readme.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() in FENCES:
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
            problems.append(f"{readme}:{line}: code block has no `file` reference above it")
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


def step_dirs(args):
    """The step directories the arguments select: numbers pick root steps, prefixes pick series."""
    numbers = {int(a) for a in args if a.isdigit()}
    prefixes = [a.rstrip("/") for a in args if not a.isdigit()]
    if not args:
        yield ROOT, "README.md (root)"
        if (ROOT / "genui" / "README.md").exists():
            yield ROOT / "genui", "genui/README.md"
    for step in sorted(ROOT.glob("step_*/")):
        if prefixes and not numbers:
            continue
        if numbers and int(step.name.split("_")[1]) not in numbers:
            continue
        yield step, step.name
    for step in sorted(list(ROOT.glob("genui/*/step_*/")) + list(ROOT.glob("rsi/step_*/"))):
        rel = step.relative_to(ROOT).as_posix()
        if numbers and not prefixes:
            continue
        if prefixes and not any(rel.startswith(p) for p in prefixes):
            continue
        yield step, rel


def main():
    total, failures = 0, []
    for step, label in step_dirs(sys.argv[1:]):
        found = check_step(step)
        count = sum(1 for _ in snippets(step / "README.md")) if (step / "README.md").exists() else 0
        total += count
        print(f"{label:<44} {count:>2} snippets  {'ok' if not found else f'{len(found)} problems'}")
        failures += found
    for f in failures:
        print("  " + f)
    print(f"{total} snippets checked, {len(failures)} problems")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
