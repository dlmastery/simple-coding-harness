# 10.31 · Compare harness generation and harness improvement

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A source audit and a local comparison of a generated harness before and after one revision.

## Why this matters

Generating infrastructure, improving its task output, and improving its generator are different claims.

## Before you start

Complete [10.30: Reduce cost without hiding quality loss](../step_30_cost_quality/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-31</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Your generated classification harness and both primary papers.

**Budget:** Read methods first; one harness edit and two checks or fits. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

HarnessDev evaluates created and revised harnesses, with creator and executor roles separated. Harness-of-Harness instead keeps its model, base harness, roles, and runtime policy fixed while software and execution evidence change. Its planner, developer, and tester have separate invocations and permissions. For the classroom activity, keep the builder fixed, revise one generated ML harness component, and measure behavior. This local choice is not the changed object in every source.



![Name the object that changes. In Harness-of-Harness, the developed software changes while the agent configuration remains fixed.](../../../assets/diagrams/lab-10-31.png)

*Read the diagram:* Name the object that changes. In Harness-of-Harness, the developed software changes while the agent configuration remains fixed.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.31, Compare harness generation and harness improvement, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** If a generated harness improves, must its generator have improved?

### 1. Read and map the methods

Identify the changed object in each source.

```text
Read each paper’s methods, experiments, and limitations. Create a two-column map of fixed components, changed artifact, evaluation, and resources, with section links. For Harness-of-Harness, distinguish the developed software from the fixed agent harness. For HarnessDev, distinguish feedback-set adaptation from held-out evaluation.
```

**Observe:** The mapping is based on primary methods rather than titles.

### 2. Run a bounded local analogue

Keep the changed object explicit.

```text
Revise one component of your generated harness using an observed failure. Test parent and child under matching conditions. Record the unchanged builder version and explain the limit of the analogy.
```

**Observe:** The local result concerns the harness, not automatically its generator.

## Check your result

The source audit is completed before paper-specific mechanism claims. The local experiment identifies what changed and what was evaluated.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Propose a generator comparison on two fresh briefs. Explain why evaluating only one generated artifact is weak evidence for a general builder claim.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Generation and improvement are distinct operations.
- Infrastructure claims need their own evaluation.
- Reading depth should be visible in research teaching.

## Research connection

[HarnessDev](https://arxiv.org/abs/2609.01437) and [Harness-of-Harness](https://arxiv.org/abs/2609.01481), both submitted 1 September 2026. Relevant method and evaluation sections were inspected; neither system was reproduced here.

**Activity type: source audit and mechanism exercise.** You inspect the source and execute a small local analogue. The task, models, resources, and evaluation differ from the paper.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Can a fixed builder produce an improved harness?
2. What does an abstract establish?
3. What should precede a faithful adaptation?
4. What evaluates a better generator?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Yes. The harness can be revised without changing the builder.

2. The authors’ high-level claims and framing, not every methodological detail.

3. Inspection of the relevant method, evaluation, resources, and limitations.

4. Outcomes of generated systems across prespecified fresh briefs under comparable resources.

</details>

## What's next

Compare raw history with a compact memory under an executable task. Continue to [10.32: Compare raw history and summarized memory](../../10_feedback_and_transfer/step_32_memory_interface/README.md).
