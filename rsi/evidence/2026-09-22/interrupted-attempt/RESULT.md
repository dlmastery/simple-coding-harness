# Keep the failed attempt, then continue

This supplements 02.05's earlier orderly pause with a real stale-running record and one later fit. It is an author walkthrough, with no learner answers.

The first driver reached its no-training wait stub but failed its launcher-versus-worker PID check. Cleanup stopped its owned process handle. A later Windows process query found the recorded worker PID 29336 absent while the tool's lock and running ledger remained. The original direct-worker termination sequence therefore did not pass; see FIRST-DRIVER-FAILURE.md. No estimator trained in the fixture.

Recovery inspected the actual lock PID through Windows OpenProcess. The OS returned error 87, no such PID. A continuation request with the stale lock was refused. The first recovery script expected exit 1, but the CLI correctly returned 2. That mistaken expectation and stopped script are preserved; the probe was not repeated. See REFUSAL-CORRECTION.md.

The corrective continuation verified the retained refusal and unchanged ledger, checked worker absence again, then removed only the archived stale lock. A second request was refused because trial-001 still said running. Only after changing that existing row to interrupted did one real linear/calendar fit run as trial-002. It achieved selection MAE 109.80766775073437; the separate prediction checker passed. Nine post-run invariants pass.

| State | Slots consumed | Actual model fits | Observation |
|---|---:|---:|---|
| Wait stub reached | 1 | 0 | trial-001 running; original worker lock present |
| Stale lock refusal | 1 | 0 | exit 2; no admission |
| Running record refusal | 1 | 0 | exit 2; no admission |
| Reconcile record | 1 | 0 | same trial-001 marked interrupted |
| Continue | 2 | 1 | trial-002 succeeds; trial-001 proposal and frozen contract unchanged |

The three-slot ceiling is unchanged. One slot remains, but the separately declared supplement is finished, so it does not spend that slot. No final evaluation or new task selection occurred. Public-data and earlier-result exposure remain explicit.

## Costs and limits

The successful fit records 0.07603 seconds. The interrupted ledger retains zero recorded fit time because the estimator was never called; its total process time was not captured before the driver's failed check. Zero fit time does not mean free orchestration. The four successful recovery command observations have separate startup/check time in their logs. Author preparation and provider inference are unmeasured.

This checks stale-lock refusal, running-record refusal, manual reconciliation, charged-slot persistence and a new candidate identity after recovery. It does not resume optimizer state, interrupt a real training algorithm, establish independent agent context, or validate a remote scheduler. It does not validate the failed driver's PID assumption. A lock names the worker that wrote it; a launcher handle can identify another process. Uncertain process identity must stop recovery.

The existing resume-shared-budget-v1 illustration was inspected and preserved. It depicts the original orderly pause; this additional run starts with an interrupted fixture instead. Its conceptual warning that an interrupted attempt keeps its slot is demonstrated by the new ledger. The source tool and checker are copied for provenance, not as an independently runnable archived package.
