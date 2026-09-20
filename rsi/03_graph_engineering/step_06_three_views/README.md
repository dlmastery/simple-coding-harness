# 03.06 · Read the plan, data flow, and trace

[Course](../../README.md) · [Theme](../README.md)

## What you will build

Three views of one run: allowed actions, artifact movement, and actual events.

## Why this matters

A diagram can look correct even when execution took a different route.

## Before you start

Complete [03.05: Resume only the affected work](../step_05_recover/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/03-06</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The workflow graph, a successful trace, and a failed trace from this theme.

**Budget:** No fits; inspect two existing traces. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

The control graph says which action may follow. Data flow says which artifact each action consumes or produces. The trace records what happened at a particular time. A branch can exist in the graph without being taken in a run. A missing trace event is not supplied by drawing the node.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 03.06, Read the plan, data flow, and trace, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Does a drawn verifier node prove that the verifier ran?

### 1. Separate the views

Make their questions distinct.

```text
Create VIEWS.md with a control graph, a data-flow table, and a time-ordered trace for one completed run. Use actual artifact names and candidate IDs.
```

**Observe:** Each view answers a different question.

### 2. Find the mismatch

Use a failed run to test the distinction.

```text
Compare the failed trace with the intended graph. Identify an allowed-but-unexecuted action and an output that therefore cannot be claimed. Save the audit.
```

**Observe:** The audit refuses to treat a planned check as completed evidence.

## Check your result

VIEWS.md distinguishes permission to act, required data, and observed execution. Every claimed completed check has a trace event and output.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Add a new check node to the plan without rerunning the experiment. Explain why old results do not gain that check retroactively.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Plans specify possibilities; traces record events.
- Data flow exposes input dependencies.
- A later diagram edit cannot change historical evidence.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What does the control graph establish?
2. What does the trace establish?
3. Why is data flow separate?
4. Can a planned check be counted as passed?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The intended allowed structure of execution.

2. Recorded events for a particular run, subject to the trace’s integrity and completeness.

3. Actions can occur in order yet consume the wrong or stale artifacts.

4. No. It must execute against the relevant candidate and produce valid evidence.

</details>

## What's next

The routes are explicit. Now make the meaning of their objects explicit too. Continue to [04.01: Name the objects in an experiment](../../04_ontology_engineering/step_01_entities/README.md).
