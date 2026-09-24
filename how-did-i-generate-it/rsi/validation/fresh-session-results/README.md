# A skill survives a fresh session

Lab 01.05 asks a simple question: can another agent run the same experiment
from saved instructions, without the earlier conversation? On 23 September
2026, two agents received separate packets with no parent conversation.

| Packet | Allocation | Observed behavior |
|---|---|---|
| Complete task, skill and handoff | One baseline attempt | Ran the constant/calendar bike baseline with seed 17; the course checker passed. |
| Skill and handoff, missing task brief | Zero fits | Identified the missing scientific specification and stopped without fitting. |

The complete run predicts the training median, 109 rentals per hour. Its
selection MAE is 159.947912 rentals per hour. [Independent checks](CHECKS.md)
recompute every selection row from the pinned source and compare prediction
bytes with the earlier recipe. Equal predictions are the expected result of
reusing an unchanged skill. They are not evidence of improvement.

## Inspect the handoff

Start with [the two input packets](../fresh-session-plan/README.md),
[the pre-dispatch identities](PRE-DISPATCH-SOURCES.csv), and
[the actual context boundary](SESSION-BOUNDARY.md).

Then read the [complete session's report](complete/FINAL-REPORT.md),
[its context exposure](complete/CONTEXT-EXPOSURE.md),
[its saved predictions](complete/trial-001/predictions.csv), and
[the missing-task findings](missing/FINDINGS.md).
The [independent checker source](verify_handoff.py) runs without fitting a model.
The [file manifest](MANIFEST.csv) records byte identities of all 58 original
child outputs. The independent checker passed 13,115 assertions, mainly
row-by-row identity, target and prediction checks across 4,358 selection rows.

## What this establishes

The available coding-agent host can recover and execute this fixed procedure
from the complete packet. The second context recognizes that a seed and model
name do not define a scientific task. It asks for missing inputs instead of
inventing the target, metric or split.

There is one exposure deviation. While locating the data card, the complete
agent's broad filename search displayed historical evidence filenames and
candidate names. It reports that no historical scores, predictions or evidence
contents were opened. We retain that disclosure and do not claim a packet-only
context. The required data inspection also summarizes the public final
partition; no final performance evaluation ran.

These agents share filesystem access, dependencies and host instructions.
Their command records and read ledgers are available, but are not an OS-level
access audit or a complete provider inference transcript. Learner prediction,
teach-back and quiz responses were skipped. Other agent products and remote
compute were not tested. All earlier study budgets remain closed; this separate
one-attempt handoff allocation is now exhausted.

The next learning step is [a bounded experiment loop](../../../../rsi/02_loop_engineering/README.md).
It adds repeated decisions to the fixed procedure. This check alone provides
no evidence that the procedure learns or improves itself.
