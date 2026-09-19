"""What every lesson's test_step.py shares: a temporary lesson directory with
copies of the packs, the tool scripts called in-process, the pack contract
every lesson must meet, and the optional live `claude -p` smoke test.
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from _lib import cli, packs

RSI = Path(__file__).resolve().parents[2]
TOOLS = RSI / "tools"
TASKS = RSI / "tasks"
HOOK = RSI / "hooks" / "gate.py"

_MODULES = {}


def tool(name, *argv):
    """Run rsi/tools/<name>.py in-process with these arguments; the result dict (a refusal is {"error": ...})."""
    if name not in _MODULES:
        spec = importlib.util.spec_from_file_location(f"rsi_tool_{name}", TOOLS / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return cli.call(_MODULES[name].main, [str(a) for a in argv])


def tool_cli(name, *argv, cwd=None):
    """The same through a real subprocess: the JSON contract on stdout, exit 0."""
    proc = subprocess.run([sys.executable, str(TOOLS / f"{name}.py"), *[str(a) for a in argv]], capture_output=True, text=True, cwd=cwd)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def workspace(lesson_dir, tmp, *names, mirror=".claude"):
    """Copy .claude/skills/<name> of a lesson into tmp/.claude/skills/<name>; returns the copies (one path, or a list)."""
    out = []
    for name in names:
        dest = Path(tmp) / ".claude" / "skills" / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(Path(lesson_dir) / mirror / "skills" / name, dest)
        out.append(dest)
    return out[0] if len(out) == 1 else out


def task(name):
    """A curriculum task file by its bare name (adult_income, breast_cancer, ..., exam)."""
    return next(iter(sorted(TASKS.glob(f"*_{name}.json"))))


def commands_in(text):
    """The tool scripts a SKILL.md names: every `tools/<name>.py`."""
    return sorted(set(re.findall(r"tools/([a-z_]+)\.py", text)))


def forbidden_tools(tools_md):
    out, section = [], None
    for line in tools_md.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
        elif line.startswith("- ") and section == "forbidden":
            out += [t.strip().strip("`") for t in line[2:].split(" - ")[0].split(",")]
    return [t for t in out if t]


def pack_contract(lesson_dir):
    """Every reason the lesson's packs break the contract; empty = fine."""
    lesson_dir = Path(lesson_dir)
    problems = []
    claude, agents = lesson_dir / ".claude" / "skills", lesson_dir / ".agents" / "skills"
    if not claude.exists():
        return ["no .claude/skills"]
    if packs.read_pack(claude) != packs.read_pack(agents):
        problems.append(".claude/skills and .agents/skills differ")
    settings = lesson_dir / ".claude" / "settings.json"
    if not settings.exists() or "gate.py" not in settings.read_text(encoding="utf-8"):
        problems.append(".claude/settings.json lacks the gate.py hook")
    for skill in sorted(claude.rglob("SKILL.md")):
        if "template" in skill.parts:
            continue
        pack = skill.parent
        try:
            meta, body = packs.parse_front_matter(skill.read_text(encoding="utf-8"))
        except ValueError as e:
            problems.append(f"{pack.name}: {e}")
            continue
        md = meta.get("metadata") or {}
        for key in ("type", "version", "rsi"):
            if key not in md:
                problems.append(f"{pack.name}: front matter metadata lacks {key}")
        for name in commands_in(body):
            if not (TOOLS / f"{name}.py").exists():
                problems.append(f"{pack.name}: SKILL.md names tools/{name}.py, which does not exist")
        tools_md = pack / "tools.md"
        if tools_md.exists():
            procedure = body.split("## Procedure")[1].split("## Rules")[0] if "## Procedure" in body else body
            for name in forbidden_tools(tools_md.read_text(encoding="utf-8")):
                if f"tools/{name}.py" in procedure:
                    problems.append(f"{pack.name}: the procedure names {name}, which tools.md forbids")
    return problems


def readme_prompt(lesson_dir):
    """The prompt the README tells the reader to type: the first fenced ```text block after 'How to execute it'."""
    text = (Path(lesson_dir) / "README.md").read_text(encoding="utf-8")
    after = text.split("## How to execute it", 1)[1]
    m = re.search(r"```text\n(.*?)```", after, re.S)
    return m.group(1).strip() if m else None


def live(lesson_dir, prompt=None, timeout=1800):
    """RSI_LIVE=1: run the lesson once with Claude Code headless from the lesson directory; returns the final text."""
    if os.environ.get("RSI_LIVE") != "1":
        import pytest
        pytest.skip("set RSI_LIVE=1 to run the claude -p smoke test")
    prompt = prompt or readme_prompt(lesson_dir)
    proc = subprocess.run(["claude", "-p", prompt, "--allowedTools", "Bash,Read,Write,Edit,Skill"], cwd=lesson_dir,
                          capture_output=True, text=True, timeout=timeout, shell=(os.name == "nt"))
    assert proc.returncode == 0, proc.stderr
    return proc.stdout
