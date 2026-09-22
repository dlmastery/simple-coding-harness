# 01.04 · Check outputs with a separate calculation

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 01, One experiment → lab 4 of 5. [Find this theme in the course map](../../COURSE-MAP.md#theme-01) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

An output checker that derives error from prediction rows and rejects a mismatch.

## Why this matters

A solver’s confidence cannot substitute for measuring its output.

## Before you start

Complete [01.03: Turn the process into a skill](../step_03_make_a_skill/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/01-04</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The fixed baseline skill and a successful prediction file.

**Budget:** No model fits; two checker runs. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A separate calculation can recompute a metric without trusting the report writer. That is useful separation of responsibilities. It is not necessarily independent context or access control: the same host agent may still see every file.

**A concrete example.** Suppose a prediction row has a plausible error but refers to source row 12, which belongs to training. The arithmetic can be correct and the selection claim still invalid. A checker with expected row identities rejects that substitution. A checker given only “MAE 159.95” cannot detect it.

![Two runs of the same checker use common expected selection IDs, source targets, and candidate identity. The original symbolic rows S1, S2, S3 are compared with a teaching copy containing training row T1 instead of S2.](../../assets/illustrations/row-identity-check-v1.png)

*S1, S2, S3, and T1 are symbolic IDs. The red text in the altered table is an annotation, not a prediction value. Change only the ID in the real teaching copy; preserve prediction values and the original file. Both runs use the same checker code and reference inputs despite the different illustration colors. Check the full row set, duplicates, candidate identity, and targets from pinned data. The archive lock means preserve the original; it does not establish access control. Record actual verdicts and nonzero failure status.*

[Open the illustration at full size](../../assets/illustrations/row-identity-check-v1.png).

<details>
<summary>See the step diagram</summary>

![The checker starts from prediction rows. It does not accept the solver’s reported score as its input truth.](../../assets/diagrams/lab-01-04.png)

*Read the diagram:* The checker starts from prediction rows. It does not accept the solver’s reported score as its input truth.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 01.04, Check outputs
with a separate calculation, one step at a
time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Could a mathematically correct checker still approve the wrong candidate?

### 1. Generate the checker

Give the check its own inputs.

```text
Generate a checker that reads the expected
candidate identity and recipe from the run
records, prediction rows, expected partition
row IDs, source targets from the pinned
data, and declared metric. Match rows to
source targets instead of trusting copied
actual values. Recompute MAE and reject
missing, duplicate, or mismatched rows. Run
it on the baseline. Save its code and
output.
```

**Observe:** The checker checks identity and completeness as well as arithmetic.

### 2. Substitute one row

Demonstrate an actual refusal.

```text
In a labelled copy, replace one selection
row ID with a training row ID. Run the
checker and retain its nonzero result. Do
not alter the original predictions.
```

**Observe:** The wrong partition row is rejected even if the summary score looks reasonable.

## Check your result

The valid file passes and the substituted-row file fails. CHECK-REPORT.md describes exactly what the checker reads and cannot protect.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Generated checker | Reads expected row identities and source targets as well as predictions and the claimed metric. |
| CHECK-REPORT.md | States the valid verdict, substituted-row refusal, exit statuses, and the checker’s access limits. |
| Unchanged original and altered copy | Make it possible to inspect the exact substitution that caused the failure. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Give the checker only a metric number without predictions. Explain which checks become impossible.

## If something goes wrong

If the altered row passes, check that the tool compares the full identity set and detects duplicates, rather than only counting rows. If a valid file fails, inspect identity types, ordering requirements, and source version before relaxing a rule. A separate calculation is useful even when the same agent can read both sides; label that boundary accurately.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A verifier needs evidence, not just a reported score.
- Identity checks prevent comparisons between different objects.
- Separate code does not imply an inaccessible evaluator.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why compare row identities?
2. Is a second role prompt independent evaluation?
3. What does a deliberate failing input add?
4. What requires a stronger boundary?

<details>
<summary>Hint</summary>

A candidate, a row set, and a number must refer to the same experiment. Ask what substitution could leave the number plausible while changing the scientific question.

</details>

<details>
<summary>Explained answers</summary>

1. A correct metric on the wrong rows answers a different question.

2. No. The same context can retain prior information and the same permissions.

3. It tests whether the checker detects a specific error.

4. Claims that depend on the candidate being unable to see or alter evaluation cases and logic.

</details>

## What's next

Test whether the skill works after the conversation state is gone. Continue to [01.05: Reuse the skill in a fresh session](../step_05_reuse_the_skill/README.md).
