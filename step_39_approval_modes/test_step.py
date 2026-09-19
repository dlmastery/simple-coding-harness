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

from harness import agent, checkpoint, commands, context, hooks, instructions, jobs, llm, mcp_client, memory, modes, permissions, plan, prompt, sandbox, session, subagent, todos, tools  # noqa: E402
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
    monkeypatch.setattr(session, "ENABLED", True)
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


# ------------------------------------------------- round 2: every call gets a result


def scripted_model(monkeypatch, replies):
    """A fake call_llm that answers from a list, repeating the last reply."""
    replies = list(replies)
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append(messages)
        return (replies.pop(0) if len(replies) > 1 else replies[0]), dict(USAGE)

    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    return requests


def test_bad_tool_calls_each_get_a_result_and_the_loop_goes_on(fresh, monkeypatch):
    """Malformed arguments, an unknown tool and a raising tool: one tool message each, then the model answers."""
    broken = SimpleNamespace(id="b1", function=SimpleNamespace(name="bash", arguments="{broken"))
    scripted_model(monkeypatch, [
        use(broken, call("b2", "no_such_tool", {"x": 1}), call("b3", "read_file", {"path": "missing.txt"}), call("b4", "bash", {})),
        say("all four came back as errors"),
    ])
    messages = agent.turn([{"role": "system", "content": "s"}], "go")
    results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
    assert results["b1"].startswith("Error: the arguments of bash are not a JSON object:")
    assert results["b2"] == "Error: no tool named 'no_such_tool'."
    assert results["b3"].startswith("Error: FileNotFoundError:")
    assert results["b4"] == "Blocked by policy: bash: missing argument 'command'"
    assert messages[-1] == {"role": "assistant", "content": "all four came back as errors"}
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "tool", "tool", "tool", "assistant"]


def test_utf8_round_trip_through_the_file_tools_and_bash(fresh, monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: "y")  # python -c is rated ask
    text = "héllo ✓ — ünïcode\r\nline two\n"
    assert tools.write_file("u.txt", text) == "Wrote u.txt"
    assert tools.read_file("u.txt") == text  # newline="" keeps the CRLF as it was
    assert (fresh / "u.txt").read_bytes() == text.encode("utf-8")
    out = tools.bash(f'{sys.executable} -c "print(\'h\\u00e9llo \\u2713\')"')
    assert out.strip() == "héllo ✓"
    assert tools.write_file("deep/er/new.txt", "x") == "Wrote deep/er/new.txt" and (fresh / "deep" / "er" / "new.txt").exists()
    assert tools.str_replace("u.txt", "", "y").startswith("Error: old_str is empty")


def test_a_timeout_returns_the_output_so_far(fresh, monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: "y")
    run = sandbox.run
    monkeypatch.setattr(tools.sandbox, "run", lambda command: run(command, timeout=1))
    result = tools.bash(f'{sys.executable} -c "print(\'first line\', flush=True); import time; time.sleep(30)"')
    assert result.startswith("Timed out after 1s and was killed. Output so far:")
    assert "first line" in result


def test_write_todos_rejects_a_bad_list_and_keeps_the_old_one(fresh):
    todos.TODOS[:] = [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]
    assert todos.write_todos([{"content": "x", "activeForm": "y", "status": "sideways"}]).startswith("Error: item 0 has status 'sideways'")
    assert todos.write_todos([{"content": "x"}]).startswith("Error: item 0 needs a string 'activeForm'")
    assert todos.write_todos("nope") == "Error: todos must be a list of items."
    assert todos.TODOS == [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]
    assert todos.write_todos([]) == "Todo list cleared." and todos.TODOS == []


def test_rewind_offers_user_messages_only_so_no_tool_call_is_orphaned(fresh, monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "r"},
        {"role": "assistant", "content": "done one"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "done two"},
    ]
    session.save(messages)
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "replay", lambda m: None)
    monkeypatch.setattr(ui, "resumed", lambda m, label="": None)
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    kept = commands.handle("/rewind", messages)
    assert offered == ["turn 1    one", "turn 2    two"]  # only user rows
    assert [m["role"] for m in kept] == ["system", "user", "assistant", "tool", "assistant"]
    for i, m in enumerate(kept):
        if m.get("tool_calls"):
            assert kept[i + 1]["role"] == "tool"


