# Observed lineage

Compiled after execution from the saved state, decisions, and instruction hashes. The pre-execution plan is in PROTOCOL.md; prepared and proposed checkpoints retain the earlier states.

| Path and generation | Active improver entering the round | Proposed improver | Active improver leaving the round | Retained task skill |
|---|---|---|---|---|
| Fixed, 1 | Training MAE, strict gain | None | Same version and hash | Linear, calendar |
| Fixed, 2 | Training MAE, strict gain | None | Same version and hash | Linear, calendar and weather |
| Revision comparison, 1 | Training MAE, strict gain | Selection MAE, strict gain | Parent; outcomes tied | Linear, calendar |
| Revision comparison, 2 | Training MAE, strict gain | Training MAE, minimum 15% relative gain | Parent; proposed rule retained a worse selection result | Linear, calendar and weather |

The second proposal was derived from the version actually retained after generation 1. It did not silently inherit the rejected selection-based proposal. Thus its 15% margin applies to training MAE. Treating it as a selection-margin rule would misread the actual lineage.

Both paths stopped after two generations. All twelve fits are charged in FITS.csv. The fixed path consumed four; the revision comparison consumed eight. Two later requests for a third generation were refused without a fit. Both proposal/resume boundaries kept the current parent active until comparison finished.

No revision to the improver was accepted in this run. Increasing generation numbers, saving candidate procedures, or improving the final retained task score would not justify claiming otherwise.
