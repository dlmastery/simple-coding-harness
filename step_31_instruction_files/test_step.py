"""Step 31 offline tests. A temp tree stands in for the home directory, a
git root and the working directory below it; git_root is stubbed so no git
command runs. /init gets a fake subagent and scripted answers at the
approve prompt. The loop smoke test runs one turn with a fake model and
checks the system message it received.
"""

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, context, hooks, instructions, jobs, llm, plan, prompt, session, subagent, todos  # noqa: E402
from harness.ui import ui  # noqa: E402

USAGE = {"prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": None, "cached_tokens": 3}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def say(text):
    return FakeMessage(content=text, tool_calls=None)


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Every test starts in act mode, with no hooks, no jobs, and no real home or session store."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(instructions, "LOADED", [])
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    jobs.kill_all()
    yield
    jobs.kill_all()


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """home/.simple-harness, repo (the git root), repo/pkg, repo/pkg/leaf (the cwd)."""
    home = tmp_path / "home" / ".simple-harness"
    repo = tmp_path / "repo"
    leaf = repo / "pkg" / "leaf"
    for directory in (home, leaf):
        directory.mkdir(parents=True)
    monkeypatch.setattr(instructions, "git_root", lambda cwd=None: repo.resolve())
    return SimpleNamespace(home=home, repo=repo, pkg=repo / "pkg", leaf=leaf)


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def answers(monkeypatch, *lines):
    """Script what the user types at the prompts, in order."""
    queue = list(lines)
    asked = []

    def read(text="> "):
        asked.append(text)
        return queue.pop(0)

    monkeypatch.setattr(prompt, "read", read)
    return asked


# -------------------------------------------------------------- discovery


def test_discovery_order_is_home_then_root_to_leaf(tree):
    (tree.home / "AGENTS.md").write_text("home rules", encoding="utf-8")
    (tree.repo / "AGENTS.md").write_text("repo rules", encoding="utf-8")
    (tree.pkg / "AGENTS.md").write_text("pkg rules", encoding="utf-8")
    (tree.leaf / "AGENTS.md").write_text("leaf rules", encoding="utf-8")
    (tree.repo.parent / "AGENTS.md").write_text("above the root: never read", encoding="utf-8")

    found = instructions.find_instructions(tree.leaf)
    assert found == [tree.home / "AGENTS.md", tree.repo / "AGENTS.md", tree.pkg / "AGENTS.md", tree.leaf / "AGENTS.md"]

    text = instructions.instructions_prompt(tree.leaf)
    order = [text.index(part) for part in ("home rules", "repo rules", "pkg rules", "leaf rules")]
    assert order == sorted(order)
    assert "above the root" not in text
    assert instructions.LOADED == found


def test_claude_md_is_an_alias_and_agents_md_wins_when_both_exist(tree):
    (tree.repo / "CLAUDE.md").write_text("only claude here", encoding="utf-8")
    (tree.leaf / "AGENTS.md").write_text("agents", encoding="utf-8")
    (tree.leaf / "CLAUDE.md").write_text("claude twin", encoding="utf-8")
    found = instructions.find_instructions(tree.leaf)
    assert found == [tree.repo / "CLAUDE.md", tree.leaf / "AGENTS.md"]
    text = instructions.instructions_prompt(tree.leaf)
    assert "only claude here" in text and "agents" in text and "claude twin" not in text


def test_no_files_gives_an_empty_prompt_and_an_empty_loaded_list(tree):
    assert instructions.find_instructions(tree.leaf) == []
    assert instructions.instructions_prompt(tree.leaf) == ""
    assert instructions.LOADED == []


def test_each_file_is_cut_at_the_limit_and_says_so(tree):
    (tree.repo / "AGENTS.md").write_text("a" * 25_000, encoding="utf-8")
    (tree.leaf / "AGENTS.md").write_text("short", encoding="utf-8")
    text = instructions.instructions_prompt(tree.leaf)
    assert text.count("a") < 25_000 and "a" * instructions.MAX_CHARS in text
    assert "[truncated: this file has 25,000 characters; only the first 20,000 are shown]" in text
    assert text.endswith("short")  # the second file is whole
    assert instructions.read_instructions(tree.leaf / "AGENTS.md") == "short"


def test_headers_name_each_file_relative_to_the_working_directory(tree):
    (tree.home / "AGENTS.md").write_text("h", encoding="utf-8")
    (tree.repo / "AGENTS.md").write_text("r", encoding="utf-8")
    (tree.leaf / "CLAUDE.md").write_text("l", encoding="utf-8")
    text = instructions.instructions_prompt(tree.leaf)
    assert "# Instructions from ~/.simple-harness/AGENTS.md" in text
    assert "# Instructions from ../../AGENTS.md" in text
    assert "# Instructions from CLAUDE.md" in text


def test_git_root_falls_back_to_the_working_directory(tmp_path, monkeypatch):
    def no_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", no_git)
    assert instructions.git_root(tmp_path) == tmp_path.resolve()
    assert instructions.search_dirs(tmp_path) == [instructions.HOME, tmp_path.resolve()]

    def not_a_repo(*args, **kwargs):
        return SimpleNamespace(returncode=128, stdout="")

    monkeypatch.setattr(subprocess, "run", not_a_repo)
    assert instructions.git_root(tmp_path) == tmp_path.resolve()


