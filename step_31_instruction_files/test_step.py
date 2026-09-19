"""Step 31 offline tests. A temp tree stands in for the home directory, a
git root and the working directory below it; git_root is stubbed so no git
command runs. /init gets a fake subagent and scripted answers at the
approve prompt. The loop smoke test runs one turn with a fake model and
checks the system message it received.
"""

import json
import os
import sys
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


# ------------------------------------------------- robustness (shared by every step)

from harness import commands, permissions, prompt, subagent, tools  # noqa: E402 - the tests below need them whatever the step imports above


def _fake_model(replies):
    """A call_llm stand-in that answers with the next reply, whatever keywords the loop passes."""
    queue = list(replies)

    def fake(messages, tools=None, on_delta=None, **_):
        return queue.pop(0), USAGE

    return fake


def test_bad_arguments_an_unknown_tool_and_a_raising_tool_each_get_one_tool_message(monkeypatch, tmp_path):
    """The loop never dies on a tool call: every call gets exactly one result, then the model goes on."""
    monkeypatch.setattr(permissions, "PROJECT", tmp_path.resolve())
    broken = SimpleNamespace(id="c1", function=SimpleNamespace(name="bash", arguments='{"command": "echo hi"'))  # cut short
    unknown = call("c2", "no_such_tool", {"x": 1})
    raising = call("c3", "read_file", {"path": str(tmp_path / "missing.txt")})
    wrong = call("c4", "write_file", {"path": str(tmp_path / "a.txt")})  # content missing
    reply = FakeMessage(content=None, tool_calls=[broken, unknown, raising, wrong])
    monkeypatch.setattr(agent, "call_llm", _fake_model([reply, say("recovered")]))

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    results = {m["tool_call_id"]: m["content"] for m in out if m["role"] == "tool"}
    assert list(results) == ["c1", "c2", "c3", "c4"] and out[-1]["content"] == "recovered"
    assert results["c1"].startswith("Error: the arguments of bash are not a JSON object:")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: ") and results["c3"].endswith("missing.txt is not a file.")
    assert results["c4"].startswith("Error: TypeError:")
    assert tools.execute(call("c5", "bash", {}))[1] == "Blocked by policy: bash: missing argument 'command'"


def test_utf8_round_trip_through_write_file_read_file_and_bash(monkeypatch, tmp_path):
    monkeypatch.setattr(permissions, "PROJECT", tmp_path.resolve())
    target = tmp_path / "deep" / "unicode.txt"
    text = "naïve café — 日本語 ✓\r\nsecond line\n"
    assert tools.execute(call("w", "write_file", {"path": str(target), "content": text}))[1] == f"Wrote {target}"
    assert target.read_bytes() == text.encode("utf-8")  # parent made, line endings kept
    assert tools.execute(call("r", "read_file", {"path": str(target)}))[1] == text
    assert tools.execute(call("e", "str_replace", {"path": str(target), "old_str": "", "new_str": "x"}))[1].startswith("Error: old_str is empty")
    out = tools.bash(f"{sys.executable} -c \"print('日本語 ✓')\"")
    assert "日本語 ✓" in out


def test_write_todos_with_a_bad_status_returns_an_error_and_leaves_the_list_alone():
    todos.write_todos([{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b", "status": "pending"}]) == "Error: item 0 needs a non-empty 'activeForm'."
    assert todos.write_todos("not a list") == "Error: todos must be a list."
    assert todos.TODOS == before
    assert todos.write_todos([]) == "Todo list cleared."


def test_rewind_offers_only_user_turns_so_no_tool_call_is_orphaned(monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "ok"},
        {"role": "assistant", "content": "done one"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "done two"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.append(rows) or 1)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    monkeypatch.setattr(session, "rewind_to", lambda count: None)
    out = commands.handle("/rewind", messages)
    assert len(offered[0]) == 2 and offered[0][0].startswith("1 ") and "one" in offered[0][0]  # the index of the user message, never a tool call
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]  # cut before "two"
    for message in out:
        for tool_call in message.get("tool_calls") or []:
            assert any(m.get("tool_call_id") == tool_call["id"] for m in out)


def test_a_subagent_cannot_run_a_tool_it_was_not_offered(monkeypatch):
    seen = []
    monkeypatch.setitem(tools.TOOLS, "write_file", lambda path, content: seen.append(path) or "written")
    replies = [
        FakeMessage(content=None, tool_calls=[call("s1", "write_file", {"path": "x.txt", "content": "1"}), call("s2", "task", {"description": "again"})]),
        say("report"),
    ]
    monkeypatch.setattr(llm, "call_llm", _fake_model(replies))
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: None)
    assert subagent.task("look around") == "report" and seen == []


def test_ctrl_c_mid_turn_fills_the_missing_results_and_the_prompt_comes_back(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(session, "save", lambda messages: None)

    def boom(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(agent, "call_llm", _fake_model([FakeMessage(content=None, tool_calls=[call("c1", "bash", {"command": "sleep 60"})])]))
    out = agent.turn([{"role": "system", "content": "s"}], "wait")  # the turn catches ctrl-c and answers the pending call itself
    assert out[-1] == {"role": "tool", "tool_call_id": "c1", "content": agent.INTERRUPTED} and seen[-1] == "interrupted"


def test_ask_returns_none_to_leave_and_empty_to_continue(monkeypatch):
    def eof(text="> "):
        raise EOFError

    monkeypatch.setattr(prompt, "read", eof)
    assert ui.ask() is None
    monkeypatch.setattr(prompt, "read", lambda text="> ": "   ")
    assert ui.ask() == ""
    assert "/exit" in commands.COMMANDS


def test_bash_rules_ask_about_substitutions_redirections_and_env():
    assert permissions.decide("ls $(pwd)") == "ask" and permissions.decide("cat `which python`") == "ask"
    assert permissions.decide("echo hi > out.txt") == "ask" and permissions.decide("git log | tee log.txt") == "ask"
    assert permissions.decide("find . -name x -delete") == "ask" and permissions.decide("find . -name x") == "allow"
    assert permissions.decide("cat x 2>&1") == "allow" and permissions.split_command("cat x 2>&1") == ["cat x 2>&1"]
    assert permissions.decide("env") == "ask" and permissions.split_command("ls\nrm -rf /") == ["ls", "rm -rf /"]
    assert permissions.decide("ls\nrm -rf /") == "deny"
    assert permissions.check("write_file", {"path": ".git/config"})[0] == "ask"


def test_session_load_repairs_a_dangling_tool_call(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    session.SESSION_DIR.mkdir(parents=True)
    lines = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
    ]
    session.path_for("crashed").write_text("\n".join(json.dumps(line) for line in lines) + "\n{half a line", encoding="utf-8")
    messages = session.load("crashed")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": "(the harness stopped before this tool ran; no result was recorded)"}
    assert len(messages) == 4


def test_init_keeps_the_handoff_note_of_a_compaction(tree, monkeypatch):
    monkeypatch.chdir(tree.leaf)
    monkeypatch.setattr(subagent, "task", lambda description=None, descriptions=None: "# Guide")
    answers(monkeypatch, "y")
    notes(monkeypatch)
    system = llm.build_system_prompt(str(tree.leaf)) + "\n\n<summary>\nwhat happened before\n</summary>"
    messages = [{"role": "system", "content": system}]
    commands.handle("/init", messages)
    assert "# Instructions from AGENTS.md" in messages[0]["content"]
    assert messages[0]["content"].endswith("<summary>\nwhat happened before\n</summary>")
