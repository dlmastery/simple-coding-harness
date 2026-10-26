# Contract for a generated compute adapter

[Guide](README.md)

The research procedure proposes a candidate. The adapter runs it and returns evidence. The adapter does not change the target, split, metric, or promotion rule to suit the backend.

| Operation | Required behavior | Evidence |
|---|---|---|
| Validate | Check versions, paths, resources, and remaining budget before submission | Validation verdict with concrete failures |
| Submit | Allocate a unique attempt and submit the frozen candidate once | Candidate ID, attempt ID, job ID, time, resource request |
| Inspect | Read actual backend state without creating another job | State, timestamps, active resource use where available |
| Collect | Retrieve outputs and check identity, completeness, and hashes | Logs, predictions, artifacts, checksums, terminal status |
| Cancel | Stop the named attempt and confirm the backend is no longer running it | Cancel request and observed stopped state |
| Resume | Validate the checkpoint and continue its charged history | Checkpoint identity, compatible versions, accumulated cost |
| Retry | Create a new linked attempt after a recorded failure | Failure cause, retry count, new job ID, cumulative cost |

The generated implementation may use a local process, scheduler, or service API. Its serialization is an agent implementation detail. The learner sees a Markdown brief and readable report.

## State and accounting

Distinguish planned, queued, running, succeeded, failed, cancelled, and unknown. A network timeout leaves state unknown until reconciled; it does not authorize blind resubmission. A completed backend job can still fail output validation.

Record transitions as append-only events where the backend permits. Persist the job identity before polling. Reconcile an uncertain submission against its idempotency key or scheduler metadata before retrying. Do not count a cached result as new training.

Retain wall time, training time, evaluation time, retries, allocated accelerator time, peak memory when measured, and agent inference cost where available. Mark missing values unknown, not zero. Explain the distinction between allocated and active accelerator time.

## Scientific compatibility

A result identifies data, split, evaluator, model recipe, code, environment, seed policy, and proposing procedure. Reject missing or mismatched identities before promotion. For training resumption, validate optimizer, progress, random-state, and data-order requirements as well as model weights.

When the experiment deliberately changes an interface, create a new contract and a new comparison. Preserve the older result under its original contract.

## Boundary

This document is a contract for code the agent generates. It does not itself enforce isolation, spending limits, or cancellation. The backend checks must demonstrate each claimed behavior. Host-side budget checks can lag; use actual scheduler or service limits where supported and disclose any remaining overshoot risk.
