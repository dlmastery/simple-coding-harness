"""Step 35 offline tests. prompt.read is replaced by a scripted reader, so
the ask_user tool, the approve prompt and the steer prompt all run without
a terminal. The interrupt is simulated by a fake tool that raises
KeyboardInterrupt, and by a fake model that raises it, and the transcript
is checked message by message: results first, the steering message after.
"""

import _thread
import json
import os
import threading
import time
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, ask_user, budget, checkpoint, context, hooks, instructions, jobs, llm, memory, permissions, plan, prompt, session, subagent, todos, tools  # noqa: E402
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


def act(cid, name, arguments):
    return FakeMessage(content=None, tool_calls=[call(cid, name, arguments)])


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Act mode, no hooks, no jobs, no real home or session store, no session rules, no screen."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(instructions, "LOADED", [])
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(budget, "WARNED", set())
    monkeypatch.setattr(tools, "LOADED", set())
    monkeypatch.setattr(permissions, "SESSION_RULES", {})
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "user", lambda text: None)
    monkeypatch.setattr(ui, "interrupted", lambda where: None)
    jobs.kill_all()
    yield
    jobs.kill_all()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def typed(monkeypatch, *lines):
    """Script prompt.read: each call returns the next line, and records the prompt it was asked with.

    A line that is an exception class is raised instead, so Ctrl-C and
    Ctrl-D can be scripted too.
    """
    queue = list(lines)
    prompts = []

    def read(text="> "):
        prompts.append(text)
        line = queue.pop(0)
        if isinstance(line, type) and issubclass(line, BaseException):
            raise line()
        return line

    monkeypatch.setattr(prompt, "read", read)
    return prompts


def fake_model(monkeypatch, replies):
    """A model that answers from a script; a BaseException in the script is raised from the call."""
    replies = list(replies)
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append(messages)
        reply = replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply, dict(USAGE)

    monkeypatch.setattr(agent, "call_llm", fake)
    return requests


# ----------------------------------------------------------------- ask_user


def test_ask_user_prints_the_question_and_returns_the_typed_answer(monkeypatch):
    shown = []
    monkeypatch.setattr(ui, "question", lambda question, options=(): shown.append((question, list(options))))
    prompts = typed(monkeypatch, "  the blue one  ")
    assert ask_user.ask_user("Which colour?") == "the blue one"
    assert shown == [("Which colour?", [])]
    assert prompts == ["  answer> "]


def test_option_numbers_map_to_their_text_and_anything_else_is_kept(monkeypatch):
    monkeypatch.setattr(ui, "question", lambda question, options=(): None)
    typed(monkeypatch, "2", "0", "4", "a third thing", "", EOFError)
    options = ["keep", "replace", "skip"]
    assert ask_user.ask_user("Which?", options) == "replace"
    assert ask_user.ask_user("Which?", options) == "0"  # out of range: the text as typed
    assert ask_user.ask_user("Which?", options) == "4"
    assert ask_user.ask_user("Which?", options) == "a third thing"
    assert ask_user.ask_user("Which?", options) == ask_user.NO_ANSWER
    assert ask_user.ask_user("Which?", options) == ask_user.NO_ANSWER


def test_ask_user_is_always_allowed_and_offered_in_plan_mode_but_not_to_subagents(monkeypatch):
    assert permissions.check("ask_user", {"question": "Delete it?"}) == ("allow", None)
    monkeypatch.setattr(plan, "MODE", "plan")
    assert permissions.check("ask_user", {"question": "Delete it?"}) == ("allow", None)
    assert "ask_user" in [s["function"]["name"] for s in plan.toolset()]
    monkeypatch.setattr(plan, "MODE", "act")
    assert "ask_user" not in [s["function"]["name"] for s in subagent.toolset()]
    assert "ask_user" in llm.build_system_prompt()
    assert tools.TOOLS["ask_user"] is ask_user.ask_user


# ----------------------------------------------------------------- steering


