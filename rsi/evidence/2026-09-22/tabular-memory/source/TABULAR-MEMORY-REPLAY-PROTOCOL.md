# Retain checked development experience before task transfer

Declared after the 96 development attempts, before memory compilation or
replay selection. No more development models may be fitted. This phase uses
only the six declared development tasks and their train/selection records.
No reserved-task file or final prediction is required.

Verify the three evidence archives and independent check results. Keep all
96 attempts, with candidate generation and failure status. The actor writes
the interpretation after those checks; passing a score check does not certify
the actor's explanation. Store persistent experience separately from current
run state. Later comparisons freeze this experience store.

## An executable retrieval rule

Within task kind, rank the 16 candidates by observed normalized selection
loss for each development task. Failures rank last. Do not mix classification
accuracy with regression MAE. Combine these ranks using peer weights.

Each task's training-only profile contains: twice categorical-input fraction;
log1p(feature count)/log(66); half log1p(training rows)/log(2401); and twice
the fraction of zero targets for regression (zero for classification).
Euclidean distance defines proximity. Local peer weights are proportional
to 1/(0.1 + distance), normalized to sum to one. Blend equal peer weights
with local weights using alpha in {0, 0.5, 1}. Use candidate-name order for
equal weighted ranks. No task ID, name or target unit is an input to retrieval.

## Replay selection

Leave one development task out of the memory used for its replay. Each fold
therefore has only two same-kind peers. Use four common probes first:
classification linear/Extra Trees/RBF C=1/histogram boosting; regression
median/linear/random forest/RBF C=1. Fill the remaining four slots from the
weighted ranking, excluding already chosen candidates. Reveal each recorded
outcome only after choosing it. An unrecorded candidate must refuse replay.

Three weights by six tasks by eight slots give exactly 144 lookups and zero
new fits. Choose the weight with smallest mean normalized best selection
loss; ties favor smaller alpha. Record all choices, peer identities and
revealed outcomes. Independently check the replay and selection before use.

The weight itself is selected on development outcomes, so leave-one-task-out
replay is still development, not the final method comparison. It does not
estimate generalization across an industry task distribution. This finite
recorded-candidate replay supplements the earlier actual discovery-tree
study; it does not reproduce the full Dream-RSI algorithm. The later study
must compare actual fits under equal budgets and keep held-out scoring fixed.
