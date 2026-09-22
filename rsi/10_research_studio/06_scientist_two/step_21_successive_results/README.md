# 10.21 · Distinguish better discoveries from a better scientist

[Course](../../../README.md) · [Theme](../../README.md)

**You are here:** Theme 10, Research studio → lab 21 of 38. [Find this theme in the course map](../../../COURSE-MAP.md#theme-10) · [Whole-course mindmap](../../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A two-step research lineage and an audit of the researcher’s own changes.

## Why this matters

Successively better scientific artifacts do not alone show that the research procedure improved.

## Before you start

Complete [10.20: Answer a criticism with evidence](../step_20_review_rebuttal/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/10-21</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Two completed hypothesis studies and their researcher instructions.

**Budget:** No fits required; optional one fresh test only if predeclared. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A previous result can become the baseline for a new investigation. Track the result lineage separately from the researcher version. If the procedure stays fixed while solutions improve, the evidence concerns accumulated research outputs. Testing a better researcher needs a comparison of research processes.

**A concrete example.** The first study produces a better feature recipe. The second uses that recipe as its baseline and finds another gain. If both studies followed the same research instructions, the results improved while the recorded researcher stayed fixed. Accumulated outputs and improved research ability need separate lineages.

![Two studies retain artifact records while the stored researcher stays R0. A separate unexecuted comparison puts old R0 and revised R1 on identical fresh baselines and compares outcomes and costs.](../../../assets/illustrations/discovery-and-researcher-v2.png)

*A1 and A2 name retained-state records, not guaranteed new or better solutions. Rejection can preserve the previous artifact. An unchanged procedure hash says nothing by itself about changing memory, context, tools, or model versions, so record those too. The lower scene is the proposed comparison from the transfer exercise; this lab requires no new fits. Compare research outcomes under matched conditions before making a claim about a better research procedure.*

[Open the illustration at full size](../../../assets/illustrations/discovery-and-researcher-v2.png).

<details>
<summary>See the step diagram</summary>

![Better research outputs and a better research procedure are distinct objects of evaluation.](../../../assets/diagrams/lab-10-21.png)

*Read the diagram:* Better research outputs and a better research procedure are distinct objects of evaluation.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.21, Distinguish
better discoveries from a better scientist,
one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Can a fixed scientist procedure produce several better solutions in sequence?

### 1. Trace successive results

Separate artifacts from their producer.

```text
Create DISCOVERY-LINEAGE.md with hypotheses,
baselines, retained results, and costs. Add
the researcher-procedure hash to every edge.
```

**Observe:** Result progression and researcher changes are visible separately.

### 2. Audit the claim

Apply the same standard to local and paper-reported work.

```text
Use audit-rsi-claim to classify your
lineage. Read ScientistTwo’s evaluation
sections and state which outputs they
assess. Distinguish improved scientific
artifacts from demonstrated improvement of
an improver.
```

**Observe:** The conclusion follows the measured object.

## Check your result

The audit names the evaluated object. It does not infer researcher self-improvement from successive task gains alone.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| DISCOVERY-LINEAGE.md | Connects hypotheses, baselines, retained results, costs, and researcher versions. |
| Local/source audit | Names the object actually evaluated in each case. |
| Proposed researcher comparison | Starts old and new procedures from the same fresh baseline rather than recycling their accumulated advantages. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Propose a matched experiment where old and new researcher procedures start from the same fresh baseline.

## If something goes wrong

If a researcher hash is unavailable, mark the missing version evidence instead of assuming it stayed fixed. Conversely, an unchanged file does not prove all context and memory stayed fixed. Record those other retained states before making a claim about the entire research system.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Research artifacts and research procedures have different lineages.
- Successive discovery can use a fixed method.
- A stronger researcher claim needs a stronger comparison.

## Research connection

[ScientistTwo](https://arxiv.org/abs/2609.19644), Jaehyun Nam, Jinsung Yoon, Yanzhou Pan, Yubo Wang, Rui Meng, Parthasarathy Ranganathan, and Tomas Pfister; Google Cloud AI Research and University of Waterloo; 17 September 2026.

**Activity type: mechanism exercise.** You execute a small classroom mechanism. Its task, models, and budget differ from the source. Local observations do not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What can a rising solution score show?
2. What does an unchanged researcher hash suggest?
3. What compares researcher quality?
4. Does the laptop exercise validate frontier scientific performance?

<details>
<summary>Hint</summary>

Compare the result artifact with the procedure that produced it. Improvement in the first does not identify a change in the second.

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
