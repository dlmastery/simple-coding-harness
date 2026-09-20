# 01.01 · Write the data science process

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A five-action process from task framing to a checked baseline report.

## Why this matters

An implicit process is hard to inspect. Writing its dependencies exposes missing decisions.

## Before you start

Complete [00.04: Check the evidence behind the answer](../../00_start_here/step_04_check_the_evidence/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/01-01</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The task brief, data report, and checked baseline from theme 00.

**Budget:** No fits; inspect existing evidence. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A process says what actions turn an input into an output. For this task: frame the question, inspect the data, fix the split, fit the baseline, and check the result. These are actions with products. “Be accurate” is an aim, not an executable action.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 01.01, Write the data science process, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Which action must happen before fitting if you want a meaningful comparison later?

### 1. Name the actions

Turn intentions into observable work.

```text
Create PROCESS.md with five actions: frame, inspect, split, fit, check. For each give its input, output, and completion check. Use the bike task. Do not add retries or search.
```

**Observe:** Every action leaves something a reader can inspect.

### 2. Walk one record through

Check that the sequence has no unexplained jump.

```text
Trace one baseline result backward through this process. Identify where the target, input availability, partition, and metric were fixed. Save a short gap review.
```

**Observe:** The choices that make the score meaningful precede the fit.

## Check your result

Each action has a concrete input and output. Task, split, and metric are fixed before model fitting. The process contains no learner-designed improvement loop.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Move split design after fitting. Explain what temptation this creates and why a later good score would be harder to interpret.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A useful process names actions and their products.
- Evaluation decisions belong before search.
- No learner-designed loop does not mean numerical algorithms contain no iterations.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Is “make a strong model” an executable process step?
2. Why fix the split early?
3. Can linear regression use an iterative solver here?
4. What makes a process inspectable?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. It lacks a concrete action and completion check. Fitting a declared baseline is a step.

2. It prevents choosing evaluation conditions in response to favorable results.

3. Yes. The lesson removes an outer improvement loop, not internal numerical computation.

4. Named inputs, actions, outputs, and checks that connect to actual evidence.

</details>

## What's next

Run the written sequence once without adapting it. Continue to [01.02: Run the process without changing it](../step_02_run_the_process/README.md).
