import json
import os
import sys
import threading
import time
from types import SimpleNamespace

import httpx
import openai
import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, context, hooks, jobs, permissions, plan, prompt, session, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

PY = f'"{sys.executable}"'  # `python` on the PATH may be a Store alias; the interpreter running the tests is not


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [c.model_dump() for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def python_job(code):
    """A shell command that runs one line of Python in the background."""
    return f"{PY} -c \"{code}\""


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Every test starts in act mode with no hooks and no jobs, and ends with no job running."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(jobs, "_counter", 0)  # ids start at job-1 again
    jobs.kill_all()
    yield
    jobs.kill_all()


@pytest.fixture
def quiet(monkeypatch):
    """Keep tests off the disk and off the terminal."""
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "note", lambda text: None)


# --------------------------------------------------------------------- jobs


def test_background_job_finishes_and_status_shows_its_output():
    started = jobs.bash_background(python_job("print('hello from the job')"))
    assert started.startswith("Started job-1:")
    waited = jobs.job_wait("job-1", timeout=30)
    assert waited.startswith("job-1: exited with code 0")
    assert "hello from the job" in waited
    status = jobs.job_status("job-1")
    assert status.startswith("job-1: exited with code 0") and status.endswith("hello from the job")
    assert jobs.running() == []
    assert jobs.job_status("job-9").startswith("Error: no job 'job-9'. Known jobs: job-1.")


def test_job_kill_stops_a_sleeping_job_and_its_process_tree():
    jobs.bash_background(python_job("import time; time.sleep(60)"))
    job = jobs.JOBS["job-1"]
    assert job.running()
    assert jobs.job_wait("job-1", timeout=1).startswith("job-1 is still running after 1s.")
    before = time.time()
    killed = jobs.job_kill("job-1")
    assert time.time() - before < 15
    assert killed.startswith("Killed job-1.\njob-1: killed (exit code")
    assert not job.running() and job.process.poll() != 0
    assert jobs.job_kill("job-1").startswith("job-1 had already ended.")


def test_job_kill_reaches_a_grandchild_that_ignores_the_first_signal():
    # the shell starts python, which starts another python that sleeps: the whole tree must go
    grandchild = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); time.sleep(60)"
    jobs.bash_background(python_job(grandchild))
    time.sleep(2)  # let the grandchild start
    before = time.time()
    jobs.job_kill("job-1")
    assert time.time() - before < 15
    assert not jobs.JOBS["job-1"].running()


def test_job_wait_clamps_and_checks_its_timeout(monkeypatch):
    monkeypatch.setattr(jobs, "MAX_WAIT", 1)
    jobs.bash_background(python_job("import time; time.sleep(60)"))
    before = time.time()
    assert jobs.job_wait("job-1", timeout=3600).startswith("job-1 is still running after 1s.")  # an hour became MAX_WAIT
    assert time.time() - before < 10
    assert jobs.job_wait("job-1", timeout="1").startswith("job-1 is still running after 1s.")  # a string of digits is fine
    assert jobs.job_wait("job-1", timeout="soon") == "Error: timeout must be a number of seconds, got 'soon'"
    assert jobs.job_wait("job-1", timeout=None).startswith("job-1 is still running after 1s.")  # None means the default
    assert "at most 300" in next(s for s in jobs.JOB_SCHEMAS if s["function"]["name"] == "job_wait")["function"]["parameters"]["properties"]["timeout"]["description"]


def test_jobs_run_through_the_sandbox_wrapper(monkeypatch):
    seen = []

    def wrap(command):
        seen.append(command)
        return None  # no sandbox on this machine: run it as a plain shell command

    monkeypatch.setattr(jobs.sandbox, "wrap", wrap)
    jobs.bash_background(python_job("print(1)"))
    assert seen == [python_job("print(1)")]
    assert "1" in jobs.job_wait("job-1", timeout=30)


def test_late_block_lists_a_running_job_until_its_end_is_reported():
    assert "<jobs>" not in context.reminder()["content"]
    jobs.bash_background(python_job("import time; time.sleep(60)"))
    content = context.reminder()["content"]
    assert "<jobs>" in content and "job-1: running for" in content and "time.sleep(60)" in content
    assert content.index("</env>") < content.index("<jobs>")
    jobs.job_kill("job-1")
    assert "<jobs>" not in context.reminder()["content"]  # the kill reported the end
    jobs.bash_background(python_job("print(2)"))
    jobs.JOBS["job-2"].process.wait(timeout=30)
    assert "job-2: exited with code 0" in context.reminder()["content"]  # ended, not yet read
    jobs.job_status("job-2")
    assert "<jobs>" not in context.reminder()["content"]


