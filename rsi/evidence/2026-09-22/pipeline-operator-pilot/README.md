# Do richer pipeline operators create useful headroom?

**Only partly in this task set.** We added pairwise interactions and numeric quantile transformations to six model families. Of 72 new attempts, 71 completed and one hit its 60-second timeout. The expanded reference improved on the interaction-classification control, but did not improve the previous best on the other five tasks. This remains a development experiment, not an RSI effectiveness result.

The [protocol](../../../../how-did-i-generate-it/rsi/validation/PIPELINE-OPERATOR-PILOT-PROTOCOL.md) and [implementation](../../../../how-did-i-generate-it/rsi/scripts/pipeline_operator_pilot.py) were pushed at `6bbe1d5` before fitting. All data rows and original predictions came from the [first pilot](../headroom-pilot/README.md). No final evaluation was performed. There are 60 total candidate configurations per task: 48 earlier fits plus 12 new ones.

## Measured result

Both predeclared eight-attempt controls produce the same retained result here. The strengthened control includes six raw defaults plus linear pairwise and quantile pipelines, so those simple extensions are available to a sound baseline too.

| Task | Eight-attempt control | Best of 60 candidates | Interpretation |
|---|---:|---:|---|
| Bike demand, MAE | 87.124258 | 87.124258 | No additional selection headroom |
| Red wine quality, MAE | 0.486231 | 0.486231 | No additional selection headroom |
| Breast cancer, balanced accuracy | 96.598108% | 96.598108% | No additional selection headroom |
| Digits, balanced accuracy | 97.767668% | 98.192053% | Existing small hyperparameter gap; new operators did not improve the reference |
| Friedman, MAE | 1.142092 | 1.110106 | Existing small hyperparameter gap; new operators did not improve the reference |
| Interaction classification, balanced accuracy | 90.941328% | 92.914249% | Pairwise features plus extra trees add a useful candidate |

On the interaction task, extra trees with pairwise features improve selection balanced accuracy by **1.972921 percentage points** over the eight-attempt control. The prior 48-candidate reference scored 91.911670%, so the new operator improves that reference by **1.002579 percentage points**. These are selection comparisons, with no independent uncertainty estimate or final-task confirmation. They do not prove that an agent learned to find this candidate efficiently.

## Why cost changes the experiment

The digits random forest with pairwise features took 46.48 seconds of subprocess time and performed worse than its raw counterpart. Pairwise histogram boosting on digits timed out at 60.04 seconds. That attempt remains in [the result table](extension-results.csv), with no invented score or refunded budget.

Recorded successful fitting took 128.564 seconds and successful prediction took 2.748 seconds. These totals omit the unknown portion of the timed-out process spent fitting. **Total charged subprocess time was 313.987 seconds**, including the timeout and interpreter startup. Agent inference and full orchestration costs are unknown. A candidate-count budget alone cannot support a total-compute efficiency claim.

The retained findings support two next steps: use a controlled family of nonlinear interaction tasks to test whether a learned procedure can exploit real headroom, and retain real-data checks where no gain may occur. Keep the saturated tasks as foundations and negative controls. The advanced run must include actual branching, retained policy changes, fresh task instances and cost accounting; another static leaderboard is insufficient.

## Verification and provenance

The independent [checker](../../../../how-did-i-generate-it/rsi/scripts/check_pipeline_operators.py) passes **583 checks**. It recomputes MAE and balanced accuracy from predictions, checks row IDs and nonnegative count predictions, preserves failed-attempt costs, verifies source identities and reconstructs both fixed controls. The first invocation rejected a `4.44e-16` CSV round-trip difference in one inherited score because it demanded exact floating-point equality. The [failed-check record](CHECKER-FIRST-FAILURE.md) and [original checker](checker-before-float-fix.py) are preserved. The corrected checker uses exact task/candidate/status identities and a `1e-12` numeric tolerance. No fit or prediction changed.

- [New attempts](extension-results.csv), [combined reference](combined-results.csv) and [control comparisons](headroom.csv)
- [Prediction checks](CHECKS.csv), [source identities](SOURCE-IDENTITIES.csv) and [archive identities](ARCHIVE-MANIFEST.csv)
- [Timeout record](attempts/digits/boost-0-pairwise/result.csv)
- [Actual command sequence](COMMANDS.md)

The archive preserves 378 source and evidence files with verified copied bytes. The first pilot's 288 fits are referenced, not repeated. Across both pilots there were **360 admitted attempts: 359 completed fits and one timeout**. Student prediction, teach-back and independent-agent replication remain untested. All seven repaired method comparisons remain pending; these pilots establish their experimental starting point.
