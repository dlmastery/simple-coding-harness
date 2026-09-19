"""Step 36 offline tests. The agent definitions are read from this step's
.agents/agents directory; the loop tests drive agents.run, tools.execute,
commands.handle("/pipeline ...") and agent.turn with a fake model that
answers by the role named in the system prompt. Nothing is launched.
"""

import _thread
import json
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, agents, checkpoint, commands, context, hooks, instructions, jobs, llm, memory, permissions, pipeline, plan, sandbox, session, subagent, todos, tools  # noqa: E402
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
    """A temp workspace as cwd, temp stores, no hooks, no jobs, the shipped agents."""
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
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda *a, **k: None)
    jobs.kill_all()
    yield workspace
    jobs.kill_all()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def role_of(messages):
    """Which shipped agent a request is for, read from the first line of its system prompt."""
    first = messages[0]["content"].strip().splitlines()[0]
    for name in ("planner", "worker", "reviewer"):
        if f"You are the {name}" in first:
            return name
    return "main"


class Scripted:
    """A thread-safe fake call_llm: one reply list per role, and a log of every request.

    A role's replies are handed out in order; the last one repeats, so a
    role that always says the same thing needs one entry.
    """

    def __init__(self, **queues):
        self.queues = {role: list(replies) for role, replies in queues.items()}
        self.requests = []  # (role, tools offered, user request) per call
        self.lock = threading.Lock()

    def __call__(self, messages, tools=None, on_delta=None, on_restart=None):
        role = role_of(messages)
        with self.lock:
            self.requests.append((role, [s["function"]["name"] for s in tools or []], messages[1]["content"]))
            replies = self.queues[role]
            reply = replies.pop(0) if len(replies) > 1 else replies[0]
        return reply, USAGE

    def install(self, monkeypatch):
        monkeypatch.setattr(agent, "call_llm", self)
        monkeypatch.setattr(llm, "call_llm", self)
        return self


def names(schemas):
    return [s["function"]["name"] for s in schemas]


# ------------------------------------------------------------- definitions


def test_the_shipped_definitions_load():
    found = agents.find_agents([STEP / ".agents" / "agents"])
    assert list(found) == ["planner", "reviewer", "worker"]
    assert found["planner"]["tools"] == ["bash", "read_file", "read_skill"]
    assert found["worker"]["tools"] == ["bash", "read_file", "read_skill", "write_file", "str_replace"]
    assert found["reviewer"]["max_turns"] == 10 and found["worker"]["max_turns"] == 20
    assert found["planner"]["prompt"].startswith("You are the planner")
    assert found["reviewer"]["description"].startswith("Checks the workspace")
    assert {name: a["path"] for name, a in agents.AGENTS.items()} == {name: a["path"] for name, a in found.items()}


def test_a_definition_without_front_matter_is_skipped_and_a_nameless_one_takes_the_file_name(tmp_path):
    folder = tmp_path / "defs"
    folder.mkdir()
    (folder / "bare.md").write_text("no front matter here", encoding="utf-8")
    (folder / "nameless.md").write_text("---\ndescription: x\n---\nbody", encoding="utf-8")
    (folder / "ok.md").write_bytes(b"---\r\nname: ok\r\ndescription: fine\r\ntools: bash, read_file\r\n---\r\nbody")
    found = agents.find_agents([folder])
    assert list(found) == ["nameless", "ok"]
    assert found["nameless"]["tools"] is None and found["nameless"]["max_turns"] == agents.DEFAULT_MAX_TURNS
    assert found["ok"]["tools"] == ["bash", "read_file"] and found["ok"]["prompt"] == "body"  # a comma string, and CRLF line ends


def test_a_broken_definition_is_skipped_with_a_note_and_the_rest_still_load(tmp_path, monkeypatch):
    seen = notes(monkeypatch)
    folder = tmp_path / "defs"
    folder.mkdir()
    (folder / "unclosed.md").write_text("---\nname: x\ndescription: never closed\nbody", encoding="utf-8")
    (folder / "badyaml.md").write_text("---\nname: [\n---\nbody", encoding="utf-8")
    (folder / "spaced.md").write_text("---\nname: my agent\n---\nbody", encoding="utf-8")
    (folder / "turns.md").write_text("---\nname: turns\nmax_turns: many\n---\nbody", encoding="utf-8")
    (folder / "zero.md").write_text("---\nname: zero\nmax_turns: 0\n---\nbody", encoding="utf-8")
    (folder / "ok.md").write_text("---\nname: ok\n---\nbody", encoding="utf-8")
    found = agents.find_agents([folder])
    assert list(found) == ["ok", "zero"]  # unclosed: no front matter at all, skipped without a note
    assert found["zero"]["max_turns"] == agents.DEFAULT_MAX_TURNS
    assert len(seen) == 3 and all("skipped" in note for note in seen)
    assert any("my agent" in note for note in seen) and any("not valid YAML" in note for note in seen) and any("many" in note for note in seen)