def test_kill_all_ends_every_job_and_removes_the_logs():
    jobs.bash_background(python_job("import time; time.sleep(60)"))
    jobs.bash_background(python_job("import time; time.sleep(60)"))
    processes = [job.process for job in jobs.JOBS.values()]
    logs = [job.log for job in jobs.JOBS.values()]
    jobs.kill_all()
    assert all(process.poll() is not None for process in processes)
    assert not any(log.exists() for log in logs)
    assert jobs.JOBS == {}


def test_background_jobs_follow_the_bash_rules(monkeypatch):
    assert permissions.check("bash_background", {"command": "ls -la"}) == ("allow", "run in background: ls -la")
    assert permissions.check("bash_background", {"command": "python serve.py"}) == ("ask", "run in background: python serve.py")
    assert permissions.check("bash_background", {"command": "rm -rf build"})[0] == "deny"
    assert permissions.check("job_status", {"job_id": "job-1"}) == ("allow", None)
    monkeypatch.setattr(plan, "MODE", "plan")
    assert permissions.check("bash_background", {"command": "ls"})[0] == "deny"  # not in the plan tool set
    names = {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert {"bash_background", "job_status", "job_wait", "job_kill"} <= names
    assert not {"bash_background", "job_status", "job_wait", "job_kill"} & {s["function"]["name"] for s in subagent.toolset()}


def test_jobs_command_lists_the_jobs(monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/jobs", messages) is messages
    assert notes == ["no background jobs in this session"]
    jobs.bash_background(python_job("print(3)"))
    jobs.JOBS["job-1"].process.wait(timeout=30)
    commands.handle("/jobs", messages)
    assert notes[-1].startswith("job-1    exited with code 0")
    assert "/jobs" in commands.COMMANDS


# ------------------------------------------------------------ subagents


def scripted(scripts, barrier=None):
    """A thread-safe fake call_llm: the script is chosen by the request text, the
    step by how many assistant messages are in the list. No shared counter.

    With a barrier, every first call waits until the others have arrived: the
    subagents must be in flight at the same time, or the barrier breaks.
    """
    calls = []
    lock = threading.Lock()

    def fake(messages, tools=None, on_delta=None):
        request = messages[1]["content"]
        step = sum(1 for m in messages if m["role"] == "assistant")
        with lock:
            calls.append((request, threading.current_thread().name))
        if barrier is not None and step == 0:
            barrier.wait()
        return scripts[request][step], {"prompt_tokens": 1, "completion_tokens": 1}

    return fake, calls


def test_three_parallel_subagents_return_three_reports_in_order(quiet, monkeypatch):
    scripts = {
        "alpha": [FakeMessage(content=None, tool_calls=[call("a1", "bash", {"command": "echo alpha"})]), FakeMessage(content="alpha report", tool_calls=None)],
        "beta": [FakeMessage(content="beta report", tool_calls=None)],
        "gamma": [FakeMessage(content=None, tool_calls=[call("g1", "bash", {"command": "echo gamma"})]), FakeMessage(content="gamma report", tool_calls=None)],
    }
    fake, calls = scripted(scripts, barrier=threading.Barrier(3, timeout=10))
    monkeypatch.setattr(subagent, "MAX_PARALLEL", 3)
    monkeypatch.setattr("harness.llm.call_llm", fake)
    tags = []
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: tags.append((description, tag)))

    result = subagent.task(descriptions=["alpha", "beta", "gamma"])

    assert result == (
        "## subagent 1: alpha\n\nalpha report\n\n"
        "## subagent 2: beta\n\nbeta report\n\n"
        "## subagent 3: gamma\n\ngamma report"
    )
    assert sorted(tags) == [("alpha", 1), ("beta", 2), ("gamma", 3)]
    assert len(calls) == 5
    assert all(thread.startswith("subagent") for _, thread in calls)  # pool threads, never the caller's


def test_one_description_still_runs_one_subagent(quiet, monkeypatch):
    fake, calls = scripted({"solo": [FakeMessage(content="solo report", tool_calls=None)]})
    monkeypatch.setattr("harness.llm.call_llm", fake)
    assert subagent.task(description="solo") == "solo report"
    assert subagent.task("solo") == "solo report"
    assert [request for request, _ in calls] == ["solo", "solo"]
    assert subagent.task().startswith("Error: give a description")
    schema = subagent.TASK_SCHEMA["function"]["parameters"]
    assert set(schema["properties"]) == {"description", "descriptions"}
    assert "anyOf" not in schema and "required" not in schema  # both optional: strict-schema providers reject anyOf at the root


def test_a_single_subagent_that_crashes_is_a_report_too(quiet, monkeypatch):
    def fake(messages, tools=None, on_delta=None):
        raise ValueError("bad reply")  # not a model failure: loop() answers those itself

    monkeypatch.setattr("harness.llm.call_llm", fake)
    assert subagent.task(description="solo") == "Error: the subagent failed with ValueError: bad reply"


def test_a_subagent_cannot_run_a_tool_it_was_not_offered(quiet, monkeypatch):
    scripts = {"sneaky": [
        FakeMessage(content=None, tool_calls=[call("s1", "bash_background", {"command": "echo hi"}), call("s2", "write_file", {"path": "x.txt", "content": "x"})]),
        FakeMessage(content="denied twice", tool_calls=None),
    ]}
    fake, _ = scripted(scripts)
    monkeypatch.setattr("harness.llm.call_llm", fake)
    seen = []
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: seen.append((name, result)))
    assert subagent.task(description="sneaky") == "denied twice"
    assert seen == [("bash_background", "Blocked by policy: bash_background is not available to this agent"), ("write_file", "Blocked by policy: write_file is not available to this agent")]
    assert jobs.JOBS == {}  # no job was started


