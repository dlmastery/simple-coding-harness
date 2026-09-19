---
name: synth_shift_b
index: 6
title: Synthetic shifted table B (three clusters per class, imbalanced, small)
role: curriculum
target: target
metric: roc_auc
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: synthetic
  n_samples: 450
  n_features: 8
  n_informative: 4
  n_redundant: 0
  n_clusters_per_class: 3
  class_sep: 0.8
  flip_y: 0.03
  weights: [0.85, 0.15]
  random_state: 6
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---
# Intent: Synthetic shifted table B (three clusters per class, imbalanced, small)

## What to improve
ROC-AUC on a seeded `make_classification` table with three clusters per class, 15 % positives and 450 rows.

## Why
The superstition test, part two: the same columns, now trees win again and the class is rare - the `class_weight` card must apply and the `model` card learned on problem 5 must be demoted, not obeyed.

## What counts as success
A higher best validation score, or the same score reached with fewer wasted fits, than the control arm (`memory: off`) at the same budget of 24 fits and the same seed - and the locked test split scored exactly once, after FREEZE. A run that peeks at the test split proves nothing.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal. On this table: 450 rows, 8 features, 2 classes, imbalance near 0.15, categorical 0.
