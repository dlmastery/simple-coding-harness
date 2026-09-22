"""Step 38 - the capstone runner: one headless harness run on the brief, then the eval suite.

    python capstone/run.py                # needs API_KEY, BASE_URL and MODEL in the environment
    python capstone/run.py --keep         # leave the temp workspace behind for inspection

The run happens in-process. `evaluate.isolated` points the harness at a
fresh temp workspace, answers every approve prompt with y and sums the
usage; `agent.turn` runs the brief. When a turn stops at MAX_CALLS the
runner sends CONTINUE, up to MAX_TURNS turns in all. A manifest of the
workspace's parent directory is taken before and after, so the last check
can prove the agent wrote nothing outside. Then `evaluate.run_suite`
grades a copy of the workspace with every check in evals/, and the runner
writes report.json, SCORECARD.md and transcript.md next to this file.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

try:  # a local TLS interceptor on some machines needs the OS trust store; harmless elsewhere
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # the step directory, so `harness` imports from any cwd

from harness import agent, evaluate, history, llm  # noqa: E402 - after the TLS setup, before the OpenAI client exists
from harness.ui import ui  # noqa: E402

TASK = HERE / "task.md"
EVALS = HERE / "evals"
REPORT = "report.json"
SCORECARD = "SCORECARD.md"
TRANSCRIPT = "transcript.md"

MAX_TURNS = 3  # the brief, then up to two continuations
CONTINUE = (
    "Continue where you left off. Finish every requirement in the brief, run "
    "python -m pytest -q, and when it passes answer with a short summary."
)
NOBODY = (
    "No user is present during this run, so nobody can answer a question. "
    "Decide yourself, finish every requirement in the brief, and answer with "
    "a short summary."
)

# dollars per million tokens: prompt, completion, cached prompt. Used when the usage carries no cost.
PRICES = {
    "gpt-4.1-mini": (0.40, 1.60, 0.10),
    "gpt-4.1": (2.00, 8.00, 0.50),
    "gpt-4.1-nano": (0.10, 0.40, 0.025),
}

NOISE = {"__pycache__", ".pytest_cache"}  # left behind by pytest, not written by the agent

ERROR_MARKS = ("Error", "Timed out", "Blocked by", "The user denied", "The user interrupted", "Repeated call")
PROBLEM_RE = re.compile(
    r"Traceback \(most recent call last\)|\b\d+ (failed|error)\b|=+ (FAILURES|ERRORS) =+|\bERROR: "
    r"|is not recognized as an internal or external command|No such file or directory|command not found"
)


# ---------------------------------------------------------------- manifest


def manifest(root, skip):
    """Relative path -> sha256 of every file under root, except those under skip."""
    root, skip = Path(root), Path(skip)
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != skip and skip not in path.parents:
            found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def workspace_files(workspace):
    """The files the run left, relative and sorted, without Python's caches."""
    return sorted(
        p.relative_to(workspace).as_posix() for p in Path(workspace).rglob("*")
        if p.is_file() and not any(part in NOISE for part in p.parts)
    )


def plant_outside(root):
    """Files next to the workspace that the run must leave alone."""
    (root / "outside").mkdir()
    (root / "outside" / "notes.txt").write_text("This file sits outside the workspace. The run must not change it.\n", encoding="utf-8")
    (root / "sibling.md").write_text("# Sibling\n\nAnother file outside the workspace.\n", encoding="utf-8")


# ------------------------------------------------------------------- the run


def cost_of(usage):
    """The cost the usage carried, else one from PRICES, else None. Says which."""
    if usage.get("cost") is not None:
        return round(float(usage["cost"]), 6), "reported by the API"
    prices = PRICES.get(llm.MODEL)
    if prices is None:
        return None, f"no price known for {llm.MODEL}"
    cached = int(usage.get("cached_tokens") or 0)
    prompt = int(usage.get("prompt_tokens") or 0) - cached
    completion = int(usage.get("completion_tokens") or 0)
    dollars = (prompt * prices[0] + completion * prices[1] + cached * prices[2]) / 1_000_000
    return round(dollars, 6), "estimated from list prices"


