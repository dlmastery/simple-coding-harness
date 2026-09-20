# 01.04 · Check outputs with a separate calculation

[Course](../../README.md) · [Theme](../README.md)

## What you will build

An output checker that derives error from prediction rows and rejects a mismatch.

## Why this matters

A solver’s confidence cannot substitute for measuring its output.

## Before you start

Complete [01.03: Turn the process into a skill](../step_03_make_a_skill/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/01-04</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The fixed baseline skill and a successful prediction file.

**Budget:** No model fits; two checker runs. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A separate calculation can recompute a metric without trusting the report writer. That is useful separation of responsibilities. It is not necessarily independent context or access control: the same host agent may still see every file.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 01.04, Check outputs with a separate calculation, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Could a mathematically correct checker still approve the wrong candidate?

### 1. Generate the checker

Give the check its own inputs.

```text
Generate a checker that reads the candidate ID, prediction rows, expected partition row IDs, and declared metric. Recompute MAE and reject missing, duplicate, or mismatched rows. Run it on the baseline. Save its code and output.
```

**Observe:** The checker checks identity and completeness as well as arithmetic.

### 2. Substitute one row

Demonstrate an actual refusal.

```text
In a labelled copy, replace one selection row ID with a training row ID. Run the checker and retain its nonzero result. Do not alter the original predictions.
```

**Observe:** The wrong partition row is rejected even if the summary score looks reasonable.

## Check your result

The valid file passes and the substituted-row file fails. CHECK-REPORT.md describes exactly what the checker reads and cannot protect.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Give the checker only a metric number without predictions. Explain which checks become impossible.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A verifier needs evidence, not just a reported score.
- Identity checks prevent comparisons between different objects.
- Separate code does not imply an inaccessible evaluator.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why compare row identities?
2. Is a second role prompt independent evaluation?
3. What does a deliberate failing input add?
4. What requires a stronger boundary?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. A correct metric on the wrong rows answers a different question.

2. No. The same context can retain prior information and the same permissions.

3. It tests whether the checker detects a specific error.

4. Claims that depend on the candidate being unable to see or alter evaluation cases and logic.

</details>

## What's next

Test whether the skill works after the conversation state is gone. Continue to [01.05: Reuse the skill in a fresh session](../step_05_reuse_the_skill/README.md).
