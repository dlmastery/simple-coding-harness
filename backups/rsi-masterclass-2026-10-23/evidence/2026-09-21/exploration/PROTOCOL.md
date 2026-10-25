# Broad probes and one focused fit

Lab 10.03 author walkthrough, 21 September 2026. Use a fresh sibling workspace and three fits in total, all in one frozen experiment. Three result-check subprocesses are permitted, one after each fit. Stop on unexpected failures; do not refund attempts. Use the supplied bike task, source hash, train/selection split, MAE, allowed features, and seed 17. No final evaluation.

First fit the constant/calendar baseline (training median). Then fit linear/calendar. The first asks what a feature-independent prediction misses; the second tests whether calendar inputs explain selection variation. Preserve both results regardless of score.

After those two fits, save selection-only error summaries by hour and weather category. For weather categories with at least 50 rows, compare mean signed residuals (actual minus prediction). If their range exceeds 10 rentals per hour, the planned third probe is linear/all: keep the model family and add the permitted weather group. Otherwise use tree/calendar to probe nonlinear calendar structure. This is a declared teaching heuristic, not an optimal information-gain algorithm; group differences can be confounded. Record the actual decision and remaining question before the final fit.

Pause the driver after saving initial analysis. The author agent reads the outputs and writes DECISION.md. Resume only from two completed fits and that recorded decision; freeze its hash before fit three. Then check the final result, compare selection scores, and stop at three fits. Record fit time, subprocess wall time, observed recipe, and unknown agent reasoning cost separately.

For the duplicate counterexample, inspect the earlier 02.06 arm-A baseline repeat and its two saved prediction hashes. This is reused evidence, not a fourth fit or a newly executed third-attempt duplicate arm. Explain that deterministic repeats can check reproducibility but do not answer a new feature question.

No task-specific memory file is loaded into this run. The author context has seen this public dataset and earlier results, so this is not a cold-start or blind exploration test. Final-result information must not be consulted to make the current decision. Learner predictions, quiz, and teach-back are untested.
