# Capstone 11.02: declared two-generation comparison

Declared before this experiment's fits. This is an author walkthrough, not a learner assessment or an autonomous discovery claim. It extends the sealed 11.01 white-wine regression package in a new sibling workspace. The earlier two baseline fits belong to 11.01; they remain visible and do not enter this eight-fit experiment.

## Question and changed object

Can a revised internal selection instruction govern a later model-research round, and what result does that round retain? The task skill specifies a model recipe. The improver selects which task-skill proposal to retain. The author proposes one revision to this improver after inspecting generation-one development evidence. The controller, models, external comparison and evaluation remain fixed. This demonstrates an author-guided revision of an improvement procedure, not a system that invents or edits its own controller.

Use the original white-wine inputs and ordinal quality target, original grouped split, all eleven permitted inputs, and MAE. Keep preprocessing within training data. The dataset, partitions and model implementations are inherited from 11.01. Public local files are accessible to the author; they are not technically secret. Do not inspect evaluation predictions or scores before the terminal phase.

## Allocation and decision rules

Eight actual CPU fits total, no parallel fits, two generations maximum:

1. Generation one: ridge and unrestricted tree, two fits. I0 ranks by training MAE. Ties retain the earlier candidate. Save the selected task skill S1 and the full decision trace.
2. Inspect both training and selection MAE. If the training winner is worse on selection, propose one change: I1 ranks by selection MAE. Otherwise report the missing motivating failure and stop; do not spend the remaining fits searching for it.
3. Generation two: copy S1 byte for byte into two arms. Each arm fits the incumbent model first, then the other models from the fixed menu ridge, tree, forest in that order. Three fits per arm, identical seeds, inputs and model settings. I0 and I1 each govern the three successive retention decisions through the frozen selector. I1 is a candidate under trial, not already accepted.
4. The unchanged external gate compares selection MAE of each arm's retained task recipe. Retain I1 only if its result is at least 1e-12 lower. Otherwise retain I0. Freeze both arm choices and this decision before final evaluation. There is no permitted rewrite of this rule.
5. The terminal evaluator uses the already fitted saved models on the original evaluation partition. It makes no fit and no new promotion decision. Report original and revised arm scores, including disagreement with selection. Close the experiment. No third generation or post-evaluation search is permitted.

The fixed menu and known weak I0 are teaching controls. The same development task is reused; this is not a fresh-task comparison or statistical evidence of a generally better improver. No retained post-acceptance round is allocated. Later use is the candidate's generation-two trial, which must be labelled as such.

## Execution and checks

Version the original package before fits. Add saved fitted models and training predictions. Freeze hashes of the external protocol, package, controller and I0; freeze I1 separately after its proposal, before comparison. Record which exact instruction the selector reads, all comparisons and all rejected model recipes. Save pre-final artifact hashes. Recompute selection and training MAE from predictions and verify row roles, original targets and model predictions. The terminal evaluator checks frozen artifact identities before opening evaluation targets.

Record each command, exit status, wall time, attempt, fit time, failed request and rejection. Use a 60-second timeout per command. A failed fit remains charged. Stop on a changed contract or identity. Retrying an interrupted fit requires an unused attempt; this protocol does not allocate spare fits. A final-phase interruption leaves the final lock in place for diagnosis; do not silently reopen it.

Test refusal of an extra fit after the eight attempts, and a repeated final evaluation after closure. These requests must perform zero fits. Preserve any unexpected result. Author/inference time and billing are unavailable; do not claim total efficiency. Learner prediction, quiz and teach-back are unattempted.

## Audit and handoff

Write lineage, matched outcomes, costs, claim audit, progress and an evidence-removal exercise. Use an explicitly labelled author review if no peer is available. Removing the inherited-use trace should remove direct evidence for the selection actions while leaving endpoint files; explain what can and cannot be reconstructed. Preserve the complete original pack. Do not fabricate peer feedback.

No new illustration is required: retain the existing 11.02 concept figure and explain how its candidate trial, external decision and later-use boundary map to this run. Archive generated source, readable skills, commands, predictions, fitted models, hashes and failures; exclude only environment caches and record exclusions. Check publication links and raw Git blob identity, then commit and push the authorized branch.
