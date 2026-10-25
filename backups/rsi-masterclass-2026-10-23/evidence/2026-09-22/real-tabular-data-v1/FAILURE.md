# Preserved preparation failure

Task 361236 stopped preparation before any model fit. The raw auction ARFF
has nine columns. The published OpenML description explicitly excludes
verification.result; its quality metadata counts eight usable columns including
the target. The v1 loader did not yet interpret ignore_attribute and refused
the mismatch. Earlier eight prepared tasks and all nine downloaded originals
remain unchanged. No predictions were made and no split was used for training.

The corrected v2 preparation will honor source-declared ignored and row-ID
columns, preserve an exclusion table, reuse these exact downloaded bytes and
prepare a new workspace. This fixes source interpretation; it does not change
the declared hash splitting, caps, task roles or benchmark gate.
