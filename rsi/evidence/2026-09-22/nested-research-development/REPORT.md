# Checked development comparison

Balanced accuracy is better when higher; MAE is better when lower.

| Task | Metric | parent | i0 | i1 |
|---|---|---:|---:|---:|
| 6: letter | balanced_accuracy | 0.894004 | 0.894004 | 0.894004 |
| 23: cmc | balanced_accuracy | 0.533812 | 0.533812 | 0.538851 |
| 31: credit-g | balanced_accuracy | 0.706604 | 0.706604 | 0.714416 |
| 361235: airfoil_self_noise | MAE | 1.197255 | 1.197255 | 1.197255 |
| 361237: concrete_compressive_strength | MAE | 3.111243 | 3.111243 | 3.111243 |
| 361247: naval_propulsion_plant | MAE | 0.000684 | 0.000684 | 0.000684 |

Normalized paired loss differences below are better when negative.

| Comparison | Mean change | 95% task-bootstrap interval | Better / tied / worse |
|---|---:|---|---|
| i0 minus parent | +0.000000 | [+0.000000, +0.000000] | 0 / 6 / 0 |
| i1 minus parent | -0.002142 | [-0.003906, +0.000000] | 2 / 4 / 0 |

Six public tasks, one model seed, 10,000 task bootstrap draws stratified by kind.
Intervals are exploratory and unadjusted for multiple comparisons. A source
rewrite is not proof of changed behavior or improved quality.

This phase executed 216 search attempts and 18 scoring refits.
Recorded worker-process time: 485.393 seconds.
This excludes coding-agent inference and cannot establish total research-cost savings.

Inspect BEHAVIOR-CHANGES.csv for actual differing constructed models and COSTS.csv
for all researcher costs. Losing searches remain charged.

These tasks were already exposed in prior work. Their former final rows are
development evaluation here. Do not describe these as fresh transfer results.
The fixed promotion rule is evaluated separately in VERDICTS.csv.
