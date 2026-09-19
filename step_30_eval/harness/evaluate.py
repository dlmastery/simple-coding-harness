"""Step 30 - the evaluation harness: run a suite of tasks through the loop
and score every run.

A suite is a directory of task directories. Each task holds `task.md` (the
prompt), an optional `workspace/` (copied into a fresh temp directory before
the run) and one checker: `check.py` (run with the workspace as cwd, exit 0
is a pass), `expect.txt` (a substring of the final answer) or `judge.md`
(instructions for an LLM judge that must answer PASS or FAIL first).

Every task runs `agent.turn` in-process, in a fresh copy of its workspace,
with a fresh message list and a fresh session. The harness keeps state at
module level, and some of that state was computed from the working
directory when the module was imported. The `isolated` context manager
swaps that state for the task and puts it back afterwards.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from . import agent, context, hooks, jobs, llm, memory, permissions, plan, sandbox, session, skills, todos
from .ui import ui

# a note from the loop that means the turn did not finish, whatever the checker would say
TROUBLE = ("model call failed", "stopped after")

CHECKERS = ("check.py", "expect.txt", "judge.md")

TOKEN_KEYS = ("prompt_tokens", "completion_tokens", "cached_tokens")  # summed per run

CHECK_TIMEOUT = 300  # seconds a check.py may take

REPORT_NAME = "eval_report.json"

JUDGE_SYSTEM = (
    "You grade the work of a coding agent. Read the grading instructions, "
    "the task, the agent's final answer and the list of files left in the "
    "workspace. Reply with the single word PASS or FAIL on the first line, "
    "then one line that says why."
)


@dataclass
class Task:
    """One task directory, read once."""

    name: str
    path: Path
    prompt: str
    checker: str  # check.py, expect.txt or judge.md


@dataclass
class Result:
    """What one run of one task produced."""

    task: str
    run: int
    passed: bool
    seconds: float
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    cost: float | None
    answer: str
    detail: str      # what the checker said
    workspace: str   # the temp copy the run worked in


# ------------------------------------------------------------------ suite


def find_checker(task_dir):
    """The first checker file present, in CHECKERS order, or None."""
    return next((name for name in CHECKERS if (task_dir / name).exists()), None)


def load_suite(suite_dir):
    """Every task directory with a task.md and a checker, sorted by name."""
    suite_dir = Path(suite_dir)
    if not suite_dir.is_dir():
        raise FileNotFoundError(f"suite directory not found: {suite_dir}")
    tasks = []
    for task_dir in sorted(p for p in suite_dir.iterdir() if p.is_dir()):
        prompt_file = task_dir / "task.md"
        checker = find_checker(task_dir)
        if not prompt_file.exists() or checker is None:
            ui.note(f"skipped {task_dir.name}: needs task.md and one of {', '.join(CHECKERS)}")
            continue
        tasks.append(Task(task_dir.name, task_dir, prompt_file.read_text(encoding="utf-8").strip(), checker))
    return tasks


# -------------------------------------------------------------- isolation


@contextmanager
def isolated(workspace, session_dir, session_id, usage, notes=None):
    """Run one task as if the harness had started in `workspace`.

    Module-level state that was computed from the working directory at
    import time is pointed at the workspace: the permission and sandbox
    project roots, the hook config paths, the git status baseline, the
    skills. State that accumulates during a chat is emptied: the todo list,
    the plan and the mode, the session context from hooks, the background
    jobs. The session module writes to a fresh file under `session_dir`,
    and the memory store is an empty one next to it, so a run neither sees
    nor changes what the user's own chats remembered. `ui.approve` answers
    yes, every usage dict the loop reports is summed into `usage`, and every
    note the loop prints is kept in `notes`. Everything is restored on the
    way out, whatever happened inside, and any job the task left running is
    killed.
    """
    saved = {
        "cwd": os.getcwd(),
        "session": (session.SESSION_DIR, session.CURRENT, session.WRITTEN),
        "permissions": permissions.PROJECT,
        "sandbox": sandbox.PROJECT,
        "hooks": (hooks.CONFIG_PATHS, list(hooks.SESSION_CONTEXT)),
        "memory": memory.MEMORY_DIRS,
        "skills": (skills.SKILL_DIRS, skills.SKILLS),
        "status": context.LAST_STATUS,
        "todos": list(todos.TODOS),
        "plan": (plan.MODE, plan.PLAN, list(plan.FEEDBACK)),
        "approve": ui.approve,
        "usage": ui.usage,
        "note": ui.note,
    }
    workspace = Path(workspace).resolve()
    os.chdir(workspace)
    session.SESSION_DIR, session.CURRENT, session.WRITTEN = Path(session_dir), session_id, 0
    permissions.PROJECT = workspace
    sandbox.PROJECT = workspace
    hooks.CONFIG_PATHS = [hooks.CONFIG_PATHS[0], workspace / ".agents" / "hooks.json"]
    hooks.SESSION_CONTEXT.clear()
    memory.MEMORY_DIRS = [Path(session_dir).parent / "memory" / "project", Path(session_dir).parent / "memory" / "_user"]
    skills.SKILL_DIRS = [workspace / ".agents" / "skills"]
    skills.SKILLS = skills.find_skills()
    context.LAST_STATUS = context.git_status()
    todos.TODOS.clear()
    plan.set_mode("plan")  # forgets the old plan and its feedback...
    plan.set_mode("act")   # ...and the task runs with every tool
    jobs.kill_all()
    ui.approve = lambda reason: True
    lock = threading.Lock()  # subagent threads report usage too

    def record(stats):
        with lock:
            for key, value in (stats or {}).items():
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
        saved["usage"](stats)

    def keep(text):
        if notes is not None:
            notes.append(text)
        saved["note"](text)

    ui.usage = record
    ui.note = keep
    try:
        yield workspace
    finally:
        jobs.kill_all()  # a job the task left behind must not outlive its workspace
        os.chdir(saved["cwd"])
        session.SESSION_DIR, session.CURRENT, session.WRITTEN = saved["session"]
        permissions.PROJECT = saved["permissions"]
        sandbox.PROJECT = saved["sandbox"]
        hooks.CONFIG_PATHS = saved["hooks"][0]
        hooks.SESSION_CONTEXT[:] = saved["hooks"][1]
        memory.MEMORY_DIRS = saved["memory"]
        skills.SKILL_DIRS, skills.SKILLS = saved["skills"]
        context.LAST_STATUS = saved["status"]
        todos.TODOS[:] = saved["todos"]
        plan.MODE, plan.PLAN, plan.FEEDBACK[:] = saved["plan"]
        ui.approve = saved["approve"]
        ui.usage = saved["usage"]
        ui.note = saved["note"]


def system_prompt_for(workspace):
    """The system prompt with its working-directory line pointed at the workspace."""
    return llm.build_system_prompt(str(workspace))


# --------------------------------------------------------------- checking


NOISE = {"__pycache__", ".pytest_cache"}  # left by the agent's own test runs; not the judge's business


def file_list(workspace):
    """Every file under the workspace, relative, sorted, one per line."""
    paths = sorted(p.relative_to(workspace).as_posix() for p in Path(workspace).rglob("*") if p.is_file() and not NOISE & set(p.parts))
    return "\n".join(paths) or "(empty)"


def run_check_py(task, workspace):
    """Run the task's check.py with the workspace as cwd. Exit 0 is a pass."""
    try:
        completed = subprocess.run(
            [sys.executable, str(task.path / "check.py")],
            cwd=workspace, capture_output=True, text=True, timeout=CHECK_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, f"check.py took more than {CHECK_TIMEOUT}s"
    output = (completed.stdout + completed.stderr).strip()
    tail = "\n".join(output.splitlines()[-10:])
    return completed.returncode == 0, f"check.py exited {completed.returncode}" + (f"\n{tail}" if tail else "")


def run_expect(task, answer):
    """Pass when the expected text appears in the final answer."""
    expected = (task.path / "expect.txt").read_text(encoding="utf-8").strip()
    found = expected in answer
    return found, f"expected {expected!r} {'found' if found else 'missing'} in the answer"


def run_judge(task, workspace, answer):
    """Ask the model to grade the run. The first word of its reply decides."""
    instructions = (task.path / "judge.md").read_text(encoding="utf-8").strip()
    request = (
        f"<instructions>\n{instructions}\n</instructions>\n\n"
        f"<task>\n{task.prompt}\n</task>\n\n"
        f"<answer>\n{answer or '(no answer)'}\n</answer>\n\n"
        f"<workspace>\n{file_list(workspace)}\n</workspace>"
    )
    message, _ = llm.call_llm([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": request}], tools=[])
    verdict = (message.content or "").strip()
    first = verdict.split(None, 1)[0].strip(".:,").upper() if verdict else ""
    return first == "PASS", f"judge said: {verdict[:200] or '(nothing)'}"


def check(task, workspace, answer):
    """Run the task's checker. Returns (passed, detail)."""
    if task.checker == "check.py":
        return run_check_py(task, workspace)
    if task.checker == "expect.txt":
        return run_expect(task, answer)
    return run_judge(task, workspace, answer)


# ---------------------------------------------------------------- running


def run_task(task, run=1, suite_name="suite", keep=False):
    """One run of one task in a fresh temp workspace. Returns a Result."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-{task.name}-"))
    workspace = root / "workspace"
    if (task.path / "workspace").is_dir():
        shutil.copytree(task.path / "workspace", workspace)
    else:
        workspace.mkdir()
    session_id = f"eval-{suite_name}-{task.name}-{run}-{datetime.now():%Y%m%d-%H%M%S-%f}"

    usage = {}
    notes = []
    answer = ""
    started = time.perf_counter()
    with isolated(workspace, root / "sessions", session_id, usage, notes) as cwd:
        messages = [{"role": "system", "content": system_prompt_for(cwd)}]
        try:
            messages = agent.turn(messages, task.prompt)
            answer = agent.last_reply(messages)
            trouble = [note for note in notes if note.startswith(TROUBLE)]
            if trouble:  # the loop kept the transcript valid, but the turn did not finish
                raise RuntimeError(trouble[0])
            passed, detail = check(task, cwd, answer)  # a judge that cannot be reached fails the run too
        except Exception as failed:  # noqa: BLE001 - one broken run must not end the suite
            passed, detail = False, f"run failed: {type(failed).__name__}: {failed}"
        seconds = time.perf_counter() - started

    if not keep:
        shutil.rmtree(root, ignore_errors=True)
    return Result(
        task=task.name, run=run, passed=passed, seconds=round(seconds, 3),
        prompt_tokens=int(usage.get("prompt_tokens", 0)),
        completion_tokens=int(usage.get("completion_tokens", 0)),
        cached_tokens=int(usage.get("cached_tokens", 0)),
        cost=usage.get("cost"), answer=answer, detail=detail, workspace=str(workspace),
    )


def summarise(name, results):
    """Totals over a list of results, for one task or the whole suite."""
    passed = sum(1 for r in results if r.passed)
    costs = [r.cost for r in results if r.cost is not None]
    return {
        "name": name,
        "runs": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 3) if results else 0.0,
        "seconds": round(sum(r.seconds for r in results), 3),
        "prompt_tokens": sum(r.prompt_tokens for r in results),
        "completion_tokens": sum(r.completion_tokens for r in results),
        "cached_tokens": sum(r.cached_tokens for r in results),
        "cost": round(sum(costs), 6) if costs else None,
    }


def build_report(suite_dir, tasks, results, repeat, started):
    """The report dict: per-task totals with every result, and a suite total."""
    return {
        "suite": suite_dir.name,
        "model": llm.MODEL,
        "started": started.isoformat(timespec="seconds"),
        "repeat": repeat,
        "tasks": [
            summarise(task.name, [r for r in results if r.task == task.name])
            | {"checker": task.checker, "results": [asdict(r) for r in results if r.task == task.name]}
            for task in tasks
        ],
        "summary": summarise(suite_dir.name, results) | {"tasks": len(tasks)},
    }


def run_suite(suite_dir, repeat=1, keep=False):
    """Run every task `repeat` times. Returns the report dict and writes it to the suite dir.

    The report is written whatever ends the loop, so a ctrl-c halfway
    through a long --repeat leaves the runs that finished on disk.
    """
    suite_dir = Path(suite_dir)
    tasks = load_suite(suite_dir)
    started = datetime.now()
    results = []
    try:
        for task in tasks:
            for run in range(1, repeat + 1):
                ui.note(f"eval {task.name} run {run}/{repeat}")
                results.append(run_task(task, run, suite_dir.name, keep))
    finally:
        report = build_report(suite_dir, tasks, results, repeat, started)
        (suite_dir / REPORT_NAME).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(cli):
    """The `harness eval` subcommand: run, print the table, exit 0 only if every run passed."""
    ui.headless()  # progress on stderr; the table and the report path on stdout
    report = run_suite(cli.suite, repeat=cli.repeat, keep=cli.keep)
    ui.eval_table(report)
    print(f"report: {Path(cli.suite) / REPORT_NAME}")
    summary = report["summary"]
    return 0 if summary["runs"] and summary["passed"] == summary["runs"] else 1
