# Diagnose the objective before adding more search

The root coding agent proposed changes after reading the
[public-data baseline](../real-tabular-baseline/README.md). The
[proposal](source/PROPOSAL.md) precedes the new fits. The original builder is
retained byte for byte as an imported ancestor.

All **24 attempts succeeded**. **471 independent checks pass**. The
[report](REPORT.md) and [comparison table](COMPARISON.csv) retain native
scores and normalized losses. The archive preserves all original execution
files with [byte identities](ARCHIVE-MANIFEST.csv).

Numeric scaling and regularization changes slightly improve selection
balanced accuracy on the three classification tasks. The original portfolio
retains its better regression models for abalone and auction verification.
On solar flare, the training-median reference improves MAE from 0.365629 to
0.325926, while absolute-error boosting ties the reference.

The solar-flare result repairs an omitted conventional control. It does not
establish RSI. More complicated models do not automatically help when many
identical observed inputs have different outcomes and the target is mostly
zero. Matching the training objective to the reported metric is a useful
research rule; its value on later tasks still needs testing.

These are development selection scores from extra fits, not an equal-budget
method advantage. No final score or reserved-task fit was produced. The
remaining development allowance is four attempts per task, 24 total. A new
written proposal must precede that work, followed by a frozen method comparison.