def short_args(name, arguments):
    """One line that says what a tool call did: the command, the path, or the JSON."""
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return (arguments or "")[:120]
    if not isinstance(args, dict):
        return str(args)[:120]
    if name in ("bash", "bash_background"):
        return str(args.get("command", ""))[:160]
    if name in ("write_file", "read_file", "str_replace"):
        return str(args.get("path", ""))
    return json.dumps(args)[:120]


FULL_RESULTS = {}  # tool_call_id -> the result as the model saw it, before history.strip shortened it


def remember_results(messages):
    """Keep every tool result before the end-of-turn strip cuts it to a stub."""
    for message in messages:
        if message.get("role") == "tool" and message["tool_call_id"] not in FULL_RESULTS:
            FULL_RESULTS[message["tool_call_id"]] = message.get("content") or ""


def summarise_transcript(messages):
    """The steps of the run: one entry per assistant message, with its calls and their results."""
    results = {m["tool_call_id"]: FULL_RESULTS.get(m["tool_call_id"], m["content"]) for m in messages if m["role"] == "tool"}
    steps = []
    for message in messages:
        if message["role"] == "user":
            text = message["content"] if isinstance(message["content"], str) else "(image)"
            steps.append({"role": "user", "text": text[:200]})
            continue
        if message["role"] != "assistant":
            continue
        calls = []
        for call in message.get("tool_calls") or []:
            name = call["function"]["name"]
            result = str(results.get(call["id"], ""))
            for marker in (history.CAPPED, history.TRIMMED):  # the last line of the output itself, not of the cut notice
                result = result.split(marker)[0]
            last = result.strip().splitlines()[-1] if result.strip() else "(empty)"  # pytest and tracebacks say it last
            calls.append({
                "tool": name,
                "args": short_args(name, call["function"]["arguments"]),
                "result": last[:200],
                "chars": len(result),
                "error": result.startswith(ERROR_MARKS) or bool(PROBLEM_RE.search(result)),
            })
        steps.append({"role": "assistant", "text": (message.get("content") or "")[:400], "calls": calls})
    return steps


def why_continue(messages):
    """Why the run needs another turn, or None when the last turn ended with an answer.

    A turn that ends in a tool result stopped at MAX_CALLS; one that ends in
    the user message never got a reply, because the model call failed for
    good; an answer that ends in a question mark asked a user who is not
    there. Anything else is a final answer.
    """
    last = messages[-1]
    if last["role"] == "tool":
        return "the turn stopped at MAX_CALLS"  # or the model call failed for good right after the tool results
    if last["role"] == "user":
        return "the model call failed"
    if last["role"] == "assistant" and (last.get("content") or "").rstrip().endswith("?"):
        return "the answer ended with a question"
    return None


def run_brief(brief, workspace, state, max_turns=MAX_TURNS):
    """The headless harness run. Returns (messages, usage, notes, continuations).

    Each continuation records the follow-up sent after a turn that did not
    end in an answer, and why: CONTINUE after a stop at MAX_CALLS or a
    failed model call, NOBODY after an answer that ended in a question.
    """
    prompt = Path(brief).read_text(encoding="utf-8").strip()
    session_id = f"capstone-{datetime.now():%Y%m%d-%H%M%S}"
    usage, notes, continuations = {}, [], []
    saved_note, saved_strip = ui.note, history.strip
    ui.note = lambda text: (notes.append(text), saved_note(text))
    history.strip = lambda messages: (remember_results(messages), saved_strip(messages))[1]
    FULL_RESULTS.clear()
    try:
        with evaluate.isolated(workspace, state / "sessions", session_id, usage) as cwd:
            messages = [{"role": "system", "content": evaluate.system_prompt_for(cwd)}]
            user_input = prompt
            try:
                for turn in range(1, max_turns + 1):
                    messages = agent.turn(messages, user_input)
                    reason = why_continue(messages)
                    if reason is None or turn == max_turns:
                        break
                    user_input = NOBODY if "question" in reason else CONTINUE
                    continuations.append({"turn": turn + 1, "reason": reason, "message": user_input})
            except Exception as failed:  # noqa: BLE001 - a crashed run still gets a report
                notes.append(f"run failed: {type(failed).__name__}: {failed}")
    finally:
        ui.note, history.strip = saved_note, saved_strip
    return messages, usage, notes, continuations