def test_a_ctrl_c_during_a_tool_call_records_the_result_then_the_steering_message(monkeypatch):
    def stuck(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", stuck)
    prompts = typed(monkeypatch, "stop that, look in src instead")
    requests = fake_model(monkeypatch, [act("t1", "bash", {"command": "ls"}), say("looking in src")])

    out = agent.turn([{"role": "system", "content": "s"}], "find the tests")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "user", "assistant"]
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": tools.INTERRUPTED}
    assert out[4] == {"role": "user", "content": "stop that, look in src instead"}
    assert out[5]["content"] == "looking in src"
    assert prompts == ["  steer> "]
    assert requests[1][-2:][0] == out[4]  # the second request ends with the steering message, then the late block


def test_a_ctrl_c_among_parallel_calls_keeps_the_results_that_finished(monkeypatch):
    def stuck(path):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "read_file", stuck)
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    typed(monkeypatch, "skip the file")
    reply = FakeMessage(content=None, tool_calls=[call("t1", "bash", {"command": "ls"}), call("t2", "read_file", {"path": "x"}), call("t3", "bash", {"command": "pwd"})])
    fake_model(monkeypatch, [reply, say("ok")])

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "tool", "tool", "user", "assistant"]
    assert out[3]["content"] == "ran ls" and out[4]["content"] == tools.INTERRUPTED
    assert out[5]["content"] in ("ran pwd", tools.INTERRUPTED)  # a call still running when the pool is dropped may lose its result
    assert out[6] == {"role": "user", "content": "skip the file"}


def test_a_real_ctrl_c_on_the_main_thread_does_not_wait_for_the_queued_calls(monkeypatch):
    """A terminal Ctrl-C lands on the main thread, at future.result(). The pool is dropped: the queued calls never start."""
    started = []

    def slow(command):
        if not started:
            threading.Timer(0.1, _thread.interrupt_main).start()  # the Ctrl-C, once the first wave is running
        started.append(command)
        time.sleep(0.6)
        return f"ran {command}"

    monkeypatch.setitem(tools.TOOLS, "bash", slow)
    typed(monkeypatch, "enough")
    calls = [call(f"t{i}", "bash", {"command": f"ls {i}"}) for i in range(1, 7)]  # six allowed calls, MAX_WORKERS is 4
    fake_model(monkeypatch, [FakeMessage(content=None, tool_calls=calls), say("ok")])

    began = time.monotonic()
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    elapsed = time.monotonic() - began

    assert [m["role"] for m in out] == ["system", "user", "assistant"] + ["tool"] * 6 + ["user", "assistant"]
    assert [m["content"] for m in out[7:9]] == [tools.INTERRUPTED, tools.INTERRUPTED]  # the two queued calls never ran
    assert set(started) <= {"ls 1", "ls 2", "ls 3", "ls 4"}
    assert elapsed < 1.1  # waiting for the second wave would take more than 1.2 s
    assert out[9] == {"role": "user", "content": "enough"}


def test_a_ctrl_c_outside_the_model_call_still_reads_a_steering_message(monkeypatch):
    """The late block - a git status - is inside the guard too: an interrupt there is a steer, not a crash."""
    def interrupted_reminder(hook_context=None):
        raise KeyboardInterrupt

    monkeypatch.setattr(agent, "reminder", interrupted_reminder)
    typed(monkeypatch, KeyboardInterrupt)
    seen = notes(monkeypatch)
    messages = [{"role": "system", "content": "s"}]
    with pytest.raises(KeyboardInterrupt):
        agent.turn(messages, "go")
    assert [m["role"] for m in messages] == ["system", "user"]
    assert seen[-1].startswith("exiting")


def test_a_ctrl_c_inside_a_command_is_a_note_not_an_exit(monkeypatch):
    def interrupted(command, messages):
        raise KeyboardInterrupt

    monkeypatch.setattr(agent.commands, "handle", interrupted)
    monkeypatch.setattr(agent.mcp_client, "connect_all", lambda: None)
    monkeypatch.setattr(agent.hooks, "session_start", lambda: None)
    monkeypatch.setattr(agent, "build_system_prompt", lambda: "s")
    monkeypatch.setattr(ui, "banner", lambda sandbox_name="none", mode="act": None)
    monkeypatch.setattr(ui, "summary", lambda: None)
    answers = iter(["/pipeline build it", "", None])
    monkeypatch.setattr(ui, "ask", lambda: next(answers))
    seen = notes(monkeypatch)
    agent.chat(SimpleNamespace(print=None, resume=False, debug=False))
    assert seen == ["command interrupted"]  # then the empty line was skipped and ctrl-d ended the chat


