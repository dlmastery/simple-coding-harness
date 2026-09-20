# 10.18 · Turn a limitation into a scientific hypothesis

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A baseline, a testable hypothesis, and a prespecified experiment.

## Why this matters

An interesting idea becomes a research question when you can state what evidence would support or contradict it.

## Before you start

Complete [10.17: Update the skill updater on a slower schedule](../../05_meta_skill_evolution/step_17_meta_skills/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-18</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The bike baseline and selection error slices. No final outcomes.

**Budget:** Two fits: baseline and one intervention. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

ScientistTwo motivates a research workflow built around hypotheses and experiments. Our classroom question is narrow: does adding permitted weather information help a fixed linear recipe beyond calendar inputs? This is a prediction study, not a causal claim about weather.



![Turn an observed limitation into a falsifiable hypothesis before changing the experiment.](../../../assets/diagrams/lab-10-18.png)

*Read the diagram:* Turn an observed limitation into a falsifiable hypothesis before changing the experiment.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.18, Turn a limitation into a scientific hypothesis, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** What observation would make you reject the proposed explanation?

### 1. Write the hypothesis

Connect a limitation to a measurable consequence.

```text
Create HYPOTHESIS.md with observed limitation, proposed mechanism, intervention, metric, baseline, expected result, alternative explanation, and rejection condition. Use the fixed bike contract.
```

**Observe:** The hypothesis could be wrong.

### 2. Run the experiment

Produce evidence for the stated question.

```text
Fit linear/calendar and linear/all under matching settings. Save predictions, slice errors, costs, and a conclusion tied to the predeclared question.
```

**Observe:** The conclusion addresses the intervention rather than a broad intelligence claim.

## Check your result

The hypothesis precedes results. One declared factor changes. A failed hypothesis remains a valid research outcome.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Rewrite “weather improves demand prediction” as a conditional statement tied to this task, model, period, and metric.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A hypothesis predicts an observable difference.
- A baseline defines the comparison.
- Predictive evidence is not automatically causal evidence.

## Research connection

[ScientistTwo](https://arxiv.org/abs/2609.19644), Jaehyun Nam, Jinsung Yoon, Yanzhou Pan, Yubo Wang, Rui Meng, Parthasarathy Ranganathan, and Tomas Pfister; Google Cloud AI Research and University of Waterloo; 17 September 2026.

**Activity type: mechanism exercise.** You execute a small classroom mechanism. Its task, models, and budget differ from the source. Local observations do not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why include an alternative explanation?
2. What is the intervention?
3. Does this reproduce autonomous scientific discovery?
4. What makes a negative result useful?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. It prevents treating one favorable outcome as uniquely proving the proposed mechanism.

2. Adding the permitted weather feature group while holding the linear recipe and evaluation fixed.

3. No. It is a small mechanism exercise with a supplied task and limited search.

4. It rules out or narrows a hypothesis under the tested conditions.

</details>

## What's next

Screen ideas cheaply, then use ablations to test contributions. Continue to [10.19: Screen ideas and test their contributions](../step_19_screen_ablate/README.md).
