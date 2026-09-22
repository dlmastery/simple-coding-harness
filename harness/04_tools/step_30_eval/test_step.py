"""Step 30 offline tests. A scripted fake model plays the agent: it reads the
task prompt to pick a script and the count of assistant messages to pick
the step, so it is stateless and safe to call from a subagent thread. The
suite under test is the shipped evals/ directory.
"""

import json
import os
import shutil
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, context, evaluate, hooks, jobs, llm, memory, permissions, plan, sandbox, session, skills, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

STEP = Path(__file__).parent
EVALS = STEP / "evals"

USAGE = {"prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": None, "cached_tokens": 3}


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


def say(text):
    return FakeMessage(content=text, tool_calls=None)


def use(*calls):
    return FakeMessage(content=None, tool_calls=list(calls))


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Every test starts in act mode with no hooks and no jobs, and never touches the real session store."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "note", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    jobs.kill_all()
    yield
    jobs.kill_all()


# ---------------------------------------------------------- the fake model


def scripted(scripts, usage=USAGE, subagent_report="parse_config is defined in app/settings.py, line 7."):
    """A thread-safe fake call_llm and the list of what it saw per call.

    The script is picked by a key found in the task prompt, the step by how
    many assistant messages the list already holds. A subagent request
    gets a fixed report. The judge gets whatever `scripts["judge"]` says.
    """
    seen = []
    lock = threading.Lock()

    def fake(messages, tools=None, on_delta=None):
        system = messages[0]["content"]
        with lock:
            seen.append({"cwd": os.getcwd(), "session": session.CURRENT, "system": system})
        if system.startswith(evaluate.JUDGE_SYSTEM):
            return say(scripts["judge"]), usage
        if "exploration subagent" in system:
            return say(subagent_report), usage
        prompt = messages[1]["content"]
        key = next(k for k in scripts if k in prompt)
        step = sum(1 for m in messages if m["role"] == "assistant")
        return scripts[key][step], usage

    return fake, seen


HELLO = use(call("w1", "write_file", {"path": "hello.txt", "content": "hello\n" * 5}))

SCRIPTS = {
    "hello.txt": [HELLO, say("done")],
    "pytest": [say("The tests already pass.")],  # it changed nothing, so check.py fails
    "parse_config": [use(call("t1", "task", {"description": "which file defines parse_config?"})), say("The function is in `settings.py`.")],
}


@pytest.fixture
def quiet(monkeypatch):
    """Keep the loop tests off the disk and off the terminal."""
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "usage", lambda stats: None)


@pytest.fixture
def suite(tmp_path):
    """A copy of the shipped suite, so the report lands in the temp dir, not in evals/."""
    shutil.copytree(EVALS, tmp_path / "evals")
    return tmp_path / "evals"


@pytest.fixture
def model(monkeypatch):
    fake, seen = scripted(SCRIPTS)
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    return seen


# ------------------------------------------------------------------ suite


def test_load_suite_finds_the_three_shipped_tasks_and_their_checkers():
    tasks = evaluate.load_suite(EVALS)
    assert [(t.name, t.checker) for t in tasks] == [("find_function", "expect.txt"), ("fix_test", "check.py"), ("write_hello", "check.py")]
    assert tasks[0].prompt.startswith("Somewhere in this project") and "task subagent" in tasks[0].prompt
    assert (EVALS / "fix_test" / "workspace" / "test_calc.py").exists()
    assert not (EVALS / "write_hello" / "workspace").exists()  # an empty workspace is fine


def test_load_suite_skips_a_task_without_a_checker_or_a_prompt(tmp_path):
    (tmp_path / "good").mkdir()
    (tmp_path / "good" / "task.md").write_text("do it")
    (tmp_path / "good" / "expect.txt").write_text("ok")
    (tmp_path / "no_checker").mkdir()
    (tmp_path / "no_checker" / "task.md").write_text("do it")
    (tmp_path / "no_prompt").mkdir()
    (tmp_path / "no_prompt" / "check.py").write_text("")
    (tmp_path / "stray.txt").write_text("not a task")
    assert [t.name for t in evaluate.load_suite(tmp_path)] == ["good"]
    with pytest.raises(FileNotFoundError):
        evaluate.load_suite(tmp_path / "missing")