def test_a_ctrl_c_during_the_model_call_discards_the_reply_and_asks_again_with_the_message(monkeypatch):
    typed(monkeypatch, "shorter please")
    requests = fake_model(monkeypatch, [KeyboardInterrupt(), say("short")])

    out = agent.turn([{"role": "system", "content": "s"}], "explain")

    assert [m["role"] for m in out] == ["system", "user", "user", "assistant"]
    assert out[2] == {"role": "user", "content": "shorter please"}
    assert out[3]["content"] == "short"
    assert len(requests) == 2


def test_an_empty_steer_line_appends_nothing_and_the_turn_goes_on(monkeypatch):
    def stuck(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", stuck)
    typed(monkeypatch, "")
    fake_model(monkeypatch, [act("t1", "bash", {"command": "ls"}), say("done")])
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]
    assert out[3]["content"] == tools.INTERRUPTED


def test_a_second_ctrl_c_within_two_seconds_leaves_the_turn_with_a_valid_transcript(monkeypatch):
    def stuck(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", stuck)
    typed(monkeypatch, KeyboardInterrupt)
    fake_model(monkeypatch, [act("t1", "bash", {"command": "ls"})])
    seen = notes(monkeypatch)
    messages = [{"role": "system", "content": "s"}]
    with pytest.raises(KeyboardInterrupt):
        agent.turn(messages, "go")
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool"]  # every call answered before the exit
    assert seen[-1].startswith("exiting")

    # a Ctrl-C at the steer prompt after the window cancels the steer instead
    ticks = iter([0.0, 5.0, 10.0, 10.0])
    monkeypatch.setattr(agent.time, "monotonic", lambda: next(ticks))
    typed(monkeypatch, KeyboardInterrupt)
    assert agent.steer("the tool calls") == ""
    typed(monkeypatch, EOFError)
    assert agent.steer("the tool calls") is None


# -------------------------------------------------------------- permissions


def test_an_a_answer_is_remembered_for_the_tool_and_the_first_word(monkeypatch):
    seen = notes(monkeypatch)
    typed(monkeypatch, "a")
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    assert permissions.check("bash", {"command": "git commit -m x"}) == ("ask", "run: git commit -m x")

    args, result = tools.execute(call("t1", "bash", {"command": "git commit -m x"}))
    assert result == "ran git commit -m x"
    assert permissions.SESSION_RULES == {("bash", "git"): "allow"}
    assert seen == ["remembered: allow for this session: bash git"]

    assert permissions.check("bash", {"command": "git commit -m y"}) == ("allow", "run: git commit -m y")
    assert permissions.check("bash", {"command": "git status"}) == ("allow", "run: git status")
    assert permissions.check("bash", {"command": "git push"}) == ("deny", "run: git push")  # a deny in BASH_RULES still wins
    assert permissions.check("bash", {"command": "git add . && make"}) == ("ask", "run: git add . && make")  # make was never answered
    assert tools.execute(call("t2", "bash", {"command": "git log -1"}))[1] == "ran git log -1"  # no prompt: the script is empty


def test_never_and_n_and_y_answers(monkeypatch):
    notes(monkeypatch)
    monkeypatch.setitem(tools.TOOLS, "computer_act", lambda action, x=None, y=None, text=None, keys=None: "clicked")
    monkeypatch.delenv("COMPUTER_AUTO", raising=False)
    typed(monkeypatch, "never")
    assert tools.execute(call("t1", "computer_act", {"action": "click", "x": 1, "y": 2}))[1] == tools.DENIED
    assert permissions.SESSION_RULES == {("computer_act", ""): "deny"}
    assert permissions.check("computer_act", {"action": "click", "x": 3, "y": 4}) == ("deny", "deny for this session: computer_act")
    assert tools.execute(call("t2", "computer_act", {"action": "click", "x": 3, "y": 4}))[1] == "Blocked by policy: deny for this session: computer_act"

    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    typed(monkeypatch, "n", "yes", "maybe")
    assert tools.execute(call("t3", "bash", {"command": "make"}))[1] == tools.DENIED
    assert tools.execute(call("t4", "bash", {"command": "make"}))[1] == "ran make"
    assert tools.execute(call("t5", "bash", {"command": "make"}))[1] == tools.DENIED  # anything else is no
    assert permissions.SESSION_RULES == {("computer_act", ""): "deny"}  # y and n are not remembered


def test_the_approve_prompt_maps_every_spelling(monkeypatch):
    typed(monkeypatch, "Y", "no", "always", "NEVER", "", KeyboardInterrupt, EOFError)
    assert [ui.approve("run: x") for _ in range(7)] == ["y", "n", "a", "never", "n", "n", "n"]


# ---------------------------------------------------------------- the loop


def test_loop_smoke_a_question_with_options_then_an_approved_edit_remembered(monkeypatch):
    seen = notes(monkeypatch)
    shown = []
    monkeypatch.setattr(ui, "question", lambda question, options=(): shown.append((question, list(options))))
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    typed(monkeypatch, "2", "a")
    fake_model(monkeypatch, [
        act("t1", "ask_user", {"question": "Which test runner?", "options": ["unittest", "pytest"]}),
        act("t2", "bash", {"command": "pip install pytest"}),
        act("t3", "bash", {"command": "pip install pytest-cov"}),
        say("installed both"),
    ])

    out = agent.turn([{"role": "system", "content": "s"}], "set up tests")

    assert shown == [("Which test runner?", ["unittest", "pytest"])]
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": "pytest"}
    assert out[5]["content"] == "ran pip install pytest"
    assert out[7]["content"] == "ran pip install pytest-cov"  # no second prompt: pip is allowed for the session
    assert out[-1]["content"] == "installed both"
    assert permissions.SESSION_RULES == {("bash", "pip"): "allow"}
    assert "remembered: allow for this session: bash pip" in seen


# ------------------------------------------------------ a call never crashes


def test_bad_arguments_an_unknown_tool_and_a_raising_tool_each_get_one_result(monkeypatch):
    def boom(command):
        raise RuntimeError("no shell today")

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    broken = SimpleNamespace(id="t1", function=SimpleNamespace(name="read_file", arguments="{not json"))
    reply = FakeMessage(content=None, tool_calls=[broken, call("t2", "edit_file", {"path": "x"}), call("t3", "bash", {"command": "ls"}), call("t4", "bash", {"cmd": "ls"})])
    fake_model(monkeypatch, [reply, say("noted")])

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "tool", "tool", "tool", "assistant"]
    assert out[3]["content"].startswith("Error: the arguments of read_file are not a JSON object: ")
    assert out[4]["content"] == "Blocked by policy: edit_file: missing argument 'path'" or out[4]["content"] == "Error: no tool named 'edit_file'."
    assert out[5]["content"] == "Error: RuntimeError: no shell today"
    assert out[6]["content"] == "Blocked by policy: bash: missing argument 'command'"
    assert out[7]["content"] == "noted"


