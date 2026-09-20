# 10.25 · Track model–harness pairs across cycles

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A version table and a small labelled simulation of alternating model and harness changes.

## Why this matters

A model checkpoint can perform differently with a new harness. Evaluate the pair that actually runs.

## Before you start

Complete [10.24: See what grouped rewards contribute](../step_24_grpo/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-25</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Two synthetic model versions and two synthetic harness versions, plus a declared outcome table.

**Budget:** Four table evaluations in a simulation; no LLM training. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

ScienceBuddy couples harness adaptation with weight learning across repeated cycles. Our simulation represents the pair explicitly. It is constructed to show interaction: a harness may suit one model better than another. Synthetic scores illustrate the accounting and comparison, not the paper’s measured gains.

**A concrete example.** The [executed simulation](../../../evidence/2026-09-20/sciencebuddy-laptop/10-25/PAIRS.md) uses invented scores: M0 gets 0.40 with H0 and 0.70 with H1; M1 gets 0.80 and 0.60 respectively. Selecting H1 helps M0. Changing the model label to M1 makes the inherited H1 worse than H0. Reselecting the harness then helps. The table constructs this interaction; no model was trained.

![Track model and harness versions as a pair. Changing either can alter compatibility with the other.](../../../assets/diagrams/lab-10-25.png)

*Read the diagram:* Track model and harness versions as a pair. Changing either can alter compatibility with the other.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.25, Track
model–harness pairs across cycles, one step
at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Must the best harness for model A remain best for model B?

### 1. Define paired state

Avoid mixing incompatible versions.

```text
Generate a labelled synthetic 2-by-2 table
of model and harness versions with an
interaction. Record the constructed values
and why they illustrate the concept. Create
PAIRS.md with both version IDs for each
result.
```

**Observe:** Each result belongs to a pair.

### 2. Simulate the cycle

Track what changes at each stage.

```text
Run one harness-selection step, one
model-update placeholder, and another
harness-selection step over the table. Mark
the model update as a simulation, not
training. Keep a fixed evaluation table.
```

**Observe:** Changing one component can change the best partner.

## Check your result

Every simulated result names both versions. Synthetic values are never mixed with paper or classroom measurements. The fixed reflector and feedback-source distinctions are checked against the paper.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Synthetic outcome table and PAIRS.md | Identify both versions for all four values and label their constructed origin. |
| Alternating-cycle trace | Marks each harness choice and the simulated model-update placeholder. |
| Extension plan | States what actual checkpoints, rewards, training, and evaluation would replace the placeholder. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Draft a larger-compute extension that replaces the placeholder with real training and specifies how checkpoints, rewards, and paired evaluation would be recorded.

## If something goes wrong

If a result names only the model, add the harness identity before interpreting it. If the simulator changes table values to force a favorable story, retain the initial table and declare a separate scenario. Do not mix these synthetic scores with the paper’s reported accuracy or your actual wine measurements.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Evaluate the model–harness pair.
- Alternating changes can interact.
- A simulated update must remain visibly distinct from training.

## Research connection

[ScienceBuddy](https://arxiv.org/abs/2609.17523), Shuhan Xue, Jianyuan Zhong, Ziyuan Nan, and colleagues; 15 September 2026. The full author list and affiliations are on the primary paper.

**Activity type: simulation.** You execute rules over labelled synthetic states. Those values are not trained-model measurements or the paper’s results.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why track both versions?
2. Can a harness gain be attributed to weights alone?
3. What does this simulation establish?
4. What is needed for a real extension?

<details>
<summary>Hint</summary>

Compare harnesses within each model row. A change in the preferred partner reveals why the pair must be evaluated together.

</details>

<details>
<summary>Explained answers</summary>

1. The deployed behavior depends on their combination.

2. Not without a comparison that holds the harness fixed.

3. How to track and reason about coupled state, not empirical co-evolution performance.

4. Actual training and harness execution with source-aligned data, rewards, resources, checkpoints, and evaluation.

</details>

## What's next

Audit the reported gains without mixing metrics or feedback sources. Continue to [10.26: Read the ScienceBuddy results precisely](../step_26_audit_results/README.md).
