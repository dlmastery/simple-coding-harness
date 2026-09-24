# A fixed three-attempt loop

- Task: bike
- Models: constant,linear,tree
- Features: calendar
- Seed: 17
- Limit: 3
- Retain: lower selection MAE
- Tie: keep earlier candidate

Before each step, read STATE.md and the actual trial ledger. Refuse if their spent count, current candidate or retained candidate disagree. The next model is the next entry in the fixed Models list. Save the state read by this step before fitting. After the checked fit, record the current and retained candidates separately, then save a new state version. Failed admitted attempts remain charged; stop on an unexpected failure instead of choosing an undocumented repair.

At three spent attempts, refuse further steps. A comparison report must agree with the minimum valid selection MAE. Keep the task, raw source, metric and chronological partitions fixed. Do not inspect final outcomes or change the recipe order after seeing results. This loop searches task candidates; its own procedure stays fixed.