def test_parallel_subagents_take_turns_at_the_approval_prompt(quiet, monkeypatch):
    scripts = {
        name: [FakeMessage(content=None, tool_calls=[call(f"{name}1", "bash", {"command": f"python -c print('{name}')"})]), FakeMessage(content=f"{name} done", tool_calls=None)]
        for name in ("one", "two", "three")
    }
    fake, _ = scripted(scripts, barrier=threading.Barrier(3, timeout=10))
    monkeypatch.setattr(subagent, "MAX_PARALLEL", 3)
    monkeypatch.setattr("harness.llm.call_llm", fake)
    monkeypatch.setattr(ui, "approve", ui.__class__.approve.__get__(ui))  # the real one, which reads the prompt under the lock
    inside = []
    overlaps = []

    def read(text):  # what prompt_toolkit would refuse: a second prompt while one is open
        inside.append(1)
        if len(inside) > 1:
            overlaps.append(text)
        time.sleep(0.2)
        inside.pop()
        return "n"

    monkeypatch.setattr(prompt, "read", read)
    monkeypatch.setattr(ui.console, "print", lambda *a, **k: None)
    result = subagent.task(descriptions=["one", "two", "three"])
    assert overlaps == [] and "one done" in result and "three done" in result


def test_a_failing_subagent_does_not_sink_the_others(quiet, monkeypatch):
    def fake(messages, tools=None, on_delta=None):
        if messages[1]["content"] == "bad":
            raise ValueError("bad reply")
        return FakeMessage(content="fine", tool_calls=None), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr("harness.llm.call_llm", fake)
    result = subagent.task(descriptions=["good", "bad"])
    assert result.startswith("## subagent 1: good\n\nfine\n\n## subagent 2: bad\n\nError: subagent 2 failed with ValueError: bad reply")


# --------------------------------------------------------------- the loop


def test_loop_smoke_job_then_parallel_task(quiet, monkeypatch):
    replies = [
        FakeMessage(content=None, tool_calls=[call("t1", "bash_background", {"command": python_job("print('built')")})]),
        FakeMessage(content=None, tool_calls=[call("t2", "job_wait", {"job_id": "job-1", "timeout": 30}), call("t3", "task", {"descriptions": ["one", "two"]})]),
        FakeMessage(content="done", tool_calls=None),
    ]
    subagent_replies = {"one": [FakeMessage(content="report one", tool_calls=None)], "two": [FakeMessage(content="report two", tool_calls=None)]}
    fake_sub, _ = scripted(subagent_replies)

    def fake_main(messages, tools=None, on_delta=None):
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake_main)
    monkeypatch.setattr("harness.llm.call_llm", fake_sub)
    out = agent.turn([{"role": "system", "content": "s"}], "build it, then look around")
    assert out[3]["content"].startswith("Started job-1:")
    assert out[5]["content"].startswith("job-1: exited with code 0") and "built" in out[5]["content"]
    assert out[6]["content"] == "## subagent 1: one\n\nreport one\n\n## subagent 2: two\n\nreport two"
    assert out[-1]["content"] == "done"


# ----------------------------------------------- the error paths of the loop


def raw_call(cid, name, arguments):
    """A tool call whose arguments are exactly this string, valid JSON or not."""
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def fake_model(monkeypatch, *replies):
    """A call_llm that plays the replies in order, for the main loop."""
    queue = list(replies)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (queue.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))


