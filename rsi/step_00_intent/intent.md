---
name: adult_income
index: 1
title: "Adult Census Income (> 50k)"
role: curriculum
target: target
metric: roc_auc
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: csv
  path: data/adult_sample.csv
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---
# Intent: Adult Census Income (> 50k)

## What to improve
ROC-AUC of a classifier that predicts whether income is above 50K on the bundled 6,000-row Adult sample, under a budget of 24 fits per arm, searching the shared recipe space (model in logreg / rf / hgb, one hyper-parameter, scale, encode, class weight).

## Why
Mixed numeric and categorical columns and a class imbalance: the first lessons a pack can learn are encoding and class weight, and they are the first cards the verifier writes.

## What counts as success
A higher best validation score, or the same score reached with fewer wasted fits, than the control arm (`memory: off`) at the same budget of 24 fits and the same seed - and the locked test split scored exactly once, after FREEZE. A run that peeks at the test split proves nothing.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal. On this table: about 6,000 rows, 14 features, 2 classes, imbalance near 0.24, categorical 1.
