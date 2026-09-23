# Follow the result, then follow the rule

[Course](README.md) · [Capstones](11_capstones/README.md) · [Source instructions for every lab](SOURCE-ARTIFACTS.md)

This is an example teaching portfolio built from actual author walkthroughs. It connects three different kinds of evidence. The experiments are separate; their records and costs remain separate too. A peer reproduction is prepared but has not occurred.

![Three stories connect a prediction, a task-skill revision, and later use of a changed improver.](assets/illustrations/capstone-teach-back-v2.png)

*The picture supplies the story structure. Its bike equation and contrasting-case rule are examples, not measurements below. Here we trace white-wine predictions, a separate unit-conversion repair, and a changed selection rule. The peer scene is illustrative; review is pending.*

[Open the illustration at full size](assets/illustrations/capstone-teach-back-v2.png).

## One row becomes a prediction

The [task brief](evidence/2026-09-21/capstone-harness/package/TASK.md) asks for a white-wine quality estimate from eleven laboratory inputs. The [data card](evidence/2026-09-21/capstone-harness/package/DATA-CARD.md) explains provenance and limits. Equal input rows stay in one partition, and preprocessing uses training rows only.

Take zero-based dataset row 26. Its inputs include fixed acidity 6.9 and alcohol 10.0; its observed quality is 6. Quality is the target for checking, never an input. The saved split assigns this row to selection.

| Retained model | Prediction | Absolute error |
|---|---:|---:|
| Tree selected by the original rule | 7.000000 | 1.000000 |
| Forest selected by the revised rule | 6.264954 | 0.264954 |

Open the [complete row](evidence/2026-09-22/portfolio/ROW-26.csv) and [linked predictions](evidence/2026-09-22/portfolio/ROW-PREDICTIONS.csv). This row makes MAE understandable: subtract the observed target from a prediction, take the absolute value, then average such errors over the declared partition. One favorable row cannot establish overall superiority; the full comparison below supplies aggregate evidence.

## A failed check changes a task skill

In a separate [unit-conversion exercise](evidence/2026-09-21/meta-skills/README.md), two candidate recipes have equal constructed quality. One takes 800 milliseconds and the other one second. These durations are fixtures, not measured model training. The original task skill treats an unknown unit as seconds and makes the [wrong choice](evidence/2026-09-21/meta-skills/prerequisites/parent-milliseconds/RESULT.md).

The author adds a millisecond conversion to the [child task skill](evidence/2026-09-21/meta-skills/skills/TASK-SKILL-v1.md). The [target check](evidence/2026-09-21/meta-skills/10-16/target/RESULT.md) and a [seconds regression check](evidence/2026-09-21/meta-skills/10-16/second/RESULT.md) pass. The updater stays fixed. This is a task-procedure repair; it does not by itself show a changed improver. The child still has an unsafe fallback for other unknown units, so two passes do not prove a complete repair.

## A changed improver governs later choices

Return to the white-wine capstone. [I0](evidence/2026-09-21/capstone-recursion/I0.md) ranks candidate recipes by training error. It selects an overfit tree. After seeing the development result, the author saves [one proposed change](evidence/2026-09-21/capstone-recursion/CHANGE-PROPOSAL.md): [I1](evidence/2026-09-21/capstone-recursion/I1.md) ranks by selection error.

Both later arms start from identical tree-recipe bytes and fit the same tree, ridge and forest recipes. The [original-rule trace](evidence/2026-09-21/capstone-recursion/g2-i0-TRACE.csv) keeps the tree; the [revised-rule trace](evidence/2026-09-21/capstone-recursion/g2-i1-TRACE.csv) ends at forest. Each decision identifies the exact instruction used. Matching recipes produce identical selection predictions, so the changed retention rule explains the different endpoint in this controlled comparison.

The [external gate](evidence/2026-09-21/capstone-recursion/PROMOTION.csv) accepts I1 before final evaluation. [Frozen final results](evidence/2026-09-21/capstone-recursion/FINAL-RESULTS.csv) are MAE 0.675403 for the original arm and 0.546309 for the revised arm. Eight fits ran. The later use was a candidate trial; no post-acceptance third generation occurred. The author supplied the edit, and the original rule was deliberately weak. Read the [claim audit](evidence/2026-09-21/capstone-recursion/CLAIM-AUDIT.md) before making a broader claim.