def test_each_definition_is_a_registered_tool():
    for name in ("planner", "worker", "reviewer"):
        full = f"agent_{name}"
        assert full in tools.TOOLS and tools.TOOLS[full].__name__ == full
        [schema] = [s for s in tools.TOOL_SCHEMAS if s["function"]["name"] == full]
        assert schema["function"]["parameters"]["required"] == ["request"]
        assert schema["function"]["description"].startswith(agents.AGENTS[name]["description"])
    assert agents.register() == ["agent_planner", "agent_reviewer", "agent_worker"]
    assert names(tools.TOOL_SCHEMAS).count("agent_worker") == 1  # registering twice does not duplicate


def test_the_main_system_prompt_lists_the_agents():
    prompt = llm.build_system_prompt()
    for name in ("planner", "worker", "reviewer"):
        assert f"- agent_{name}: {agents.AGENTS[name]['description']}" in prompt
    assert agents.agents_prompt().splitlines()[0].startswith("- agent_planner: ")


# --------------------------------------------------------------- tool sets


def test_withheld_tools_are_respected():
    assert names(agents.toolset(agents.AGENTS["planner"])) == ["bash", "read_file", "read_skill"]
    assert names(agents.toolset(agents.AGENTS["worker"])) == ["bash", "read_file", "read_skill", "write_file", "str_replace"]
    everything = names(agents.toolset({"tools": None}))
    assert "bash" in everything and "write_file" in everything
    for name in everything:  # a definition may have the edit tools; nothing else on the withheld list
        assert not name.startswith("agent_") and (name not in subagent.WITHHELD or name in agents.EDIT_TOOLS)
    for name in names(subagent.toolset()):  # the exploration subagent is as before, and cannot start an agent
        assert not name.startswith("agent_") and name not in subagent.WITHHELD
    greedy = agents.toolset({"tools": ["bash", "task", "agent_worker", "write_todos"]})
    assert names(greedy) == ["bash"]  # a definition cannot ask for a withheld tool


def test_an_agent_tool_runs_a_loop_with_its_own_prompt_and_tools(fresh, monkeypatch):
    fake = Scripted(planner=[use(call("b1", "bash", {"command": "echo hi"})), say("1. Do the thing")]).install(monkeypatch)
    args, result = tools.execute(call("a1", "agent_planner", {"request": "plan it"}))
    assert result == "1. Do the thing"
    role, offered, request = fake.requests[0]
    assert role == "planner" and offered == ["bash", "read_file", "read_skill"] and request == "plan it"
    assert agents.run("nobody", "x") == "Error: no agent named 'nobody'."


# ----------------------------------------------------------------- the plan


def test_parse_plan_reads_numbered_lines_and_the_parallel_tag():
    text = "Here is the plan:\n\n1. Add the model\n2) Add the view [parallel]\n 3.  Add the tests  [Parallel] \nnot a step\nDone."
    steps = pipeline.parse_plan(text)
    assert [(s.number, s.title, s.parallel) for s in steps] == [(1, "Add the model", False), (2, "Add the view", True), (3, "Add the tests", True)]
    assert [[s.number for s in wave] for wave in pipeline.waves(steps)] == [[1], [2, 3]]
    assert pipeline.outline(steps).splitlines() == ["1. Add the model", "2. Add the view [parallel]", "3. Add the tests [parallel]"]
    assert pipeline.parse_plan("no numbers here") == []
    assert pipeline.verdict_of("PASS\nall good") == "PASS" and pipeline.verdict_of("**FAIL**: no tests") == "FAIL"
    assert pipeline.verdict_of("Looks fine to me") == "FAIL" and pipeline.verdict_of("") == "FAIL"


# ------------------------------------------------------------- the pipeline


