# 06.06 · Recreate and compare generated harnesses

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A clean-start reproducibility report for two generated harnesses.

## Why this matters

A generated system that depends on hidden local state is difficult to share or evaluate.

## Before you start

Complete [06.05: Generate a classification harness](../step_05_second_task/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/06-06</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Both briefs, generated harnesses, dependency records, and prior results.

**Budget:** Two baseline fits, one per task. No new search. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Recreation uses the saved brief, builder version, generated files, dependencies, and data versions. Different source code can implement the same contract, so compare behavior and evidence as well as file hashes. If generation is stochastic, do not assume byte-identical output.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 06.06, Recreate and compare generated harnesses, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Must two valid generated harnesses have identical code?

### 1. Prepare the clean starts

Remove dependence on the old chat.

```text
Write a handoff for each harness with brief, builder version, generated entry point, pinned data, setup, and acceptance checks. Create clean output folders.
```

**Observe:** A reader can locate every dependency.

### 2. Reproduce and explain

Compare behavior under the same task contract.

```text
Run each baseline from the saved generated system. Compare predictions, metric, refusal behavior, and versions with the earlier run. Record any difference without selecting the most favorable rerun.
```

**Observe:** The report distinguishes reproduction of behavior from identical generated text.

## Check your result

Both task contracts remain intact. Actual runs and negative checks are recorded. The report does not confuse generator output diversity with improvement.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Change the builder’s proposal instructions and label it a new builder version. State the comparison needed before calling it a better builder.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Saved generation inputs support reproducibility.
- Behavioral equivalence can matter more than identical code.
- Improving a builder requires comparing builders, not just their artifacts.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What must be versioned?
2. Is differing code automatically a failure?
3. Can a favorable rerun replace an unfavorable original silently?
4. What would test a better builder?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Brief, builder, generated harness, data, dependencies, and evaluator contract.

2. No. Check whether it satisfies the same declared behavior and evidence requirements.

3. No. Preserve both and account for the additional selection opportunity and cost.

4. Matched-budget comparisons of harnesses it produces across prespecified fresh tasks and failure cases.

</details>

## What's next

Before changing the system itself, distinguish the different self-* mechanisms. Continue to [07.01: Correct one result](../../07_understanding_self_star/step_01_correction/README.md).
