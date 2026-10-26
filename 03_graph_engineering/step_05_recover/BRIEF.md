# Lab 03.05 brief

A recovery trace that preserves valid upstream artifacts and reruns affected descendants.

Starting state: The graph with data check, fit, metric check, and report. Use the existing baseline predictions.

Prediction to ask: Which nodes should rerun after a report-writing failure? What if the split changed instead?

Execution limit: No new fit unless an upstream data or recipe change actually requires it; at most one fit.

Follow the README steps. Keep source data and the supplied evaluation contract unchanged. Use the canonical course skills. Generate any required code yourself. Save observations, failures, and the learner’s progress in the separate workspace. Do not invent student answers, measurements, or protected evaluator access.

Acceptance: The successful recovery does not create an extra fit. The changed-split case invalidates all dependent evidence.
