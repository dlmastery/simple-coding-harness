---
name: hgb-for-imbalanced-multiclass
when: [imbalanced, multiclass]
then: model=hgb
validated: true
horizon: 1
---
On digits (10 classes, rarest 0.097) hgb was net +12 in model comparisons, rf net +4 and logreg net -16.
