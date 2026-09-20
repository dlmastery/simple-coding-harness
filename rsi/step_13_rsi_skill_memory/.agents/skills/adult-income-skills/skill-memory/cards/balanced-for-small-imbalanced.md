---
name: balanced-for-small-imbalanced
when: [small, imbalanced]
then: class_weight=balanced
validated: true
horizon: 1
---
On synthetic table B (450 rows, 15 percent positives) class_weight=balanced won all 11 comparisons against none in the rf family (0.7685 against 0.6888 at depth 16), the only field that moved the score.
