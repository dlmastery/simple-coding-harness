# 07.04 · Improve a task skill with a fixed procedure

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A parent and child research skill compared under one unchanged improvement procedure.

## Why this matters

A system can improve its solver while the method that creates improvements stays fixed.

## Before you start

Complete [07.03: Retain and use a lesson](../step_03_persistent_learning/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/07-04</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** A task skill, failed trace, and the canonical improve-research-skill procedure.

**Budget:** Four fits maximum across matched parent and child comparisons. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

The task skill chooses ML experiments. The improver reads failures, proposes one skill edit, and tests it. In this lab the improver’s instructions remain unchanged. The modified object is the solver’s research skill, so any benefit is self-improvement under a fixed improver.



![The task skill changes while its updater stays fixed. This is not yet an inherited change to the updater.](../../assets/diagrams/lab-07-04.png)

*Read the diagram:* The task skill changes while its updater stays fixed. This is not yet an inherited change to the updater.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 07.04, Improve a task skill with a fixed procedure, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Which file must stay unchanged for this to remain the fixed-improver comparison?

### 1. Propose one skill edit

Target a documented procedural weakness.

```text
Use improve-research-skill. Preserve the parent task skill. Propose one edit based on selection evidence, such as requiring an error-slice diagnosis before the second model choice. Save the unchanged improver hash and child skill.
```

**Observe:** The proposal identifies its mutable target.

### 2. Compare the skills

Measure behavior and cost.

```text
Give parent and child the same starting task and two fits each. Record their choices before fitting, retained results, and available total costs. Keep a child that fails acceptance as a rejected candidate.
```

**Observe:** The comparison may support benefit, harm, or uncertainty.

## Check your result

The improver version remains fixed. The child is actually used. The acceptance decision follows a declared rule and preserves rejected edits.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Edit the improver itself in a separate unexecuted proposal. Explain why this creates a different experiment that needs another comparison.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Self-improvement can target a solver under a fixed improver.
- A changed skill must be executed before claiming an effect.
- No improvement is a legitimate result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Which component changes?
2. Which component stays fixed?
3. Does a better solver score prove a better improver?
4. Why retain rejected child skills?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The task-level research skill.

2. The procedure that proposes and evaluates task-skill edits.

3. No. This experiment does not change or compare improvers.

4. They reveal the search process, costs, and failed hypotheses instead of showing only survivors.

</details>

## What's next

Organization is a different dimension. Let routing change and inspect the consequences. Continue to [07.05: Let work reorganize under local rules](../step_05_organization/README.md).
