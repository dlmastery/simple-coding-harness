"""Step 36 - the plan, work, review pipeline behind /pipeline.

The planner agent turns the task into a numbered plan, one step per line.
parse_plan() reads the lines "N. title" and the optional "[parallel]" tag.
Each step then goes to the worker agent, and the worker's result goes to
the reviewer agent, which answers PASS or FAIL with reasons. A step that
fails is sent to the worker once more with the reviewer's notes, and
reviewed again. Steps the plan marked [parallel] run at the same time on
the subagent pool; every other step waits for the one before it. The
outcome is one row per step for the summary table.
"""

import re
from dataclasses import dataclass, field
from functools import partial

from . import agents, subagent

RETRIES = 1  # a failed step is worked again this many times

STEP_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*\S)\s*$")     # "1. title" or "1) title"
PARALLEL_RE = re.compile(r"\s*\[parallel\]\s*", re.I)  # the tag that marks an independent step


@dataclass
class Step:
    number: int
    title: str
    parallel: bool = False
    attempts: int = 0
    verdict: str = "skipped"
    notes: str = ""
    reports: list = field(default_factory=list)  # what the worker said, one entry per attempt


def parse_plan(text):
    """The numbered lines of a plan, in order. Other lines are ignored."""
    steps = []
    for line in (text or "").splitlines():
        match = STEP_RE.match(line)
        if not match:
            continue
        title, tagged = PARALLEL_RE.subn(" ", match.group(2))
        steps.append(Step(int(match.group(1)), " ".join(title.split()), parallel=bool(tagged)))
    return steps


def waves(steps):
    """Group the steps into runs: consecutive [parallel] steps share a wave, every other step is its own."""
    grouped = []
    for step in steps:
        if step.parallel and grouped and grouped[-1][0].parallel:
            grouped[-1].append(step)
        else:
            grouped.append([step])
    return grouped


def outline(steps):
    """The plan as the agents see it, one line per step."""
    return "\n".join(f"{s.number}. {s.title}" + (" [parallel]" if s.parallel else "") for s in steps)


VERDICT_RE = re.compile(r"^\W*(?:verdict|result)?\W*(PASS|FAIL)\b", re.I)  # PASS, **PASS**, "Verdict: PASS"


def verdict_of(review):
    """PASS or FAIL from the first non-empty line of the review; anything else is FAIL."""
    lines = [line for line in (review or "").splitlines() if line.strip()]
    match = VERDICT_RE.match(lines[0]) if lines else None
    return "PASS" if match and match.group(1).upper() == "PASS" else "FAIL"


def missing_agents():
    """The pipeline's agents that have no definition, so the command can stop before the first model call."""
    return [name for name in ("planner", "worker", "reviewer") if name not in agents.AGENTS]


def work_request(task, steps, step, notes=None):
    text = f"Task: {task}\n\nThe plan:\n{outline(steps)}\n\nYour step, and only this step: {step.number}. {step.title}\n"
    if notes:
        text += f"\nA reviewer failed your previous attempt. Fix these points:\n{notes}\n"
    return text

def review_request(task, steps, step, report):
    return (
        f"Task: {task}\n\nThe plan:\n{outline(steps)}\n\nThe step under review: {step.number}. {step.title}\n\n"
        f"The worker reported:\n{report}\n\nCheck the workspace and the diff against this step. Answer PASS or FAIL first, then the reasons.\n"
    )


def run_step(task, steps, step, tag=None):
    """Work one step, review it, and retry once on FAIL. Fills in the step and returns it."""
    notes = None
    for attempt in range(1 + RETRIES):
        step.attempts = attempt + 1
        report = agents.run("worker", work_request(task, steps, step, notes), tag=tag)
        step.reports.append(report)
        review = agents.run("reviewer", review_request(task, steps, step, report), tag=tag)
        step.verdict = verdict_of(review)
        step.notes = " ".join(review.split())
        if step.verdict == "PASS":
            break
        notes = review
    return step


def guarded_step(task, steps, step, tag=None):
    """run_step, but a crash becomes a FAIL row: one failure must not sink the others."""
    try:
        return run_step(task, steps, step, tag=tag)
    except Exception as failure:  # noqa: BLE001
        step.verdict = "FAIL"
        step.notes = f"{type(failure).__name__}: {failure}"
        return step


def run(task):
    """Plan the task, work and review every step, and return (plan text, steps)."""
    missing = missing_agents()
    if missing:
        return f"Error: no agent named {', '.join(repr(m) for m in missing)}.", []
    plan = agents.run("planner", task, tag="planner")
    steps = parse_plan(plan)
    for wave in waves(steps):
        if len(wave) == 1:
            guarded_step(task, steps, wave[0], tag=f"step {wave[0].number}")
        else:
            subagent.gather([partial(guarded_step, task, steps, step, f"step {step.number}") for step in wave])
    return plan, steps


def summary(steps):
    """One row per step for the table: number, title, attempts, verdict, notes."""
    return [(s.number, s.title, s.attempts, s.verdict, s.notes) for s in steps]
