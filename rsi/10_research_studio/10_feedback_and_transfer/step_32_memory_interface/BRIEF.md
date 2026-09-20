# Lab 10.32 brief

A tiny state-tracking task with an exact checker and two memory representations.

Starting state: A synthetic sequence of inventory changes, such as add 3, remove 1, add 2, with a known final count.

Prediction to ask: Can a shorter summary be worse if it omits one state-changing event?

Execution limit: Two short task attempts and one counterexample; no model-weight training.

Follow the README steps. Keep source data and the supplied evaluation contract unchanged. Use the canonical course skills. Generate any required code yourself. Save observations, failures, and the learner’s progress in the separate workspace. Do not invent student answers, measurements, or protected evaluator access.

Acceptance: The checker uses original events. Correct and faulty summaries are distinguished. The report does not claim model training or a full S3Gym reproduction.
