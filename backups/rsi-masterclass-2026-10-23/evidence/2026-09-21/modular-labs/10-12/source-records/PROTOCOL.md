# Two generations on the bike task

Declared on 20 September 2026 before this run. This author walkthrough addresses labs 09.02 and 09.06. It uses a new sibling workspace and leaves all earlier closed experiments intact. The student-facing interface remains the lesson prompts and Markdown skills; the maintainer writes the execution driver.

## Question and prior knowledge

Can a fixed improver govern two task-skill generations? Can a tested revision become the active improver, govern a later task-skill change, and remain active when another revision is rejected? Can a process stop after a proposal and resume without treating the proposal as accepted?

The earlier public bike walkthrough already showed that a calendar tree loses to a calendar linear model on selection MAE, while adding weather to the linear model helps. Those observations motivate this constructed teaching sequence. This is not a blind test, an independent replication, or discovery of a competitive research algorithm. The new measurements can disagree with the expected path; keep that outcome and stop without replacing cases or rules.

## Fixed task and external rule

Use the repository-pinned UCI Bike Sharing rows, target `cnt`, and supplied preprocessing/model definitions from `rsi/tools/lab.py`. Train on 2011 and select on January–June 2012. Do not fit or score July–December final rows. Observed weather makes this a retrospective prediction task, not a day-ahead forecast. Use seed 17, training-only preprocessing, nonnegative predictions, and MAE.

Each comparison refits the parent and proposed task skill from scratch. Save training and selection predictions, row identities, targets, metrics, exact skills, source hashes, command statuses, and costs. Recompute metrics and validate row/target alignment before deciding. Both improver arms receive identical model/feature candidates and fit allowances; check their matched prediction bytes.

The external rule chooses the improver whose retained task skill has strictly lower selection MAE. Ties keep the active parent improver. This is a fixed development rule, using the same selection partition as the revised internal rule. It is deliberately transparent but is not an independent effectiveness evaluation. No final generalization claim follows from it. The separate 09.05 experiment already illustrates a distinct final-scoring stage; do not reopen it here.

## Fixed-improver baseline: lab 09.02

Start from a task skill using a linear model with calendar fields. The versioned improver's fixed proposal schedule changes the family to a tree in generation 1, then adds weather fields to the retained family in generation 2. Its promotion rule accepts only a strictly lower training MAE. The deliberately weak training-based rule remains byte-identical across both generations.

Run at most two fits per generation: parent and child. Keep accepted and rejected task skills. Four fits maximum, no replacements. Report selection MAE even though this baseline's internal promotion rule uses training MAE. Generation numbers alone do not make this procedure recursive.

For the additional-change diagnostic, use an actually rejected child if one exists. Otherwise, copy a recorded generation into a clearly labelled fixture, change its verdict to rejection, and deliberately set its proposed child as active. Check that this ancestry contradicts the fixture's verdict. Do not represent the mutated verdict as an experimental outcome. This diagnostic performs no fits and does not alter the real active state.

## Revised-improver lineage: lab 09.06

Start from the same linear/calendar task skill and training-based improver v0. Allow two generations, four fits per generation (two arms × parent/child), eight fits total.

1. Before generation 1, derive candidate v1 by changing only the internal promotion partition from training to selection. Preserve the proposal schedule. This author-guided edit is motivated by the previously observed overfitting failure. Save the proposal and stop the process before comparison. The active pointer must still name v0. Resume in another process, run both arms, apply the fixed external rule, and checkpoint the retained improver and its retained task skill.
2. In generation 2, read the exact accepted improver from the prior checkpoint. It governs the next task-skill proposal and its promotion decision. Derive another candidate from that active version by requiring at least 15% relative gain on its named internal metric. This tests an over-conservative margin intended to resist small selection fluctuations. Stop after saving the proposal, verify that active state has not changed, then resume and compare both arms under the same external rule. An inferior or tied improver proposal stays archived but inactive.

A constrained interpreter executes the explicitly supported Markdown instructions. The author designs the schedule and revisions; no autonomous invention or general Markdown interpretation is claimed. The unchanged outer controller selects among improvers. This is an author-guided inherited-procedure experiment, not a demonstration that the improver autonomously rewrites every level of its own implementation.

## Budgets, interruption, and checks

Maximum: twelve real fits across the separate baseline and revised paths. Reserve each attempt in a persistent ledger before launching a fit. Failures consume attempts and stop execution for diagnosis. Each fit runs sequentially in a separate Python child process with a 60-second timeout. There is no automatic retry or budget extension. Save process wall time separately from fit time; inference and authoring costs are unknown.

Use separate prepare, propose, compare, and audit commands. The planned interruption is a clean process exit after writing a proposal, before promotion. It does not test forced mid-fit termination or a live-lock recovery. Resume must check the accepted ancestry, source identity, and consumed resources. After generation 2, reject an additional advance request before fitting. Inspect a deliberately invalid active-pointer fixture without changing real state.

Learner predictions, quiz answers, and teach-back remain unattempted. Record this as a same-author-context run; fresh Python processes do not create independent coding-agent contexts. Keep all generated source, fixtures, successful and failed commands, predictions, decisions, costs, and progress snapshots. Report actual outcomes even if no improver is promoted. Two generations cannot establish sustained acceleration.
