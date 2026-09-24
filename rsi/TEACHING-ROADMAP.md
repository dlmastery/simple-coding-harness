# Teach the course one capability at a time

[Lecture slides and speaker notes](PRESENTATION.md): 37-slide PowerPoint review draft with the course figures and measured results.

[Course](README.md) · [Glossary](GLOSSARY.md) · [Every lab](COURSE-MAP.md) · [Instructor guide](instructor/README.md)

The teaching goal is that students can follow one chain: a data question produces an experiment; a failure motivates a procedure change; a revised improver governs later work; a fair comparison determines what the change achieved. They should be able to explain a failure as clearly as a success.

Keep the bike-demand task familiar while introducing one new mechanism. Transfer to wine classification after students understand the workflow. The research studio then asks them to recognize those mechanisms in current papers. Capstones test whether they can use the ideas without following the original example exactly.

![The bike-demand project connects the twelve themes through experiments, dependable workflows, systems and builders, changes and evidence, research studio, and capstones.](assets/illustrations/course-mindmap-v2.png)

*Use this existing course map to locate the next teaching block. The branches group concepts; they are not universal RSI levels.* [Open the full-size map](assets/illustrations/course-mindmap-v2.png).

## Choose a scope

| Route | What to teach | What students can reasonably demonstrate |
|---|---|---|
| Two-hour orientation | Selected activities from 00.01, 00.03 and 00.04, with setup completed beforehand | Explain one prediction, inspect a baseline and detect a false summary. This is a preview, not three completed labs or an RSI qualification. |
| Core course | All 58 labs in themes 00–09; blocks 1–8 below | Build a bounded ML workflow, generate a harness, distinguish self-* mechanisms and audit a changed improver. |
| Full masterclass | All 101 labs; blocks 1–18 below | Add the complete research studio, transfer, source audit, independent capstone work and peer handoff. |

The current author estimates are **19.5–34 hours** of reading and guided discussion for the core and **49.8–82 hours** for the full masterclass. Setup, code execution, debugging, deeper paper reading and independent project work need additional time. These are not measured learner durations.

The 18 blocks below are a suggested calendar, not 18 single lectures. A weekly block makes an approximately 18-week course; split dense blocks across meetings or extend the calendar. In particular, blocks 4 and 5 each cover eleven short labs. Do not assume that one two-hour class can complete either block.

## Prepare before the first class

