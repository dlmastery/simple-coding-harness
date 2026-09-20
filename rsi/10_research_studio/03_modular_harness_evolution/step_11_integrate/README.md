# 10.11 · Integrate edits and test transfer

[Course](../../../README.md) · [Theme](../../README.md)

**You are here:** Theme 10, Research studio → lab 11 of 38. [Find this theme in the course map](../../../COURSE-MAP.md#theme-10) · [Whole-course mindmap](../../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

An integration check for two individually tested harness edits.

## Why this matters

Two useful changes can conflict when combined.

## Before you start

Complete [10.10: Localize a harness problem](../step_10_localize/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-11</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Two versioned component edits and their individual tests. If only one edit exists, prepare a second small interface change before declaring the comparison. Use executable fixtures with a fit stub; no model training is needed.

**Budget:** Seven fixture executions: four versions on the original case, baseline and combined versions on one fresh case, and one malformed-interface check. No fits. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Check each edit alone and then the combination under the same interface contract. A context change may remove information that a completion check expects. Integration therefore needs its own evidence, followed by a case that did not select either edit.

**A concrete example.** Edit A shortens a context record by removing a units field. Edit B adds a completion check that requires units. Each can pass under its own prior fixtures, yet their combination fails. A shared interface table reveals the conflict before a model fit is needed.

![Two useful edits can conflict when combined. Test the integrated system and its transfer separately.](../../../assets/diagrams/lab-10-11.png)

*Read the diagram:* Two useful edits can conflict when combined. Test the integrated system and its transfer separately.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.11, Integrate edits
and test transfer, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Can two individually passing components fail together?

### 1. Inspect the interfaces

Look for conflicting assumptions.

```text
Write an interface table for the two edits:
produced fields, consumed fields, meanings,
and failure behavior. Identify one possible
conflict before running. Save baseline, edit
A alone, edit B alone, and combined
versions. Declare one original fixture, one
fresh transfer fixture, and a
malformed-interface fixture. Replace real
fitting with a recorded stub.
```

**Observe:** The combined system has a declared contract.

### 2. Run integration and transfer

Measure the whole combination.

```text
Run all four versions on the original
fixture. Run the unchanged baseline and
combined version on the fresh fixture.
Preserve all six outcomes, component hashes,
and any failure. Reserve the seventh
execution for the missing-field check below.
Do not start model training.
```

**Observe:** The combined result is evaluated rather than inferred from local wins.

## Check your result

The combined version has its own tests and identity. Transfer cases are distinguished from selection cases. Failed integration is not hidden. Seven fixture records account for the complete budget.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Four version identities and interface table | Define baseline, A, B, and A+B, including field meanings. |
| Six original/transfer fixture outcomes | Compare all four on the original case and baseline versus A+B on the fresh case. |
| Seventh missing-field refusal | Confirms a precise failure before the fit stub; no training occurs. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

For the seventh execution, remove one field expected by the second component in the declared malformed fixture. Run the combined system and confirm a clear interface failure before the fit stub.

## If something goes wrong

If the generated harness starts real training, stop and repair the declared fit stub before continuing. If a fresh fixture was chosen after observing combined failure, label it as diagnostic rather than predeclared transfer. Keep both independently checked edits available when their combination is rejected.

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

A component’s local assumptions become another component’s inputs. Check their meanings and availability, not just matching field names.

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