def worker_that_writes(fake):
    """A worker reply: write the file the step names, then report. The retry writes 'hello'."""

    def reply(messages, tools=None, on_delta=None, on_restart=None):
        request = messages[1]["content"]
        step = next(line for line in request.splitlines() if line.startswith("Your step"))
        name = step.split("Create ")[1].split()[0]
        if len(messages) == 2:  # the first call of this loop: write the file
            content = "hello" if "reviewer failed" in request else "draft"
            return use(call(f"w-{name}", "write_file", {"path": name, "content": content})), USAGE
        return say(f"wrote {name}"), USAGE

    def routed(messages, tools=None, on_delta=None, on_restart=None):
        if role_of(messages) == "worker":
            with fake.lock:
                fake.requests.append(("worker", names(tools or []), messages[1]["content"]))
            return reply(messages, tools)
        return fake(messages, tools)

    return routed


def test_the_pipeline_plans_works_reviews_and_retries_once(fresh, monkeypatch):
    seen = notes(monkeypatch)
    tables = []
    monkeypatch.setattr(ui, "pipeline", lambda rows: tables.append(rows))
    fake = Scripted(
        planner=[say("Plan:\n1. Create a.txt\n2. Create b.txt [parallel]\n3. Create c.txt [parallel]")],
        reviewer=[say("FAIL\na.txt must say hello"), say("PASS\nlooks right")],
    )
    routed = worker_that_writes(fake)
    monkeypatch.setattr(agent, "call_llm", routed)
    monkeypatch.setattr(llm, "call_llm", routed)

    messages = commands.handle("/pipeline make three files", [{"role": "system", "content": "s"}])
    assert messages == [{"role": "system", "content": "s"}]  # the pipeline leaves the transcript alone
    session.save(messages)  # as chat() does after every command
    assert (fresh / "a.txt").read_text() == "hello" and (fresh / "b.txt").read_text() == "draft" and (fresh / "c.txt").read_text() == "draft"

    [rows] = tables
    assert [(n, title, attempts, verdict) for n, title, attempts, verdict, _ in rows] == [
        (1, "Create a.txt", 2, "PASS"), (2, "Create b.txt", 1, "PASS"), (3, "Create c.txt", 1, "PASS"),
    ]
    worker_requests = [request for role, _, request in fake.requests if role == "worker"]
    assert len(worker_requests) == 8  # two calls per loop: one writes, one reports; step 1 ran twice
    retry = [request for request in worker_requests if "reviewer failed" in request]
    assert len(retry) == 2 and "a.txt must say hello" in retry[0] and "Your step, and only this step: 1. Create a.txt" in retry[0]
    reviews = [request for role, _, request in fake.requests if role == "reviewer"]
    assert len(reviews) == 4 and reviews[0].startswith("Task: make three files") and "The worker reported:\nwrote a.txt" in reviews[0]
    assert seen[-1] == "pipeline: 3 step(s), 3 passed, 0 failed"

    # the edits of the whole pipeline are one checkpoint turn: one /undo takes them all back
    assert checkpoint.turns() == [1] and len(checkpoint.manifest(1)) == 3
    commands.handle("/undo", messages)
    assert not (fresh / "a.txt").exists() and not (fresh / "b.txt").exists() and not (fresh / "c.txt").exists()


def test_parallel_steps_run_at_the_same_time(fresh, monkeypatch):
    """Two [parallel] steps overlap: each worker waits until the other has started."""
    monkeypatch.setattr(ui, "pipeline", lambda rows: None)
    monkeypatch.setattr(ui, "note", lambda text: None)
    gate = threading.Barrier(2, timeout=5)

    def fake(messages, tools=None, on_delta=None, on_restart=None):
        role = role_of(messages)
        if role == "planner":
            return say("1. One [parallel]\n2. Two [parallel]"), USAGE
        if role == "worker":
            gate.wait()  # a sequential run would hang here; the Barrier's timeout turns that into a failure
            return say("done"), USAGE
        return say("PASS"), USAGE

    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    plan_text, steps = pipeline.run("go")
    assert [(s.number, s.verdict) for s in steps] == [(1, "PASS"), (2, "PASS")]


