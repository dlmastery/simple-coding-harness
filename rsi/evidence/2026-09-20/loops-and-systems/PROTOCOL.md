# Loop, coordination, and repetition walkthrough

Declared on 20 September 2026, before this run. This author walkthrough covers labs 02.06, 05.02–05.05, and 08.01. It uses a new sibling workspace, the pinned teaching datasets, the current runtime, and the existing environment. The author has already seen several public baseline results. This is an execution check, not a blind study or a test with a learner.

## Fixed comparisons and budgets

| Lab | Main activity | Budget | Additional activity |
|---|---|---|---|
| 02.06 | Arm A repeats constant/calendar. Arm B starts with the same recipe and selects one model change from its hourly selection-error report. Both retain the lower selection MAE. Seed 17. | Four fits: two per arm. | Write an unequal-budget counterexample without additional fits. Do not claim the optional ten-fit extension ran. |
| 05.02 | Route bike regression to median/MAE and wine classification to majority/balanced accuracy. Check actual wine groups and class recalls. | Two baseline fits; one per task. | Reject an unknown task and a known task with no target type; no fits. |
| 05.03 | Build a bike context packet from its contract, current ledger, and data card. Compare a current note with a stale note. | Two context checks; no fits. | Remove the input-availability statement in a labelled copy and explain the unsafe inference; no model run. |
| 05.04 | Run a baseline through ready, running, awaiting-check, and complete. Test missing check and ambiguous target. | One fit and two main handoff fixtures. | One separately declared wrong-candidate fixture; no extra fit. |
| 05.05 | Compare full system and system without its domain check on valid and leaked-feature proposals. Measure whether the proposal reaches a dry-run fit stub. A tool allowlist remains as overlapping protection. | Four main fixture executions; no fits. | Two separately declared fixture executions with both protections removed. |
| 08.01 | Compare tree and forest using calendar features at seeds 17, 29, and 43, on the same split. Report all paired MAE differences and costs. | Six fits; three per recipe. | Show which difference a best-seed-only report would select and why that discards evidence; no further fits. |

Total: thirteen new CPU fits. Freeze attempt limits in each runtime workspace. The routed bike workspace has a two-attempt contract, with exactly one attempt used; lab 05.03 needs that real partially completed state. Its remaining attempt is reserved, not permission for this driver to spend it. All other fit limits equal the counts shown. No final evaluation is requested.

Arm B chooses linear/calendar if the baseline's largest hourly mean absolute error is at least 1.5 times its smallest; otherwise it chooses tree/calendar. Record the observed hourly values and decision before the second fit. This explicit teaching rule is intentionally simple. It does not prove that the selected model is optimal or that feedback caused a general advantage. Both arms have equal fit counts; proposal and review costs need separate accounting.

## Execution and acceptance

Each child command has a 60-second timeout. Keep stdout, stderr, exit status, elapsed wall time, complete candidate predictions, failed attempts, and checker reports. Recompute scores with the supplied row/target checker. Record source revision, tool and driver hashes, versions, plans, and immutable input snapshots. Stop on an unexpected result; do not silently rerun a failed fit.

The router and coordinator are fixed, agent-written implementations. Their Markdown instructions and executed transition rules are inspectable. They do not involve separate agent workers, technical evaluator isolation, LLM training, learned routing, or recursive improvement. A fresh process is not a fresh coding-agent context.

Check handoffs using task and candidate identity and the prediction-file digest, not the displayed metric alone. An absent checker result stays awaiting-check. An ambiguous target enters needs-clarification. A check for another candidate is rejected even if its score is valid. No fabricated human decision can unblock it.

For wine, derive partition membership from the pinned source and ensure no identical feature vector crosses partitions. Recompute the majority model's ordinary accuracy, both class recalls, and balanced accuracy from its actual predictions.

For the ablation, never call the fitting tool on the intentionally leaked fixture. Removing only the domain check may have no effect because the allowlist is still active. Keep that null result. The second removal answers a different question about combined protection.

For repeated models, keep all three paired seeds, mean and range of differences, fit times, and a plot. Three seeds on one fixed split cannot establish a population estimate. The recipes differ in family and complexity; this is a stability exercise, not a one-factor causal analysis.

## Evidence boundary

Record learner predictions, quiz answers, and teach-back as unattempted. Agent-inference cost is unknown, not zero. Child-command wall times include startup and checks and overlap any parent duration; do not add nested timings. Do not describe this run as complete validation of all activities or all coding agents. Preserve negative results. The optional unequal-budget fit extension, another native agent, GPU backends, and cluster execution remain untested.
