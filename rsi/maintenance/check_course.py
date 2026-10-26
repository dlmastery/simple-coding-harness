"""Check that every relative link in the course's Markdown files points to a file that exists."""

import re
import sys
from pathlib import Path

RSI = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def broken_links():
    for md in sorted(RSI.rglob("*.md")):
        if any(part in {"runs", "replay"} for part in md.relative_to(RSI).parts):
            continue
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (md.parent / target).exists():
                yield md.relative_to(RSI), target


if __name__ == "__main__":
    bad = list(broken_links())
    for md, target in bad:
        print(f"{md}: broken link {target}")
    print(f"check_course: {'FAIL' if bad else 'ok'} ({len(bad)} broken links)")
    sys.exit(1 if bad else 0)