def test_git_root_uses_rev_parse_when_git_is_there(tmp_path):
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        pytest.skip("git is not installed")
    repo = tmp_path / "repo"
    (repo / "a" / "b").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    assert instructions.same(instructions.git_root(repo / "a" / "b"), repo.resolve())
    assert [instructions.same(d, want) for d, want in zip(instructions.search_dirs(repo / "a" / "b"), [instructions.HOME, repo, repo / "a", repo / "a" / "b"])] == [True] * 4


# --------------------------------------------------------- system prompt


def test_system_prompt_carries_the_files_before_the_skills_index(tree):
    (tree.repo / "AGENTS.md").write_text("Run `make test` before every commit.", encoding="utf-8")
    text = llm.build_system_prompt(str(tree.leaf))
    assert f"Your current working directory is: {tree.leaf}" in text
    assert llm.INSTRUCTIONS_INTRO.strip() in text
    assert "# Instructions from ../../AGENTS.md" in text
    assert "Run `make test` before every commit." in text
    assert text.index("# Instructions from") < text.index("You have skills available.")
    assert llm.instructions_section(str(tree.leaf)).startswith(llm.INSTRUCTIONS_INTRO)


def test_system_prompt_without_files_has_no_instruction_section(tree):
    text = llm.build_system_prompt(str(tree.leaf))
    assert "# Instructions from" not in text and llm.INSTRUCTIONS_INTRO.strip() not in text
    assert llm.instructions_section(str(tree.leaf)) == ""


# --------------------------------------------------------------- commands


def test_init_writes_agents_md_from_a_fake_subagent_after_yes(tree, monkeypatch):
    monkeypatch.chdir(tree.leaf)
    asked = []

    def fake_task(description=None, descriptions=None):
        asked.append(description)
        return "# Guide\n\nBuild: `make`. Test: `make test`."

    monkeypatch.setattr(subagent, "task", fake_task)
    seen = notes(monkeypatch)
    prompts = answers(monkeypatch, "y")
    messages = [{"role": "system", "content": llm.build_system_prompt(str(tree.leaf))}]
    assert "# Instructions from" not in messages[0]["content"]

    out = commands.handle("/init", messages)

    assert out is messages
    assert asked == [commands.INIT_QUESTION.strip()] and "test" in asked[0].lower()
    assert prompts == ["  approve? (y/n)> "]
    assert (tree.leaf / "AGENTS.md").read_text(encoding="utf-8") == "# Guide\n\nBuild: `make`. Test: `make test`.\n"
    assert any("wrote" in note for note in seen)
    assert "# Instructions from AGENTS.md" in messages[0]["content"] and "Test: `make test`." in messages[0]["content"]


def test_init_writes_nothing_after_no_or_an_empty_report(tree, monkeypatch):
    monkeypatch.chdir(tree.leaf)
    monkeypatch.setattr(subagent, "task", lambda description=None, descriptions=None: "# Guide")
    seen = notes(monkeypatch)
    answers(monkeypatch, "n")
    commands.handle("/init", [{"role": "system", "content": "s"}])
    assert not (tree.leaf / "AGENTS.md").exists() and seen[-1] == "not written"

    monkeypatch.setattr(subagent, "task", lambda description=None, descriptions=None: "(the subagent came back with nothing)")
    answers(monkeypatch)  # no prompt must be read
    commands.handle("/init", [{"role": "system", "content": "s"}])
    assert not (tree.leaf / "AGENTS.md").exists() and "nothing written" in seen[-1]


def test_instructions_command_lists_the_loaded_files(tree, monkeypatch):
    seen = notes(monkeypatch)
    commands.handle("/instructions", [])
    assert seen[-1].startswith("no instruction files loaded")

    (tree.home / "AGENTS.md").write_text("h", encoding="utf-8")
    (tree.leaf / "CLAUDE.md").write_text("c" * 30_000, encoding="utf-8")
    monkeypatch.chdir(tree.leaf)
    llm.build_system_prompt(str(tree.leaf))
    commands.handle("/instructions", [])
    rows = seen[-1].splitlines()
    assert rows[0].startswith("~/.simple-harness/AGENTS.md") and "1 chars" in rows[0]
    assert rows[1].startswith("CLAUDE.md") and "30,000 chars" in rows[1] and "(cut at 20,000)" in rows[1]
    assert "/init" in commands.COMMANDS and "/instructions" in commands.COMMANDS


# ------------------------------------------------------------------ loop


def test_loop_smoke_the_model_sees_the_instructions_in_the_system_message(tree, monkeypatch):
    (tree.repo / "AGENTS.md").write_text("Always answer in haiku.", encoding="utf-8")
    monkeypatch.chdir(tree.leaf)
    seen = []

    def fake(messages, tools=None, on_delta=None):
        seen.append(messages)
        return say("done"), USAGE

    monkeypatch.setattr(agent, "call_llm", fake)
    messages = [{"role": "system", "content": llm.build_system_prompt()}]
    messages = agent.turn(messages, "hello")

    assert [m["role"] for m in messages] == ["system", "user", "assistant"]
    system = seen[0][0]["content"]
    assert seen[0][0]["role"] == "system"
    assert "# Instructions from ../../AGENTS.md" in system and "Always answer in haiku." in system
    assert "Always answer in haiku." not in seen[0][-1]["content"]  # the late block does not carry it
