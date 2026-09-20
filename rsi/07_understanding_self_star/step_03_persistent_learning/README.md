# 07.03 · Retain and use a lesson

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A versioned memory note that changes a later decision.

## Why this matters

A saved lesson only matters to future behavior if a later process retrieves and uses it.

## Before you start

Complete [07.02: Test a reflection before trusting it](../step_02_reflection/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/07-03</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** A tested reflection, a new case, and a fresh session where available.

**Budget:** One later task or fit; preserve a no-memory comparison if already available. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Learning can be implemented through changed weights, memory, skills, or other retained state. This lab uses external memory. State the mechanism precisely: the host model reads a saved rule. A larger memory file is not evidence of better decisions.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 07.03, Retain and use a lesson, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** What would demonstrate use of the memory rather than mere file existence?

### 1. Retain the narrow rule

Preserve scope and evidence.

```text
Write MEMORY-v1.md with the validated rule, when it applies, when it does not, and links to its supporting and failing cases. Keep the original trace separate.
```

**Observe:** The note retains a bounded lesson, not an unconditional slogan.

### 2. Apply it later

Trace persistence into behavior.

```text
In a new task context, read MEMORY-v1.md and record the decision it changes before execution. Run the task and compare with the declared no-memory behavior. Label a same-context exercise if a new session is unavailable.
```

**Observe:** A decision trace supports actual use.

## Check your result

The memory version is identified. A later action is linked to a specific rule. The result distinguishes use from benefit.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Apply the rule to a case outside its stated scope. Predict possible negative transfer before running a small check.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- External memory is one form of retained adaptation.
- Persistence, use, and benefit are separate claims.
- A useful lesson includes its scope.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Did the language-model weights change?
2. Does reading memory prove it helped?
3. What is negative transfer?
4. Is persistent learning automatically recursive improvement?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. No. The changed state is an external memory artifact.

2. No. Compare behavior and outcomes with a suitable baseline.

3. A retained lesson harms performance on another case or task.

4. No. The procedure that writes and checks memory may remain fixed.

</details>

## What's next

Use a fixed improver to revise a task skill and measure its effect. Continue to [07.04: Improve a task skill with a fixed procedure](../step_04_self_improvement/README.md).
