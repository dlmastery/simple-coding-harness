---
name: heldout_2
index: 2
title: "Held-out benchmark 2 (three clusters per class, another seed)"
role: pool
target: target
metric: roc_auc
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: synthetic
  n_samples: 500
  n_features: 8
  n_informative: 4
  n_redundant: 1
  n_clusters_per_class: 3
  class_sep: 0.6
  flip_y: 0.05
  weights: [0.7, 0.3]
  random_state: 202
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---
# Intent: Held-out benchmark 2 (three clusters per class, another seed)

## What to improve
ROC-AUC on the second held-out table.

## Why
Two problems average the noise of one.

## What counts as success
A higher best validation score, or the same score reached with fewer wasted fits, than the control arm (`memory: off`) at the same budget of 24 fits and the same seed - and the locked test split scored exactly once, after FREEZE. A run that peeks at the test split proves nothing.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal. On this table: 500 rows, 8 features, 2 classes, imbalance near 0.3, categorical 0.
