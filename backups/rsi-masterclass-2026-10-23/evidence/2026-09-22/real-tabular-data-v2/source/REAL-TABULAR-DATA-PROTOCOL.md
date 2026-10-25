# Prepare the public benchmark panel without fitting models

The previous goal turn made progress: it completed and published the frozen
discovery-policy comparison, preserved a rejected builder revision and checked
an outcome-independent metadata inventory. This preparation continues that
work. It does not reopen either completed experiment.

## Sources and roles

Use the six regression candidates in the original inventory and the six
classification candidates resolved in its source review. Exclude the repeated
Multiple Features views as already documented. Preserve original metadata and
file identities; report any schema discrepancy rather than repairing it silently.

Assign development and later procedure-comparison roles now, before raw data
inspection or fitting:

| Role | Classification task IDs | Regression task IDs |
|---|---|---|
| Development | 3, 16, 28 | 361234, 361236, 361244 |
| Later procedure comparison | 6, 23, 31 | 361235, 361237, 361247 |

This alternates positions in each sorted six-task list. Task 28 stays in
development because earlier experiments used scikit-learn digits. Verify and
record the actual overlap. None of these public datasets is a secret test.
Metadata and schema inspection precede procedure development; do not call
that fully blind evaluation. Different feature views of the same source must
not cross the task-role boundary.

## Download and inspect

Download the exact OpenML ARFF URLs already recorded. Retain raw bytes, SHA256,
reported MD5 where available, request URL, retrieval time, dataset version,
target, attribution and license notes. Download failure is an acquisition
failure, not a model failure. Preserve it before using a documented fallback.

Parse declared nominal/numeric types. Report row and column counts, missing
values, constant inputs, duplicate feature groups and conflicting targets in
those groups. Do not use label values to select favorable datasets. Resolve
incompatibility or source ambiguity before training. Show designed/simulated
data as such when the source establishes that provenance.

## Freeze row roles

Canonicalize each input row using its declared types, then hash the input values
without the target. Identical feature rows receive the same group identity.
Hash that identity with the fixed salt `rsi-real-tabular-v1`; bucket modulo ten
assigns 0–5 to training, 6–7 to selection and 8–9 to final rows. This is a
deterministic grouped 60/20/20 adaptation, not the original suite's full
cross-validation protocol. Keep the published task definitions for comparison.

For laptop runs, cap training at 2,400 rows and selection/final at 800 each.
Select entire feature groups in ascending salted-hash order within each role,
stopping before the cap. Never split a duplicate group across row roles.
Record excluded groups and resulting counts. No target-driven resampling,
stratification rescue or new seed is permitted. Missing classes or unusable
partitions need a recorded technical decision before fitting.

Fit all learned transforms inside candidate pipelines on training rows only.
Keep final arrays outside the candidate workspace. Data preparation may check
row identity and label support, but must not evaluate model predictions.
Record the public procedural boundary and the fact that the maintainer can
read local files. Later improvement code must receive only train/selection.

This phase authorizes data acquisition, parsing, schema checks and split
preparation, with **zero model fits**. The actual method comparison, budgets,
promotion rules and final scoring procedure require a separate frozen protocol.
