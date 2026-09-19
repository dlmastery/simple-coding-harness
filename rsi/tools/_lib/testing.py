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


# ---------------------------------------------------------------- the test as the agent (lessons 06 on)


def policy_line(pack):
    """The `Search policy: <name>` line of a pack's SKILL.md (the line a meta pack may patch); obey-memory if absent."""
    files = [Path(pack) / "SKILL.md", *sorted((Path(pack) / "modules").glob("*.md"))]
    text = "\n".join(p.read_text(encoding="utf-8") for p in files if p.exists())
    return packs.policy_line(text) or "obey-memory"


def play_arm(pack, task_path, arm="memory", memory_off=False, policy=None, seed=0, freeze_memory=False, batch=8, run=None):
    """Play the actor skill's procedure on one arm with the policy text of SKILL.md (`_lib/policies.py`): open the
    arm, fit in batches until FREEZE, score the best once. Returns the scorecard. The policy is the pack's
    `Search policy:` line unless given; the control arm always walks the static list."""
    from _lib import memory, policies, recipe, tasks
    from _lib.state import Run

    policy = "static" if memory_off else (policy or policy_line(pack))

    argv = ["--pack", str(pack), "--task", str(task_path), "--arm", arm, "--seed", str(seed)] + (["--run", str(run)] if run else [])
    opened = tool("load_splits", *argv, *(["--memory", "off"] if memory_off else []), *(["--freeze-memory"] if freeze_memory else []))
    assert "error" not in opened, opened
    r = Run(pack, task_path, arm, seed, run)
    schema = json.loads((Path(pack) / "schema.json").read_text(encoding="utf-8"))
    static = schema.get("recipes", recipe.static_list())
    forbid = schema.get("forbid", [])
    cards = [] if r.memory_off else memory.load(r.memory_path)
    profile = tasks.profile(r.task)
    fits, tried = [], []
    while True:
        order = policies.policy_order(policy, static, cards, profile, fits, seed=seed, forbid=forbid)
        todo = [x for x in order if x not in tried][:batch]
        if not todo:
            break
        out = tool("fit_recipe", *argv, "--recipes", json.dumps(todo))
        assert "error" not in out, out
        for res in out["results"]:
            tried.append(res["recipe"])
            if not res.get("refused"):
                fits.append(({"recipe": res["recipe"]}, {"n": res["n"], "val_score": res["val_score"]}))
        if out.get("FREEZE"):
            break
    scored = [f for f in fits if f[1]["val_score"] is not None]
    best = max(scored, key=lambda f: f[1]["val_score"])[0]["recipe"]
    test = tool("score_test", *argv, "--recipe", json.dumps(best))
    assert "test_score" in test, test
    return tool("scorecard", *argv)


def play_verifier(pack, task_path, verifier, seed=0, run=None, of="memory"):
    """The verifier skill's procedure: the tally of the memory arm's log (or another arm's), then the cards the rule names."""
    argv = ["--pack", str(pack), "--task", str(task_path), "--seed", str(seed), "--arm", of] + (["--run", str(run)] if run else [])
    rows = tool("read_traces", *argv, "--scope", "problem", "--tally", "--of", of)
    cards = rows["cards_by_rule"]
    if not cards:
        return {"written": 0, "cards": rows.get("n", 0)}
    return tool("write_card", *argv, "--as", str(verifier), "--cards", json.dumps(cards))


def play_meta(meta, actor, task_path, visit=1, words=None, edited=None, seed=0, run=None):
    """The meta skill's procedure (lesson 09): read, decide ONE change by the rule a / b / c, propose it through
    patch_pack; under `approval: human` answer with `words` (None = stop after the proposal, like an agent
    waiting for the user). Returns (decision dict, the files proposed) or (None, {}) when nothing applies."""
    from _lib import memory as mem, recipe
    from _lib.state import Run

    argv = ["--pack", str(meta), "--task", str(task_path), "--seed", str(seed)] + (["--run", str(run)] if run else [])
    if (Path(meta) / "config.json").exists() and json.loads((Path(meta) / "config.json").read_text(encoding="utf-8")).get("meta") == "off":
        return tool("patch_pack", *argv, "--target", str(actor), "--files", "{}", "--recipe", json.dumps(recipe.BASELINE)), {}
    rows_all = tool("read_traces", "--pack", str(actor), "--task", str(task_path), "--seed", str(seed), *(["--run", str(run)] if run else []), "--scope", "all")["rows"]
    cards = mem.load(Path(actor) / "memory.json")
    files_now = packs.read_pack(actor)
    files = {}
    if "Search policy: static" in files_now["SKILL.md"] and sum(1 for c in cards if mem.active(c)) >= 2:
        files["SKILL.md"] = files_now["SKILL.md"].replace("Search policy: static", "Search policy: obey-memory")
    else:
        losses, wins = {}, {}
        for problem in sorted({r["problem"] for r in rows_all}):
            w, l, _ = mem.tally([r for r in rows_all if r["problem"] == problem and r["arm"] == "memory"])
            for k, n in w.items():
                wins[k] = wins.get(k, 0) + n
            for k, n in l.items():
                losses[k] = losses.get(k, 0) + n
        never_won = sorted((k for k, n in losses.items() if n >= 3 and wins.get(k, 0) == 0 and k[0] != "hyper"), key=str)
        schema = json.loads(files_now["schema.json"])
        never_won = [k for k in never_won if {"field": k[0], "value": k[1]} not in schema.get("forbid", [])]
        if never_won:
            schema.setdefault("forbid", []).append({"field": never_won[0][0], "value": never_won[0][1]})
            files["schema.json"] = json.dumps(schema, indent=1) + "\n"
        else:
            r = Run(actor, task_path, "memory", seed, run)
            fresh = [c for c in mem.compare([{k: x[k] for k in ("recipe", "val_score", "error")} for x in r.fit_rows()], r.profile)
                     if mem.card_id(c) not in {mem.card_id(x) for x in cards}][:3]
            if fresh:
                merged = mem.load(Path(actor) / "memory.json")
                for c in fresh:
                    mem.merge(merged, c)
                files["memory.json"] = json.dumps(merged, indent=1) + "\n"
    if not files:
        return None, {}
    last = [x for x in rows_all if x["problem"] == Run(actor, task_path, "memory", seed, run).problem and x["val_score"] is not None]
    evidence = max(last, key=lambda x: x["val_score"])["recipe"] if last else recipe.BASELINE
    out = tool("patch_pack", *argv, "--target", str(actor), "--files", json.dumps({n: {"after": t} for n, t in files.items()}),
               "--recipe", json.dumps(evidence), "--summary", "one change: " + ", ".join(files), "--visit", str(visit))
    if "error" in out or out.get("landed") is not False or out.get("decision") is not None or words is None:
        return out, files
    argv2 = argv + ["--target", str(actor), "--proposal", out["id"], "--approved", words]
    if edited is not None:
        argv2 += ["--edited", json.dumps({n: {"after": t} for n, t in edited.items()})]
    return tool("patch_pack", *argv2), files
