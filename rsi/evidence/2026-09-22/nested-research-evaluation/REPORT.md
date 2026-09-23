# Checked evaluation comparison

Balanced accuracy is better when higher; MAE is better when lower.

| Task | Metric | fixed | random | parent | i0 | i1 |
|---|---|---:|---:|---:|---:|---:|
| 43: spambase | balanced_accuracy | 0.946478 | 0.948947 | 0.944437 | 0.944437 | 0.948947 |
| 45: splice | balanced_accuracy | 0.962628 | 0.962628 | 0.962628 | 0.962628 | 0.962628 |
| 2074: satimage | balanced_accuracy | 0.850292 | 0.844256 | 0.844385 | 0.844385 | 0.846324 |
| 361241: physiochemical_protein | MAE | 3.297292 | 3.297292 | 3.297292 | 3.297292 | 3.297292 |
| 361251: grid_stability | MAE | 0.006570 | 0.006417 | 0.006469 | 0.006469 | 0.006469 |
| 361260: miami_housing | MAE | 52375.824170 | 49038.580664 | 49038.580664 | 49038.580664 | 50276.967635 |

Normalized paired loss differences below are better when negative.

| Comparison | Mean change | 95% task-bootstrap interval | Better / tied / worse |
|---|---:|---|---|
| i1 minus i0 | +0.000120 | [-0.001826, +0.002390] | 2 / 3 / 1 |
| i1 minus parent | +0.000120 | [-0.001826, +0.002390] | 2 / 3 / 1 |
| i1 minus fixed | -0.002307 | [-0.005816, +0.000790] | 3 / 2 / 1 |
| i1 minus random | +0.001125 | [-0.000414, +0.003240] | 1 / 3 / 2 |

Six public tasks, one model seed, 10,000 task bootstrap draws stratified by kind.
Intervals are exploratory and unadjusted for multiple comparisons. A source
rewrite is not proof of changed behavior or improved quality.

This phase executed 360 search attempts and 30 scoring refits.
Recorded worker-process time: 1048.070 seconds.
This excludes coding-agent inference and cannot establish total research-cost savings.

Inspect BEHAVIOR-CHANGES.csv for actual differing constructed models and COSTS.csv
for all researcher costs. Losing searches remain charged.

The primary comparison is I1's generated researcher versus I0's generated
researcher. Fixed and random controls remain visible. This is a bounded
programmatic adaptation, not a frontier-system reproduction or weight update.
Add the separate 234-attempt development phase when reporting the full study cost.
