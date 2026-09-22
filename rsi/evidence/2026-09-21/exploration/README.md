# Two broad probes, then one focused question

Author walkthrough for lab 10.03, executed on 21 September 2026. Both driver phases exited 0. Three fits used one frozen experiment, seed 17, the same selection partition, and MAE. All three result checks passed.

| Attempt | Question | Recipe | Selection MAE |
|---|---|---|---:|
| 1 | What does a prediction without input variation miss? | constant/calendar, training median | 159.947912 |
| 2 | Does calendar structure explain useful variation? | linear/calendar | 109.807668 |
| 3 | Does the permitted weather group help this linear recipe? | linear/all | 99.175924 |

The [protocol](PROTOCOL.md) preceded the fits. After the first two, the driver stopped. The author inspected [hourly errors](hour-errors.csv) and [weather-group errors](weather-errors.csv), then saved the [decision](DECISION.md) before fit three. Its [hash](DECISION-FREEZE.md) stayed fixed.

For weather groups with at least 50 rows, the range of mean signed residuals was 123.443650 rentals per hour. That exceeded the declared threshold of 10 and selected the feature-group probe. The two-row extreme-weather group was excluded from this choice rule. These subgroup differences may be confounded; they are a reason to test an intervention, not evidence that weather caused the error.

Adding the weather group reduced selection MAE by 10.631744. This is a local predictive result for a fixed recipe and split. It does not establish forecast-time availability, feature-by-feature contributions, generalization beyond the task, or an improved improver. No final evaluation was performed.

The [duplicate comparison](DUPLICATE-COMPARISON.md) inspects the earlier [02.06 arm-A repeat](../../2026-09-20/loops-and-systems/02-06/arm-a/trials.csv). Its saved predictions are byte-identical. This reused comparison explains what a deterministic repeat can check without adding a fourth fit. It is not a newly randomized third-attempt duplicate arm.

Fit time totalled 0.233835 seconds. [Subprocess wall times](COMMANDS.csv) include startup and checking; agent inference, proposal, and review costs remain unknown. Every command's exit and output is retained in `commands/`; the complete [fit report](EXPLORATION-REPORT.md) gives individual costs. The author had seen this public dataset and prior results. No task-memory file was loaded, but this was not a fresh agent context. Learner predictions, teach-back, and quizzes were unattempted.

The maintained [two-stage driver](../../../../how-did-i-generate-it/rsi/scripts/run-exploration.py) preserves existing workspaces and refuses a third fit without a saved decision. The original manifest covers the run files other than itself; this README was added after archival. All copied run files were hash-verified against the workspace.
