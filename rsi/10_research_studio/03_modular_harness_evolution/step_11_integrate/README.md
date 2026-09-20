# 10.11 · Integrate edits and test transfer

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

An integration check for two individually tested harness edits.

## Why this matters

Two useful changes can conflict when combined.

## Before you start

Complete [10.10: Localize a harness problem](../step_10_localize/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-11</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Two versioned component edits, their individual tests, and a fresh transfer fixture.

**Budget:** Three fixture runs; at most three fits if needed. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Check each edit alone and then the combination under the same interface contract. A context change may remove information that a completion check expects. Integration therefore needs its own evidence, followed by a case that did not select either edit.

![Two useful edits can conflict when combined. Test the integrated system and its transfer separately.](../../../assets/diagrams/lab-10-11.png)

*Read the diagram:* Two useful edits can conflict when combined. Test the integrated system and its transfer separately.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.11, Integrate edits and test transfer, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Can two individually passing components fail together?

### 1. Inspect the interfaces

Look for conflicting assumptions.

```text
Write an interface table for the two edits: produced fields, consumed fields, meanings, and failure behavior. Identify one possible conflict before running.
```

**Observe:** The combined system has a declared contract.

### 2. Run integration and transfer

Measure the whole combination.

```text
Test each edit alone and the combined version, then use a prespecified fresh fixture within the total budget. Retain failures and compare with the unchanged harness.
```

**Observe:** The combined result is evaluated rather than inferred from local wins.

## Check your result

The combined version has its own tests and identity. Transfer cases are distinguished from selection cases. Failed integration is not hidden.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Remove one field expected by the second component in a labelled fixture and confirm a clear interface failure.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Local success does not guarantee integration success.
- Interfaces carry meaning as well as structure.
- Transfer needs cases beyond those that selected the edits.

## Research connection

[ModularRSI](https://arxiv.org/abs/2609.14857), 14 September 2026; [author repository](https://github.com/IQuestLab/ModularRSI).

**Activity type: mechanism exercise.** You execute a small classroom mechanism. Its task, models, and budget differ from the source. Local observations do not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why test the combination?
2. What does a transfer case add?
3. Can a passing schema hide a mismatch?
4. What if integration fails?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Interactions can create failures absent from either isolated edit.

2. Evidence about behavior outside the cases used to choose the changes.

3. Yes. A field can have the right format and wrong meaning.

4. Retain the failure, reject or revise the combination, and keep the last accepted version active.

</details>

## What's next

Compare agent lineage with explicit improvement-procedure lineage. Continue to [10.12: Compare agent evolution and improver evolution](../step_12_lineage/README.md).