def test_a_step_that_fails_twice_is_reported_as_failed(fresh, monkeypatch):
    seen = notes(monkeypatch)
    tables = []
    monkeypatch.setattr(ui, "pipeline", lambda rows: tables.append(rows))
    fake = Scripted(planner=[say("1. Fix it")], worker=[say("done")], reviewer=[say("FAIL\nstill broken")]).install(monkeypatch)
    commands.handle("/pipeline fix it", [])
    [rows] = tables
    assert rows == [(1, "Fix it", 2, "FAIL", "FAIL still broken")]
    assert [role for role, _, _ in fake.requests] == ["planner", "worker", "reviewer", "worker", "reviewer"]
    assert seen[-1] == "pipeline: 1 step(s), 0 passed, 1 failed"


def test_a_plan_without_numbered_steps_stops_the_pipeline(fresh, monkeypatch):
    seen = notes(monkeypatch)
    fake = Scripted(planner=[say("I could not find the code.")]).install(monkeypatch)
    commands.handle("/pipeline do it", [])
    assert [role for role, _, _ in fake.requests] == ["planner"]
    assert seen[-1] == "the planner returned no numbered steps:\nI could not find the code."
    commands.handle("/pipeline", [])
    assert seen[-1] == "usage: /pipeline <task>"
    assert "/pipeline" in commands.COMMANDS


# ---------------------------------------------------------------- the loop


def test_loop_smoke_the_main_agent_delegates_to_a_worker(fresh, monkeypatch):
    """The main agent calls agent_worker; the worker writes a file; only the worker's report crosses back."""
    fake = Scripted(
        main=[use(call("t1", "agent_worker", {"request": "create notes.md"})), say("delegated")],
        worker=[use(call("s1", "write_file", {"path": "notes.md", "content": "final"})), say("wrote notes.md")],
    ).install(monkeypatch)
    messages = agent.turn([{"role": "system", "content": "s"}], "please make notes.md")
    assert (fresh / "notes.md").read_text() == "final" and messages[-1]["content"] == "delegated"
    assert messages[3] == {"role": "tool", "tool_call_id": "t1", "content": "wrote notes.md"}
    role, offered, request = fake.requests[1]
    assert role == "worker" and "agent_worker" not in offered and "task" not in offered and request == "create notes.md"


# --------------------------------------------------- withheld means denied


def test_a_withheld_tool_is_denied_at_execution_not_just_left_out_of_the_offer(fresh, monkeypatch):
    """The planner is offered bash, read_file and read_skill. A call to anything else - an edit, a question, another agent - is denied, not run."""
    monkeypatch.setitem(tools.TOOLS, "ask_user", lambda question, options=None: "an answer nobody should see")
    fake = Scripted(
        planner=[use(
            call("p1", "write_file", {"path": "plan.txt", "content": "x"}),
            call("p2", "ask_user", {"question": "which?"}),
            call("p3", "agent_worker", {"request": "do it"}),
            call("p4", "task", {"description": "look"}),
            call("p5", "bash", {"command": "echo hi"}),
        ), say("1. Step")],
    ).install(monkeypatch)
    assert agents.run("planner", "plan it") == "1. Step"
    assert [role for role, _, _ in fake.requests] == ["planner", "planner"]  # agent_worker never ran: no worker request
    assert not (fresh / "plan.txt").exists()

    outcomes = tools.execute_all([call("x1", "write_file", {"path": "p.txt", "content": "x"}), call("x2", "bash", {"command": "echo hi"})], allowed={"bash", "read_file"})
    assert outcomes[0][1] == "Blocked by policy: write_file is not available to this agent"
    assert outcomes[1][1].strip() == "hi"
    assert tools.execute(call("x3", "ask_user", {"question": "?"}), allowed={"bash"})[1] == "Blocked by policy: ask_user is not available to this agent"


def test_the_verdict_is_read_from_the_first_non_empty_line():
    assert pipeline.verdict_of("Verdict: PASS") == "PASS"
    assert pipeline.verdict_of("\n\n**Result** - PASS.\nfine") == "PASS"
    assert pipeline.verdict_of("PASS.") == "PASS" and pipeline.verdict_of("pass, with notes") == "PASS"
    assert pipeline.verdict_of("The tests PASS but the docs are missing") == "FAIL"  # PASS is not the verdict word
    assert pipeline.verdict_of("FAIL\nthe file is missing") == "FAIL"


