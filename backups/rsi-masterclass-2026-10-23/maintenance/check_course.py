"""Check local navigation, lesson identity, source-byte integrity, and skill links.

This is publication validation, not evidence that a learner completed the course.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def check():
    problems = []
    links = 0
    roots = [ROOT, REPO / "how-did-i-generate-it/rsi", REPO / "skills/build-research-codelabs"]
    for base in roots:
        for path in base.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]*\]\(([^)\n]+)\)", text):
                target = target.strip("<>")
                if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
                    continue
                target = target.split("#", 1)[0]
                if target:
                    links += 1
                    if not (path.parent / target).exists():
                        problems.append(f"{path.relative_to(REPO)}: missing {target}")
            if "<code>" in text and text.count("<code>") != text.count("</code>"):
                problems.append(f"{path.relative_to(REPO)}: unbalanced code tags")
    lessons = sorted(p for p in ROOT.glob("[0-9][0-9]_*/**/step_*/README.md"))
    ids = []
    for path in lessons:
        match = re.match(r"# (\d{2}\.\d{2}) ·", path.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{path}: missing lesson identity")
        else:
            ids.append(match[1])
        if not (path.parent / "BRIEF.md").exists():
            problems.append(f"{path}: missing runnable brief")
    if len(ids) != len(set(ids)):
        problems.append("Duplicate lesson IDs")
    mapped = re.findall(r"^\| (\d{2}\.\d{2}) \|", (ROOT / "COURSE-MAP.md").read_text(encoding="utf-8"), re.M)
    if sorted(mapped) != sorted(ids):
        problems.append("Course map does not match authored lesson files")
    print(f"Checked {len(lessons)} lessons and {links} local links.")
    for problem in problems:
        print(problem)
    print(f"{len(problems)} publication problems.")
    return bool(problems)


if __name__ == "__main__":
    sys.exit(check())
