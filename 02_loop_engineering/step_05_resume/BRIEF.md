# Lab 02.05 brief

A checkpoint and a resumed loop that retains candidate identities and spent budget.

Starting state: A fresh three-attempt loop workspace. Stop after its first completed candidate.

Prediction to ask: After one fit and a restart, how many attempts remain in a three-attempt experiment?

Execution limit: Three total fits across the main stop/resume exercise, not three per session. The separate interrupted-worker exercise below allows one simulated spent attempt and at most one real continuation fit in its own three-slot workspace. At most four real fits across the whole lab.

Follow the README steps. Keep source data and the supplied evaluation contract unchanged. Use the canonical course skills. Generate any required code yourself. Save observations, failures, and the learner’s progress in the separate workspace. Do not invent student answers, measurements, or protected evaluator access.

Acceptance: Candidate IDs are unique. The first result survives. The restart does not replenish attempts. A stale lock is inspected before removal.
