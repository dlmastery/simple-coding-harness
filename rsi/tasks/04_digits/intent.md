---
name: digits
index: 4
title: Digits (10 classes)
role: curriculum
target: target
metric: roc_auc_ovr_macro
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: sklearn
  name: digits
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---
# Intent: Digits (10 classes)

## What to improve
Macro one-vs-rest ROC-AUC on `sklearn.datasets.load_digits` (1,797 rows, 64 pixel features, 10 classes).

## Why
Image-like and 10 classes: the tree-depth and learning-rate cards learned on tables meet their counterexamples here.

## What counts as success
A higher best validation score, or the same score reached with fewer wasted fits, than the control arm (`memory: off`) at the same budget of 24 fits and the same seed - and the locked test split scored exactly once, after FREEZE. A run that peeks at the test split proves nothing.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal. On this table: 1,797 rows, 64 features, 10 classes, imbalance near 0.099, categorical 0.
