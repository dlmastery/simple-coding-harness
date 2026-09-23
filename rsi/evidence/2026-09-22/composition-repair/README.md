# Repair an operator without inventing a performance gain

The [previous comparison](../tabular-comparison/README.md) found two source
changes that produced identical estimator settings. The revised template's
leaf size was overwritten by the next operation. This repair preserves each
template's settings during refinement and checks constructor identity before
admitting a repeated model.

![A conceptual guide to composing operations that change different parts of a research system.](../../../assets/illustrations/operator-composition-v1.png)

*The illustration explains composition. The measurements below come from
the saved integration run, not from the picture.*

## Three versions, with their chronology preserved

1. [First preflight](failed-preflight/preflight/CHECKS.csv): the repair exposed
   a signature bug before any fit. Equivalent kernel configurations stored
   `C` as integer one and floating-point one, so their signatures differed.
   The failed check, sources and planned inputs remain intact. No model ran.
2. [Corrected preflight](integration/preflight/CHECKS.csv): 420 construction
   and identity checks pass. Known continuous parameters share a numeric
   representation. Integer leaf counts remain distinct from floating-point
   fractions. The [four declared fits](integration/LEDGER.csv) then run once.
3. [Capacity review](capacity-review/CAPACITY-CHECKS.csv): source inspection
   finds that the old higher-capacity branch imposes a depth cap on an
   unlimited tree. The final builder preserves unlimited depth for factors
   above one. The full 420-check construction suite passes again, plus ten
   checks for this behavior and unchanged constructors for the earlier fits.
   No extra model is fitted.

All sources remain separately frozen. The final builder is
[this version](capacity-review/source/refinement_engine.py). The integration
fits used the earlier [corrected version](integration/source/refinement_engine.py).
The later correction affects higher factors; both actually fitted factor-0.3
constructors are verified unchanged. This distinction prevents attributing a
run to source written after it happened.

## Four real fits on previously exposed development tasks

| Task | Metric | Original | Corrected | Selection predictions changed |
|---|---|---:|---:|---:|
| Chess classification | Balanced accuracy, higher is better | 0.933346 | 0.933346 | 0 / 657 |
| Abalone regression | MAE, lower is better | 1.802186 | 1.802359 | 354 / 800 |

The [constructor/result table](integration/CONSTRUCTION-AND-RESULT.csv)
shows minimum leaf sizes changing from ten to seven for the chess template,
and ten to seventeen for the abalone template. Both retain depth two for
this deliberately low factor. Chess predictions stay identical; abalone
predictions change and its error becomes slightly worse. A meaningful source
change can still tie or regress on a task.

All four attempts succeed and consume 6.565 worker-process seconds in total.
The [25 post-run checks](integration/REPAIR-CHECKS.csv) verify allocation,
source and data identity, prediction metrics, process limits and the absence
of final data. Earlier failed construction checks used no fits. Inference,
analysis and total development costs are additional and not fully metered.

## What this fixes, and what remains

The current builder preserves template-relative tree and histogram settings.
It no longer calls a newly capped unlimited tree a higher-capacity proposal.
The bounded constructor guard detects both parameter saturation and equivalent
kernel settings under different recipe names. It does not replenish refused
proposals or grant a larger budget. It also does not prove equivalence across
arbitrary implementations or guarantee different predictions.

This is an implementation repair and integration check on known data. It is
**not a positive RSI result, a new task-transfer test or an improved-updater
comparison**. The previous evaluation stays unchanged. The next procedure must
compete with the strong fixed portfolio on newly declared tasks.

The [agent entry](../../../experiments/real-tabular/refinement-v2/README.md)
explains how to inspect this evidence without starting another run. The
[protocol](../../../../how-did-i-generate-it/rsi/validation/COMPOSITION-REPAIR-PROTOCOL.md)
declared four attempts before training; all four are spent. The
[manifest](ARCHIVE-MANIFEST.csv) records 136 byte-verified original files,
including the failed preflight and all source versions. The ten capacity
checks follow the four-fit stage and introduce zero additional model attempts.
