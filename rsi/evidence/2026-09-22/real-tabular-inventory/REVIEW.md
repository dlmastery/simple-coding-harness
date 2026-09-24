# Metadata review before a new benchmark

All 1,183 inventory checks pass. The archive contains 323 original API
responses for 107 tasks, with retrieval URLs and byte hashes. No dataset rows
or model scores were requested, and no fits ran.

The automated rule nominated six regression tasks. It nominated no
classification tasks because the older CC18 records use the ambiguous license
label `Public`. This is a metadata limitation, not evidence that those datasets
cannot be used. The original automated output remains unchanged.

## Resolve classification provenance

The following primary UCI pages explicitly state CC BY 4.0. Checked on
22 September 2026. The linked sources supply attribution; raw OpenML copies
still need identity and schema checks before publication or fitting.

| OpenML task | Dataset and primary source | Attribution |
|---:|---|---|
| 3 | [Chess, King-Rook vs. King-Pawn](https://archive.ics.uci.edu/dataset/22/chess+king+rook+vs+king+pawn) | Alen Shapiro; DOI 10.24432/C5DK5C |
| 6 | [Letter Recognition](https://archive.ics.uci.edu/dataset/59/letter+recognition) | David Slate; DOI 10.24432/C5ZP40 |
| 16 | [Multiple Features, Karhunen view](https://archive.ics.uci.edu/dataset/72/multiple+features) | Robert Duin; DOI 10.24432/C5HC70 |
| 23 | [Contraceptive Method Choice](https://archive.ics.uci.edu/dataset/30/contraceptive+method+choice) | Tjen-Sien Lim; DOI 10.24432/C59W2D |
| 28 | [Optical Recognition of Handwritten Digits](https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits) | E. Alpaydin and C. Kaynak; DOI 10.24432/C50P49 |
| 31 | [Statlog German Credit](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data) | Hans Hofmann; DOI 10.24432/C5NC77 |

These are the first six size-eligible, distinct-source candidates by task ID
after resolving those licenses. The intervening tasks 18 and 22 are other
feature views of the same Multiple Features character instances. Treating
them as independent development and transfer datasets would obscure shared
examples. Retain task 16 for this candidate panel and record the other views
as grouped exclusions. This is a provenance decision before any new fits,
not an outcome-based exclusion.

The old chess source URL returned a 404; the modern UCI page is linked above.
That page lists 35 features, while OpenML reports 37 columns including its
target. Resolve this discrepancy from the actual files; do not assume equal
names mean byte-identical data.

The earlier course used scikit-learn's digits dataset. Its relationship to
Optical Recognition must be checked; task 28 cannot be casually described as
an unexposed task-transfer test. Letter Recognition has 26 classes, which
affects per-fit resources even though its table fits the metadata limits.

## Before training

Review raw schema, labels, feature meaning, duplicate/group structure and
source changes for the six regression and six classification candidates.
Separate observational, designed and simulated data in their data cards.
Keep related source datasets on one side of any task-transfer boundary.
Specify train-only preprocessing and label handling. Declare procedure
controls, training budgets and final evaluation before running models.

No fit allocation is created by this review. The rejected synthetic harness
remains rejected; the unused conditional-final study remains unexecuted.
