---
name: hgb-for-categorical-imbalanced
when: [categorical, imbalanced]
then: model=hgb
validated: true
horizon: 1
---
On adult_income (categorical, imbalanced) hgb won 7 model comparisons and lost none, ahead of logreg (3 wins, 4 losses) and rf (0 wins, 6 losses).
