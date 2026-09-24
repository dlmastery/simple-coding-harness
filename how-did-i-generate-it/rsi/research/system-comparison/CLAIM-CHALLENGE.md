# A better model can leave the improver unchanged

**Claim to challenge:** “Our second generation retained a better ML model, so our improver recursively improved.”

**Plausible weaker explanation:** the unchanged promotion rule accepted a useful feature-group change. A new generation number and an archived improver proposal do not establish that the proposed improver became active.

Inspect [the copied lineage](../../../../rsi/evidence/2026-09-20/two-generations/LINEAGE.md), [state](../../../../rsi/evidence/2026-09-20/two-generations/STATE.csv), and [results](../../../../rsi/evidence/2026-09-20/two-generations/RESULTS.csv). The first improver proposal tied the parent and was rejected. The second used a stricter training-gain threshold, retained a worse selection result, and was rejected. Both paths therefore entered and left the relevant rounds with the same active improver. Selection MAE improved on the retained task recipe; this run provides no accepted revised-improver lineage.

The [mechanical identity check](../../../../rsi/evidence/2026-09-21/system-comparison/LOCAL-CHECK.md) connects that interpretation to the actual recorded hashes. This distinguishes a proposal from an inherited procedure. It does not make the public evaluation boundary secret or eliminate shared author context.

**What would distinguish the stronger claim?** In a new, separately budgeted experiment, freeze one released task state and both old and revised improvers. Run matched downstream tasks from that same state. Preserve which instruction each actor actually loaded, its choices, failures, and all candidate/evaluation costs. Use evaluation data unavailable to proposal and selection. Include the cost of producing the revised improver; repeat across declared tasks and seeds. The external acceptance rule must remain fixed. A beneficial result would support that bounded comparison, not unlimited acceleration.

**Resolved:** this historical run did not activate either proposed improver revision. **Unresolved:** whether either procedure would help under other conditions. The proposed experiment is not executed, and this closed two-generation run is not reopened.
