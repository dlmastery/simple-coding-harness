# 10.21 · Distinguish better discoveries from a better scientist

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A two-step research lineage and an audit of the researcher’s own changes.

## Why this matters

Successively better scientific artifacts do not alone show that the research procedure improved.

## Before you start

Complete [10.20: Answer a criticism with evidence](../step_20_review_rebuttal/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-21</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Two completed hypothesis studies and their researcher instructions.

**Budget:** No fits required; optional one fresh test only if predeclared. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A previous result can become the baseline for a new investigation. Track the result lineage separately from the researcher version. If the procedure stays fixed while solutions improve, the evidence concerns accumulated research outputs. Testing a better researcher needs a comparison of research processes.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.21, Distinguish better discoveries from a better scientist, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Can a fixed scientist procedure produce several better solutions in sequence?

### 1. Trace successive results

Separate artifacts from their producer.

```text
Create DISCOVERY-LINEAGE.md with hypotheses, baselines, retained results, and costs. Add the researcher-procedure hash to every edge.
```

**Observe:** Result progression and researcher changes are visible separately.

### 2. Audit the claim

Apply the same standard to local and paper-reported work.

```text
Use audit-rsi-claim to classify your lineage. Read ScientistTwo’s evaluation sections and state which outputs they assess. Distinguish improved scientific artifacts from demonstrated improvement of an improver.
```

**Observe:** The conclusion follows the measured object.

## Check your result

The audit names the evaluated object. It does not infer researcher self-improvement from successive task gains alone.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Propose a matched experiment where old and new researcher procedures start from the same fresh baseline.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Research artifacts and research procedures have different lineages.
- Successive discovery can use a fixed method.
- A stronger researcher claim needs a stronger comparison.

## Research connection

[ScientistTwo](https://arxiv.org/abs/2609.19644), Jaehyun Nam, Jinsung Yoon, Yanzhou Pan, Yubo Wang, Rui Meng, Parthasarathy Ranganathan, and Tomas Pfister; Google Cloud AI Research and University of Waterloo; 17 September 2026.

This is a classroom mechanism exercise. Its task, models, and budget differ from the original study. Your measured result belongs to this exercise; it does not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What can a rising solution score show?
2. What does an unchanged researcher hash suggest?
3. What compares researcher quality?
4. Does the laptop exercise validate frontier scientific performance?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Improved retained task artifacts under their evaluation conditions.

2. The stored procedure did not change, though other context or state still needs inspection.

3. Research outcomes produced from matched fresh starts under comparable resources.

4. No. It teaches the structure of the research and evidence questions.

</details>

## What's next

Study how researcher requests and corrections become executable tasks. Continue to [10.22: Turn a researcher correction into a task](../../07_sciencebuddy/step_22_human_task/README.md).
