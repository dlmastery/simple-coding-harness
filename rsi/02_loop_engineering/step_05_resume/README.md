# 02.05 · Resume without losing the experiment

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A checkpoint and a resumed loop that retains candidate identities and spent budget.

## Why this matters

Restarting the program should not silently restart the scientific experiment.

## Before you start

Complete [02.04: Stop repeated failure and oscillation](../step_04_stop_the_loop/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/02-05</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** A fresh three-attempt loop workspace. Stop after its first completed candidate.

**Budget:** Three total fits across both sessions, not three per session. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A checkpoint records durable state: contract, completed and interrupted attempts, retained candidate, remaining budget, and next action. A process ID or live lock is different: it tells you whether work may still be running. Resuming must reconcile both.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 02.05, Resume without losing the experiment, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** After one fit and a restart, how many attempts remain in a three-attempt experiment?

### 1. Stop at a boundary

Save a state you can inspect.

```text
Run only the constant/calendar candidate. Save PROGRESS.md with its ID, contract, consumed attempt, two remaining attempts, and the next planned action. Stop further fitting.
```

**Observe:** The checkpoint accounts for completed work.

### 2. Resume from files

Continue the same experiment.

```text
Read PROGRESS.md and the actual ledger. Inspect active processes and locks. Resume the next two distinct recipes without overwriting the first trial. Stop at the original total limit.
```

**Observe:** The final ledger contains the whole experiment across sessions.

## Check your result

Candidate IDs are unique. The first result survives. The restart does not replenish attempts. A stale lock is inspected before removal.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Prepare a labelled teaching checkpoint with a running trial whose process has exited. Mark it interrupted and preserve its spent attempt before continuing.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A restart changes process state, not the experiment’s identity.
- Spent resources survive interruption.
- A checkpoint must agree with the actual ledger.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. How many attempts remain after one of three completed fits?
2. Why inspect a lock before deleting it?
3. Should an interrupted attempt disappear?
4. What if the evaluator changed before resume?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Two, regardless of how many sessions are opened.

2. Another process may still be writing the workspace. Deleting its lock permits conflicting writes.

3. No. Keep its identity, failure state, and known cost; unknown cost stays unknown.

4. Stop and start a new reviewed experiment. Do not mix results under different contracts.

</details>

## What's next

Compare blind repetition with a procedure that uses feedback. Continue to [02.06: Compare two ways to spend the same attempts](../step_06_compare_loops/README.md).
