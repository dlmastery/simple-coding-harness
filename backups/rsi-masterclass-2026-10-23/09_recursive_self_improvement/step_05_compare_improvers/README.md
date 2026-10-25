# 09.05 · Measure whether the revised improver helps

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 09, Changes and their evidence → lab 5 of 7. [Find this theme in the course map](../../COURSE-MAP.md#theme-09) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A matched comparison of improvements produced by two improver versions.

## Why this matters

The new improver may produce a strong current solver yet be worse at producing future improvements.

## Before you start

Complete [09.04: Use the revised improver in the next round](../step_04_inherit/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/09-05</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Frozen v0 and v1 improvers, identical parent task skill, and prespecified fresh comparison cases.

**Budget:** Two rounds per improver, at most two fits per round; eight fits total. Count proposal and check overhead. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

The outcome is the improvement each procedure produces from the same starting solver under comparable resources. Compare retained descendants, not the most attractive intermediate score. Use fresh contexts where available and state contamination if both procedures share one context. A small experiment can remain inconclusive.

**A concrete example.** The saved [eight-fit comparison](../../evidence/2026-09-20/clean-journey/09-05/README.md) uses two synthetic tasks. A training-based promotion rule retains an overfit regression tree and raises final MAE from 22.74 to 81.47. A revised selection-based rule keeps the parent, so its gain is zero and it avoids the loss. Both rules retain a useful classification edit, raising final balanced accuracy from 0.87 to 0.92. The candidates and fit allowances match. The author prepared both procedures in one context; these two constructed cases do not establish a general improver advantage. The [six-task extension](../../evidence/2026-09-22/tabular-comparison/README.md) uses sound local-search parents and fixed/random controls. Revised updater versus original updater with the revised harness improves two final task scores, ties three and worsens one. Its mean normalized-loss change is −0.009343, with an exploratory interval spanning zero. The fixed portfolio is strongest overall. A favorable comparison with one parent is not a claim of beating ordinary model selection. In that [later comparison](../../evidence/2026-09-22/nested-research-evaluation/README.md), both improvement paths start from the same initial researcher, then inherit their own retained parents. I1 improves two reserved tasks, ties three and worsens one against I0. The mean loss change is +0.000120 and its interval includes zero. Comparing full improvement paths does not require their retained descendants to remain identical.

![The same parent task skill feeds two improver arms, each with two rounds, retained descendants, and complete attempt and cost records. Their outcomes are compared against the common baseline.](../../assets/illustrations/improver-comparison-v1.png)

*Apply the declared retention rules during each round. The I0 and I1 labels on the descendant reports identify the producing improver; give task skills their own version identities. Compare retained results and all known costs, including failures. Separate folders do not establish independent contexts. Eight fits is a maximum; benefit, regression, and inconclusive outcomes are all possible.*

[Open the illustration at full size](../../assets/illustrations/improver-comparison-v1.png).

<details>
<summary>See the step diagram</summary>

![Compare the improvements produced by the two improvers from matched starts. Do not compare only their instruction text.](../../assets/diagrams/lab-09-05.png)

*Read the diagram:* Compare the improvements produced by the two improvers from matched starts. Do not compare only their instruction text.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 09.05, Measure whether
the revised improver helps, one step at a
time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Could v1 win on the current task but lose on improvement produced per unit cost?

### 1. Freeze the protocol

Define the comparison before execution.

```text
Write IMPROVER-COMPARISON.md with starting
skill, tasks, budgets, acceptance rule,
repetitions, context boundary, and measured
costs. Do not use cases that selected v1 as
fresh evidence.
```

**Observe:** The comparison is about future improvement work.

### 2. Run both arms

Measure descendants and overhead.

```text
Execute v0 and v1 from matched starting
artifacts. Keep all proposals, failed
checks, descendants, and costs. Compare
retained gains over the common baseline and
report uncertainty. If fresh independent
contexts are unavailable, label that
limitation prominently.
```

**Observe:** The evidence can show benefit, regression, or insufficient information.

## Check your result

Both arms start from the same solver. Their resource limits and known costs are reported. The conclusion concerns the tested improvers and tasks only.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Matched-comparison protocol | Freezes two cases, both improvers, identical starting task skills, two fits per arm/case, and the external metric. |
| Eight fit and decision records | Include attempted and rejected revisions and all available costs. |
| Retained-outcome comparison | Judges the artifact each improver actually retained, with narrow claims about the two cases. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Show how reporting only the best child from each arm hides failed proposals and selection cost.

## If something goes wrong

If one improver is judged by its best discarded candidate and the other by its retained candidate, recompute the comparison consistently. If agent costs are unknown, do not claim equal total resources. If both arms have identical outcomes, inspect whether their changed rule encountered a case where it could matter; a null result remains valid evidence.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A better solver is not automatically a better improver.
- Measure gains produced from comparable starts.
- Retained descendants and total research costs matter.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What is the main dependent outcome?
2. Why use fresh cases?
3. Does one win establish sustained acceleration?
4. What if total agent cost is unknown?

<details>
<summary>Hint</summary>

Judge each improver by the consequences of its decisions. Identical candidate scores can still lead to different retained systems.

</details>

<details>
<summary>Explained answers</summary>

1. The improvement produced by each improver under the declared comparison, together with its cost and reliability.

2. Cases used to design or select v1 can favor it and weaken the generalization claim.

3. No. That requires repeated generational evidence beyond a two-version comparison.

4. State it and avoid claiming equal total-resource superiority.

</details>

## What's next

Run a short lineage with checkpoints and a stopping rule. Continue to [09.06: Run bounded recursive generations](../step_06_bounded_generations/README.md).
