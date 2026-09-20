# 05.02 · Choose a skill for the task

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A router that sends bike regression and wine classification to suitable fixed procedures.

## Why this matters

A metric or model that fits one task can be wrong for another. Reuse should preserve meaning.

## Before you start

Complete [05.01: Combine fixed components into a useful system](../step_01_combine_components/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/05-02</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Both data cards, the domain vocabulary, and two fresh workspaces.

**Budget:** Two fits: one constant baseline for each task. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

The task brief identifies the target type and evaluation rule. Regression estimates a count and uses MAE. The derived wine classification task predicts whether quality is at least 7 and uses balanced accuracy. Routing chooses an already defined procedure; it does not learn a new one.

**A concrete example.** For an illustrative classification set with 90 negative and 10 positive cases, predicting negative every time gives 90% ordinary accuracy. Negative recall is 1 and positive recall is 0, so balanced accuracy is (1 + 0) / 2 = 0.5. The apparent success depends on the metric. The wine route must make the minority-class failure visible.

![Routing selects an existing procedure appropriate to the task. It does not learn a new procedure.](../../assets/diagrams/lab-05-02.png)

*Read the diagram:* Routing selects an existing procedure appropriate to the task. It does not learn a new procedure.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 05.02, Choose a skill for the task, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Would a majority-only wine classifier look better under accuracy than under balanced accuracy?

### 1. Build the route table

Connect task meaning to method.

```text
Write ROUTING.md with input task, target type, data card, model baseline, metric, and required checks. Reject an unrecognized task instead of guessing.
```

**Observe:** Each route has a scientifically appropriate metric.

### 2. Execute both routes

Test transfer of the system structure.

```text
Run a constant bike baseline and a majority wine baseline. Inspect wine class balance and both class recalls. Save a comparison of what is shared and what differs.
```

**Observe:** The majority classifier has balanced accuracy 0.5 when both classes occur.

## Check your result

The two tasks use their own contracts. Identical wine feature rows stay in one partition. Unknown tasks are rejected.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| ROUTING.md | Maps each recognized task to its data card, target, baseline, metric, and checks. |
| Separate bike and wine baseline records | Use distinct contracts and preserve each task’s actual predictions and metric. |
| Task comparison and unknown-task refusal | Explain shared structure, changed scientific choices, both wine class recalls, and the rejected unknown input. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Give the router a task with no target type. Require a clarification of the scientific question before choosing a metric.

## If something goes wrong

If both routes report MAE or the same target name, inspect whether the task contract was copied without adaptation. If wine results omit a class, check the duplicate-group split and class presence before interpreting balanced accuracy. An unknown target type needs a task decision before the router can select a meaningful evaluator.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Routing selects a method for a known task.
- Shared workflow structure does not mean shared metrics.
- An unknown task should expose missing information.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why not use raw accuracy alone for wine?
2. Is task routing self-organization?
3. What transfers from regression to classification?
4. What needs adaptation?

<details>
<summary>Hint</summary>

Ask what an all-negative classifier gets right and what it never gets right. Then check whether the chosen metric exposes both facts.

</details>

<details>
<summary>Explained answers</summary>

1. Class imbalance can make majority prediction look strong while missing every positive example.

2. Not by itself. A fixed route table is predefined organization.

3. Framing, provenance, split discipline, baseline comparison, evidence, and budgets.

4. Target definition, models, metrics, error analysis, and relevant data checks.

</details>

## What's next

Give the system the right reference information and current task state. Continue to [05.03: Retrieve what matters and retain task state](../step_03_context_and_state/README.md).
