# 10.03 · Choose experiments that reduce uncertainty

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A small exploration plan that moves from broad probes to a focused ML question.

## Why this matters

A fixed benchmark list can hide what the agent still does not understand about a new environment.

## Before you start

Complete [10.02: Audit a frontier announcement](../../00_reading_frontier_research/step_02_announcements/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-03</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Bike regression with no retained task-specific memory. Use selection data only.

**Budget:** Three small fits maximum. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

The classroom exercise first probes two distinct limitations, then spends the last attempt on one uncertainty. Broad coverage and targeted investigation have different purposes. Keep the choice rule visible; exploration is not permission to change the task metric.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.03, Choose experiments that reduce uncertainty, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Would three nearly identical fits reveal as much as two contrasting probes and one targeted follow-up?

### 1. Choose broad probes

State what each attempt teaches.

```text
Plan a constant baseline and a calendar linear model. For each state the uncertainty it addresses. Freeze the task and three-fit budget.
```

**Observe:** The probes ask different questions.

### 2. Focus the final attempt

Use observed outcomes to allocate work.

```text
Run the probes, inspect selection errors, and choose one final permitted recipe to test a specific unresolved hypothesis. Record the decision before fitting.
```

**Observe:** The final action follows evidence from exploration.

## Check your result

The plan distinguishes broad and focused work. All attempts and costs are retained. No final test information guides exploration.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Spend the third attempt on a duplicate recipe in a labelled comparison. Explain what information it can and cannot add.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Exploration has an information goal.
- Focused follow-up should state the uncertainty it tests.
- More attempts are not automatically more useful experience.

## Research connection

[RSIAgent](https://arxiv.org/abs/2609.15364), Sibo Zhu and colleagues, Aether AI, UC San Diego, and UIUC; 14 September 2026.

This is a classroom mechanism exercise. Its task, models, and budget differ from the original study. Your measured result belongs to this exercise; it does not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What changes during this lab?
2. Does that alone establish RSI?
3. Why record the question before fitting?
4. What is lost by duplicate deterministic probes?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The choice of task-level experiment based on observed development feedback.

2. No. The exploration procedure can remain fixed.

3. It makes the information goal falsifiable and prevents hindsight rewriting.

4. They add little about new mechanisms, though they may test repeatability.

</details>

## What's next

Separate outcome verification from the actor’s memory-writing responsibility. Continue to [10.04: Verify the outcome, then let the actor write memory](../step_04_actor_memory/README.md).
