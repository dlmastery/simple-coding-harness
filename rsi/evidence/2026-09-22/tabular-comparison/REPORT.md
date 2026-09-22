# Matched procedure comparison on six reserved tasks

All procedures received the same four starting probes and eight search attempts. The source and choices were frozen before final scoring. Lower normalized loss is better; the native classification metric is balanced accuracy and the regression metric is MAE.

## Final task scores

| Task | Metric | Fixed | Random | Memory | Parent | Harness | Updater |
|---|---|---:|---:|---:|---:|---:|---:|
| 6: letter | balanced_accuracy | 0.894004 | 0.877528 | 0.894004 | 0.880007 | 0.880007 | 0.880007 |
| 23: cmc | balanced_accuracy | 0.514592 | 0.536937 | 0.548682 | 0.539631 | 0.514592 | 0.548682 |
| 31: credit-g | balanced_accuracy | 0.714416 | 0.714416 | 0.714416 | 0.702954 | 0.709740 | 0.702954 |
| 361235: airfoil_self_noise | MAE | 1.197255 | 1.451440 | 1.451440 | 1.451440 | 1.451440 | 1.451440 |
| 361237: concrete_compressive_strength | MAE | 3.111243 | 4.107391 | 3.738154 | 4.107391 | 4.107391 | 3.738154 |
| 361247: naval_propulsion_plant | MAE | 0.000684 | 0.000996 | 0.000996 | 0.000997 | 0.000997 | 0.000997 |

## Prespecified comparisons

Differences below are child minus parent normalized final loss. Negative favors the child. Intervals use a stratified task bootstrap and are exploratory with only three tasks of each kind. They do not correct for multiple comparisons or establish general superiority.

| Contrast | Mean difference | Descriptive 95% interval | Better / tied / worse |
|---|---:|---|---|
| harness-minus-parent | +0.003042 | [-0.003393, +0.012519] | 1 / 4 / 1 |
| updater-minus-harness | -0.009343 | [-0.021838, +0.002262] | 2 / 3 / 1 |
| memory-minus-fixed | +0.014333 | [+0.002969, +0.024115] | 1 / 2 / 3 |
| memory-minus-random | -0.009496 | [-0.019082, -0.001958] | 3 / 3 / 0 |

## Actual work and scope

Search: 288 admitted attempts, 0 failures or invalid outcomes, 709.242 worker-process seconds. Final scoring: 36 charged refits, 0 failures or invalid outcomes, 83.241 worker-process seconds.

Each procedure actually spent eight search fits per task. This study cannot claim fewer fits. The preceding 96 development fits, replay work and unmetered coding-agent inference are additional. Worker time excludes the complete research and orchestration cost.

The root coding agent authored the harness and updater revisions; a bounded program generated the inner proposals. Later skill use and source inheritance are observable. The study does not establish autonomous invention, post-promotion deployment, sustained acceleration or a reproduction of each named research system. The six public tasks are classroom adaptations.