Students need basic ML vocabulary: tables, features, targets, fitting and prediction error. They need no prior RSI or harness experience. Use [the glossary](GLOSSARY.md#one-experiment) for a short refresher when needed.

Have the agent perform [workspace setup](00_start_here/step_02_prepare_the_workspace/README.md) on each student's actual machine. Check file access, commands, dependencies and a small plot. Use CPU defaults and a separate learner workspace. Keep hosted-agent costs visible. An unavailable capability should produce a specific setup issue, not a pretend execution.

The instructor should rehearse one valid baseline and one intended refusal. Have a labelled author example available for discussion if a student's setup fails. Record that student activity as observation until the student can execute it.

## The full teaching calendar

Use the [course map](COURSE-MAP.md) for direct links to every numbered lesson. Ranges below are inclusive. Complete each listed range in order; the full route includes all 101 labs exactly once.

| Block | Labs and focus | Bring forward | Leave with, and explain |
|---|---|---|---|
| 1 | **00.01–00.04:** one trustworthy prediction | Basic ML vocabulary and setup access | Task brief, checked baseline and evidence note. Explain where one reported error came from. |
| 2 | **01.01–01.05:** a fixed process and a saved skill | Baseline predictions and data report | Process, learner-owned skill and handoff. Show what must survive when the chat changes. |
| 3 | **02.01–02.06:** feedback, state and bounded loops | The fixed skill and its weak result | Hypothesis, ledger, stop/refusal and resume records. Explain why a restart does not restore spent attempts. |
| 4 | **03.01–04.05:** route work and check its meaning | Loop state, predictions and failure examples | Workflow, domain facts and invariant checks. Distinguish a routing error from a scientifically invalid input. |
| 5 | **05.01–06.06:** a system and a harness builder | Workflow, domain checks and task skill | Fixed-system comparison, two readable briefs and generated bike/wine harnesses. Identify the unchanged builder. |
| 6 | **07.01–07.08:** the self-* family | Procedure versions and actual traces | Correction, memory, revision and simulation records; self-play policy updates. Identify what changes in each mechanism. |
| 7 | **08.01–08.06:** comparisons that deserve trust | Parent/child skills and usable predictions | Repetitions, frozen evaluation, costs, ablation, transfer and rollback records. Explain an alternative cause of an apparent gain. |
| 8 | **09.01–09.07:** revise the improver | Fixed-improver baseline and evaluation rules | Versioned improver, later-use trace and claim audit. Separate structure, benefit and acceleration. |
| 9 | **10.01–10.06:** definitions, announcements, exploration and memory | Core-course claim audit | Source cards, probes and frozen-memory comparison. Distinguish outcome validity from the validity of a lesson inferred from it. |
| 10 | **10.07–10.12:** Dream-RSI and modular evolution | Recorded task outcomes and source-reading habits | Discovery tree, replay, online confirmation, component edits and lineage audit. Explain what an unvisited branch cannot tell you. |
| 11 | **10.13–10.17:** AIDE² and meta-skill schedules | Inner researcher and update traces | Nested-cost comparison, separate ignition question and inherited updater revision. Distinguish being a better researcher from being a better improver. |
| 12 | **10.18–10.21:** ScientistTwo | Baseline errors and fixed evaluation | Hypothesis, screen, ablation, response to criticism and discovery lineage. Separate better outputs from a better scientific procedure. |
| 13 | **10.22–10.26:** ScienceBuddy | Wine predictions and reporting failures | Request/rubric, reporting-skill checks, grouped-reward calculation, model–harness pair simulation and result audit. Explain exactly what did and did not train. |
| 14 | **10.27–10.32:** reusable knowledge, procedure graphs, GUI and cost | Skills, traces, checked reports and browser capability where available | Rejected skill with retained knowledge, graph repair, GUI trace and cost/quality comparison. Explain why cheaper invalid output is not a gain. |
| 15 | **10.33–10.38:** scaffolds, model–harness fit, composition and limits | Research comparison notes and versioned procedures | Assistance removal, interface repair, operator simulation, reference checks, system matrix and bottleneck model. State which acceleration evidence is still missing. |
| 16 | **11.01–11.02:** build and test the capstone | A new task idea and bounded protocol | Runnable new harness and a recursive experiment with retained failures. State the changed object and the comparison before results. |
| 17 | **11.03–11.04:** portability and independent judgment | Frozen capstone artifacts | Actual small compatibility checks and a new primary-source audit. Separate executed support from generated setup. |
| 18 | **11.05:** peer reproduction and teach-back | Complete evidence-linked portfolio | A peer's real run and feedback, or an explicit pending record. Explain the whole chain without relying on paper names. |

For a two-hour orientation, prepare the baseline prerequisites and use roughly 20 minutes for the question and a data row, 30 for one baseline, 25 for its evidence check, 25 for a false-summary case and discussion, and 20 for explanation and next steps. This agenda is an instructor estimate; code execution may need a separate session.

## A repeatable teaching session

Use a 90-minute meeting for one substantial lab or selected steps. It is not a promise to finish several complete labs.

| Minutes | Instructor and student activity |
|---|---|
| 0–10 | Recall the previous result. Show the failure or limitation that motivates today's idea. |
| 10–20 | Explain the illustration. Ask students to trace one arrow and predict one outcome. |
| 20–45 | Students direct the agent through the next bounded action. The agent writes code; students own the scientific choices. |
| 45–60 | Open actual outputs, including a failure or counterexample. Compare them with the prediction. |
| 60–75 | Ask students to explain the mechanism and one changed condition. Use the lab quiz; offer hints before answers. |
| 75–90 | Save the lab note and progress, reconcile the budget, and identify the next action. |

If execution takes longer, stop at a valid checkpoint and resume next meeting. Preserve the experiment's contract, ledger and final lock. A timetable never authorizes extra fits or removal of a required check.

For paired work, one student states the scientific intent while the other checks the evidence. Swap roles at the next step. Do not let the agent answer the student's prediction or award itself a teach-back pass.

## Decide when students are ready to continue

| Gate | Ask for this demonstration | If it is unclear |
|---|---|---|
| After block 2 | Follow one row into a prediction and metric; show the saved process | Return to the baseline and hand-check two errors. |
| After block 4 | Explain why valid syntax can hide leakage; show a refused path | Compare one route error with one meaning error using existing fixtures. |
| After block 5 | Point to brief, builder, generated harness and its actual run | Keep the builder fixed and compare what changes across the two task briefs. |
| After block 6 | Classify correction, memory, organization and policy learning by the changed object | Use the glossary's example/counterexample pairs before another run. |
| After block 8 | Trace an improver revision into a later action and judge its benefit separately | Use the same saved outcomes to contrast the two decision rules. Do not invent another result. |
| After block 15 | Explain one paper through its local exercise and name three missing parts of a reproduction | Read the activity type and primary methods again; narrow the claim. |
| After block 18 | Let a peer find the evidence and reproduce a small run | Repair the handoff and preserve the failed attempt and actual feedback. |

Use the existing [0–2 lab-note rubric](instructor/README.md#assess-a-lab-note) for prediction, observation, explanation and limit. A high score on some criteria should not conceal a misunderstanding about leakage or the solver/improver distinction. Revisit that concept before increasing complexity. This is a teaching rubric, not a validated assessment instrument.

## Plan the capstone early

Begin collecting project questions after block 5. Students should propose a prediction unit, available inputs and a meaningful baseline before choosing an elaborate agent architecture.

At block 8, ask for a one-page sketch naming the solver, mutable improver and fixed external comparison. This is planning only. It does not add fits beyond the lessons' budgets.

At block 15, review the proposed task, data permission, evaluator, attempt allowance and claim criteria. Reject unbounded plans such as “keep improving until it works.” Require a laptop demonstration first. A GPU or cluster extension needs its own declared resources and actual backend checks.

During blocks 16–18, require a valid run, a meaningful failure, version ancestry, actual later use of a changed improver, a matched comparison and a readable [portfolio](PORTFOLIO.md). A well-supported negative or inconclusive result can satisfy the learning outcome. Use the [peer guide](instructor/PEER-REVIEW.md) for reproduction and teach-back.

## Shorter courses and optional depth

The core route ends after block 8. If time remains, choose a studio group by its learning question:

| Question | Studio route | Prerequisite evidence |
|---|---|---|
| How can an agent learn from exploration? | 10.03–10.06 | Frozen task, ledger and checked outcome |
| What can replay save, and what can it miss? | 10.07–10.09 | Actual candidate outcomes and known costs |
| Can better researchers improve researchers? | 10.13–10.17 | Fixed inner researcher and prior skill-update traces |
| How should an agent conduct scientific work? | 10.18–10.26 | Hypothesis and comparison skills; wine predictions for the rubric work |
| How do we retain useful procedures and control costs? | 10.27–10.36 | Saved skills, traces, graph and checks; browser access for the live GUI lab |

Read 10.01–10.02 before any selected group. Prepare the starting artifacts named by each lab. A selected route is a shorter course; do not call it completion of all 101 labs. In the full masterclass, every studio group is included. Optional full-scale paper reproduction and GPU training remain separate extensions.

## Teach through the agent

Give the tutor this instruction:

```text
Read rsi/AGENTS.md, rsi/TEACHING-ROADMAP.md,
and rsi/skills/rsi-tutor/SKILL.md.
We are beginning block [number].
Inspect my completed labs and available artifacts.
Name any missing prerequisite before execution.
Explain the next lab with one concrete example.
Use the glossary for unfamiliar terms.
You write the implementation; I make predictions
and explain the evidence.
Respect each lab's budget and learning checkpoints.
Save actual progress, skipped responses and next steps.
```

For the first teaching pilot, record setup time, confusing words, incorrect predictions, useful illustrations and recovery difficulties. Revise the material from that evidence. The calendar is a planning aid until real learners test its pace.