def test_a_missing_definition_stops_the_pipeline_before_any_model_call(monkeypatch):
    seen = notes(monkeypatch)
    fake = Scripted(planner=[say("1. x")]).install(monkeypatch)
    monkeypatch.setattr(agents, "AGENTS", {"planner": agents.AGENTS["planner"]})
    assert pipeline.missing_agents() == ["worker", "reviewer"]
    commands.handle("/pipeline do it", [])
    assert fake.requests == []
    assert seen[-1] == "the pipeline needs the worker, reviewer definition(s) in .agents/agents; none ran"
    assert pipeline.run("do it") == ("Error: no agent named 'worker', 'reviewer'.", [])


def test_a_ctrl_c_during_a_parallel_wave_does_not_wait_for_the_queued_steps(fresh, monkeypatch):
    """The wave runs on subagent.gather: a Ctrl-C drops the pool, so the steps still queued never start."""
    monkeypatch.setattr(subagent, "MAX_PARALLEL", 1)
    started = []

    def fake(messages, tools=None, on_delta=None, on_restart=None):
        role = role_of(messages)
        if role == "planner":
            return say("1. One [parallel]\n2. Two [parallel]\n3. Three [parallel]"), USAGE
        if role == "worker":
            started.append(messages[1]["content"])
            if len(started) == 1:
                threading.Timer(0.05, _thread.interrupt_main).start()
            time.sleep(0.5)
            return say("done"), USAGE
        return say("PASS"), USAGE

    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    began = time.monotonic()
    with pytest.raises(KeyboardInterrupt):
        pipeline.run("go")
    assert time.monotonic() - began < 1.2  # three sequential 0.5 s steps would take 1.5 s
    time.sleep(0.6)  # the one running worker finishes on its own; the other two never start
    assert len(started) == 1


# --------------------------------------------------- a call never crashes


def test_bad_arguments_an_unknown_tool_and_a_raising_tool_each_get_one_result(monkeypatch):
    def boom(command):
        raise RuntimeError("no shell today")

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    broken = SimpleNamespace(id="t1", function=SimpleNamespace(name="read_file", arguments="{not json"))
    reply = use(broken, call("t2", "edit_file", {"path": "x"}), call("t3", "bash", {"command": "ls"}), call("t4", "bash", {"cmd": "ls"}))
    Scripted(main=[reply, say("noted")]).install(monkeypatch)

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "tool", "tool", "tool", "assistant"]
    assert out[3]["content"].startswith("Error: the arguments of read_file are not a JSON object: ")
    assert out[4]["content"] == "Error: no tool named 'edit_file'."
    assert out[5]["content"] == "Error: RuntimeError: no shell today"
    assert out[6]["content"] == "Blocked by policy: bash: missing argument 'command'"
    assert out[7]["content"] == "noted"


def test_utf8_survives_write_file_read_file_and_bash(fresh):
    text = "héllo wörld — ünïcode ✓\r\nline two\n"
    assert tools.write_file("deep/u.txt", text) == "Wrote deep/u.txt"  # the parent directory is made
    assert tools.read_file("deep/u.txt") == text  # the CRLF comes back as written
    assert tools.execute(call("t1", "read_file", {"path": "missing.txt"}))[1].startswith("Error: FileNotFoundError")
    assert "llo" in tools.bash("echo héllo") and "Error" not in tools.bash("echo héllo")


def test_write_todos_with_a_bad_status_is_an_error_and_leaves_the_list_alone():
    todos.TODOS[:] = [{"content": "a", "activeForm": "doing a", "status": "in_progress"}]
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos("not a list") == "Error: todos must be a list"
    assert todos.TODOS == before


def test_rewind_offers_only_user_messages_and_a_resumed_pending_call_that_fails_becomes_an_error(monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "ls"})}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "ok"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t2", "type": "function", "function": {"name": "bash", "arguments": "{not json"}}]},
    ]
    notes(monkeypatch)
    monkeypatch.setattr(agent, "run_results", lambda *a, **k: 1 / 0)  # a crash below run_results
    assert agent.recover(messages) == 1
    assert messages[-1] == {"role": "tool", "tool_call_id": "t2", "content": "Error: ZeroDivisionError: division by zero"}

    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    monkeypatch.setattr(ui, "replay", lambda messages: None)
    monkeypatch.setattr(ui, "clear", lambda: None)
    out = commands.rewind(messages)
    assert len(offered) == 2 and [m["role"] for m in out] == ["system", "user", "assistant", "tool"]  # cut before "two": no orphan