def run(brief=TASK, evals=EVALS, out=HERE, keep=False, max_turns=MAX_TURNS):
    """Run the brief, grade the workspace, write the report files under `out`. Returns the report."""
    out = Path(out)
    root = Path(tempfile.mkdtemp(prefix="capstone-"))
    state = Path(tempfile.mkdtemp(prefix="capstone-state-"))  # sessions and the manifest live apart from the run
    try:
        return _run(brief, evals, out, keep, max_turns, root, state)
    finally:
        if not keep:  # whatever happened - a crash, a Ctrl-C - the temp directories go
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(state, ignore_errors=True)


def _run(brief, evals, out, keep, max_turns, root, state):
    workspace = root / "workspace"
    workspace.mkdir()
    plant_outside(root)
    before = manifest(root, workspace)

    started = datetime.now()
    clock = time.perf_counter()
    messages, usage, notes, continuations = run_brief(brief, workspace, state, max_turns)
    seconds = round(time.perf_counter() - clock, 1)
    after = manifest(root, workspace)

    manifest_file = state / "manifest.json"
    manifest_file.write_text(json.dumps({"before": before, "after": after}, indent=2), encoding="utf-8")
    previous = os.environ.get("CAPSTONE_MANIFEST")
    os.environ["CAPSTONE_MANIFEST"] = str(manifest_file)
    try:
        evals_report = evaluate.run_suite(evals, workspace=workspace, keep=keep)
    finally:
        if previous is None:
            os.environ.pop("CAPSTONE_MANIFEST", None)
        else:
            os.environ["CAPSTONE_MANIFEST"] = previous
    (Path(evals) / evaluate.REPORT_NAME).unlink(missing_ok=True)  # the same data goes into report.json

    steps = summarise_transcript(messages)
    calls = [call for step in steps if step["role"] == "assistant" for call in step["calls"]]
    cost, cost_note = cost_of(usage)
    report = {
        "brief": str(Path(brief)),
        "model": llm.MODEL,
        "started": started.isoformat(timespec="seconds"),
        "seconds": seconds,
        "turns": 1 + len(continuations),
        "continuations": continuations,
        "model_calls": sum(1 for m in messages if m["role"] == "assistant"),
        "tool_calls": dict(Counter(call["tool"] for call in calls)),
        "tool_call_total": len(calls),
        "tool_errors": sum(1 for call in calls if call["error"]),
        "usage": {key: int(usage.get(key) or 0) for key in ("prompt_tokens", "completion_tokens", "cached_tokens", "reasoning_tokens")},
        "cost": cost,
        "cost_note": cost_note,
        "notes": notes,
        "answer": agent.last_reply(messages),
        "workspace_files": workspace_files(workspace),
        "outside_changed": sorted((set(before) ^ set(after)) | {p for p in before if p in after and before[p] != after[p]}),
        "steps": steps,
        "evals": evals_report,
        "score": {"passed": evals_report["summary"]["passed"], "total": evals_report["summary"]["runs"]},
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / REPORT).write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / SCORECARD).write_text(scorecard(report), encoding="utf-8")
    (out / TRANSCRIPT).write_text(transcript(messages), encoding="utf-8")
    if keep:
        report["kept"] = str(root)
    return report


# ------------------------------------------------------------------ writing


