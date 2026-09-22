# Foundation checks with preserved failures

Author walkthrough for labs 03.03, 04.03, and 04.04, executed on 21 September 2026. The driver exited 0. These runs close specific missing author-execution records; they do not test learner understanding or independent-agent portability.

## Join checks: 03.03

The [four-scenario report](03-03/JOIN-REPORT.md) records one permitted join and three stopped cases:

| Inputs | Actual decision |
|---|---|
| Two passes for A under v1 | proceed |
| Only data evidence available | incomplete |
| Data for A, resources for B | reject identity |
| Data under v1, resources under v2 | reject contract |

Separate data and resource functions ran sequentially. Their inputs and output records are preserved in each case folder. The resource values are declared teaching fixtures; available RAM or cluster capacity was not measured.

The [delay exercise](03-03/missing/DELAY-TRACE.md) belongs to the missing scenario: stop at synthetic tick 1, archive the late result at tick 2, and keep the decision incomplete. These ticks are logical events, not a measured concurrent execution. No fifth join decision or fit occurred.

## Invariant checks: 04.03

All [six fact tables and verdicts](04-03/RULE-TESTS.md) are retained. Each invariant has one accepted case and one rejected case with exactly one violation: direct target derivation, transform fitting outside train, and selection on final. The supplied domain tool stayed unchanged.

The separate [units extension](04-03/units-check.mjs) accepted [MAE with units](04-03/units-present-RESULT.md) and rejected [MAE without units](04-03/units-missing-RESULT.md). It checks a nonempty unit label. It does not prove that the units are dimensionally correct or that the metric was computed correctly.

The tool's rejection of unknown relation names was inspected in its source but was not allocated a separate case here. Missing facts, indirect derivation chains, and agreement with a real experiment remain outside these demonstrations.

## Contradiction and renaming: 04.04

The [repair report](04-04/REPAIR-REPORT.md) preserves all three tables and their results. The original failed with three violations; the corrected copy passed; the consistently renamed original failed with the same three violations. The [renamed check](04-04/renamed/DOMAIN-CHECK.md) still identifies target derivation for `harmless_feature`.

The correction changes a teaching record. It does not repair an executed model or make an exposed final set unseen. The report explains the additional computation and evaluation work a real repair would require.

## Run record

Used: four join scenarios, nine base domain-check subprocesses, two units-check subprocesses, zero model fits. [Timings](COST.csv) include subprocess startup where applicable; they exclude agent inference and the complete authoring process. See the [protocol](PROTOCOL.md), [input freeze](DOMAIN-INPUT-FREEZE.md), [environment](ENVIRONMENT.md), and [progress](PROGRESS.md). Learner predictions, teach-back, and quizzes were unattempted.

The maintained [author driver](../../../../how-did-i-generate-it/rsi/scripts/run-foundation-gaps.mjs) refuses to overwrite its workspace. Sixty original files were copied and hash-verified, including the original run manifest. The manifest lists the other 59 run files. This README was added after archival.
