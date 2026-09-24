# A case-sensitive label check failed

The first audit exited 1 after writing its nineteen verdicts. Eighteen passed. The wine result uses “Balanced accuracy” at the start of a sentence, while the audit searched for lowercase “balanced accuracy”. The result did contain the correct metric and runtime.

[The original check results](CHECKS-FIRST-PASS.csv) and [original audit source](audit-saved-reuse-first-pass.mjs) are preserved. The maintained audit compares metric labels without letter-case sensitivity. It still requires the recorded Python version. No source evidence, predictions, contract, ledger or score changed. The archived source is for inspection; its original relative execution location was the maintenance scripts directory.

This repair changes a documentation-label check, not a scientific acceptance threshold. The next invocation repeats read-only checks and regenerates review documents; neither invocation trains a model.
