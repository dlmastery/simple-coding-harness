# Proposed improver change

Observed failure: an intentionally altered report claims MAE 10 while the saved predictions yield about 159.948. The result checker detects this. The weak improver's summary-only rule would recommend an invalid promotion.

Change one procedural requirement: before deciding whether to promote a task-skill revision, run the existing prediction-based checker on its candidate output. Reject a failed check and preserve its evidence. Compare scores only after validity passes.

Expected effect: fewer promotions based on incorrect summaries. Cost: an extra data read and metric recomputation. Counterexample: a valid low-error candidate must still be eligible; the rule must not reject merely because it differs from the baseline.

This is a constructed reliability case. It does not establish a broad gain in ML research ability or equal-total-cost improvement.
