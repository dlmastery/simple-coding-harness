---
name: hgb-for-imbalanced-multiclass
when: [imbalanced, multiclass]
then: model=hgb
validated: true
horizon: 1
---
On digits (10 classes, rarest class 0.097) hgb won 14 of its 16 model comparisons at the middle hyper, losing only to scaled rf without class weight (0.999 both), and logreg lost all 16.
