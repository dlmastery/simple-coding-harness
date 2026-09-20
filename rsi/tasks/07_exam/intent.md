---
name: exam
index: 7
title: "Exam: a held-out synthetic table the pack never wrote to"
role: exam
target: target
metric: roc_auc
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: synthetic
  n_samples: 600
  n_features: 10
  n_informative: 5
  n_redundant: 2
  n_clusters_per_class: 2
  class_sep: 0.9
  flip_y: 0.05
  weights: [0.75, 0.25]
  random_state: 7
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---
# Intent: Exam: a held-out synthetic table the pack never wrote to

## What to improve
ROC-AUC on a third seeded table, run with the memory frozen: the pack as the curriculum left it against the same pack with the memory off, over five seeds of the split.

## Why
The paper's evidence bar: effective recursion needs a stronger successor under a comparable budget and an independent evaluation. This problem is never learned from - `write_card` refuses on it - so a win here is transfer, not memorisation.

## What counts as success
The memory arm beats the control arm on at least 3 of 5 seeds (a higher test score, or the same score with fewer wasted fits), the pack's `memory.json` is byte-identical before and after, and the report names every applicable card that did not transfer.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it. Nothing is written to any pack during the exam.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal. On this table: 600 rows, 10 features, 2 classes, imbalance near 0.25, categorical 0.
