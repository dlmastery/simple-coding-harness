# 06.03 · Inspect what the builder decided

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A review that maps each important generated behavior back to the brief.

## Why this matters

A generator can quietly invent a split, skip a check, or increase the budget. Review should expose those choices.

## Before you start

Complete [06.02: Generate a first harness](../step_02_generate/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/06-03</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The generated harness and its first run.

**Budget:** No new fits. Inspect generated files and one trace. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Trace requirements forward to implementation and evidence backward to requirements. For example, “two attempts maximum” should appear in control logic and an over-budget refusal. A sentence in the README alone does not show the limit runs.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 06.03, Inspect what the builder decided, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Where would you look to verify the attempt limit?

### 1. Map requirements

Connect intent to actual behavior.

```text
Create REVIEW.md mapping target, features, split, metric, budget, refusal, and outputs to generated files and runtime evidence. Mark undocumented builder choices.
```

**Observe:** Every key requirement has an implementation location or a visible gap.

### 2. Inspect one hidden assumption

Find a plausible failure before it scales.

```text
Inspect preprocessing and candidate selection. Verify transformations fit only on training data and selection uses the declared partition. Save the evidence and any repair needed.
```

**Observe:** The review reaches operations, not only documentation.

## Check your result

The review distinguishes stated, implemented, and executed requirements. Any generated assumption is explicit.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

In a diagnostic copy, alter the README’s budget while leaving code unchanged. Explain why a documentation-only review misses the mismatch.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Generated implementation can drift from intent.
- A requirement needs both code and behavioral evidence when applicable.
- Readable documentation is not enforcement.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What is traceability here?
2. Why inspect train-only preprocessing?
3. Does a README limit constrain execution by itself?
4. What should happen to an undocumented scientific assumption?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The connection from requirement to implementation to observed check result.

2. Evaluation information can leak through transformations even without using labels directly.

3. No. The running procedure or tool must apply it.

4. Make it explicit and resolve it against the brief before accepting the result.

</details>

## What's next

Test the generated system with an input it is supposed to refuse. Continue to [06.04: Test the generated harness’s boundaries](../step_04_test_refusal/README.md).
