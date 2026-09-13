"""Step 38 offline tests. No model runs: a scripted fake plays the agent and
writes the reference solution into the workspace, so the whole capstone
pipeline (headless run, manifest, checks, report files) is exercised with
no key. The checks themselves run for real against capstone/reference and
against an empty workspace. fastapi and httpx must be installed.
"""

import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

STEP = Path(__file__).resolve().parent
CAPSTONE = STEP / "capstone"
EVALS = CAPSTONE / "evals"
REFERENCE = CAPSTONE / "reference"
sys.path.insert(0, str(CAPSTONE))

import run as capstone  # noqa: E402 - capstone/run.py

from harness import agent, budget, checkpoint, context, evaluate, hooks, instructions, llm, memory, permissions, plan, session, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

USAGE = {"prompt_tokens": 100, "completion_tokens": 20, "reasoning_tokens": None, "cached_tokens": 40}
CHECKS = ["1_server_starts", "2_crud", "3_tests_pass", "4_readme", "5_no_outside_changes"]


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


def write(cid, name):
    """A write_file call that copies one reference file into the workspace."""
    return call(cid, "write_file", {"path": name, "content": (REFERENCE / name).read_text(encoding="utf-8")})


def scripted(steps):
    """A fake call_llm that answers step by step, and the list of what it saw."""
    seen = []
    lock = threading.Lock()

    def fake(messages, tools=None, on_delta=None):
        with lock:
            seen.append({"cwd": os.getcwd(), "system": messages[0]["content"], "users": [m["content"] for m in messages if m["role"] == "user" and isinstance(m["content"], str)]})
        index = sum(1 for m in messages if m["role"] == "assistant")
        return steps[min(index, len(steps) - 1)], dict(USAGE)

    return fake, seen


