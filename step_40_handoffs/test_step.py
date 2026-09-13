"""Step 40 offline tests. The agent definitions are read from this step's
.agents/agents directory; the loop tests drive agent.turn and
commands.handle with a fake model that answers by the agent named in the
system prompt. Nothing is launched.
"""

import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, agents, checkpoint, commands, context, handoff, hooks, instructions, jobs, llm, memory, modes, permissions, plan, sandbox, session, subagent, todos, tools  # noqa: E402
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
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
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