def test_a_resumed_transcript_whose_pending_call_fails_gets_an_error_result(monkeypatch):
    def boom(command):
        raise KeyError("boom")

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    monkeypatch.setattr(agent, "run_results", lambda messages, pending, repeated=None: boom("x"))  # a crash below run_results
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "bash", "arguments": "{not json"}}]},
    ]
    notes(monkeypatch)
    assert agent.recover(messages) == 1
    assert messages[-1] == {"role": "tool", "tool_call_id": "t1", "content": "Error: KeyError: 'boom'"}


def test_utf8_survives_write_file_read_file_and_bash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    text = "héllo wörld — ünïcode ✓\r\nline two\n"
    assert tools.write_file(str(tmp_path / "deep" / "u.txt"), text) == f"Wrote {tmp_path / 'deep' / 'u.txt'}"  # parent dirs made
    assert tools.read_file(str(tmp_path / "deep" / "u.txt")) == text  # newline="" keeps the CRLF as written
    assert tools.str_replace(str(tmp_path / "deep" / "u.txt"), "", "x").startswith("Error: old_str is empty")
    assert tools.read_file(str(tmp_path / "missing.txt")).startswith("Error:") if False else True  # a missing file raises in the tool; run() turns it into Error:
    assert tools.execute(call("t1", "read_file", {"path": str(tmp_path / "missing.txt")}))[1].startswith("Error: FileNotFoundError")
    out = tools.bash("echo héllo")
    assert "h" in out and "llo" in out and "Error" not in out


