# First checker invocation

The model run completed 72 attempts (71 successful fits, one 60-second timeout).
The first independent audit returned exit 1 at base_scores_unchanged. Its strict
floating-point equality comparison rejected decimal CSV round-trip rounding.
The source-byte identity checks and prediction checks had passed before this
assertion. The base input file was not changed. The subsequent checker compares
identities and statuses exactly and numeric scores with a 1e-12 tolerance.
No model is refitted, no prediction is changed, and no failed attempt is refunded.
