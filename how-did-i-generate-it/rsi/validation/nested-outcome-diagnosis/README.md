# Why some final results still tie

This is a read-only analysis of the completed study. It uses 39 archived
inputs, verifies their manifest identities and passes 133 checks. It performs
zero fits, changes no procedure and makes no new promotion decision.

The [full table](OUTCOMES.csv) separates the experiments a researcher tried,
the constructor it selected and the predictions it finally produced. A new
source file can change the first without changing the last.

## I1 changes the search, but three prediction vectors still tie

All procedures begin with the same eight conventional probes. I1 changes the
constructed model at each of the remaining four search positions on every
task. The selected outcome then depends on what those searches discover.

| Task | I1 versus the parent | Changed final predictions | What explains the result |
|---|---|---:|---|
| Spam | Better balanced accuracy | 15 of 800 | Different selected boosting settings |
| DNA splice | Tied balanced accuracy | 0 of 622 | Different selected SVM settings, identical class predictions |
| Satellite pixels | Better balanced accuracy | 24 of 800 | Different selected boosting settings |
| Protein | Tied MAE | 0 of 800 | Same selected five-neighbor constructor |
| Grid stability | Tied MAE | 0 of 800 | Same selected refined SVM constructor |
| Miami housing | Worse MAE | 800 of 800 | Different selected model family |

All three tied I1 outcomes have identical prediction vectors. They are not
small gains hidden by rounding, and they are not different predictions whose
aggregate scores happen to cancel. DNA shows another useful distinction:
different constructors can still make the same class decisions on these rows.
This does not imply identical probabilities or behavior on all possible inputs.

I0 changes three search positions on spam and satellite and none on the
other four tasks. It ends with the same constructor and predictions as the
parent on all six tasks. Its six ties therefore have a concrete explanation.

## Selection and final rankings can disagree

I1 keeps an earlier shared probe on spam, DNA and protein. It selects a later
candidate on the other three tasks. The different search therefore does not
always displace the common starting portfolio.

On spam and satellite, I1's chosen model has worse selection loss than the
parent's chosen model but better final loss. On housing, the direction
reverses: I1 reduces normalized selection loss by 0.010109, then increases
normalized final loss by 0.007169. These observed rank reversals explain why
selection gains cannot stand in for final gains. They do not identify whether
sampling variation, distribution differences or a particular search choice
caused the reversal.

These findings do not establish that classification or regression is the
wrong task class. They show that this particular twelve-fit procedure has
real behavioral changes with limited and inconsistent effects on retained
predictions. The study does not measure the best attainable score on each
dataset. A larger search space, a different budget or more tasks would define
a new comparison, and would still need to beat strong controls.

The final tasks are now exposed. This diagnostic cannot be used to tune a
replacement and then call the same final results an untouched evaluation.

## Inspect the calculation

- [OUTCOMES.csv](OUTCOMES.csv) gives all twelve parent/child comparisons.
- [INPUTS.csv](INPUTS.csv) records every original input's size and SHA-256.
- [CHECKS.csv](CHECKS.csv) records the 133 checks.
- [Executed analysis source](diagnose_nested_outcomes.py) uses the standard
  library to recompute balanced accuracy or MAE, match rows and truths,
  inspect selected constructor identities and count changed predictions.
- [The full study](../../../../rsi/evidence/2026-09-22/nested-research-evaluation/README.md)
  retains all controls, uncertainty and costs. This diagnostic adds no new
  efficacy claim or model attempts.
