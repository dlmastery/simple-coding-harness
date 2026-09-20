# Domain check

- FAIL: model uses total_users, which is derived from the target.
- FAIL: scaler is fit on final; fitted transforms must use train only.
- FAIL: search selects on final; that consumes the final evaluation.

This checks three declared invariants and relation names. It is not a complete scientific validator.
