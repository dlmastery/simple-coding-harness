"""Step 38 - check 4: README.md exists and a run section names the uvicorn command."""

import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import fail, ok  # noqa: E402

readme = Path("README.md")
if not readme.exists():
    fail("README.md is missing")
text = readme.read_text(encoding="utf-8", errors="replace")
if len(text.strip()) < 80:
    fail("README.md is nearly empty")

headings = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^#{1,6}[ \t]+(.+)$", text, re.MULTILINE)]
run_headings = [(pos, title) for pos, title in headings if re.search(r"\brun", title, re.IGNORECASE)]
if not run_headings:
    fail(f"no heading mentions run; headings are {[title for _, title in headings]}")

start, title = run_headings[0]
following = [pos for pos, _ in headings if pos > start]
section = text[start:following[0] if following else len(text)]
if "uvicorn" not in section:
    fail(f"the section {title!r} does not name the uvicorn command")
ok(f"README.md has a {title!r} section with the uvicorn command")