# ---------------------------------------------------------------- the run


def test_suite_passes_two_tasks_and_fails_one(model, suite):
    before = os.getcwd()
    report = evaluate.run_suite(suite, keep=True)

    assert set(report) == {"suite", "model", "started", "repeat", "tasks", "summary"}
    assert report["suite"] == "evals" and report["repeat"] == 1
    by_name = {t["name"]: t for t in report["tasks"]}
    assert by_name["write_hello"]["passed"] == 1 and by_name["find_function"]["passed"] == 1
    assert by_name["fix_test"]["passed"] == 0 and by_name["fix_test"]["results"][0]["detail"].startswith("check.py exited 1")
    assert report["summary"]["runs"] == 3 and report["summary"]["passed"] == 2 and report["summary"]["pass_rate"] == 0.667
    assert set(by_name["write_hello"]["results"][0]) == {"task", "run", "passed", "seconds", "prompt_tokens", "completion_tokens", "cached_tokens", "cost", "answer", "detail", "workspace"}
    assert by_name["write_hello"]["results"][0]["answer"] == "done"

    # tokens are the sum of every usage dict the loop reported; cost is None when no usage had one
    assert by_name["write_hello"]["prompt_tokens"] == 20 and by_name["write_hello"]["completion_tokens"] == 8 and by_name["write_hello"]["cached_tokens"] == 6
    assert by_name["find_function"]["prompt_tokens"] == 30  # two main calls and one subagent call
    assert report["summary"]["cost"] is None and by_name["fix_test"]["cost"] is None

    # the report is written next to the tasks
    written = json.loads((suite / evaluate.REPORT_NAME).read_text(encoding="utf-8"))
    assert written["summary"] == report["summary"]
    assert not (EVALS / evaluate.REPORT_NAME).exists()  # the shipped suite is untouched

    # each task ran in its own temp copy of its workspace, never in the suite dir
    workspaces = {t["name"]: Path(t["results"][0]["workspace"]) for t in report["tasks"]}
    assert len(set(workspaces.values())) == 3
    for name, workspace in workspaces.items():
        assert suite not in workspace.parents and workspace.name == "workspace"
    assert (workspaces["write_hello"] / "hello.txt").read_text() == "hello\n" * 5  # written into the copy...
    assert not (suite / "write_hello" / "hello.txt").exists()                        # ...not into the task
    assert (workspaces["fix_test"] / "calc.py").read_text() == (suite / "fix_test" / "workspace" / "calc.py").read_text()
    assert (workspaces["find_function"] / "app" / "settings.py").exists()

    # the model saw the workspace as cwd and in the system prompt, and a fresh session per task
    main_calls = [s for s in model if "exploration subagent" not in s["system"]]
    assert {Path(s["cwd"]).resolve() for s in main_calls} == {w.resolve() for w in workspaces.values()}
    for s in main_calls:
        assert f"working directory is: {s['cwd']}" in s["system"]
    sub_calls = [s for s in model if "exploration subagent" in s["system"]]
    assert len(sub_calls) == 1
    assert (f"working in {workspaces['find_function']}." in sub_calls[0]["system"]
            or f"working in {workspaces['find_function'].resolve()}." in sub_calls[0]["system"])  # macOS reports /var as /private/var
    assert len({s["session"] for s in model}) == 3 and all(s["session"].startswith("eval-evals-") for s in model)
    assert os.getcwd() == before
    for workspace in workspaces.values():  # --keep left them for inspection; the test tidies up
        shutil.rmtree(workspace.parent, ignore_errors=True)


