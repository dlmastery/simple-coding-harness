# 09.03 · Propose a change to the improver

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A child improver that changes how future task-skill revisions are chosen or tested.

## Why this matters

To improve the improvement process, the target of an edit must reach that process.

## Before you start

Complete [09.02: Run repeated improvement with an unchanged improver](../step_02_fixed_improver/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/09-03</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The fixed-improver lineage and its complete failure records.

**Budget:** One improver proposal and two small procedural checks; no broad search. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Suppose the fixed improver promotes a skill after one favorable case and misses a known regression. A candidate improver can require a contrasting case before promotion. This changes the procedure for improving task skills. The proposal remains a hypothesis until it governs later work and receives a fair comparison.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 09.03, Propose a change to the improver, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Could an extra regression check improve reliability while reducing the number of proposals tried?

### 1. Diagnose the improver

Target a procedural failure rather than a model setting.

```text
Use the full lineage to identify one weakness in IMPROVER-v0. Write a proposal changing one diagnosis, proposal, allocation, or selection rule. State its expected benefit, overhead, and falsifying case.
```

**Observe:** The mutable target is the improvement procedure.

### 2. Create the child

Preserve a runnable version.

```text
Save IMPROVER-v1.md without overwriting v0. Test its instructions on one favorable and one regressing fixture. Keep the evaluator unchanged and record the changed decision.
```

**Observe:** The candidate improver has a concrete behavioral difference.

## Check your result

The edit affects future skill improvement. Parent and child remain available. The report does not claim effectiveness from text quality alone.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Compare “write more thoughtful proposals” with “test a contrasting case before promotion.” Explain which is easier to inspect and falsify.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- An improver revision targets how improvements are produced.
- Added checks have resource costs.
- A better-looking procedure is still an unproven candidate.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why is this more than a task-model change?
2. What does the fixture test establish?
3. Does that prove a better improver?
4. What must remain outside the edit?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. It changes how later task-skill changes are evaluated or selected.

2. That the new instruction can produce the intended decision difference on those fixtures.

3. No. Later matched comparisons are still required.

4. The evaluation contract used to judge the proposed improvement.

</details>

## What's next

Make the next improvement round actually inherit the child procedure. Continue to [09.04: Use the revised improver in the next round](../step_04_inherit/README.md).
