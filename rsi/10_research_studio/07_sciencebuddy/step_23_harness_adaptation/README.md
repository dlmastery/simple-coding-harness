# 10.23 · Adapt the harness to the rubric

[Course](../../../README.md) · [Theme](../../README.md)

**You are here:** Theme 10, Research studio → lab 23 of 38. [Find this theme in the course map](../../../COURSE-MAP.md#theme-10) · [Whole-course mindmap](../../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A reporting-skill revision that responds to the rubric without changing model weights.

## Why this matters

Harness adaptation is often confused with training. Track the surface that actually changes.

## Before you start

Complete [10.22: Turn a researcher correction into a task](../step_22_human_task/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-23</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The task, rubric, and failed report fixture from 10.22.

**Budget:** One skill edit and four checker runs: parent and child on complete and incomplete evidence fixtures. No model-weight training. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Keep the agent’s language-model weights fixed. Edit a learner-owned reporting skill to require class-wise evidence and a claim check. Then test the revised procedure. This isolates harness adaptation; it does not implement the paper’s weight-learning component.

**A concrete example.** The [recorded child procedure](../../../evidence/2026-09-20/sciencebuddy-laptop/10-23/CHANGE-PROPOSAL.md) passes the complete-evidence case and reports missing evidence in the incomplete case. That refusal is correct behavior even though the requested model comparison remains unfinished. A deterministic reporter executed these instructions; this does not measure how an independent language-model session would respond to the edit.

![Hold the model fixed while testing a harness edit. Keep the rubric fixed during this comparison.](../../../assets/diagrams/lab-10-23.png)

*Read the diagram:* Hold the model fixed while testing a harness edit. Keep the rubric fixed during this comparison.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.23, Adapt the
harness to the rubric, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Would saving a new reporting instruction change the language model’s parameters?

### 1. Revise the procedure

Target the observed omission.

```text
Create a child reporting skill from the
failed rubric case. Require evidence-linked
class recalls and an explicit limit
statement. Preserve parent and child
versions.
```

**Observe:** The changed artifact is an external skill.

### 2. Run the rubric checks

Measure the revised behavior.

```text
Use parent and child on the same complete
and incomplete evidence fixtures, making
four report/check pairs. Retain every output
and verdict. Do not invent missing class
evidence to satisfy the rubric. State
whether the shared agent context limits
causal interpretation.
```

**Observe:** The child’s actual output can be compared with its parent.

## Check your result

The report names a harness change and does not claim a weight update. Both positive and negative rubric cases are exercised.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Parent and child reporting skills | Show the external instruction edit and unchanged rubric. |
| Four report/check pairs | Cover both skill versions on complete and incomplete evidence fixtures. |
| Adaptation report | Distinguishes measured reporting behavior from unperformed model-weight training. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Make the child skill longer without adding a useful requirement. Explain why more instructions need not improve the result.

## If something goes wrong

If the child passes only by manufacturing a value absent from the fixture, retain that failure and reject the edit. If the parent sees the child’s instruction in the same conversation, state that context exposure limits causal attribution. The four-check budget includes both evidence conditions; no extra fit is needed.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Harness edits and parameter updates are distinct mechanisms.
- Rubric feedback can target a narrow procedural omission.
- Instruction length is not a quality measure.

## Research connection

[ScienceBuddy](https://arxiv.org/abs/2609.17523), Shuhan Xue, Jianyuan Zhong, Ziyuan Nan, and colleagues; 15 September 2026. The full author list and affiliations are on the primary paper.

**Activity type: mechanism exercise.** You execute a small classroom mechanism. Its task, models, and budget differ from the source. Local observations do not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What changed in this lab?
2. What stayed fixed?
3. Does a passing rubric prove general scientific competence?
4. What evidence would show actual weight training?

<details>
<summary>Hint</summary>

Track which file changed and whether any optimizer updated model parameters. New instructions do not imply new language-model weights.

</details>

<details>
<summary>Explained answers</summary>

1. The external reporting procedure.

2. The language-model weights and the evaluation rubric.

3. No. It checks the declared task criteria.

4. A training process with parameter updates, checkpoints, objective, data, and evaluation records.

</details>

## What's next

Understand the grouped-reward calculation before discussing real GRPO training. Continue to [10.24: See what grouped rewards contribute](../step_24_grpo/README.md).