def test_repeat_doubles_the_run_count(model, suite):
    report = evaluate.run_suite(suite, repeat=2)
    assert report["repeat"] == 2 and report["summary"]["runs"] == 6 and report["summary"]["passed"] == 4
    for task in report["tasks"]:
        assert task["runs"] == 2 and [r["run"] for r in task["results"]] == [1, 2]
        assert task["results"][0]["workspace"] != task["results"][1]["workspace"]
    by_name = {t["name"]: t for t in report["tasks"]}
    assert by_name["fix_test"]["pass_rate"] == 0.0 and by_name["write_hello"]["pass_rate"] == 1.0
    assert not Path(by_name["write_hello"]["results"][0]["workspace"]).exists()  # removed without --keep


def test_a_crashing_run_is_a_failed_result_not_a_dead_suite(monkeypatch):
    def broken(messages, tools=None, on_delta=None):
        raise RuntimeError("model unreachable")

    monkeypatch.setattr(agent, "call_llm", broken)
    task = evaluate.load_suite(EVALS)[2]
    result = evaluate.run_task(task)
    assert result.task == "write_hello" and not result.passed
    # the loop turned the crash into a note and kept the transcript valid; the run is still a failure, not a checker verdict
    assert result.detail == "run failed: RuntimeError: model call failed: model unreachable" and result.answer == ""


def test_a_run_that_hits_the_call_budget_is_a_failed_run(monkeypatch):
    monkeypatch.setattr(agent, "MAX_CALLS", 2)
    forever = lambda messages, tools=None, on_delta=None: (use(call("b", "bash", {"command": "echo again"})), USAGE)
    monkeypatch.setattr(agent, "call_llm", forever)
    result = evaluate.run_task(evaluate.load_suite(EVALS)[2])
    assert not result.passed and result.detail == "run failed: RuntimeError: stopped after 2 model calls in one turn; say 'continue' to go on"


def test_a_judge_that_cannot_be_reached_fails_the_run_not_the_suite(tmp_path, monkeypatch):
    (tmp_path / "graded").mkdir()
    (tmp_path / "graded" / "task.md").write_text("say hello")
    (tmp_path / "graded" / "judge.md").write_text("PASS if the answer says hello.")
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (say("hello"), USAGE))

    def down(messages, tools=None, on_delta=None):
        raise RuntimeError("judge unreachable")

    monkeypatch.setattr(llm, "call_llm", down)
    result = evaluate.run_task(evaluate.load_suite(tmp_path)[0])
    assert not result.passed and result.detail == "run failed: RuntimeError: judge unreachable" and result.answer == "hello"


def test_ctrl_c_still_writes_the_runs_that_finished(model, suite, monkeypatch):
    real = evaluate.run_task
    count = []

    def interrupted(task, run=1, suite_name="suite", keep=False):
        if len(count) == 1:
            raise KeyboardInterrupt
        count.append(task.name)
        return real(task, run, suite_name, keep)

    monkeypatch.setattr(evaluate, "run_task", interrupted)
    with pytest.raises(KeyboardInterrupt):
        evaluate.run_suite(suite)
    written = json.loads((suite / evaluate.REPORT_NAME).read_text(encoding="utf-8"))
    assert written["summary"]["runs"] == 1 and [t["runs"] for t in written["tasks"]] == [1, 0, 0]


# --------------------------------------------------------------- checkers


def test_check_py_passes_once_the_fix_is_in(tmp_path):
    task = next(t for t in evaluate.load_suite(EVALS) if t.name == "fix_test")
    workspace = tmp_path / "workspace"
    shutil.copytree(task.path / "workspace", workspace)
    assert evaluate.check(task, workspace, "")[0] is False
    calc = workspace / "calc.py"
    calc.write_text(calc.read_text().replace("return a - b", "return a + b"))
    passed, detail = evaluate.check(task, workspace, "fixed the sign in add")
    assert passed and detail.startswith("check.py exited 0")


def test_expect_txt_is_a_substring_of_the_answer():
    task = next(t for t in evaluate.load_suite(EVALS) if t.name == "find_function")
    assert evaluate.check(task, EVALS, "It lives in app/settings.py.") == (True, "expected 'settings.py' found in the answer")
    assert evaluate.check(task, EVALS, "It lives in models.py.") == (False, "expected 'settings.py' missing in the answer")


