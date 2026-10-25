# Data preparation for the nested procedure comparison

This phase acquires and checks data only. It allocates **zero model fits**.
The selected tasks are 43, 45, 2074, 361241, 361251 and 361260, with sources
and limitations recorded in [the task decision](NEXT-PROCEDURE-TASKS.md).
They are reserved for the next procedure comparison. The previous evaluated
tasks may inform its development, but do not regain untouched-test status.

Copy the saved OpenML task records and data descriptors with their hashes.
Download each pinned ARFF URL and require its supplied MD5 to match. Preserve
raw bytes, acquisition failures, timestamps, schema, exclusions and all
preparation sources. Do not replace a task because of a model score. If a
file or schema cannot be reconciled, stop and record the issue.

Remove declared ignored/identifier attributes from predictors. Preserve their
original values in a separate grouping record. For Miami, exact PARCELNO
identities must not cross partitions. Exact duplicate-feature rows must stay
together for every task, including when their target labels conflict. Join
these constraints by connected components. Splice instance names can prevent
identical-record reuse; do not claim that they establish gene independence.
No gene, protein, sender or satellite-location identity will be invented.

Check the grid regression inputs for a derived stability-class outcome.
Exclude it if present and record the reason before model fitting. Missing
targets, unknown target types or unexplained schema differences stop the
preparation. Missing predictors remain explicit for train-fitted imputation.

Assign groups deterministically using the salt `rsi-nested-public-v1`, task
ID and a target-free group identity. Hash buckets 0–5 are training, 6–7 are
selection and 8–9 are final. Cap these at 2,400, 800 and 800 rows respectively.
Visit groups in salted-hash order, keep complete groups, and skip a group
that would exceed the remaining cap. Preserve excluded groups. Every class
must remain represented in each retained classification partition; otherwise
stop and review the design without fitting.

The independent checker must reconstruct source rows, exclusions, group
boundaries and deterministic allocation. Verify partition values and row
identities, source metadata counts, target types, group conflicts, row caps
and class coverage. Keep final files under an evaluator directory. Structural
checks can inspect their identities and support; no model score is allowed.
The filesystem boundary remains procedural, not a private evaluation service.

Report the source-specific limits: corpus-specific email features, uncertain
gene/protein independence, overlapping satellite neighborhoods, simulated
grid data and retrospective property prices. Passing these checks does not
establish deployment validity or causal claims. Freeze the subsequent
researcher/improver execution protocol and budgets before any fitting.
