"""Lesson 03 - a meta skill generates the loop harness: the template fills into lesson 02's pack, it lints against the\nintent, the writer proposes and waits, and only the user's words land it (twice gives the same bytes).

Offline (seconds, no key, no agent): the pack contract - front matter, every file the procedure names
exists, no forbidden tool in the procedure, `.claude/skills` == `.agents/skills`, the hook line, the
intent files - plus this lesson's own claims. Live (`RSI_LIVE=1`): the recorded run, `claude -p` from
this directory with the README's prompt, then the assertions on the artifacts the skill must leave.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
RSI = HERE.parent
SKILLS = HERE / ".claude" / "skills"
MIRROR = HERE / ".agents" / "skills"
RUNS = HERE / "runs"
PACKS = ['loop-writer']
INTENTS = ['../tasks/01_adult_income/intent.md']
CLAUDE_ARGS = ["--allowedTools", "Bash,Read,Write,Edit,Skill", "--setting-sources", "project", "--strict-mcp-config"]
RUNTIME_FILES = {"state.json", "traces.jsonl", "scorecard.json", "loop.log", "model.pkl", "curve.json", "exam.json", "score.json",
                 "plan.json", "working.md"}
FILE_RE = re.compile(r"`([\w./-]+\.(?:md|json|yaml|csv|jsonl))`")


# ---------------------------------------------------------------- reading packs


def front_matter(text):
    assert text.startswith("---\n"), "no front matter"
    head, body = text[4:].split("\n---\n", 1)
    return yaml.safe_load(head), body


def section(body, name):
    """The text under `## <name>` up to the next `## ` heading ("" when absent)."""
    m = re.search(rf"^## {re.escape(name)}\s*$", body, re.M)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def forbidden_tools(tools_md):
    """The tool names under `## Forbidden`: each bullet is `name, name - why`."""
    out = []
    for line in section(tools_md, "Forbidden").splitlines():
        if line.startswith("- "):
            out += [t.strip().strip("`") for t in line[2:].split(" - ")[0].split(",")]
    return [t for t in out if t]


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def skill(pack):
    return front_matter((SKILLS / pack / "SKILL.md").read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def state(pack, task, arm):
    return json.loads((RUNS / pack / task / arm / "state.json").read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- the pack contract (every lesson)


@pytest.mark.parametrize("pack", PACKS)
def test_front_matter(pack):
    meta, body = skill(pack)
    assert meta["name"] == pack and meta["description"]
    assert set(meta["metadata"]) >= {"type", "version", "rsi"}
    for heading in ("Boot order", "Procedure", "Rules", "Done when"):
        assert f"## {heading}" in body, f"{pack}: no {heading}"


@pytest.mark.parametrize("pack", PACKS)
def test_procedure_names_existing_files(pack):
    """Every backticked file the SKILL.md names exists: in the pack, the lesson, or the series (../tasks, ../data)."""
    meta, body = skill(pack)
    for name in set(FILE_RE.findall(body)):
        if any(s in name for s in ("runs/", "<", "*", "helpers/", "proposals/", "versions/")) or re.match(r"[A-Z]/", name):
            continue
        if name.split("/")[-1] in RUNTIME_FILES or re.match(r"p\d{3}", name.split("/")[-1]):
            continue
        candidates = [SKILLS / pack / name, SKILLS / pack / "template" / name, HERE / name, RSI / name.lstrip("./"), SKILLS / name,
                      *(other / name for other in SKILLS.iterdir()), *(SKILLS / pack).rglob(Path(name).name)]
        assert any(c.exists() for c in candidates), f"{pack}: SKILL.md names {name}, which does not exist"


@pytest.mark.parametrize("pack", PACKS)
def test_forbidden_tools_absent_from_procedure(pack):
    tools_md = (SKILLS / pack / "tools.md").read_text(encoding="utf-8")
    forbidden = forbidden_tools(tools_md)
    assert forbidden, f"{pack}: tools.md has no Forbidden list"
    procedure = section(skill(pack)[1], "Procedure")
    for name in forbidden:
        assert not re.search(rf"`{name}\b", procedure), f"{pack}: the procedure names `{name}`, which tools.md forbids"
    for name in forbidden:
        assert f"`{name}(" not in section(tools_md, "Allowed"), f"{pack}: {name} is both allowed and forbidden"


def test_mirror_identical():
    assert tree(SKILLS) == tree(MIRROR), ".claude/skills and .agents/skills differ"


def test_hook_installed():
    settings = json.loads((HERE / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks = [h for entry in settings["hooks"]["PreToolUse"] if entry["matcher"] == "Bash" for h in entry["hooks"]]
    command = hooks[0]["command"]
    assert "score_test" in command and '"frozen": true' in command, "the hook does not gate score_test on FREEZE"
    assert "apply" in command and ".approved" in command, "the hook does not gate apply on an approval file"
    assert "exit 2" in command


def test_no_python_shipped():
    """The owner's rule: nothing under a lesson is Python except this file (runs/ is the agent's, not shipped)."""
    shipped = [p for p in HERE.rglob("*.py") if "runs" not in p.parts and "__pycache__" not in p.parts]
    assert [p.name for p in shipped] == ["test_step.py"], shipped


@pytest.mark.parametrize("intent", INTENTS)
def test_intent_contract(intent):
    meta, body = front_matter((HERE / intent).read_text(encoding="utf-8"))
    for key in ("name", "index", "title", "role", "target", "metric", "budget_fits", "models", "data", "test", "profile_keys"):
        assert key in meta, f"{intent}: front matter lacks {key}"
    assert meta["budget_fits"] == 24 and meta["test"] == "locked, scored once after FREEZE"
    assert meta["metric"] in ("roc_auc", "roc_auc_ovr_macro") and set(meta["models"]) <= {"logreg", "rf", "hgb"}
    assert meta["data"]["kind"] in ("csv", "sklearn", "synthetic")
    for heading in ("What to improve", "Why", "What counts as success", "What is off limits", "The profile the verifier may condition on"):
        assert f"## {heading}" in body, f"{intent}: body lacks {heading}"


# ---------------------------------------------------------------- this lesson's claims (offline)

TEMPLATE = SKILLS / "loop-writer" / "template"
FILL = {"task": "adult_income", "task_slug": "adult-income", "task_dir": "01_adult_income", "title": "Adult Census Income (> 50k)",
        "metric": "roc_auc", "budget_fits": "24"}


def filled():
    out = {}
    for p in TEMPLATE.iterdir():
        text = p.read_text(encoding="utf-8")
        for k, v in FILL.items():
            text = text.replace("{{" + k + "}}", v)
        out[p.name] = text
    return out


def test_template_has_the_five_files_and_placeholders():
    assert sorted(p.name for p in TEMPLATE.iterdir()) == ["SKILL.md", "loop.json", "recipes.json", "schema.json", "tools.md"]
    text = "".join(p.read_text(encoding="utf-8") for p in TEMPLATE.iterdir())
    for k in FILL:
        assert "{{" + k + "}}" in text or k in ("title",), k
    assert "{{" not in "".join(filled().values()), "a placeholder the fill does not cover"


def test_filled_template_lints_against_the_intent():
    """What the writer produces is lesson 02's pack: same rules, same 24 recipes, the intent's budget, the test rule."""
    f = filled()
    intent = front_matter((RSI / "tasks" / "01_adult_income" / "intent.md").read_text(encoding="utf-8"))[0]
    schema, loop, recipes = json.loads(f["schema.json"]), json.loads(f["loop.json"]), json.loads(f["recipes.json"])
    assert schema["n_fits"] == intent["budget_fits"] == loop["N"] == len(recipes) == 24
    assert schema["test_rule"] == intent["test"] and schema["metric"] == intent["metric"] and schema["models"] == intent["models"]
    meta, body = front_matter(f["SKILL.md"])
    assert meta["name"] == "adult-income-loop" and all(f"## {h}" in body for h in ("Boot order", "Procedure", "Rules", "Done when"))
    assert "## Allowed" in f["tools.md"] and "## Forbidden" in f["tools.md"]
    lesson_02 = RSI / "step_02_loop_harness" / ".claude" / "skills" / "adult-income-loop"
    assert json.loads((lesson_02 / "recipes.json").read_text(encoding="utf-8")) == recipes
    assert (lesson_02 / "loop.json").read_text(encoding="utf-8") == f["loop.json"]


def test_writer_waits_for_the_user():
    body = skill("loop-writer")[1]
    procedure = section(body, "Procedure")
    assert "approve / edit / reject" in procedure and "Stop and wait" in procedure
    assert procedure.index("`propose") < procedure.index("`apply")
    assert ".approved" in procedure and ".rejected" in procedure
    assert skill("loop-writer")[0]["metadata"]["patches"] == ["adult-income-loop/*"]

# ---------------------------------------------------------------- the recorded run (RSI_LIVE=1)


def readme_prompt():
    """The prompt the README tells the reader to type: the first ```text block after "How to execute it"."""
    text = (HERE / "README.md").read_text(encoding="utf-8").split("## How to execute it", 1)[1]
    return re.search(r"```text\n(.*?)```", text, re.S).group(1).strip()


def reset():
    """Start from the shipped packs: on the first live run copy both mirrors to a pristine copy under the system temp
    directory (outside the agent's view), afterwards restore them from there; runs/ is cleared. The README says how to
    reset by hand."""
    pristine = Path(tempfile.gettempdir()) / "rsi_pristine" / HERE.name
    if not pristine.exists():
        pristine.mkdir(parents=True)
        shutil.copytree(SKILLS, pristine / ".claude")
        shutil.copytree(MIRROR, pristine / ".agents")
    if RUNS.exists():
        shutil.rmtree(RUNS)
    for root, src in ((SKILLS, ".claude"), (MIRROR, ".agents")):
        shutil.rmtree(root)
        shutil.copytree(pristine / src, root)
    for extra in ['.claude/skills/adult-income-loop', '.agents/skills/adult-income-loop']:
        if (HERE / extra).exists():
            shutil.rmtree(HERE / extra) if (HERE / extra).is_dir() else (HERE / extra).unlink()


def claude(prompt, cont=False, timeout=2400):
    """One `claude -p` turn from this directory; the stream is recorded under runs/_recording/, the final text returned."""
    exe = shutil.which("claude")
    assert exe, "claude is not on the PATH"
    args = [exe, "-p"] + (["--continue"] if cont else []) + [prompt, *CLAUDE_ARGS, "--output-format", "stream-json", "--verbose"]
    started = time.time()
    proc = subprocess.run(args, cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          stdin=subprocess.DEVNULL, timeout=timeout)
    (RUNS / "_recording").mkdir(parents=True, exist_ok=True)
    n = len(list((RUNS / "_recording").glob("*.jsonl"))) + 1
    (RUNS / "_recording" / f"{n:02d}.jsonl").write_text(proc.stdout, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr[-2000:]
    result = [o for o in (json.loads(l) for l in proc.stdout.splitlines() if l.startswith("{")) if o.get("type") == "result"]
    assert result and not result[-1].get("is_error"), proc.stdout[-2000:]
    print(f"[{result[-1]['num_turns']} turns, {int(time.time() - started)} s]")
    return result[-1]["result"]


def live_or_skip():
    if os.environ.get("RSI_LIVE") != "1":
        pytest.skip("set RSI_LIVE=1 to record the lesson with claude -p")


def test_live_claude_code():
    """The recorded run, two turns: the proposal is shown and nothing lands; `approve` lands the five files, byte-identical
    to the filled template, in both mirrors, with the user's words in the trace."""
    live_or_skip()
    reset()
    text = claude(readme_prompt())
    assert "approve" in text.lower() and "reject" in text.lower()
    proposals = RUNS / "loop-writer" / "adult_income" / "proposals"
    assert (proposals / "p001.json").exists() and not (proposals / "p001.approved").exists()
    assert not (SKILLS / "adult-income-loop").exists(), "the pack landed before the user answered"
    text2 = claude("approve", cont=True)
    assert (proposals / "p001.approved").read_text(encoding="utf-8").strip() == "approve"
    landed = SKILLS / "adult-income-loop"
    assert sorted(p.name for p in landed.iterdir()) == ["SKILL.md", "loop.json", "recipes.json", "schema.json", "tools.md"]
    assert tree(landed) == tree(MIRROR / "adult-income-loop")
    for name, expected in filled().items():
        assert (landed / name).read_text(encoding="utf-8") == expected, f"{name} differs from the filled template"
    events = [r for r in rows(RUNS / "loop-writer" / "adult_income" / "traces.jsonl") if "event" in r]
    assert [e["event"] for e in events] == ["propose", "apply"] and events[-1]["approved"] == "approve"
    assert "p001" in text2
