---
name: hgb-for-small
when: [small]
then: model=hgb
validated: true
horizon: 1
---
On breast_cancer (569 rows, small) hgb won all 16 model comparisons against logreg and rf, which each lost 8.
