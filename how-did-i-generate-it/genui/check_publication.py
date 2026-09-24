"""Check GenUI navigation, source backup and selected illustration placement."""
import hashlib
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "0d10b486064a9a39f49c028f2cacf902db22ee51"


def main():
    paths = subprocess.check_output([
        "git", "ls-files", "--cached", "--others", "--exclude-standard", "--",
        "genui", "how-did-i-generate-it/genui"], cwd=ROOT, text=True).splitlines()
    problems, links = [], 0
    for name in sorted(set(paths)):
        if not name.endswith(".md"):
            continue
        path = ROOT / name
        text = path.read_text(encoding="utf-8-sig")
        # Code examples may contain Markdown-looking syntax, not actual links.
        text = re.sub(r"(?ms)^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1[ \t]*$", "", text)
        text = re.sub(r"`+[^`\n]*`+", "", text)
        for target in re.findall(r"\[[^\]]*\]\(([^)\n]+)\)", text):
            target = target.strip("<>").split("#", 1)[0]
            if not target or re.match(r"^[a-zA-Z][\w+.-]*:", target):
                continue
            links += 1
            if not (path.parent / target).exists():
                problems.append(f"{name}: missing {target}")
    lessons = sorted((ROOT / "genui").glob("[0-9][0-9]_*/step_*/README.md"))
    themes = sorted((ROOT / "genui").glob("[0-9][0-9]_*/README.md"))
    assert len(lessons) == 23 and len(themes) == 7
    for path in lessons + themes:
        assert "<!-- genui-orientation -->" in path.read_text(encoding="utf-8")
    overview = (ROOT / "genui/README.md").read_text(encoding="utf-8")
    for path in lessons:
        assert path.parent.relative_to(ROOT / "genui").as_posix() + "/" in overview
    for name in ("two-decisions-v2.png", "learning-path-v1.png"):
        assert f"assets/illustrations/{name}" in overview
        assert (ROOT / "genui/assets/illustrations" / name).stat().st_size > 10000
    # Check all original files, without normalizing line endings.
    original = subprocess.check_output(["git", "ls-tree", "-rz", SOURCE, "genui"], cwd=ROOT)
    expected = {}
    for entry in original.split(b"\0"):
        if entry:
            meta, name = entry.split(b"\t", 1)
            expected["original/" + name.decode()] = meta.split()[2].decode()
    archive = ROOT / "how-did-i-generate-it/genui/backups/genui-before-refresh.zip"
    with zipfile.ZipFile(archive) as zipped:
        assert {i.filename for i in zipped.infolist() if not i.is_dir()} == set(expected)
        for name, blob in expected.items():
            data = zipped.read(name)
            assert hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == blob, name
    print(f"Checked {len(lessons)} lessons, {len(themes)} themes, {links} local links, two selected infographics and {len(expected)} original backup files.")
    for problem in problems:
        print(problem)
    print(f"{len(problems)} publication problems.")
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