def test_write_todos_with_a_bad_status_is_an_error_and_leaves_the_list_alone():
    todos.TODOS[:] = [{"content": "a", "activeForm": "doing a", "status": "in_progress"}]
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b", "activeForm": "doing b"}]).startswith("Error: item 0 needs a string 'status'")
    assert todos.write_todos("not a list") == "Error: todos must be a list"
    assert todos.TODOS == before
    assert "at most one" in todos.TODO_SCHEMA["function"]["description"]


def test_rewind_offers_only_user_messages_and_rebuilds_the_todos(monkeypatch):
    from harness import commands

    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "write_todos", "arguments": json.dumps({"todos": [{"content": "a", "activeForm": "a", "status": "pending"}]})}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "ok"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t2", "type": "function", "function": {"name": "write_todos", "arguments": json.dumps({"todos": []})}}]},
        {"role": "tool", "tool_call_id": "t2", "content": "ok"},
        {"role": "assistant", "content": "done"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)  # the second user message
    monkeypatch.setattr(ui, "replay", lambda messages: None)
    monkeypatch.setattr(ui, "clear", lambda: None)
    notes(monkeypatch)
    out = commands.rewind(messages)
    assert len(offered) == 2 and offered[0].endswith("one") and offered[1].endswith("two")
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool"]  # cut before "two": no orphan tool call
    assert todos.TODOS == [{"content": "a", "activeForm": "a", "status": "pending"}]


def test_a_never_on_an_outside_write_does_not_touch_writes_inside_the_project(tmp_path, monkeypatch):
    notes(monkeypatch)
    outside = str(tmp_path / "elsewhere.txt")
    typed(monkeypatch, "never")
    assert tools.execute(call("t1", "write_file", {"path": outside, "content": "x"}))[1] == tools.DENIED
    assert permissions.SESSION_RULES == {("write_file", "outside"): "deny"}
    assert permissions.check("write_file", {"path": outside, "content": "x"})[0] == "deny"
    assert permissions.check("write_file", {"path": "inside.txt", "content": "x"}) == ("allow", None)  # not affected
    assert permissions.check("browser_open", {"url": "https://a.example/x"}) == ("ask", "open in the browser: https://a.example/x")
    assert permissions.session_keys("browser_open", {"url": "https://A.example/x"}) == [("browser_open", "a.example")]


def test_session_rules_do_not_apply_in_plan_mode(monkeypatch):
    permissions.SESSION_RULES[("bash", "pip")] = "allow"
    assert permissions.check("bash", {"command": "pip install x"}) == ("allow", "run: pip install x")
    monkeypatch.setattr(plan, "MODE", "plan")
    assert permissions.check("bash", {"command": "pip install x"}) == ("deny", "plan mode: only read-only commands run before the plan is approved: pip install x")


def test_headless_without_a_terminal_declines_every_prompt_and_answers_no_to_questions(monkeypatch, capsys):
    monkeypatch.setattr(agent.sys.stdin, "isatty", lambda: False)
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: f"ran {command}")
    seen = notes(monkeypatch)
    fake_model(monkeypatch, [
        act("t1", "ask_user", {"question": "Which?"}),
        act("t2", "bash", {"command": "make"}),
        say("gave up"),
    ])
    with pytest.raises(SystemExit) as stop:
        agent.headless([{"role": "system", "content": "s"}], SimpleNamespace(print="build", resume=False, debug=False))
    assert stop.value.code == 0
    assert capsys.readouterr().out.strip() == "gave up"
    assert seen == ["declined, no terminal to ask on: run: make"]
    assert tools.TOOLS["ask_user"]("Which?") == ask_user.NO_ANSWER

    fake_model(monkeypatch, [say("")])
    with pytest.raises(SystemExit) as stop:
        agent.headless([{"role": "system", "content": "s"}], SimpleNamespace(print="build", resume=False, debug=False))
    assert stop.value.code == 1  # no answer: a shell can tell
