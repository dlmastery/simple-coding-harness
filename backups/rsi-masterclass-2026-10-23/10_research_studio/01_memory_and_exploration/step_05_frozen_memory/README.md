# 10.05 · Evaluate with memory frozen

[Course](../../../README.md) · [Theme](../../README.md)

**You are here:** Theme 10, Research studio → lab 5 of 38. [Find this theme in the course map](../../../COURSE-MAP.md#theme-10) · [Whole-course mindmap](../../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A memory-versus-no-memory comparison with updates disabled during evaluation.

## Why this matters

Continuing to learn from evaluation cases changes what the evaluation measures.

## Before you start

Complete [10.04: Verify the outcome, then let the actor write memory](../step_04_actor_memory/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/10-05</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** One retained memory version and prespecified fresh task fixtures.

**Budget:** Two matched evaluation runs, at most two fits each. The additional adaptation-copy activity allows one memory update and zero extra fits. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Freeze the memory artifact before the comparison. Both arms use the same task and budget; one may read the frozen memory and the other must have no exposure to it for a clean comparison. The evaluation adds no new lessons. Separately initialized contexts and controlled information access are needed to isolate a memory effect. A shared-context demonstration can check file freezing but cannot establish that stronger claim.

**A concrete example.** In the [four-fit author demonstration](../../../evidence/2026-09-21/memory-labs/README.md#frozen-comparison), both arms followed the same residual rule and added weather inputs. Both obtained evaluation MAE 7.027189070. The memory file stayed unchanged, but the author had already seen it when designing both paths. That is evidence of file freezing and equal fit budgets, not a clean measurement of memory benefit. A later copy update used no additional fits and did not measure adaptation performance. The [six-task extension](../../../evidence/2026-09-22/tabular-comparison/README.md) gives fixed, random and frozen-memory procedures the same four probes and eight actual fits. Memory improves three final scores and ties three against random search, but loses to the fixed portfolio overall. A memory advantage is therefore control-dependent; the comparison does not justify always retrieving the earlier winner.

![Two planned evaluation arms share fresh cases, tools, and budgets. Only one can read frozen memory. Both record outcomes and costs, while a shared-context example warns that file identity does not prove no prior exposure.](../../../assets/illustrations/frozen-memory-comparison-v1.png)

*This depicts the intended comparison, not established isolation or a measured memory benefit. Confirm what each arm can actually read, including prior conversation, files, and other retrieval sources. The hash equality is a condition to check after the run. If the agent cannot start separate controlled contexts, label the activity a shared-context demonstration and limit the claim. The crossed arrow below rejects a clean-ablation inference; it does not suggest that disabling writes erases earlier exposure.*

[Open the illustration at full size](../../../assets/illustrations/frozen-memory-comparison-v1.png).

<details>
<summary>See the step diagram</summary>

![Freeze memory before comparing access conditions. Evaluation does not update that memory.](../../../assets/diagrams/lab-10-05.png)

*Read the diagram:* Freeze memory before comparing access conditions. Evaluation does not update that memory.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.05, Evaluate with
memory frozen, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** What would be confounded if only the memory arm could learn from test feedback?

### 1. Freeze the artifact

Identify exactly what is evaluated.

```text
Record the memory hash, scope, and
evaluation cases before running. Prepare
memory and no-memory arms with matched
starting artifacts and budgets.
```

**Observe:** The candidate is fixed before outcomes.

### 2. Compare without updating

Measure the retained state.

```text
Run both arms and record actual decisions,
results, and costs. Check the memory hash
afterward. If using one context, state that
the no-memory arm may be contaminated and do
not claim a clean ablation.
```

**Observe:** The boundary determines the strength of the conclusion.

## Check your result

The memory stays unchanged. Resource equality and context exposure are reported. The result does not claim a full RSIAgent reproduction.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Memory hash and comparison plan | Freeze content, cases, budgets, and permitted exposure before evaluation. |
| Two arm records | Retain decisions, outcomes, costs, and actual context boundaries. |
| Freeze and claim check | Confirms file stability while stating whether the no-memory boundary was real. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

After evaluation, declare one update to a separate memory copy with zero extra fits. Compare its before/after hashes and confirm the frozen original is unchanged. Explain why measuring adaptation performance would require a separate experiment, a new budget, and declared update timing; this copy activity does not measure a performance benefit.

## If something goes wrong

If the memory file changes during evaluation, preserve the run and reclassify it as adaptation rather than frozen-memory testing. Do not rerun until a separate protocol is declared. If a fresh context is unavailable, execute a labelled shared-context demonstration and restrict the conclusion instead of pretending the agent forgot the note.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Freeze retained state for a clean evaluation question.
- No-memory comparison needs a real information boundary.
- Adaptation during evaluation is a different protocol.

## Research connection

[RSIAgent](https://arxiv.org/abs/2609.15364), Sibo Zhu and colleagues, Aether AI, UC San Diego, and UIUC; 14 September 2026.

**Activity type: mechanism exercise.** You execute a small classroom mechanism. Its task, models, and budget differ from the source. Local observations do not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why check the hash afterward?
2. Can the same agent forget a note because instructed to?
3. What does a memory gain establish?
4. Does it prove a better memory-writing procedure?

<details>
<summary>Hint</summary>

A checksum checks file identity. It does not check what the model already knows from the conversation.

</details>

<details>
<summary>Explained answers</summary>

1. It detects a changed memory artifact, though it cannot prove all context remained controlled.

2. Not reliably enough to claim independent no-memory evaluation.

3. A benefit under this protocol and task scope, if the comparison is valid.

4. No. That requires comparing procedures that generate memory.

</details>

## What's next

Separate short-lived working state from reusable experience. Continue to [10.06: Separate working state from reusable experience](../step_06_working_and_experience/README.md).
