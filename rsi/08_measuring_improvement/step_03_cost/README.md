# 08.03 · Count the cost of research

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 08, Changes and their evidence → lab 3 of 6. [Find this theme in the course map](../../COURSE-MAP.md#theme-08) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A resource ledger that includes proposals, checks, retries, failed work, and fitting.

## Why this matters

A method can look better because it spent more resources outside the model-fit counter.

## Before you start

Complete [08.02: Freeze selection before final evaluation](../step_02_final_boundary/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/08-03</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Two procedure traces and their candidate ledgers.

**Budget:** No new fits; reconcile existing measurements. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Resources are not interchangeable. Record agent tokens or provider charges when available, local fit seconds, total wall time, evaluator calls, and later GPU-hours. Unknown values stay unknown. Equal fit counts are useful but do not imply equal total research cost.

**A concrete example.** The [measured bike procedures](../../evidence/2026-09-20/self-star-and-measurement/08-03/COST.md) each used two fits and two checks, even though each retained only one candidate. Counting only winners would halve the recorded attempts. Now consider a separate numerical illustration: A needs 20 fit-seconds plus p proposal-seconds; B needs 30 + 10 = 40 seconds. With sequential stages and otherwise equal costs, A loses its time advantage when p exceeds 20. These invented costs illustrate a threshold; they are not the run’s measurements.

![Proposal, data, fit, checking, review, retry, and failure records feed a complete cost ledger. The retained candidate is only a subset. A separate invented example shows how proposal overhead can erase a fit-time advantage.](../../assets/illustrations/research-cost-ledger-v1.png)

*Account for the full search effort, including work that failed or did not help. Wall time, tokens, fit time, and GPU-hours measure different resources; do not add overlapping durations or unlike units. The token counter is an instrument icon, not a zero-usage observation. Leave unavailable usage unknown. The 20+p versus 30+10 comparison is invented arithmetic with sequential stages and equal other costs. It is not a measured result from this course, and equal fit counts do not establish equal total cost.*

[Open the illustration at full size](../../assets/illustrations/research-cost-ledger-v1.png).

<details>
<summary>See the step diagram</summary>

![Research cost includes proposing, running, checking, and failed work. Fit time is only one component.](../../assets/diagrams/lab-08-03.png)

*Read the diagram:* Research cost includes proposing, running, checking, and failed work. Fit time is only one component.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 08.03, Count the cost
of research, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Which procedure could appear efficient if its failed proposals were omitted?

### 1. Build the ledger

Account for the full route to the result.

```text
Create COST.md for both traces. Include
proposal generation, data inspection,
fitting, evaluation, review, retries,
failures, and final checking. Mark
unavailable agent costs explicitly.
```

**Observe:** No cost category silently becomes zero.

### 2. Reinterpret the comparison

Match the conclusion to available accounting.

```text
Compare retained quality at matched known
resources. State whether total-cost
superiority can be assessed. Show the effect
of including rejected attempts in the count.
```

**Observe:** A narrower defensible conclusion may replace an attractive broad claim.

## Check your result

The ledger reconciles every attempt. Unknown cost is distinct from zero. The report states what resource equality was actually achieved.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| COST.md for both procedures | Reconciles proposals, fits, checks, failures, retries, final evaluation, and unknown categories. |
| Attempt-to-cost mapping | Links each ledger item to a measurement or an explicit missing value. |
| Revised efficiency claim | Names the quality measure and the resource actually matched or compared. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Add a large proposal-generation cost to a labelled numerical illustration. Determine when a fit-efficient method becomes more expensive overall.

## If something goes wrong

If totals are smaller than their components, check units, overlapping parallel work, and whether wall time was added to included fit time. Avoid double counting. If provider usage is unavailable, leave it unknown rather than estimating it from a local duration. A comparison can still report equal fits without claiming equal total cost.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Research overhead can dominate training cost.
- Unknown is not zero.
- Efficiency claims require a declared quality and resource comparison.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why count rejected candidates?
2. Can tokens be converted to GPU-hours without assumptions?
3. What if provider usage is unavailable?
4. Does a higher score at ten times the budget prove a better method?

<details>
<summary>Hint</summary>

A stopwatch, a token counter, and a bill answer different questions. Keep their units and missing categories visible.

</details>

<details>
<summary>Explained answers</summary>

1. They were part of the search cost required to obtain the retained artifact.

2. No. They measure different resources and require a specified pricing or compute model to combine.

3. Report the gap and restrict the cost claim.

4. It may show a better result at that budget, not superior efficiency or equal-resource performance.

</details>

## What's next

Use controlled removals to ask which change caused a benefit. Continue to [08.04: Separate the effects of memory and procedure changes](../step_04_ablation/README.md).
