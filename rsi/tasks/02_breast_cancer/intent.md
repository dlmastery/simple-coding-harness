---
name: breast_cancer
index: 2
title: Breast cancer (malignant)
role: curriculum
target: target
metric: roc_auc
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: sklearn
  name: breast_cancer
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---
# Intent: Breast cancer (malignant)

## What to improve
ROC-AUC on `sklearn.datasets.load_breast_cancer` (569 rows, 30 numeric features), the same recipe space and budget.

## Why
All numeric and small: does `scale before logreg` transfer from problem 1, and does the encoding card - which cannot apply here - stay silent?

## What counts as success
A higher best validation score, or the same score reached with fewer wasted fits, than the control arm (`memory: off`) at the same budget of 24 fits and the same seed - and the locked test split scored exactly once, after FREEZE. A run that peeks at the test split proves nothing.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal. On this table: 569 rows, 30 features, 2 classes, imbalance near 0.37, categorical 0.
