"""Step 39 offline tests. The modes are exercised through permissions.check,
tools.execute, commands.handle("/mode ...") and agent.turn with a fake
model. The approve prompt is scripted or made to fail, so a test that must
never prompt fails loudly if it does. Nothing is launched.
"""

import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.console import Console

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, checkpoint, commands, context, hooks, instructions, jobs, mcp_client, memory, modes, permissions, plan, prompt, sandbox, session, todos, tools  # noqa: E402
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


def use(*calls):
    return FakeMessage(content=None, tool_calls=list(calls))


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """A temp workspace as cwd, temp stores, no hooks, no jobs, default mode, no session rules."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(permissions, "PROJECT", workspace.resolve())
    monkeypatch.setattr(permissions, "SESSION_RULES", {})
    monkeypatch.setattr(sandbox, "PROJECT", workspace.resolve())
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(mcp_client, "CONFIG_PATHS", [tmp_path / "mcp.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(plan, "PLAN", None)
    monkeypatch.setattr(modes, "CURRENT", "default")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda *a, **k: None)
    console, live = ui.console, ui.live  # ui.headless() swaps them; put them back
    jobs.kill_all()
    yield workspace
    jobs.kill_all()
    ui.console, ui.live = console, live


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def typed(monkeypatch, *lines):
    """Script prompt.read: each call returns the next line, and records the prompt it was asked with."""
    queue = list(lines)
    prompts = []

    def read(text="> "):
        prompts.append(text)
        return queue.pop(0)

    monkeypatch.setattr(prompt, "read", read)
    return prompts


def never_prompt(monkeypatch):
    """Make the approve prompt fail the test: a mode that must not ask is caught the moment it does."""
    monkeypatch.setattr(ui, "approve", lambda reason: pytest.fail(f"the approve prompt was opened: {reason}"))


def fake_model(monkeypatch, replies):
    """A model that answers from a script."""
    replies = list(replies)
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append(messages)
        return replies.pop(0), dict(USAGE)

    monkeypatch.setattr(agent, "call_llm", fake)
    return requests


def four_calls(workspace, tmp_path):
    """The same four calls every mode is rated on."""
    return [
        ("bash", {"command": "ls"}),
        ("bash", {"command": "python x.py"}),
        ("write_file", {"path": str(workspace / "inside.txt"), "content": "x"}),
        ("write_file", {"path": str(tmp_path / "outside.txt"), "content": "x"}),
    ]


# ------------------------------------------------------------------- modes


def test_each_mode_rates_the_same_four_calls(fresh, tmp_path):
    expected = {
        "default": ["allow", "ask", "allow", "ask"],
        "accept-edits": ["allow", "ask", "allow", "ask"],
        "read-only": ["allow", "deny", "deny", "deny"],
        "auto": ["allow", "allow", "allow", "allow"],
        "plan": ["allow", "deny", "deny", "deny"],
    }
    seen = {}
    for name in modes.NAMES:
        modes.set_mode(name)
        assert modes.current() == name
        seen[name] = [permissions.check(tool, args)[0] for tool, args in four_calls(fresh, tmp_path)]
    assert seen == expected
    assert permissions.check("bash", {"command": "python x.py"}) == ("deny", "plan mode: only read-only commands run before the plan is approved: python x.py")

    modes.set_mode("read-only")
    assert permissions.check("bash", {"command": "python x.py"}) == ("deny", "read-only mode: run: python x.py")
    assert permissions.check("write_file", {"path": "inside.txt", "content": ""}) == ("deny", "read-only mode: write_file inside.txt")
    modes.set_mode("auto")
    assert permissions.check("bash", {"command": "python x.py"}) == ("allow", "auto mode: run: python x.py")
    assert permissions.check("bash", {"command": "ls"}) == ("allow", "run: ls")  # the rules said allow; the mode had nothing to change


def test_accept_edits_keeps_its_promise_when_the_rules_would_ask(fresh, monkeypatch):
    """With the shipped rules an edit inside the project already runs. The mode is the guarantee when they change."""
    rules = permissions.rules
    monkeypatch.setattr(permissions, "rules", lambda name, args: ("ask", f"{name}: {args.get('path')}") if name == "write_file" else rules(name, args))
    inside = {"path": str(fresh / "a.txt"), "content": ""}
    verdicts = {}
    for name in ("default", "accept-edits", "read-only", "auto"):
        modes.set_mode(name)
        verdicts[name] = permissions.check("write_file", inside)[0]
    assert verdicts == {"default": "ask", "accept-edits": "allow", "read-only": "deny", "auto": "allow"}
    assert modes.apply("accept-edits", "edit-outside", "ask") == "ask"  # outside the project still asks
    assert modes.apply("accept-edits", "bash", "ask") == "ask"          # the bash rules are unchanged


def test_deny_rules_and_session_nevers_survive_auto(fresh, monkeypatch):
    never_prompt(monkeypatch)
    modes.set_mode("auto")
    assert permissions.check("bash", {"command": "rm -rf build"}) == ("deny", "run: rm -rf build")
    assert permissions.check("bash", {"command": "ls && git push"})[0] == "deny"
    assert tools.execute(call("t1", "bash", {"command": "sudo make install"}))[1] == "Blocked by policy: run: sudo make install"

    permissions.remember("bash", {"command": "make"}, "deny")                  # a `never` answer from step 35
    permissions.remember("computer_act", {"action": "click"}, "deny")
    assert permissions.check("bash", {"command": "make test"}) == ("deny", "run: make test")
    assert permissions.check("computer_act", {"action": "click", "x": 1, "y": 2}) == ("deny", "deny for this session: computer_act")
    assert modes.apply("auto", "bash", "deny") == "deny"

    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    assert tools.execute(call("t2", "bash", {"command": "python x.py"}))[1] == "ran python x.py"  # an ask ran without a prompt


def test_read_only_lets_exploration_run_and_denies_the_rest(fresh, monkeypatch):
    never_prompt(monkeypatch)
    modes.set_mode("read-only")
    (fresh / "a.txt").write_text("hello", encoding="utf-8")
    assert permissions.check("bash", {"command": "cat a.txt | grep h"}) == ("allow", "run: cat a.txt | grep h")
    assert permissions.check("read_file", {"path": "a.txt"}) == ("allow", None)
    assert permissions.check("task", {"description": "x", "prompt": "y"}) == ("allow", None)
    assert permissions.check("browser_open", {"url": "https://example.org"}) == ("deny", "read-only mode: open in the browser: https://example.org")

    args, result = tools.execute(call("t1", "write_file", {"path": "a.txt", "content": "changed"}))
    assert result == "Blocked by policy: read-only mode: write_file a.txt"
    assert (fresh / "a.txt").read_text(encoding="utf-8") == "hello"
    assert tools.execute(call("t2", "read_file", {"path": "a.txt"}))[1] == "hello"


def test_the_mode_command_lists_and_switches(fresh, monkeypatch):
    seen = notes(monkeypatch)
    messages = [{"role": "system", "content": "s"}]

    assert commands.handle("/mode", messages) is messages
    assert seen[-1].splitlines()[0].startswith("* default")
    assert [line[2:].split()[0] for line in seen[-1].splitlines()] == list(modes.NAMES)

    commands.handle("/mode auto", messages)
    assert modes.CURRENT == "auto" and seen[-1].startswith("auto mode:")
    commands.handle("/mode sideways", messages)
    assert modes.CURRENT == "auto" and seen[-1].startswith("unknown mode 'sideways'")
    commands.handle("/mode", messages)
    assert "* auto" in seen[-1] and "  default" in seen[-1]


def test_plan_is_a_mode_and_the_old_mode_comes_back_on_approval(fresh, monkeypatch):
    notes(monkeypatch)
    messages = [{"role": "system", "content": "s"}]
    commands.handle("/mode accept-edits", messages)
    commands.handle("/mode plan", messages)
    assert plan.MODE == "plan" and modes.current() == "plan" and modes.CURRENT == "accept-edits"
    assert permissions.check("write_file", {"path": "x.txt", "content": ""}) == ("deny", "plan mode: write_file is not available until the plan is approved")
    assert "mode: plan" in context.reminder()["content"]

    plan.approve({"goal": "g", "steps": [{"title": "do it", "files": [], "actions": []}], "risks": []})
    assert plan.MODE == "act" and modes.current() == "accept-edits"

    commands.handle("/plan", messages)            # the step 28 command still enters plan mode...
    assert modes.current() == "plan"
    commands.handle("/mode read-only", messages)  # ...and picking a mode leaves it
    assert plan.MODE == "act" and modes.current() == "read-only"
    commands.handle("/act", messages)
    assert modes.current() == "read-only"         # /act leaves plan mode; it does not reset the approval mode


def test_the_cli_flag_the_banner_and_the_env_block_show_the_mode(fresh, monkeypatch):
    cli = agent.parser().parse_args(["--mode", "read-only"])
    assert cli.mode == "read-only"
    with pytest.raises(SystemExit):
        agent.parser().parse_args(["--mode", "sideways"])

    modes.set_mode(cli.mode)
    out = io.StringIO()
    monkeypatch.setattr(ui, "console", Console(file=out, width=200, force_terminal=False))
    ui.banner(sandbox.name(), modes.current())
    assert "mode: read-only" in out.getvalue() and "/mode" in out.getvalue()
    assert "mode: read-only\n" in context.reminder()["content"]


# ---------------------------------------------------------------- the loop


def test_the_mode_flag_auto_runs_a_turn_without_a_prompt(fresh, tmp_path, monkeypatch, capsys):
    never_prompt(monkeypatch)
    monkeypatch.setattr(ui, "ask", lambda: pytest.fail("print mode must not open the input loop"))
    outside = tmp_path / "outside.txt"
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    fake_model(monkeypatch, [
        use(call("t1", "bash", {"command": "python x.py"}), call("t2", "write_file", {"path": str(outside), "content": "out"})),
        say("both ran"),
    ])
    monkeypatch.setattr(sys, "argv", ["harness", "--mode", "auto", "-p", "run it"])

    with pytest.raises(SystemExit) as stop:
        agent.main()

    assert stop.value.code == 0
    assert capsys.readouterr().out.strip().splitlines()[-1] == "both ran"
    assert outside.read_text(encoding="utf-8") == "out"
    assert modes.CURRENT == "auto"


def test_loop_smoke_accept_edits_then_read_only(fresh, monkeypatch):
    seen = notes(monkeypatch)
    prompts = typed(monkeypatch, "y")
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    fake_model(monkeypatch, [
        use(call("t1", "write_file", {"path": "hello.py", "content": "print('hi')\n"})),
        use(call("t2", "bash", {"command": "python hello.py"})),
        say("written and run"),
        use(call("t3", "str_replace", {"path": "hello.py", "old_str": "hi", "new_str": "bye"})),
        say("the edit was blocked"),
    ])
    messages = [{"role": "system", "content": "s"}]

    commands.handle("/mode accept-edits", messages)
    messages = agent.turn(messages, "write hello.py and run it")
    assert messages[3]["content"] == "Wrote hello.py"
    assert messages[5]["content"] == "ran python hello.py"
    assert prompts == ["  allow? (y/n/a=always/never)> "]  # the edit did not ask; the command did
    assert messages[-1]["content"] == "written and run"

    commands.handle("/mode read-only", messages)
    messages = agent.turn(messages, "change it")
    assert messages[-2]["content"] == "Blocked by policy: read-only mode: str_replace hello.py"
    assert (fresh / "hello.py").read_text(encoding="utf-8") == "print('hi')\n"
    assert len(prompts) == 1  # read-only never asked
    assert "read-only mode:" in seen[-1] or seen[-1].startswith("accept-edits mode:")
