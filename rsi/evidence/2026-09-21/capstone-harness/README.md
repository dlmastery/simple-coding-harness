# A new regression brief becomes a runnable harness

Author walkthrough for capstone 11.01, executed 21 September 2026. The task predicts original white-wine quality from laboratory measurements. It differs from the earlier red-wine classification exercise in population, target, and metric.

Start with the generated [package README](package/README.md), [task contract](package/TASK.md), and [data card](package/DATA-CARD.md). The [protocol](PROTOCOL.md) allocated two actual CPU fits. Both one-attempt experiments are now exhausted.

| Check | Observed result |
|---|---|
| Data and split | 4,898 rows; no missing values; 3,961 input groups. All 937 repeated-input extra rows remain within their group. Train/selection/evaluation: 2,908/998/992 rows. |
| Original median baseline | Selection MAE **0.655310621242485**, independently recomputed from pinned targets and saved predictions |
| Fresh exported environment | Same MAE and byte-identical predictions; [export check](EXPORT-CHECK.md) |
| Invalid feature, metric, and extra-fit requests | Each returned exit 2 before a new fit |
| Altered output checks | Seven intended rejections, including rehashed wrong rows/targets and non-finite predictions |
| Failed-attempt accounting | One labelled no-training stub remained charged and its retry was refused |

Inspect [the baseline predictions](baseline-run/baseline/predictions.csv), [metrics](baseline-run/baseline/metrics.csv), [original attempts](baseline-run/ATTEMPTS.csv), [exported attempts](export/experiment/ATTEMPTS.csv), and [guard results](guard-cases/CHECKS.csv). The guard folders retain their deliberately bad files. They must not be used as successful examples.

The [handoff](HANDOFF.md) tells the next agent how to use the frozen package. The [larger-job plan](package/SCALE-PLAN.md) preserves candidate, data, evaluator, and cost interfaces but remains generated-only. No cluster backend was chosen or run.

Three setup failures remain in the archive: missing pip in the original environment, a metadata-command quoting error, and a sixty-second installation timeout. None caused a duplicate fit. The installation retry completed and pip check passed. Exact commands and statuses are in the COMMANDS CSV files and commands directory; [the author note](LAB-NOTE.md) explains recovery. [Costs](COST.md) distinguish fit time, setup, simulated attempts, and unknown inference costs.

All 138 original manifest files were copied and hash-verified. Original and revised author drivers are retained. Dependency installations and Python bytecode are excluded; installation logs and exact versions are preserved. This README was added after sealing.

This is a real generated-package and clean-environment check on one Windows host. It does not establish a better predictor, an improved builder, autonomous RSI, independent learner reproduction, another native coding-agent integration, or cluster support. Learner predictions and quizzes remain unattempted. Final evaluation was not used.
