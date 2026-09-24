# Six tasks prepared for a nested research comparison

**Data preparation is complete. No model has been fitted in this phase.**
The next experiment must test a complete researcher and the procedure that
revises it. These files do not show that either one improves.

The [task decision](../../../../how-did-i-generate-it/rsi/validation/NEXT-PROCEDURE-TASKS.md)
selected six public datasets from metadata before acquisition or new model
scores. The [preparation protocol](checked/source/NESTED-DATA-PROTOCOL.md)
defines exclusions, grouping and deterministic row caps.

| Task | Prediction | Train / selection / final | Grouping limit |
|---|---|---|---|
| 43, Spambase | Email class | 2,400 / 800 / 800 | Identical feature rows; sender identities unavailable |
| 45, splice | DNA-window class | 1,877 / 691 / 622 | Identical features and recorded instance names; gene independence unverified |
| 2074, satellite | Central-pixel class | 2,400 / 800 / 800 | Identical features; overlapping neighborhoods remain a limitation |
| 361241, protein | Decoy RMSD | 2,400 / 800 / 800 | Identical features; parent-protein identities unavailable |
| 361251, grid | Simulated stability value | 2,400 / 800 / 800 | Identical features; derived class excluded from predictors |
| 361260, Miami | Retrospective sale price | 2,400 / 800 / 800 | Identical features and equal recorded parcel IDs |

## What was checked

The [independent checker](checked/analysis-source/check_nested_data.py) uses a
separate dense-ARFF parser and an explicit graph traversal. It reconstructs
connected groups from raw records, excludes source-declared identifiers and
other ignored attributes, and reconstructs hash-based assignment and whole-group
caps. Each saved partition value matches its source value exactly after numeric
round-trip parsing. Every retained classification partition contains all classes.
Source checksums, acquisition manifests, schemas, target conflicts and summary
counts also match.

[DATA-CHECKS.csv](checked/DATA-CHECKS.csv) has 82,177 passing assertions. Most
assertions check individual component identities; this count is not a count of
independent scientific tests. [PANEL.csv](checked/PANEL.csv) records all six tasks.

The grid's `stabf` label agrees with the sign of the regression target. It is
excluded. Miami's `PARCELNO` contains very small numeric values in the pinned
file. The checker confirms that all 13,776 distinct original tokens remain
distinct after parsing. Its 156 repeated-ID rows remain in their original
groups, with no identifier crossing partitions. These are opaque recorded IDs;
the original property-number encoding has not been independently recovered.
Splice has 3,178 distinct recorded names and 12 repeated-name rows, also without
crossings. See [the identifier checks](checked/IDENTIFIER-CHECKS.csv).

Exact feature duplicates with conflicting targets are retained and grouped:
three groups in spam, one in splice, 38 in protein and nine in Miami. Neither
these checks nor the filesystem separation establish private evaluation,
independent genes/proteins, new-scene transfer or deployment validity.

## Preserved preparation failure

The [first preparation](parser-failure/source/prepare_nested_data.py) completed
four tasks and then stopped because SciPy's ARFF parser does not support the
grid's string attribute. The observed exception was
`NotImplementedError: String attributes not supported yet, sorry`.
This description is a retrospective record of the tool output, not an original
captured error log. The incomplete files and exact source remain here.

The [corrected source](checked/source/prepare_nested_data.py) accepts only the
explicitly checked grid schema in that fallback. It reuses all six original
downloads byte for byte, with acquisition lineage recorded. Both versions
performed zero model fits. No failed version or reserved task was replaced
because of model performance.

## Reproduce and continue

From the repository root, ask the coding agent to run:

```text
Run the independent nested-data checker on
rsi/evidence/2026-09-22/nested-data/checked.
Confirm source identities, grouping, exclusions and partition values.
Do not train a model or change these frozen files.
```

The agent command is `.venv/Scripts/python.exe
how-did-i-generate-it/rsi/scripts/check_nested_data.py
rsi/evidence/2026-09-22/nested-data/checked` on the recorded Windows environment.
The checker inspects final rows only for structural correctness; it computes
no model scores. A separate execution protocol must freeze researcher and
improver source, controls, budgets, promotion and analysis before training.

[ARCHIVE-MANIFEST.csv](ARCHIVE-MANIFEST.csv) covers 125 original files from both
workspaces. Every copied byte was checked. This authored report and the manifest
are additional publication files. Source attribution, licenses and limitations
are in the task decision and the six preserved OpenML descriptors.
