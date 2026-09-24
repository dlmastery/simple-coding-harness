# From a procedural failure to a later decision

The original [change proposal](../../../../rsi/evidence/2026-09-20/clean-journey/09-05/CHANGE-PROPOSAL.md) targets a specific failure: perfect training fit can accompany worse selection performance. The author changes one instruction, from promoting on training score to promoting on selection score. The author supplies both versions; there is no autonomous discovery claim.

The two [diagnostic cases](../../../../rsi/evidence/2026-09-20/clean-journey/09-05/DIAGNOSTIC-FIXTURES.csv) are synthetic numbers, not model measurements:

| Case | Training MAE, parent → child | Selection MAE, parent → child | v0 | v1 |
|---|---|---|---|---|
| Overfit | 12 → 0 | 15 → 24 | Promote | Reject |
| Useful | 12 → 8 | 15 → 10 | Promote | Promote |

These are two cases evaluated under both procedures: four recorded decisions and zero fits. The retained driver reads each procedure and computes those decisions before creating the later synthetic ML cases. Its identity still matches the historical source record. This supports the declared execution sequence; it is not an independently timestamped attestation.

“Write more thoughtful proposals” does not say which action changes. “Promote only when selection MAE is strictly lower” defines a decision that these cases can test. A contrasting-case requirement is another inspectable revision, but it is not the instruction changed in this run.

The expected benefit is fewer retained overfit children. The limitation is selection noise and repeated development exposure. Both versions already compute training and selection scores, so the changed gate does not add a model fit here. Authoring and inference costs remain unavailable. A broader effectiveness claim needs fresh cases and complete cost accounting.

The later regression round provides the inheritance evidence:

1. [BEFORE.md](../../../../rsi/evidence/2026-09-20/clean-journey/09-05/rounds/regression/v1/BEFORE.md) names the revised improver hash, task-skill hashes, new data identity and two-fit allocation.
2. The parent and child produce actual predictions under the unchanged task. Their selection MAEs are about 24.20 and 71.88.
3. [DECISION.md](../../../../rsi/evidence/2026-09-20/clean-journey/09-05/rounds/regression/v1/DECISION.md) records the selected instruction and rejects the child before final scoring.
4. The matched v0 arm retains the child. Corresponding prediction files are byte-identical across arms; the implemented promotion rule explains the differing choice in this controlled case.

Those two v1 fits are a subset of the original eight-fit comparison, not two additional fits to add again. The revision is used in a later candidate trial; this does not demonstrate an independently accepted improver autonomously launching another generation.

The new [pointer replay](POINTER-REPLAY.md) reads v1 and then v0 against the same saved scores. It changes an in-memory pointer and produces the corresponding retention choices without training or editing the original active records. It is an explicit dry run, not a new agent comparison. The fixed external MAE, cases and final procedure stay the same.
