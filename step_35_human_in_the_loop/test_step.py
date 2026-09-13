"""Step 35 offline tests. prompt.read is replaced by a scripted reader, so
the ask_user tool, the approve prompt and the steer prompt all run without
a terminal. The interrupt is simulated by a fake tool that raises
KeyboardInterrupt, and by a fake model that raises it, and the transcript
is checked message by message: results first, the steering message after.
"""

import json
import os
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
    assert [m["content"] for m in out[3:6]] == ["ran ls", tools.INTERRUPTED, "ran pwd"]
    assert out[6] == {"role": "user", "content": "skip the file"}


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
