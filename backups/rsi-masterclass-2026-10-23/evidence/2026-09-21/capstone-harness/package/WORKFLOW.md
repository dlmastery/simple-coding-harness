# From a data row to a checked decision

1. Read the scientific task. Confirm when inputs exist and what quality means.
2. Prepare a new experiment with an allocation inside the lab's combined budget. Inspect data identity, missing values, duplicate groups, split sizes, and training labels.
3. Freeze the task and package identity in CONTRACT.csv. SPLIT.csv records every row and group. An existing experiment cannot be prepared again.
4. Ask for one candidate. Validate features, metric, split, package, unique name, remaining budget, and absence of an active lock before admitting work.
5. Persist the charged attempt before fitting. Fit transforms and the model only on training. Record selection predictions and metrics, plus training MAE for later diagnostic use.
6. Recompute selection MAE from pinned targets and saved predictions. Reject row, recipe, candidate, hash, or summary mismatch.
7. Use a separately declared improvement rule to retain or reject the candidate. A passing output check establishes validity, not superiority. This baseline lab performs no improver search.

The builder chose the implementation and small model menu. TASK.md supplies the scientific meaning. The runtime enforces the declared procedural checks. The author or student still controls the host filesystem and can edit code or contracts; there is no adversarial isolation.

Logs retained on disk are not automatically memory. Later skill use and recursive improvement require their own traces and comparisons. A meta-harness generated this package; package generation alone is not RSI.