def test_bad_arguments_unknown_tool_and_a_raising_tool_each_get_one_tool_message(quiet, monkeypatch, tmp_path):
    fake_model(
        monkeypatch,
        FakeMessage(content=None, tool_calls=[
            raw_call("c1", "read_file", '{"path": '),                                   # cut off mid-stream
            raw_call("c2", "no_such_tool", "{}"),                                       # a name the registry lacks
            raw_call("c3", "bash", json.dumps({"command": "echo hi", "shell": "zsh"})),      # the tool raises (unknown keyword)
            raw_call("c4", "bash", "[1, 2]"),                                           # JSON, but not an object
            raw_call("c5", "bash", "{}"),                                               # a required argument missing
        ]),
        FakeMessage(content="None of that worked.", tool_calls=None),
    )
    messages = agent.turn([{"role": "system", "content": "s"}], "try a few things")
    results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
    assert list(results) == ["c1", "c2", "c3", "c4", "c5"]  # one tool message per call, in reply order
    assert results["c1"].startswith("Error: the arguments of read_file are not a JSON object:")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: TypeError:")
    assert results["c4"] == "Error: the arguments of bash are not a JSON object: not an object"
    assert results["c5"] == "Blocked by policy: bash: missing argument 'command'"
    assert messages[-1]["content"] == "None of that worked."  # the loop went on to the next reply


def test_a_failed_model_call_is_a_note_and_the_transcript_stays_valid(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))

    def down(messages, tools=None, on_delta=None):
        raise openai.APIConnectionError(request=httpx.Request("POST", "https://example.invalid/v1"))

    monkeypatch.setattr(agent, "call_llm", down)
    messages = agent.turn([{"role": "system", "content": "s"}], "hello?")
    assert [m["role"] for m in messages] == ["system", "user"]  # the prompt stays, nothing dangles
    assert notes[-1].startswith("model call failed:")


def test_ctrl_c_mid_turn_answers_the_pending_tool_calls(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    fake_model(monkeypatch, FakeMessage(content=None, tool_calls=[raw_call("c1", "bash", json.dumps({"command": "echo hi"}))]))

    def interrupted(tool_calls, allowed=None):
        raise KeyboardInterrupt

    monkeypatch.setattr(agent, "execute_all", interrupted)
    messages = agent.turn([{"role": "system", "content": "s"}], "run it")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": agent.INTERRUPTED}
    assert notes[-1] == "interrupted"


def test_the_turn_stops_after_max_calls(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    monkeypatch.setattr(agent, "MAX_CALLS", 3)
    forever = lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=[raw_call("c", "bash", '{"command": "echo again"}')]), {"prompt_tokens": 1, "completion_tokens": 1})
    monkeypatch.setattr(agent, "call_llm", forever)
    messages = agent.turn([{"role": "system", "content": "s"}], "loop")
    assert sum(1 for m in messages if m["role"] == "assistant") == 3
    assert messages[-1]["role"] == "tool"  # every call answered before the stop
    assert notes[-1] == "stopped after 3 model calls in one turn; say 'continue' to go on"


def test_session_load_repairs_a_dangling_tool_call(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    pending = {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]}
    (tmp_path / "old.jsonl").write_text("".join(json.dumps(m) + "\n" for m in [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}, pending]), encoding="utf-8")
    messages = session.load("old")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": session.STOPPED}
    assert session.repair([{"role": "user", "content": "hi"}], session.STOPPED) == 0  # nothing to repair


def test_rewind_offers_only_user_messages_and_leaves_no_orphan(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "x"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "ok"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    kept = commands.handle("/rewind", list(messages))
    assert len(offered) == 2 and "first" in offered[0] and "second" in offered[1]  # never the tool call
    assert kept == messages[:5]
    monkeypatch.setattr(ui, "pick", lambda title, rows: 0)
    assert commands.handle("/rewind", list(messages)) == messages[:1]
    assert (tmp_path / f"{session.CURRENT}.jsonl").exists()  # a fresh chat got its file before the marker


def test_write_todos_rejects_a_bad_status_and_leaves_the_list_alone(monkeypatch):
    monkeypatch.setattr(todos, "TODOS", [{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b"}]) == "Error: item 0 needs content, activeForm and status."
    assert todos.write_todos("b").startswith("Error:")
    assert todos.write_todos([{"content": "b", "activeForm": "b", "status": "in_progress"}, {"content": "c", "activeForm": "c", "status": "in_progress"}]).startswith("Error: 2 tasks are in_progress")
    assert todos.TODOS == before


def test_utf8_survives_write_file_read_file_and_bash(tmp_path):
    path = tmp_path / "näme.txt"
    text = "héllo wörld — ünïcode ✓\r\nline two\n"
    assert tools.write_file(str(path), text).startswith("Wrote")
    assert tools.read_file(str(path)) == text  # bytes and line endings as written
    assert tools.str_replace(str(path), "", "x") == "Error: old_str is empty."
    assert tools.bash(f'"{sys.executable}" -X utf8 -c "print(\'ünïcode ✓\')"').strip() == "ünïcode ✓"
    assert tools.write_file(str(tmp_path / "deep" / "er" / "file.txt"), "x") == f"Wrote {tmp_path / 'deep' / 'er' / 'file.txt'}"  # parents are created
