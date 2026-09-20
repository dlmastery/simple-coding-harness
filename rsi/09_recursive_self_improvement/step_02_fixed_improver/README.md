# 09.02 · Run repeated improvement with an unchanged improver

[Course](../../README.md) · [Theme](../README.md)

## What you will build

Two generations of task-skill revision governed by one fixed improver.

## Why this matters

Repeated self-improvement is the comparison baseline for recursive improvement, not proof of it.

## Before you start

Complete [09.01: Identify the solver, improver, and evaluator](../step_01_three_objects/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/09-02</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** A parent task skill, one fixed improver version, and development cases.

**Budget:** Two generations, at most two fits per generation. Include proposal and checking costs. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Generation labels track ancestry. The improver reads a solver’s failures, proposes a child task skill, and applies the same acceptance procedure each time. The solver may change repeatedly while the improver remains identical. Numbering generations does not change that fact.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 09.02, Run repeated improvement with an unchanged improver, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Can the solver improve twice without the improver improving at all?

### 1. Freeze the improver

Make the baseline identifiable.

```text
Save IMPROVER-v0.md and its hash. Predeclare two generations and a two-fit budget for each. Write the task-skill acceptance rule and permitted changes.
```

**Observe:** The control procedure is fixed before the run.

### 2. Run two generations

Preserve all proposals and decisions.

```text
Use the same improver for both rounds. Save each parent and child skill, proposal, evaluation, rejection or promotion, and costs. Verify the improver hash stays unchanged.
```

**Observe:** The lineage can show repeated solver changes under a fixed method.

## Check your result

Both rounds use the same improver. Every retained task skill has a corresponding evaluation. The conclusion says repeated self-improvement, not automatically RSI.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Use a rejected child as the next parent in a labelled diagnostic replay. Explain why that would contradict the recorded promotion policy.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Generations describe history, not necessarily recursion.
- A fixed improver can produce many solver revisions.
- Ancestry should follow actual promotion decisions.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Which version stays fixed?
2. What can improve over generations here?
3. Does persistence of a child establish its benefit?
4. Why retain failed proposals?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The improver procedure.

2. The task skill and resulting solver behavior, if measurements support it.

3. No. Persistence and evaluation are distinct.

4. They show the complete search and resource use behind the selected lineage.

</details>

## What's next

Use the baseline’s failures to propose a change to the improver itself. Continue to [09.03: Propose a change to the improver](../step_03_revise_improver/README.md).
