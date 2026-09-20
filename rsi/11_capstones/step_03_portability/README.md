# 11.03 · Test transfer and portability separately

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A compatibility matrix backed by actual small runs and clearly marked untested paths.

## Why this matters

A procedure can transfer across tasks while failing in another agent’s tool environment, or the reverse.

## Before you start

Complete [11.02: Run and audit a bounded recursive experiment](../step_02_recursive_experiment/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/11-03</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Your frozen harness, a second task or agent environment, and optional available larger-compute backend.

**Budget:** Two small smoke runs; larger jobs require a concrete resource plan. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Task transfer changes the scientific problem. Agent portability changes the host interpreting skills and operating tools. Compute portability changes execution resources. Test these dimensions separately so one successful run is not mistaken for universal support.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 11.03, Test transfer and portability separately, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Does a successful Codex run prove the same hooks work in Claude or Gemini?

### 1. Define the matrix

Separate compatibility questions.

```text
Create PORTABILITY.md with task, agent, runtime version, backend, required capabilities, and status. Use statuses planned, generated, inspected, and executed. Choose two small tests you can actually run.
```

**Observe:** Unsupported combinations remain explicit.

### 2. Execute and record

Replace intended support with evidence.

```text
Run the selected smoke tests through canonical skills. Check outputs, refusal behavior, recovery, and dependency versions. For a cluster test, record job ID, cancel, resume, and cost. Do not launch unavailable infrastructure or invent results.
```

**Observe:** Each executed cell has evidence and limits.

## Check your result

Every support claim corresponds to a run. Task transfer, agent compatibility, and backend compatibility are not merged into one label.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Remove one host capability, such as command execution, and identify which lesson outcomes can no longer be completed.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Portability has several independent dimensions.
- Readable instructions help portability but do not prove it.
- Target-environment evidence is required for support claims.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What changes in task transfer?
2. What changes in agent portability?
3. What changes in compute portability?
4. How should an untested backend be listed?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. The scientific task or distribution.

2. The host’s skill loading, tools, permissions, context behavior, and execution interface.

3. The runtime backend and resource behavior, ideally preserving task and evaluation contracts.

4. As planned or generated-only, with the missing tests stated.

</details>

## What's next

Apply the same evidence standard to someone else’s RSI claim. Continue to [11.04: Audit an unfamiliar RSI claim](../step_04_external_audit/README.md).
