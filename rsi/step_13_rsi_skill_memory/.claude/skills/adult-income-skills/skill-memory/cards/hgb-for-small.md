---
name: hgb-for-small
when: [small]
then: model=hgb
validated: true
horizon: 1
---
On the breast cancer table (569 rows, all numeric) hgb won all 16 model comparisons at the middle hyper (0.9954 against logreg 0.9937 and rf 0.9917), regardless of scale, encode or class weight.
