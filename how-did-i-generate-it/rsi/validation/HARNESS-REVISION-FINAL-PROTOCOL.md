# Evaluate a retained inner harness on new tasks

This protocol is declared before reading the six-task harness development
result. Execute it only if the already frozen development gate passes. A
failure retains the parent and the rejected proposal; it does not permit
changing the gate or retrying this comparison until it looks positive.

## Question and comparison

Does the retained child inner harness improve prediction on new instances
under the same search allowance? Compare the original broad-search harness
with the child builder and proposer in `rsi/experiments/harness-revision`.
Freeze their exact sources before generating any new evaluation task.
The coding agent authored the child using development evidence and knowledge
of the public signal grammar. The inner proposer remains deterministic.

Use seeds 9101–9112 from the unchanged generator in
`scripts/evaluate_discovery.py`. These twelve instances give two classification
and two regression cases per known signal family. Each has 1,200 training,
800 selection and 1,000 separate final rows. Final arrays stay outside every
search workspace. No selection or harness edit may use final results.

Run both arms on every task. Alternate which arm starts. Each receives
twelve admitted attempts, 120 worker-process seconds, at most 60 seconds per
worker, model seed 41 and one numerical thread. Run sequentially with temporary
idle-sleep prevention. Freeze all twenty-four selected candidate identities
before any final scoring. Refit each selection on its original training rows;
require reproduction of selection predictions before scoring final rows.

The search allocation is at most 288 attempts. The twenty-four separate scoring
refits are additional and must be reported. Preserve all failed attempts. Do
not silently retry a failed scoring process or exclude a bad method result.
An infrastructure interruption requires a documented decision before any
replacement generation; retain its full cost and history.

## Analysis and decision

Report balanced accuracy for classification and mean absolute error for
regression, every task, and actual search and scoring costs separately.
For the common loss scale, use twice the classification error in balanced
accuracy, and regression MAE divided by the final-row MAE of the training-median
predictor. Lower loss is better. Do not combine predictive and resource wins.

The primary contrast is mean child-minus-parent normalized final loss across
all twelve tasks. Use a paired task bootstrap with 10,000 samples, seed
20260923, and a percentile 95% interval. Also show task-kind means and counts
of lower, tied and higher loss, with tolerance 1e-10 for ties. Do not select
only the successful tasks for the reported comparison.

Call this comparison supportive of a predictive benefit only if the mean
loss change is negative, its interval is wholly below zero, and neither
task-kind mean worsens. Otherwise report an inconclusive or adverse result.
This is a small conditional synthetic study; its interval is not evidence
of broad real-world generalization. No further tuning uses these final tasks.

## Meaning and next step

A successful result supports this agent-authored harness revision under the
declared task distribution and budget. It is an AIDE-inspired outer revision,
not a reproduction of AIDE2, a demonstrated improvement of the updater,
ignition, sustained acceleration or net total research-cost savings. Agent
inference is unmetered. Development work remains additional.

Preserve sources, source hashes, data, actual ancestry, choices, predictions,
costs, checks and all outcomes in the authorized GitHub branch. Keep the
existing discovery-policy study separate. Later memory and meta-skill studies
must identify their own changed objects and controls.
