"""Step 40 offline tests. The agent definitions are read from this step's
.agents/agents directory; the loop tests drive agent.turn and
commands.handle with a fake model that answers by the agent named in the
system prompt. Nothing is launched.
"""

import json
import os
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, agents, checkpoint, commands, context, handoff, hooks, instructions, jobs, llm, mcp_client, memory, modes, permissions, plan, sandbox, session, subagent, todos, tools  # noqa: E402
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
    """A temp workspace as cwd, temp stores, no hooks, no jobs, the shipped agents, the default agent active."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(permissions, "PROJECT", workspace.resolve())
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
    handoff.reset()
    jobs.kill_all()
    yield workspace
    jobs.kill_all()
    handoff.reset()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def handoffs_shown(monkeypatch):
    """Capture every handoff line the UI draws."""
    seen = []
    monkeypatch.setattr(ui, "handoff", lambda previous, name, reason="": seen.append((previous, name, reason)))
    return seen


def role_of(messages):
    """Which agent a request is for, read from the first line of its system prompt."""
    first = messages[0]["content"].strip().splitlines()[0]
    for name in ("router", "coder", "reviewer", "planner", "worker"):
        if f"You are the {name}" in first:
            return name
    return "main"


class Scripted:
    """A thread-safe fake call_llm: one reply list per role, and a log of every request."""

    def __init__(self, **queues):
        self.queues = {role: list(replies) for role, replies in queues.items()}
        self.requests = []  # (role, tools offered, system prompt) per call
        self.lock = threading.Lock()

    def __call__(self, messages, tools=None, on_delta=None):
        role = role_of(messages)
        with self.lock:
            self.requests.append((role, [s["function"]["name"] for s in tools or []], messages[0]["content"]))
            replies = self.queues[role]
            reply = replies.pop(0) if len(replies) > 1 else replies[0]
        return reply, USAGE

    def install(self, monkeypatch):
        monkeypatch.setattr(agent, "call_llm", self)
        monkeypatch.setattr(llm, "call_llm", self)
        return self


def names(schemas):
    return [s["function"]["name"] for s in schemas]


def start():
    """The message list chat() starts with."""
    return [{"role": "system", "content": llm.build_system_prompt()}]


# ------------------------------------------------------------- definitions


def test_the_shipped_definitions_carry_handoff_lists():
    found = agents.find_agents([STEP / ".agents" / "agents"])
    assert list(found) == ["coder", "planner", "reviewer", "router", "worker"]
    assert found["router"]["handoffs"] == ["coder", "reviewer"]
    assert found["coder"]["handoffs"] == ["reviewer"]
    assert found["reviewer"]["handoffs"] == ["coder"]
    assert found["planner"]["handoffs"] is None and found["worker"]["handoffs"] is None
    assert found["coder"]["name"] == "coder" and found["coder"]["prompt"].startswith("You are the coder")
    assert "agent_router" in tools.TOOLS and "agent_coder" in tools.TOOLS  # a definition is still a subagent tool


def test_targets_follow_the_lists():
    assert handoff.active_name() == "main"
    assert handoff.targets() == ["coder", "reviewer", "router"]  # the default agent: every definition with a list
    assert handoff.targets(agents.AGENTS["router"]) == ["coder", "reviewer"]
    assert handoff.targets(agents.AGENTS["coder"]) == ["reviewer"]
    assert handoff.targets(agents.AGENTS["planner"]) == []
    assert handoff.targets({"name": "x", "handoffs": ["coder", "nobody"]}) == ["coder"]  # a name that is no definition is dropped


def test_the_system_prompt_lists_the_targets_and_keeps_the_rest():
    default = llm.build_system_prompt()
    assert default.lstrip().startswith("You are a coding agent.")
    assert "You may hand off to:\n- coder:" in default and "- router:" in default
    coder = handoff.system_prompt(agents.AGENTS["coder"])
    assert coder.lstrip().startswith("You are the coder.")
    assert "You are a coding agent." not in coder
    assert "You may hand off to:\n- reviewer:" in coder and "- router:" not in coder
    for line in ("Your current working directory is:", "You have skills available", "agent_planner:"):
        assert line in coder  # build_system_prompt semantics: everything the default agent gets
    planner = handoff.system_prompt(agents.AGENTS["planner"])
    assert "handoff_to" not in planner  # no list, no guidance


# --------------------------------------------------------------- tool sets


def test_the_toolset_follows_the_active_definition(monkeypatch):
    offered = names(handoff.toolset())
    assert "handoff_to" == offered[-1] and "bash" in offered and "write_file" in offered
    monkeypatch.setattr(handoff, "ACTIVE", agents.AGENTS["reviewer"])
    assert names(handoff.toolset()) == ["bash", "read_file", "read_skill", "handoff_to"]
    monkeypatch.setattr(handoff, "ACTIVE", agents.AGENTS["planner"])
    assert names(handoff.toolset()) == ["bash", "read_file", "read_skill"]  # no targets: no handoff_to
    monkeypatch.setattr(plan, "MODE", "plan")
    monkeypatch.setattr(handoff, "ACTIVE", agents.AGENTS["coder"])
    assert names(handoff.toolset()) == ["bash", "read_file", "read_skill", "task", "ask_user", "submit_plan", "handoff_to"]
    assert "handoff_to" not in names(subagent.toolset()) and "handoff_to" not in names(agents.toolset(agents.AGENTS["coder"]))


# ---------------------------------------------------------------- handoffs


def test_a_scripted_handoff_changes_the_prompt_and_the_tools(fresh, monkeypatch):
    shown = handoffs_shown(monkeypatch)
    fake = Scripted(
        main=[use(call("h1", "handoff_to", {"agent": "coder", "reason": "code is wanted"}))],
        coder=[use(call("w1", "write_file", {"path": "hi.py", "content": "print('hi')\n"})), say("wrote hi.py")],
    ).install(monkeypatch)
    messages = agent.turn(start(), "write hi.py")

    assert [role for role, _, _ in fake.requests] == ["main", "coder", "coder"]
    assert messages[3] == {"role": "tool", "tool_call_id": "h1", "content": "Handing off to coder: code is wanted. The coder agent answers from the next reply on; do not answer the user yourself."}
    assert messages[-1]["content"] == "wrote hi.py" and (fresh / "hi.py").exists()
    assert handoff.active_name() == "coder" and messages[0]["content"] == handoff.system_prompt(agents.AGENTS["coder"])
    _, offered, prompt = fake.requests[1]
    assert offered == ["bash", "read_file", "read_skill", "write_file", "str_replace", "write_todos", "task", "ask_user", "handoff_to"]
    assert prompt.lstrip().startswith("You are the coder.")
    assert shown == [("main", "coder", "code is wanted")]
    lines = [json.loads(line) for line in session.path_for("test-session").read_text(encoding="utf-8").splitlines()]
    assert {"handoff": "coder"} in lines
    assert lines.index({"handoff": "coder"}) == 4  # after the system, user, assistant and tool messages


def test_a_disallowed_handoff_returns_an_error_result(fresh, monkeypatch):
    shown = handoffs_shown(monkeypatch)
    handoff.apply("coder", messages := start())
    fake = Scripted(coder=[use(call("h1", "handoff_to", {"agent": "router", "reason": "send it back"})), say("I stay")]).install(monkeypatch)
    messages = agent.turn(messages, "go")
    assert messages[3]["content"] == "Error: coder may not hand off to 'router'. You may hand off to: reviewer."
    assert handoff.active_name() == "coder" and shown == [] and [r for r, _, _ in fake.requests] == ["coder", "coder"]
    assert handoff.handoff_to("nobody", "x") == "Error: no agent named 'nobody'. You may hand off to: reviewer."
    assert handoff.handoff_to("coder", "x") == "Error: coder is already the active agent."
    assert handoff.PENDING is None


def test_session_load_applies_the_marker(fresh, monkeypatch):
    handoffs_shown(monkeypatch)
    messages = start()
    original = messages[0]["content"]
    messages.append({"role": "user", "content": "hello"})
    session.save(messages)
    handoff.switch(messages, "router", "forced")
    messages.append({"role": "assistant", "content": "routed"})
    session.save(messages)

    handoff.reset()
    loaded = session.load("test-session")
    assert handoff.active_name() == "router"
    assert loaded[0]["content"] == handoff.system_prompt(agents.AGENTS["router"]) != original
    assert [m["role"] for m in loaded] == ["system", "user", "assistant"] and loaded[-1]["content"] == "routed"

    handoff.reset()
    session.rewind_to(2)
    handoff.switch(loaded[:2], "main", "back")
    handoff.reset()
    loaded = session.load("test-session")
    assert handoff.active_name() == "main" and loaded[0]["content"] == original and len(loaded) == 2


def test_the_summary_block_survives_a_handoff(fresh, monkeypatch):
    handoffs_shown(monkeypatch)
    messages = start()
    messages[0]["content"] += "\n\n<summary>\nwhat happened before\n</summary>"
    handoff.switch(messages, "coder", "")
    assert messages[0]["content"].startswith(handoff.system_prompt(agents.AGENTS["coder"]))
    assert messages[0]["content"].endswith("<summary>\nwhat happened before\n</summary>")


# ---------------------------------------------------------------- commands


def test_agent_and_handoff_commands(fresh, monkeypatch):
    seen = notes(monkeypatch)
    shown = handoffs_shown(monkeypatch)
    messages = start()
    commands.handle("/agent", messages)
    assert seen[-1].startswith("active agent: main") and "coder, reviewer, router" in seen[-1]

    commands.handle("/handoff reviewer", messages)
    assert handoff.active_name() == "reviewer" and shown == [("main", "reviewer", "/handoff")]
    assert messages[0]["content"] == handoff.system_prompt(agents.AGENTS["reviewer"])
    commands.handle("/agent", messages)
    assert seen[-1].startswith("active agent: reviewer") and "may hand off to: coder" in seen[-1]

    commands.handle("/handoff planner", messages)  # not on the reviewer's list, but the user is in charge
    assert handoff.active_name() == "planner" and shown[-1] == ("reviewer", "planner", "/handoff")

    commands.handle("/handoff nobody", messages)
    assert seen[-1] == "no agent named 'nobody'" and handoff.active_name() == "planner"
    commands.handle("/handoff", messages)
    assert seen[-1].startswith("usage: /handoff <name>")

    commands.handle("/handoff main", messages)
    assert handoff.active_name() == "main" and messages[0]["content"] == llm.build_system_prompt()
    assert "/agent" in commands.COMMANDS and "/handoff" in commands.COMMANDS


def test_the_env_block_names_the_active_agent(monkeypatch):
    assert "agent: main\n" in context.reminder()["content"]
    monkeypatch.setattr(handoff, "ACTIVE", agents.AGENTS["coder"])
    assert "agent: coder\n" in context.reminder()["content"]


# ---------------------------------------------------------------- the loop


def test_loop_smoke_router_to_coder_to_reviewer(fresh, monkeypatch):
    """The router hands off to the coder; the coder writes and hands off to the reviewer, who answers."""
    shown = handoffs_shown(monkeypatch)
    handoff.apply("router", messages := start())
    fake = Scripted(
        router=[use(call("h1", "handoff_to", {"agent": "coder", "reason": "code"}))],
        coder=[use(call("w1", "write_file", {"path": "a.txt", "content": "a"})), use(call("h2", "handoff_to", {"agent": "reviewer", "reason": "check it"}))],
        reviewer=[use(call("b1", "bash", {"command": "cat a.txt"})), say("PASS\na.txt says a")],
    ).install(monkeypatch)
    messages = agent.turn(messages, "make a.txt and check it")
    assert [role for role, _, _ in fake.requests] == ["router", "coder", "coder", "reviewer", "reviewer"]
    assert messages[-1]["content"] == "PASS\na.txt says a" and (fresh / "a.txt").read_text() == "a"
    assert [(p, n) for p, n, _ in shown] == [("router", "coder"), ("coder", "reviewer")]
    assert handoff.active_name() == "reviewer"
    _, offered, _ = fake.requests[3]
    assert offered == ["bash", "read_file", "read_skill", "handoff_to"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant", "tool", "assistant", "tool", "assistant", "tool", "assistant"]


# ------------------------------------------------- round 2: every call gets a result


def test_bad_tool_calls_each_get_a_result_and_the_loop_goes_on(fresh, monkeypatch):
    """Malformed arguments, an unknown tool and a raising tool: one tool message each, then the model answers."""
    broken = SimpleNamespace(id="b1", function=SimpleNamespace(name="bash", arguments="{broken"))
    Scripted(main=[
        use(broken, call("b2", "no_such_tool", {"x": 1}), call("b3", "read_file", {"path": "missing.txt"}), call("b4", "bash", {})),
        say("all four came back as errors"),
    ]).install(monkeypatch)
    messages = agent.turn(start(), "go")
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


def test_write_todos_rejects_a_bad_list_and_keeps_the_old_one(fresh):
    todos.TODOS[:] = [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]
    assert todos.write_todos([{"content": "x", "activeForm": "y", "status": "sideways"}]).startswith("Error: item 0 has status 'sideways'")
    assert todos.write_todos("nope") == "Error: todos must be a list of items."
    assert todos.TODOS == [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]


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


def test_headless_without_a_terminal_denies_every_ask_and_exits_one_without_an_answer(fresh, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(ui, "ask", lambda: pytest.fail("print mode must not open the input loop"))
    Scripted(main=[use(call("t1", "bash", {"command": "python x.py"})), say("")]).install(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["harness", "-p", "run it"])
    with pytest.raises(SystemExit) as stop:
        agent.main()
    assert stop.value.code == 1  # no answer text: a script can see the run gave nothing
    assert not session.path_for(session.CURRENT).exists()  # a one-off question leaves no session file
    assert "denied (no terminal to ask on)" in capsys.readouterr().err


def test_exit_words_and_eof_end_the_chat(fresh, monkeypatch):
    answers = iter(["", "/exit"])
    monkeypatch.setattr(ui, "ask", lambda: next(answers))
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    monkeypatch.setattr(ui, "summary", lambda: None)
    monkeypatch.setattr(agent, "turn", lambda *a, **k: pytest.fail("an empty line must not start a turn"))
    agent.chat(agent.parser().parse_args([]))
    monkeypatch.setattr(ui, "ask", lambda: None)  # ctrl-d
    agent.chat(agent.parser().parse_args([]))


# ------------------------------------------------- round 2: the handoff holes


def test_a_handed_off_agent_can_only_run_its_tool_list(fresh, monkeypatch):
    """The reviewer is offered three tools; naming write_file or remember does not run them."""
    handoffs_shown(monkeypatch)
    handoff.apply("reviewer", messages := start())
    assert permissions.check("write_file", {"path": "x.txt", "content": "x"}) == ("deny", "reviewer agent: write_file is not in its tool list")
    assert permissions.check("remember", {"name": "n", "description": "d", "content": "c"})[0] == "deny"
    assert permissions.check("bash", {"command": "ls"})[0] == "allow"
    assert permissions.check("handoff_to", {"agent": "coder", "reason": "r"})[0] == "allow"  # never cut from the list
    Scripted(reviewer=[use(call("w1", "write_file", {"path": "x.txt", "content": "x"})), say("denied")]).install(monkeypatch)
    messages = agent.turn(messages, "write x.txt")
    assert messages[3]["content"] == "Blocked by policy: reviewer agent: write_file is not in its tool list"
    assert not (fresh / "x.txt").exists()
    handoff.reset()
    assert permissions.check("write_file", {"path": "x.txt", "content": "x"})[0] == "allow"  # the default agent has every tool


def test_handoff_to_is_offered_and_allowed_in_plan_mode(fresh, monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    assert "handoff_to" in names(handoff.toolset())
    assert permissions.check("handoff_to", {"agent": "coder", "reason": "r"})[0] != "deny"
    assert permissions.check("write_file", {"path": "x", "content": "y"})[0] == "deny"  # plan mode still fences the rest


def test_listing_sessions_does_not_change_the_active_agent(fresh, monkeypatch):
    handoffs_shown(monkeypatch)
    messages = start()
    messages.append({"role": "user", "content": "old chat"})
    session.save(messages)
    handoff.switch(messages, "coder", "forced")  # the marker goes into the old chat's log
    handoff.reset()
    monkeypatch.setattr(session, "CURRENT", "newer")
    monkeypatch.setattr(session, "WRITTEN", 0)
    session.save([{"role": "system", "content": "s"}, {"role": "user", "content": "new chat"}])
    listed = session.all_sessions()
    assert sorted(s["title"] for s in listed) == ["new chat", "old chat"]
    assert handoff.active_name() == "main"  # listing applied nothing
    session.open_session("test-session")
    assert handoff.active_name() == "coder"  # opening the old chat did
    session.open_session("newer")
    assert handoff.active_name() == "main"  # a chat without a marker is the default agent's again


def test_a_marker_for_a_missing_definition_leaves_the_agent_as_it_was(fresh, monkeypatch):
    handoffs_shown(monkeypatch)
    handoff.apply("coder", messages := start())
    with pytest.raises(KeyError):
        handoff.apply("gone", messages)
    assert handoff.active_name() == "coder" and messages[0]["content"] == handoff.system_prompt(agents.AGENTS["coder"])


def test_init_keeps_the_active_agent_and_the_summary(fresh, monkeypatch):
    handoffs_shown(monkeypatch)
    handoff.apply("coder", messages := start())
    messages[0]["content"] += "\n\n<summary>\nbefore\n</summary>"
    monkeypatch.setattr(subagent, "task", lambda question: "# Guide\nrun the tests")
    monkeypatch.setattr(ui, "confirm", lambda question: True)
    monkeypatch.setattr(ui, "note", lambda text: None)
    commands.handle("/init", messages)
    assert (fresh / "AGENTS.md").read_text(encoding="utf-8").startswith("# Guide")
    assert messages[0]["content"].lstrip().startswith("You are the coder.")
    assert messages[0]["content"].endswith("<summary>\nbefore\n</summary>")
    assert "run the tests" in messages[0]["content"]  # the new file is in the prefix


def test_handoffs_per_turn_are_capped(fresh, monkeypatch):
    """coder and reviewer pass the user back and forth; after MAX_HANDOFFS the tool refuses and the active agent answers."""
    shown = handoffs_shown(monkeypatch)
    handoff.apply("coder", messages := start())
    calls = []

    def ping_pong(messages, tools=None, on_delta=None):
        """Each agent hands the user to the other one, until the tool says no."""
        calls.append(role_of(messages))
        last = [m for m in messages if m["role"] == "tool"][-1:]  # messages ends with the <env> injection, not the result
        if last and last[0]["content"].startswith("Error: handoff limit"):
            return say(f"{role_of(messages)} answers"), USAGE
        other = "reviewer" if role_of(messages) == "coder" else "coder"
        return use(call("h", "handoff_to", {"agent": other, "reason": "yours"})), USAGE

    monkeypatch.setattr(agent, "call_llm", ping_pong)
    messages = agent.turn(messages, "go")
    assert len(shown) == handoff.MAX_HANDOFFS
    errors = [m["content"] for m in messages if m["role"] == "tool" and m["content"].startswith("Error: handoff limit")]
    assert errors == ["Error: handoff limit reached this turn (4); answer the user yourself."]
    assert messages[-1]["content"] == "coder answers" and handoff.active_name() == "coder"  # four hops: back where it started
    assert len(calls) == handoff.MAX_HANDOFFS + 2 < agent.MAX_CALLS  # the loop ended by itself, not on MAX_CALLS
    handoff.new_turn()
    assert handoff.handoff_to("reviewer", "again").startswith("Handing off")  # the next turn starts from zero


def test_a_subagent_cannot_hand_off_or_write(fresh, monkeypatch):
    Scripted(main=[use(call("s1", "handoff_to", {"agent": "coder", "reason": "r"}), call("s2", "write_file", {"path": "a.txt", "content": "x"})), say("blocked")]).install(monkeypatch)
    assert subagent.task("hand off and write") == "blocked"
    assert handoff.PENDING is None and not (fresh / "a.txt").exists()
    assert "handoff_to" in subagent.WITHHELD


def test_leaving_at_the_steer_prompt_still_applies_the_handoff(fresh, monkeypatch):
    """A double Ctrl-C right after a handoff_to result: the marker is logged before the chat ends."""
    handoffs_shown(monkeypatch)
    Scripted(main=[use(call("h1", "handoff_to", {"agent": "coder", "reason": "code"}))]).install(monkeypatch)
    run_results = agent.run_results

    def interrupted(messages, tool_calls, repeated=None):
        run_results(messages, tool_calls, repeated)
        raise KeyboardInterrupt

    monkeypatch.setattr(agent, "run_results", interrupted)
    monkeypatch.setattr(agent, "steered", lambda messages, where: False)
    with pytest.raises(agent.LeaveChat):
        agent.turn(start(), "write it")
    assert handoff.active_name() == "coder"
    lines = [json.loads(line) for line in session.path_for("test-session").read_text(encoding="utf-8").splitlines()]
    assert {"handoff": "coder"} in lines