def test_recover_turns_a_failure_into_error_results(fresh, monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "p1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "ls"})}}]},
    ]
    monkeypatch.setattr(agent, "run_results", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert agent.recover(messages) == 1
    assert messages[-1] == {"role": "tool", "tool_call_id": "p1", "content": "Error: RuntimeError: boom"}
    assert agent.recover(messages) == 0  # nothing left unanswered


def test_read_only_really_denies_writes_and_ignores_session_rules(fresh, monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: pytest.fail(f"the approve prompt was opened: {reason}"))
    permissions.remember("bash", {"command": "make"}, "allow")  # an `always` from before
    modes.set_mode("read-only")
    assert permissions.check("bash", {"command": "echo hi > pwned.txt"})[0] == "deny"
    assert permissions.check("bash", {"command": "cat a.txt | tee b.txt"})[0] == "deny"
    assert permissions.check("bash", {"command": "ls $(rm -rf x)"})[0] == "deny"
    assert permissions.check("bash", {"command": "make"})[0] == "deny"  # the session rule does not apply here
    assert permissions.check("bash", {"command": "cat a.txt 2>&1 | grep h"}) == ("allow", "run: cat a.txt 2>&1 | grep h")
    assert permissions.check("remember", {"name": "x", "description": "d", "content": "c"})[0] == "deny"
    assert permissions.check("recall", {"name": "x"})[0] == "allow"
    modes.set_mode("default")
    assert permissions.check("bash", {"command": "echo hi > out.txt"})[0] == "ask"
    assert permissions.check("bash", {"command": "make"})[0] == "allow"  # and applies again in default
    assert permissions.check("bash", {"command": "env"})[0] == "ask"  # env prints the API key
    assert permissions.check("bash", {"command": "find . -name x -delete"})[0] == "ask"
    assert permissions.split_command("a 2>&1 | b\nc") == ["a 2>&1", "b", "c"]


def test_the_mode_is_logged_and_comes_back_on_load(fresh):
    modes.set_mode("auto")
    session.save([{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}])
    modes.set_mode("default", log=False)
    loaded = session.load("test-session")
    assert modes.CURRENT == "auto" and [m["role"] for m in loaded] == ["system", "user"]
    assert session.all_sessions()[0]["title"] == "hi"


def test_headless_without_a_terminal_denies_every_ask_and_exits_one_without_an_answer(fresh, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(ui, "ask", lambda: pytest.fail("print mode must not open the input loop"))
    scripted_model(monkeypatch, [use(call("t1", "bash", {"command": "python x.py"})), say("")])
    monkeypatch.setattr(sys, "argv", ["harness", "-p", "run it"])
    with pytest.raises(SystemExit) as stop:
        agent.main()
    assert stop.value.code == 1  # no answer text: a script can see the run gave nothing
    assert not session.path_for(session.CURRENT).exists()  # a one-off question leaves no session file
    err = capsys.readouterr().err
    assert "denied (no terminal to ask on)" in err


def test_exit_words_and_eof_end_the_chat(fresh, monkeypatch):
    answers = iter(["", "/exit"])
    monkeypatch.setattr(ui, "ask", lambda: next(answers))
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    monkeypatch.setattr(ui, "summary", lambda: None)
    monkeypatch.setattr(agent, "turn", lambda *a, **k: pytest.fail("an empty line must not start a turn"))
    agent.chat(agent.parser().parse_args([]))
    monkeypatch.setattr(ui, "ask", lambda: None)  # ctrl-d
    agent.chat(agent.parser().parse_args([]))


def test_a_subagent_may_only_run_what_it_was_offered(fresh, monkeypatch):
    scripted_model(monkeypatch, [use(call("s1", "write_file", {"path": "a.txt", "content": "x"})), say("blocked")])
    assert subagent.task("write a.txt") == "blocked"
    assert not (fresh / "a.txt").exists()
    args, result = tools.execute(call("s2", "write_file", {"path": "a.txt", "content": "x"}), allowed={"bash"})
    assert result == "Blocked by policy: write_file is not available to this agent"


# ------------------------------------------------- round 2: the mode binds everything


def test_read_only_binds_subagents_and_eval_too(fresh, monkeypatch):
    """A subagent in read-only mode is fenced by the same module global; --mode reaches an eval run."""
    monkeypatch.setattr(ui, "approve", lambda reason: pytest.fail(f"the approve prompt was opened: {reason}"))
    modes.set_mode("read-only")
    scripted_model(monkeypatch, [use(call("s1", "bash", {"command": "echo x > f.txt"}), call("s2", "read_file", {"path": "nope.txt"})), say("denied, then an error")])
    assert subagent.task("write f.txt") == "denied, then an error"
    assert not (fresh / "f.txt").exists()

    seen = []
    monkeypatch.setattr(agent.evaluate, "main", lambda cli: seen.append(modes.CURRENT) or 0)
    monkeypatch.setattr(agent.hooks, "run_hooks", lambda *a, **k: None)
    with pytest.raises(SystemExit) as done:
        agent.main(["--mode", "auto", "eval", "suite"])
    assert done.value.code == 0 and seen == ["auto"]  # applied before the suite ran