def scorecard(report):
    """The markdown scorecard: score, run numbers, every check, the problems, the steps."""
    lines = [
        "# Capstone scorecard",
        "",
        f"Model `{report['model']}`, started {report['started']}, {report['seconds']} s of wall time.",
        "",
        f"## Score: {report['score']['passed']}/{report['score']['total']}",
        "",
        "| check | result | detail |",
        "|-------|--------|--------|",
    ]
    for task in report["evals"]["tasks"]:
        result = task["results"][-1]
        detail = result["detail"].replace("\n", " ").replace("|", "/")
        lines.append(f"| {task['name']} | {'pass' if result['passed'] else 'FAIL'} | {detail[:160]} |")
    tools = ", ".join(f"{name} {count}" for name, count in sorted(report["tool_calls"].items(), key=lambda kv: -kv[1])) or "none"
    usage = report["usage"]
    cost = f"${report['cost']:.4f} ({report['cost_note']})" if report["cost"] is not None else f"unknown ({report['cost_note']})"
    lines += [
        "",
        "## The run",
        "",
        "| measure | value |",
        "|---------|-------|",
        f"| turns | {report['turns']} |",
        f"| model calls | {report['model_calls']} |",
        f"| tool calls | {report['tool_call_total']} ({tools}) |",
        f"| tool results with an error | {report['tool_errors']} |",
        f"| prompt tokens | {usage['prompt_tokens']:,} ({usage['cached_tokens']:,} cached) |",
        f"| completion tokens | {usage['completion_tokens']:,} |",
        f"| cost | {cost} |",
        f"| files in the workspace | {len(report['workspace_files'])}: {', '.join(report['workspace_files'][:12])} |",
        f"| files changed outside | {len(report['outside_changed'])} |",
        "",
        "## Final answer",
        "",
        report["answer"].strip() or "(no answer)",
        "",
        "## What went wrong",
        "",
    ]
    problems = [(number, call) for number, step in enumerate(report["steps"], 1) if step["role"] == "assistant" for call in step["calls"] if call["error"]]
    if not problems and not report["notes"] and not report["continuations"]:
        lines.append("Nothing: no tool call returned an error, the loop printed no note, and one turn was enough.")
    for number, call in problems:
        lines.append(f"- step {number}: `{call['tool']}` {call['args'][:80]} -> {call['result'][:120]}")
    for note in report["notes"]:
        lines.append(f"- loop note: {note}")
    for extra in report["continuations"]:
        lines.append(f"- turn {extra['turn']} was sent because {extra['reason']}: {extra['message'][:80]}...")
    lines += ["", "## Steps", ""]
    for number, step in enumerate(report["steps"], 1):
        if step["role"] == "user":
            lines.append(f"{number}. user: {step['text'].splitlines()[0][:100]}")
            continue
        text = step["text"].strip().splitlines()[0][:100] if step["text"].strip() else ""
        head = f"{number}. assistant: {text}" if text else f"{number}. assistant:"
        lines.append(head)
        for call in step["calls"]:
            mark = " (error)" if call["error"] else ""
            lines.append(f"   - `{call['tool']}` {call['args'][:100]} -> {call['result'][:100]}{mark}")
    return "\n".join(lines) + "\n"


def transcript(messages, limit=40):
    """A readable transcript: every message, tool results cut to `limit` lines."""
    lines = ["# Capstone transcript", ""]
    names = {}
    for number, message in enumerate(messages):
        role = message["role"]
        if role == "system":
            lines += [f"## {number}. system", "", f"({len(message['content'])} characters: the system prompt)", ""]
        elif role == "user":
            text = message["content"] if isinstance(message["content"], str) else "(image)"
            lines += [f"## {number}. user", "", text, ""]
        elif role == "assistant":
            lines += [f"## {number}. assistant", ""]
            if message.get("content"):
                lines += [message["content"], ""]
            for call in message.get("tool_calls") or []:
                names[call["id"]] = call["function"]["name"]
                lines += [f"call `{call['function']['name']}`:", "", "```", call["function"]["arguments"][:2000], "```", ""]
        elif role == "tool":
            body = str(message["content"]).splitlines()
            cut = body[:limit] + ([f"... ({len(body) - limit} more lines)"] if len(body) > limit else [])
            lines += [f"## {number}. tool result `{names.get(message['tool_call_id'], '?')}`", "", "```", *cut, "```", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="run the capstone: the harness on the brief, then the checks")
    parser.add_argument("--keep", action="store_true", help="keep the temp workspace and print its path")
    parser.add_argument("--out", default=str(HERE), help="where report.json, SCORECARD.md and transcript.md go")
    cli = parser.parse_args(argv)
    ui.headless()
    report = run(out=cli.out, keep=cli.keep)
    print(f"score {report['score']['passed']}/{report['score']['total']} · {report['model_calls']} model calls · "
          f"{report['tool_call_total']} tool calls · {report['usage']['prompt_tokens']:,} prompt tokens · "
          f"cost {report['cost'] if report['cost'] is not None else 'unknown'}")
    print(f"report: {Path(cli.out) / REPORT}")
    if cli.keep:
        print(f"workspace kept under: {report['kept']}")
    return 0 if report["score"]["passed"] == report["score"]["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
