# 09.05 · Measure whether the revised improver helps

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A matched comparison of improvements produced by two improver versions.

## Why this matters

The new improver may produce a strong current solver yet be worse at producing future improvements.

## Before you start

Complete [09.04: Use the revised improver in the next round](../step_04_inherit/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/09-05</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Frozen v0 and v1 improvers, identical parent task skill, and prespecified fresh comparison cases.

**Budget:** Two rounds per improver, at most two fits per round; eight fits total. Count proposal and check overhead. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

The outcome is the improvement each procedure produces from the same starting solver under comparable resources. Compare retained descendants, not the most attractive intermediate score. Use fresh contexts where available and state contamination if both procedures share one context. A small experiment can remain inconclusive.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 09.05, Measure whether the revised improver helps, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Could v1 win on the current task but lose on improvement produced per unit cost?

### 1. Freeze the protocol

Define the comparison before execution.

```text
Write IMPROVER-COMPARISON.md with starting skill, tasks, budgets, acceptance rule, repetitions, context boundary, and measured costs. Do not use cases that selected v1 as fresh evidence.
```

**Observe:** The comparison is about future improvement work.

### 2. Run both arms

Measure descendants and overhead.

```text
Execute v0 and v1 from matched starting artifacts. Keep all proposals, failed checks, descendants, and costs. Compare retained gains over the common baseline and report uncertainty. If fresh independent contexts are unavailable, label that limitation prominently.
```

**Observe:** The evidence can show benefit, regression, or insufficient information.

## Check your result

Both arms start from the same solver. Their resource limits and known costs are reported. The conclusion concerns the tested improvers and tasks only.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Show how reporting only the best child from each arm hides failed proposals and selection cost.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A better solver is not automatically a better improver.
- Measure gains produced from comparable starts.
- Retained descendants and total research costs matter.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What is the main dependent outcome?
2. Why use fresh cases?
3. Does one win establish sustained acceleration?
4. What if total agent cost is unknown?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The improvement produced by each improver under the declared comparison, together with its cost and reliability.

2. Cases used to design or select v1 can favor it and weaken the generalization claim.

3. No. That requires repeated generational evidence beyond a two-version comparison.

4. State it and avoid claiming equal total-resource superiority.

</details>

## What's next

Run a short lineage with checkpoints and a stopping rule. Continue to [09.06: Run bounded recursive generations](../step_06_bounded_generations/README.md).