def test_judge_md_asks_the_model_and_reads_the_first_word(tmp_path, monkeypatch):
    (tmp_path / "graded").mkdir()
    (tmp_path / "graded" / "task.md").write_text("write a poem into poem.txt")
    (tmp_path / "graded" / "judge.md").write_text("PASS only if poem.txt is listed and the answer mentions a poem.")
    (tmp_path / "graded" / "workspace").mkdir()
    (tmp_path / "graded" / "workspace" / "poem.txt").write_text("roses")
    task = evaluate.load_suite(tmp_path)[0]
    requests = []

    def judge(messages, tools=None, on_delta=None):
        requests.append((messages, tools))
        return say(judge.verdict), USAGE

    monkeypatch.setattr(llm, "call_llm", judge)
    judge.verdict = "PASS. The poem is there."
    assert evaluate.check(task, task.path / "workspace", "I wrote a poem.") == (True, "judge said: PASS. The poem is there.")
    judge.verdict = "fail - no poem"
    assert evaluate.check(task, task.path / "workspace", "nothing")[0] is False
    judge.verdict = ""
    assert evaluate.check(task, task.path / "workspace", "nothing") == (False, "judge said: (nothing)")

    messages, tools = requests[0]
    assert tools == [] and messages[0]["content"] == evaluate.JUDGE_SYSTEM
    body = messages[1]["content"]
    assert "<instructions>\nPASS only if" in body and "<task>\nwrite a poem" in body
    assert "<answer>\nI wrote a poem." in body and "<workspace>\npoem.txt\n</workspace>" in body


# --------------------------------------------------------------- isolation


