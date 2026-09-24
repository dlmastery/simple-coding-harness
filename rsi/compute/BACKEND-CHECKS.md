# Prove a backend with a small job

[Guide](README.md)

Run these checks on the student's authorized environment before a large search. Keep the commands and actual results. The agent generates the setup and reports the outcome in plain language.

| Check | Small experiment | Acceptance evidence |
|---|---|---|
| Data identity | Read a small allowed input and compare its manifest | Expected version and checksum; no accidental path substitution |
| Valid execution | Train or evaluate a tiny candidate | Real job ID, terminal status, predictions, recomputed score |
| Invalid input | Request a nonexistent feature in a disposable fixture | Clear refusal; no successful candidate promoted |
| Cancellation | Stop a deliberately slow harmless test job | Backend confirms it stopped; resource accounting ends |
| Interruption | Interrupt an iterative smoke trainer after a checkpoint | Resume preserves required state and cumulative cost |
| Incompatible resume | Change a version in a labelled checkpoint copy | Refusal; original checkpoint preserved |
| Uncertain submission | Simulate a lost response without submitting twice | Reconciliation finds the original attempt or safely reports unresolved state |
| Budget | Reach the tiny preset attempt or time limit | No new work admitted; active work follows declared stop policy |
| Result mismatch | Alter a copied summary while keeping predictions | Result rejected before promotion |

For an estimator without checkpoint support, replace the resumption check with a recorded failed attempt and a bounded fresh retry. Report that limitation explicitly.

Store a capability table with `tested`, `failed`, or `not tested`, plus the evidence path and date. A local simulation can test adapter logic but cannot change a remote capability to `tested`. Cloud costs, cluster permissions, drivers, distributed communication, and pre-emption need evidence from the actual backend.