SOLVE = [
    use(write("w1", "app.py")),
    use(write("w2", "test_app.py"), write("w3", "README.md")),
    use(call("b1", "bash", {"command": f"{Path(sys.executable).name} -m pytest -q -p no:cacheprovider"})),
    say("Built app.py, test_app.py and README.md. The tests pass."),
]


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """No hooks, no real home or session store, no screen, a fresh checkpoint root."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(instructions, "LOADED", [])
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(budget, "WARNED", set())
    monkeypatch.setattr(tools, "LOADED", set())
    monkeypatch.setattr(permissions, "SESSION_RULES", {})
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "note", lambda text: None)
    monkeypatch.delenv("CAPSTONE_MANIFEST", raising=False)


@pytest.fixture
def evals(tmp_path):
    """A copy of the shipped suite, so eval_report.json never lands in capstone/evals."""
    shutil.copytree(EVALS, tmp_path / "evals", ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path / "evals"


@pytest.fixture
def model(monkeypatch):
    """The scripted model that writes the reference solution and runs pytest."""
    fake, seen = scripted(SOLVE)
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    monkeypatch.setattr(llm, "MODEL", "gpt-4.1-mini")
    return seen


def same_manifest(tmp_path, monkeypatch, before=None, after=None):
    """Point CAPSTONE_MANIFEST at a manifest file; identical before and after by default."""
    before = {"outside/notes.txt": "a", "sibling.md": "b"} if before is None else before
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"before": before, "after": before if after is None else after}), encoding="utf-8")
    monkeypatch.setenv("CAPSTONE_MANIFEST", str(path))
    return path


def by_name(report):
    return {t["name"]: t["results"][-1] for t in report["tasks"]}


# --------------------------------------------------------------- the checks


def test_the_suite_has_five_check_tasks():
    tasks = evaluate.load_suite(EVALS)
    assert [t.name for t in tasks] == CHECKS
    assert all(t.checker == "check.py" for t in tasks)


def test_the_reference_solution_passes_every_check(evals, tmp_path, monkeypatch):
    same_manifest(tmp_path, monkeypatch)
    never = lambda *a, **k: pytest.fail("the agent must not run when a workspace is graded")  # noqa: E731
    monkeypatch.setattr(agent, "call_llm", never)
    monkeypatch.setattr(llm, "call_llm", never)

    report = evaluate.run_suite(evals, workspace=REFERENCE)

    assert report["workspace"] == str(REFERENCE.resolve())
    assert report["summary"]["runs"] == 5 and report["summary"]["passed"] == 5
    results = by_name(report)
    for name in CHECKS:
        assert results[name]["passed"], results[name]["detail"]
        assert "PASS:" in results[name]["detail"]
        assert results[name]["answer"] == ""  # no turn ran
    assert "7 passed" in results["3_tests_pass"]["detail"]
    assert "2 files outside the workspace" in results["5_no_outside_changes"]["detail"]
    # the reference itself is untouched: the checks ran in a copy
    assert sorted(p.name for p in REFERENCE.iterdir() if p.name != "__pycache__") == ["README.md", "app.py", "test_app.py"]


def test_every_check_fails_on_an_empty_workspace(evals, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    report = evaluate.run_suite(evals, workspace=empty)
    assert report["summary"]["passed"] == 0 and report["summary"]["runs"] == 5
    results = by_name(report)
    assert "app.py is missing" in results["1_server_starts"]["detail"]
    assert "app.py is missing" in results["2_crud"]["detail"]
    assert "no test_*.py file" in results["3_tests_pass"]["detail"]
    assert "README.md is missing" in results["4_readme"]["detail"]
    assert "CAPSTONE_MANIFEST is not set" in results["5_no_outside_changes"]["detail"]


def test_the_outside_check_reports_added_removed_and_changed_files(tmp_path, monkeypatch):
    same_manifest(tmp_path, monkeypatch, before={"keep.txt": "1", "gone.txt": "2", "edited.txt": "3"}, after={"keep.txt": "1", "edited.txt": "9", "new.txt": "4"})
    completed = subprocess.run([sys.executable, str(EVALS / "5_no_outside_changes" / "check.py")], cwd=tmp_path, capture_output=True, text=True)
    assert completed.returncode == 1
    assert "added: new.txt" in completed.stdout and "removed: gone.txt" in completed.stdout and "changed: edited.txt" in completed.stdout
    assert "1 added, 1 removed, 1 changed" in completed.stdout


def test_a_broken_app_fails_the_start_and_crud_checks_with_the_reason(evals, tmp_path):
    broken = tmp_path / "broken"
    shutil.copytree(REFERENCE, broken, ignore=shutil.ignore_patterns("__pycache__"))
    (broken / "app.py").write_text("import fastapi\napplication = fastapi.FastAPI()\n", encoding="utf-8")
    report = evaluate.run_suite(evals, workspace=broken)
    results = by_name(report)
    assert not results["1_server_starts"]["passed"] and "no module-level variable named app" in results["1_server_starts"]["detail"]
    assert not results["2_crud"]["passed"]
    assert not results["3_tests_pass"]["passed"]  # the reference tests import app.app
    assert results["4_readme"]["passed"]


# ----------------------------------------------------------------- run.py


def test_run_writes_the_report_the_scorecard_and_the_transcript(evals, model, tmp_path):
    out = tmp_path / "out"
    report = capstone.run(evals=evals, out=out)

    assert set(report) == {
        "brief", "model", "started", "seconds", "turns", "continuations", "model_calls", "tool_calls", "tool_call_total", "tool_errors",
        "usage", "cost", "cost_note", "notes", "answer", "workspace_files", "outside_changed", "steps", "evals", "score",
    }
    assert report["model"] == "gpt-4.1-mini" and report["turns"] == 1 and report["model_calls"] == 4
    assert report["tool_calls"] == {"write_file": 3, "bash": 1} and report["tool_call_total"] == 4 and report["tool_errors"] == 0
    assert report["usage"] == {"prompt_tokens": 400, "completion_tokens": 80, "cached_tokens": 160, "reasoning_tokens": 0}
    assert report["cost"] == pytest.approx((240 * 0.40 + 80 * 1.60 + 160 * 0.10) / 1_000_000) and report["cost_note"] == "estimated from list prices"
    assert report["answer"].startswith("Built app.py")
    assert report["workspace_files"] == ["README.md", "app.py", "test_app.py"]  # pytest's caches are left out
    assert report["outside_changed"] == []
    assert report["score"] == {"passed": 5, "total": 5}
    assert report["evals"]["summary"]["passed"] == 5 and report["evals"]["workspace"].endswith("workspace")

    # the steps summarise the transcript: the brief, then one entry per model call
    assert report["steps"][0]["role"] == "user" and report["steps"][0]["text"].startswith("Build a small todo API")
    assert [s["role"] for s in report["steps"][1:]] == ["assistant"] * 4
    assert [c["tool"] for c in report["steps"][2]["calls"]] == ["write_file", "write_file"]
    assert report["steps"][2]["calls"][0]["args"] == "test_app.py" and report["steps"][2]["calls"][0]["result"] == "Wrote test_app.py"
    assert "passed" in report["steps"][3]["calls"][0]["result"]

    written = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert written["score"] == report["score"]
    card = (out / "SCORECARD.md").read_text(encoding="utf-8")
    assert "## Score: 5/5" in card and "| 2_crud | pass |" in card and "| model calls | 4 |" in card
    assert "write_file 3, bash 1" in card and "Nothing: no tool call returned an error" in card
    assert report["continuations"] == []
    transcript = (out / "transcript.md").read_text(encoding="utf-8")
    assert "## 1. user" in transcript and "call `write_file`:" in transcript and "tool result `bash`" in transcript
    assert not (evals / evaluate.REPORT_NAME).exists()  # folded into report.json
    # the model saw the temp workspace, and nothing was written into the step directory
    assert all("capstone-" in s["cwd"] for s in model)
    assert not (CAPSTONE / "app.py").exists() and not (STEP / "app.py").exists()


def test_a_turn_that_stops_at_max_calls_gets_a_continue_message(evals, model, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "MAX_CALLS", 2)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["turns"] == 2 and report["model_calls"] == 4 and report["score"]["passed"] == 5
    assert any(n.startswith("stopped after 2 model calls") for n in report["notes"])
    assert report["continuations"] == [{"turn": 2, "reason": "the turn stopped at MAX_CALLS", "message": capstone.CONTINUE}]
    assert "turn 2 was sent because the turn stopped at MAX_CALLS" in (tmp_path / "out" / "SCORECARD.md").read_text(encoding="utf-8")
    users = [s["text"] for s in report["steps"] if s["role"] == "user"]
    assert len(users) == 2 and users[1].startswith("Continue where you left off")
    assert any(u.startswith("Continue where you left off") for u in model[2]["users"])  # the third call saw the nudge...
    assert not any(u.startswith("Continue where you left off") for u in model[1]["users"])  # ...and the second did not


def test_an_answer_that_ends_with_a_question_gets_the_nobody_answer(evals, tmp_path, monkeypatch):
    steps = SOLVE[:2] + [say("app.py and the tests are in. Shall I write the README now?")] + SOLVE[2:]
    fake, seen = scripted(steps)
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["turns"] == 2 and report["model_calls"] == 5 and report["score"]["passed"] == 5
    assert report["continuations"] == [{"turn": 2, "reason": "the answer ended with a question", "message": capstone.NOBODY}]
    assert any(u == capstone.NOBODY for u in seen[3]["users"]) and not any(u == capstone.NOBODY for u in seen[2]["users"])
    assert report["answer"].startswith("Built app.py")  # the summary, not the question


def test_the_third_turn_is_the_last_even_without_an_answer(evals, tmp_path, monkeypatch):
    fake, seen = scripted([say("Which database should I use?")])  # asks every time
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["turns"] == 3 and report["model_calls"] == 3 and len(seen) == 3
    assert [c["reason"] for c in report["continuations"]] == ["the answer ended with a question"] * 2


def test_a_write_outside_the_workspace_fails_the_last_check(evals, tmp_path, monkeypatch):
    steps = [use(write("w1", "app.py"), call("x1", "write_file", {"path": "../sibling.md", "content": "changed\n"}), call("x2", "write_file", {"path": "../outside/new.txt", "content": "new\n"}))] + SOLVE[1:]
    fake, _ = scripted(steps)
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["outside_changed"] == ["outside/new.txt", "sibling.md"]
    assert report["score"] == {"passed": 4, "total": 5}
    detail = by_name(report["evals"])["5_no_outside_changes"]["detail"]
    assert "added: outside/new.txt" in detail and "changed: sibling.md" in detail
    assert "| 5_no_outside_changes | FAIL |" in (tmp_path / "out" / "SCORECARD.md").read_text(encoding="utf-8")


def test_a_crashed_run_still_gets_a_report(evals, tmp_path, monkeypatch):
    def broken(messages, tools=None, on_delta=None):
        raise RuntimeError("the model exploded")

    monkeypatch.setattr(agent, "call_llm", broken)
    monkeypatch.setattr(llm, "call_llm", broken)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["notes"] == ["run failed: RuntimeError: the model exploded"]
    assert report["model_calls"] == 0 and report["answer"] == "" and report["continuations"] == []
    assert report["score"] == {"passed": 1, "total": 5}  # only the outside check passes: nothing ran
    assert "loop note: run failed: RuntimeError" in (tmp_path / "out" / "SCORECARD.md").read_text(encoding="utf-8")


def test_tool_errors_are_counted_and_listed(evals, tmp_path, monkeypatch):
    steps = [use(call("e1", "bash", {"command": "python -c \"import nothing_here\""}), call("e2", "bash", {"command": "python -m pytest -q -p no:cacheprovider missing_test.py"}))] + SOLVE
    fake, _ = scripted(steps)
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["tool_errors"] == 2 and report["tool_calls"]["bash"] == 3  # a traceback, and pytest on a missing file
    assert [c["error"] for c in report["steps"][1]["calls"]] == [True, True]
    assert capstone.PROBLEM_RE.search(".FFF.F  [100%]\n=========== FAILURES ===========\n")
    assert not capstone.PROBLEM_RE.search("7 passed in 1.2s")
    card = (tmp_path / "out" / "SCORECARD.md").read_text(encoding="utf-8")
    assert "- step 2: `bash` python -c" in card


def test_a_tool_that_raises_is_an_error_result_not_a_crash(evals, tmp_path, monkeypatch):
    steps = [use(call("r1", "read_file", {"path": "cli.py"}), call("r2", "str_replace", {"path": "nowhere.py", "old_str": "a", "new_str": "b"}))] + SOLVE
    fake, _ = scripted(steps)
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    report = capstone.run(evals=evals, out=tmp_path / "out")
    assert report["notes"] == [] and report["score"]["passed"] == 5  # the run went on to the solution
    first, second = report["steps"][1]["calls"]
    assert first["result"].startswith("Error: FileNotFoundError:") and first["error"]
    assert second["result"].startswith("Error: FileNotFoundError:") and second["error"]
    assert report["tool_errors"] == 2


# ---------------------------------------------------------- the eval flag


def test_run_suite_without_a_workspace_still_runs_the_agent(tmp_path, monkeypatch):
    shutil.copytree(STEP / "evals" / "write_hello", tmp_path / "suite" / "write_hello")
    fake, seen = scripted([use(call("w1", "write_file", {"path": "hello.txt", "content": "hello\n" * 5})), say("done")])
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    report = evaluate.run_suite(tmp_path / "suite")
    assert report["workspace"] is None and report["summary"]["passed"] == 1 and len(seen) == 2
    assert report["tasks"][0]["results"][0]["answer"] == "done"


def test_a_relative_suite_path_still_finds_the_checks(tmp_path, monkeypatch):
    shutil.copytree(EVALS, tmp_path / "evals", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REFERENCE, tmp_path / "reference", ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.chdir(tmp_path)
    report = evaluate.run_suite("evals", workspace="reference")  # both relative; the checks run after a chdir
    assert by_name(report)["4_readme"]["passed"] and by_name(report)["1_server_starts"]["passed"]
    assert os.getcwd() == str(tmp_path)


def test_the_eval_subcommand_takes_a_workspace_flag(evals, tmp_path, monkeypatch, capsys):
    same_manifest(tmp_path, monkeypatch)
    cli = agent.parser().parse_args(["eval", str(evals), "--workspace", str(REFERENCE)])
    assert cli.workspace == str(REFERENCE)
    with pytest.raises(SystemExit) as stop:
        agent.main(["eval", str(evals), "--workspace", str(REFERENCE)])
    assert stop.value.code == 0
    assert "5/5" in capsys.readouterr().out


def test_run_py_parses_its_flags():
    assert capstone.MAX_TURNS == 3 and capstone.TASK.exists() and capstone.EVALS.is_dir()
    assert capstone.short_args("bash", json.dumps({"command": "dir"})) == "dir"
    assert capstone.short_args("write_file", json.dumps({"path": "a.py", "content": "x"})) == "a.py"
    assert capstone.short_args("bash", "{not json") == "{not json"