def test_isolated_resets_cwd_keyed_state_and_restores_it(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    todos.TODOS[:] = [{"content": "old", "activeForm": "old", "status": "pending"}]
    monkeypatch.setattr(plan, "PLAN", {"goal": "old"})
    monkeypatch.setattr(context, "LAST_STATUS", {"stale.py": "M"})
    monkeypatch.setattr(hooks, "SESSION_CONTEXT", ["branch policy"])
    original = {"cwd": os.getcwd(), "project": permissions.PROJECT, "sandbox": sandbox.PROJECT, "approve": ui.approve, "usage": ui.usage, "session": session.CURRENT}
    usage = {}

    with evaluate.isolated(workspace, tmp_path / "sessions", "eval-x-1", usage) as cwd:
        assert cwd == workspace.resolve() and Path(os.getcwd()) == workspace.resolve()
        assert permissions.PROJECT == workspace.resolve() and sandbox.PROJECT == workspace.resolve()
        assert permissions.check("write_file", {"path": str(workspace / "a.txt"), "content": ""}) == ("allow", None)
        assert hooks.CONFIG_PATHS[-1] == workspace.resolve() / ".agents" / "hooks.json" and hooks.SESSION_CONTEXT == []
        assert todos.TODOS == [] and plan.PLAN is None and plan.MODE == "act" and context.LAST_STATUS == {}
        assert session.CURRENT == "eval-x-1" and session.WRITTEN == 0 and session.SESSION_DIR == tmp_path / "sessions"
        assert ui.approve("anything") is True
        ui.usage({"prompt_tokens": 5, "completion_tokens": 2, "reasoning_tokens": None, "cost": 0.5})
        ui.usage({"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.25})
        session.save([{"role": "user", "content": "hi"}])
        assert (tmp_path / "sessions" / "eval-x-1.jsonl").exists()

    assert usage == {"prompt_tokens": 6, "completion_tokens": 3, "cost": 0.75}
    assert os.getcwd() == original["cwd"] and permissions.PROJECT == original["project"] and sandbox.PROJECT == original["sandbox"]
    assert ui.approve is original["approve"] and ui.usage is original["usage"]
    assert session.CURRENT == original["session"] and session.SESSION_DIR == tmp_path / "sessions"
    assert todos.TODOS == [{"content": "old", "activeForm": "old", "status": "pending"}]
    assert plan.PLAN == {"goal": "old"} and context.LAST_STATUS == {"stale.py": "M"} and hooks.SESSION_CONTEXT == ["branch policy"]
    todos.TODOS.clear()


def test_isolated_gives_the_run_an_empty_memory_store_and_the_workspace_skills(tmp_path, monkeypatch):
    real = tmp_path / "real-memory"
    monkeypatch.setattr(memory, "MEMORY_DIRS", [real / "project", real / "_user"])
    memory.remember("house-style", "how we write", "short lines", scope="user")
    monkeypatch.setattr(skills, "SKILLS", {"home-skill": {"description": "from ~", "path": tmp_path / "SKILL.md"}})
    workspace = tmp_path / "ws"
    (workspace / ".agents" / "skills" / "ws-skill").mkdir(parents=True)
    (workspace / ".agents" / "skills" / "ws-skill" / "SKILL.md").write_text("---\nname: ws-skill\ndescription: for this task\n---\nbody\n", encoding="utf-8")

    with evaluate.isolated(workspace, tmp_path / "run" / "sessions", "eval-x-3", {}):
        assert memory.find_memories() == {}  # the user's memories are out of sight...
        assert "house-style" not in context.reminder()["content"]
        memory.remember("scratch", "from the run", "nothing lasting")
        assert list(skills.SKILLS) == ["ws-skill"]  # ...and only the workspace's skills are offered
    assert list(memory.find_memories()) == ["house-style"]  # ...and untouched by the run's own writes
    assert not (real / "project" / "scratch.md").exists() and (tmp_path / "run" / "memory" / "project" / "scratch.md").exists()
    assert list(skills.SKILLS) == ["home-skill"]


def test_the_judge_does_not_see_cache_directories(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_text("")
    (tmp_path / ".pytest_cache" / "v").mkdir(parents=True)
    (tmp_path / ".pytest_cache" / "v" / "n").write_text("")
    (tmp_path / "app.py").write_text("")
    assert evaluate.file_list(tmp_path) == "app.py"


def test_isolated_restores_everything_after_a_crash_and_kills_jobs(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    before = os.getcwd()
    with pytest.raises(RuntimeError):
        with evaluate.isolated(workspace, tmp_path / "sessions", "eval-x-2", {}):
            jobs.bash_background(f'"{sys.executable}" -c "import time; time.sleep(30)"')
            assert len(jobs.running()) == 1
            raise RuntimeError("boom")
    assert os.getcwd() == before and jobs.running() == [] and jobs.JOBS == {}


def test_cost_is_summed_when_the_usage_carries_one(monkeypatch):
    fake, _ = scripted(SCRIPTS, usage=USAGE | {"cost": 0.001})
    monkeypatch.setattr(agent, "call_llm", fake)
    task = evaluate.load_suite(EVALS)[2]
    result = evaluate.run_task(task, run=1, suite_name="evals")
    assert result.passed and result.cost == 0.002 and result.prompt_tokens == 20


# ------------------------------------------------------------ the command


def test_eval_subcommand_runs_the_suite_and_exits_with_its_status(model, suite, capsys):
    with pytest.raises(SystemExit) as stop:
        agent.main(["eval", str(suite), "--repeat", "1"])
    assert stop.value.code == 1  # fix_test failed
    out = capsys.readouterr().out
    assert "write_hello" in out and "1/1" in out and "0/1" in out and "2/3" in out
    assert f"report: {suite / evaluate.REPORT_NAME}" in out
    assert json.loads((suite / evaluate.REPORT_NAME).read_text(encoding="utf-8"))["summary"]["passed"] == 2


def test_plain_harness_and_its_flags_still_parse():
    assert agent.parser().parse_args([]).command is None
    cli = agent.parser().parse_args(["--resume", "--debug"])
    assert cli.resume and cli.debug and cli.command is None
    assert agent.parser().parse_args(["-p", "hi"]).print == "hi"
    cli = agent.parser().parse_args(["eval", "evals", "--repeat", "3", "--keep"])
    assert (cli.command, cli.suite, cli.repeat, cli.keep) == ("eval", "evals", 3, True)


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