## Explain the architecture through this project

| Concept | Point to something concrete |
|---|---|
| Process | Data inspection, fixed split, fit, prediction check and report |
| Loop | Repeated proposals and decisions with a finite attempt budget |
| Graph | Dependencies and failure routes: a prediction must exist before checking; a failed check prevents retention |
| Ontology | A target is not a feature; milliseconds and seconds have different meanings |
| System | Agent, readable skills, runner, data and checker contribute distinct operations |
| Meta-harness | A readable new-task brief led to a generated execution package |
| Self-improvement | A persisted procedure changes and is checked against its predecessor |
| Recursive structure | An improver revision reaches later improvement work; benefit and autonomy need separate evidence |

These concepts are not interchangeable names for “an agent ran a loop.” Use the [teach-back guide](instructor/PEER-REVIEW.md) to explain a new case without memorizing the table.

## Compare with sound conventional procedures

The later [public-tabular study](evidence/2026-09-22/tabular-comparison/README.md)
tests six procedures on six reserved tasks with equal eight-fit allowances.
It preserves both favorable and unfavorable examples: the revised updater
helps contraceptive-method classification and concrete-strength regression,
but hurts German-credit classification and leaves three outcomes unchanged.
Its mean uncertainty interval includes zero. Frozen memory beats random
search in this sample but loses to the fixed portfolio overall.

Trace the two later task-23 skills, then inspect the credit regression and
source-composition diagnosis. This gives the portfolio a stronger comparison
than the earlier deliberately weak training-ranking rule. It does not establish
autonomous discovery, successful post-promotion generations or general RSI.
Keep the [separate discovery-policy study](evidence/2026-09-22/discovery-final/README.md),
which measures fewer executed fits, distinct from this equal-fit comparison.

The [complete-researcher study](evidence/2026-09-22/nested-research-evaluation/README.md)
adds a distinct test of later source use. An improver rewrites a complete
twelve-fit researcher, the outer gate retains a parent, and the inherited
improver generates another researcher that actually runs on reserved tasks.
Count all 624 attempts, including losing development searches. I1 improves
spam and satellite classification, ties three tasks and worsens housing
regression against I0 and the parent; the overall interval spans zero.
Read the [illustrated results guide](RESULTS-GUIDE.md) and trace both a gain
and the housing regression. This establishes executed inheritance, not an
overall RSI gain. Keep this study separate from the eight-fit teaching case.

## Let a peer start without this chat

Open the repository in a coding agent and give it this prompt:

```text
Read rsi/AGENTS.md, the tutor skill,
rsi/PORTFOLIO.md and
rsi/instructor/PEER-REVIEW.md.
Guide my peer through the one-fit baseline
reproduction described there. Ask for their
prediction before running. You prepare the
environment and write all commands.
Preserve existing evidence. Use a new sibling
workspace and a one-attempt budget. Keep the
result and the intentional refusal.
Record only feedback that actually occurs.
```

The [small generated package](evidence/2026-09-21/capstone-harness/export/package/README.md) already passed an author clean-environment run. That does not substitute for a peer. The [peer-session record](evidence/2026-09-22/portfolio/PEER-STATUS.md) remains pending.

## Defend the limits as well as the result

Read the separate costs for the [baseline package](evidence/2026-09-21/capstone-harness/COST.md), [unit exercise](evidence/2026-09-21/meta-skills/COST.md), and [eight-fit comparison](evidence/2026-09-21/capstone-recursion/COST.md). Fit intervals exclude much of the work, and inference costs are unknown. Our [portfolio assembly check](evidence/2026-09-22/portfolio/README.md) verified thirty original file identities without fitting again.

The [portability matrix](evidence/2026-09-21/capstone-portability/PORTABILITY.md) identifies the local paths that ran and the other hosts that did not. The [source audit](evidence/2026-09-22/external-audit/CLAIM-AUDIT.md) demonstrates how to question a research claim fairly. Neither supports universal agent compatibility, cluster readiness, independent reproduction or sustained acceleration.

The defensible outcome is a runnable, inspectable teaching example with an observed local improvement, preserved failures and explicit limits. Your own portfolio should meet the same evidence standard even when its revised procedure loses.
