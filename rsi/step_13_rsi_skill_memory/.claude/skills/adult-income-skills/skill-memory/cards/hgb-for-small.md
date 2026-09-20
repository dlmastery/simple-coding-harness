---
name: hgb-for-small
when: [small]
then: model=rf
validated: true
horizon: 2
---
On synthetic table A (800 rows, one cluster per class) rf won both probe comparisons (0.9378 against hgb 0.9169 and logreg 0.8546), overturning the hgb preference this card carried from the breast cancer table.
