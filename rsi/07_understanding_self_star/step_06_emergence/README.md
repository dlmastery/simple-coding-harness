# 07.06 · Observe a collective pattern

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 07, Changes and their evidence → lab 6 of 8. [Find this theme in the course map](../../COURSE-MAP.md#theme-07) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A labelled simulation that shows how a system-level pattern depends on local interactions.

## Why this matters

“Emergent” often gets used as a synonym for impressive. Make the claimed pattern and mechanism observable.

## Before you start

Complete [07.05: Let work reorganize under local rules](../step_05_organization/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/07-06</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The queue simulation and a small local-rule extension.

**Budget:** Three main simulations and an optional two-run lateness comparison; no ML fits. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Emergence describes a pattern at the collective level that arises from component interactions. In this exercise, workers preferentially take jobs similar to their recent work, reducing a synthetic setup cost. Groups of similar jobs can form without a central grouping plan. This is a small operational example, not evidence of consciousness or general intelligence.

**A concrete example.** In the saved synthetic trace, preference for the previous job type gives a same-type adjacency fraction of 0.80, compared with 0.00 for FIFO. But randomized history still gives 0.70: this small test does not establish that accurate memory uniquely causes grouping. In a separate deadline test, the local preference finishes all work at tick 8 instead of 12, while the most overdue job is 3 ticks late instead of 1. A stronger pattern and faster batch can still mean a worse urgent-job outcome.

![A collective pattern can arise from local interactions. Observing the pattern is different from measuring useful improvement.](../../assets/diagrams/lab-07-06.png)

*Read the diagram:* A collective pattern can arise from local interactions. Observing the pattern is different from measuring useful improvement.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 07.06, Observe a
collective pattern, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Will the clustering persist if workers ignore recent jobs?

### 1. Specify the pattern

Choose an observable collective property.

```text
Extend the synthetic queue with job types
and a fixed local preference for the
previous type. Define a clustering statistic
before running. Keep the job list fixed.
```

**Observe:** The claimed pattern has a measurement.

### 2. Remove the interaction

Test dependence on local rules.

```text
Compare the preference rule with a rule that
ignores job type and one that randomizes
history using a fixed seed. Save traces and
clustering values. Label every result as
simulation.
```

**Observe:** The ablation tests whether the interaction drives the pattern.

## Check your result

The pattern is defined before measurement. Local rules and global statistic are distinct. Claims remain limited to the simulation.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Pattern definition | States the clustering statistic before inspecting traces. |
| Three simulation traces | Compare local preference, no preference, and randomized history on the same jobs. |
| Pattern and lateness report | Separates grouping, completion time, and deadline failures, including any counterexample. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Construct a job list where clustering increases lateness. Explain how a visible pattern can be undesirable.

## If something goes wrong

If every policy groups the jobs, inspect whether the input order already contains groups. If the preferred-type policy improves the clustering score while missing deadlines, retain both observations. Do not redefine emergence to mean whichever metric improved. The optional lateness pair is a new declared job fixture, not a replacement for the original comparison.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A collective pattern is not automatically a capability gain.
- Ablations can test which interactions generate a pattern.
- Define what “emergent” refers to in the specific experiment.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What is the system-level property here?
2. Was that grouping centrally specified?
3. Does emergence imply self-improvement?
4. What would weaken the causal explanation?

<details>
<summary>Hint</summary>

Name the collective pattern first. Then ask whether it depends on the interaction and whether it helps the task; these are separate claims.

</details>

<details>
<summary>Explained answers</summary>

1. Measured grouping of similar job types across the execution trace.

2. The local preference is specified; the resulting sequence arises through interactions with available jobs.

3. No. The pattern may have no benefit or may be harmful.

4. The same pattern persisting when the proposed interaction is removed, or a confounded comparison.

</details>

## What's next

Use a small game to observe experience, feedback, and a retained self-play learning update. Continue to [07.07: Learn what self-play does and does not provide](../step_07_self_play/README.md).
