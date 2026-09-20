---
name: hgb-for-categorical-imbalanced
when: [categorical, imbalanced]
then: model=hgb
validated: true
horizon: 1
---
On the adult income table (categorical, imbalanced) hgb beat logreg and rf in both probe comparisons at the middle hyper (0.9177 vs 0.9114 and 0.9054) and no other model came within 0.005 of it.
