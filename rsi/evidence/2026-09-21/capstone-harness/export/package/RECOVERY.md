# Preserve an interrupted attempt

Say “Stop this experiment and save progress.” The agent checks whether the named process is running, stops only that process if needed, and records its final state. It must not remove unrelated files or jobs.

RUNNING.lock identifies the process and candidate. If the host was interrupted, a lock can remain after the process has ended. The agent checks actual process state before recovery. Preserve the original lock and ledger in an incident copy. Mark an unfinished charged row failed or interrupted with the observed reason; only then clear the reconciled lock. Keep that row charged. This reconciliation is manual, not an implemented automatic recovery service.

These scikit-learn fits cannot resume mid-fit. A retry is a new candidate/attempt under the remaining declared budget. Do not call it checkpoint resumption. If the budget is exhausted, stop. A new experiment needs an explicit separate allocation and cannot erase a failed historical run.

A changed data hash, package hash, or split is a refusal. Restore the recorded original version to inspect an existing run; do not rewrite its contract to make altered files pass. Correct a package defect in a versioned copy, document the impact, and allocate any necessary rerun separately.

When a result check fails, keep predictions, summary, error, and ledger. Do not promote the candidate because model fitting itself exited successfully. Final evaluation remains unused unless a later protocol explicitly closes the experiment.
