# One changed rule, two different retained models

This is the author walkthrough for [capstone 11.02](../../../11_capstones/step_02_recursive_experiment/README.md). Eight real CPU fits test a revised improver under a fixed protocol. The author proposes the revision; the program executes and records it. No learner or independent peer took part.

Imagine judging a student only on questions they have already practised. A perfect score can hide weak transfer. The original rule makes the same mistake: it selects model recipes by training error. The revised rule selects them by error on the separate selection partition. The key evidence is the later decision trace that reads and applies this changed instruction.

| Stage | Original rule I0 | Revised rule I1 |
|---|---|---|
| First generation | Fits ridge and tree; retains tree with zero training error | Not yet proposed |
| Observed failure | Tree selection MAE 0.693387; ridge 0.609239 | Author proposes one ranking change from this evidence |
| Second-generation starting recipe | Tree | Identical tree recipe bytes |
| Second-generation fits | Tree, ridge, forest | Same three recipes, order, inputs and seeds |
| Rule used in the later trial | Rank by training MAE | Rank by selection MAE |
| Retained recipe | Tree | Forest |
| Selection MAE | 0.693387 | 0.553066 |
| Terminal evaluation MAE | 0.675403 | 0.546309 |

Lower MAE is better. Both choices and the external decision to accept I1 were frozen before final evaluation. Corresponding recipes produce byte-identical selection predictions across arms. The difference comes from which recipe each rule retains, not from a different model implementation or extra fit allowance.

## Follow the evidence

1. Read the [protocol](PROTOCOL.md), [generated extension](EXTENSION.md), and inherited [data card](package/DATA-CARD.md). The earlier capstone remains unchanged.
2. Compare [I0](I0.md), the [observed failure and proposal](CHANGE-PROPOSAL.md), and [I1](I1.md). Only the ranking instruction changes behavior.
3. Inspect the [first-generation trace](g1-TRACE.csv), then the [I0 later trace](g2-i0-TRACE.csv) and [I1 later trace](g2-i1-TRACE.csv). Each row identifies the skill hash, scores and actual retention decision.
4. Open the [external decision](PROMOTION.csv), [pre-final identities](PRE-FINAL.csv), [terminal results](FINAL-RESULTS.csv) and [complete fit ledger](experiment/ATTEMPTS.csv).
5. Read the [43 audit checks](AUDIT-CHECKS.csv), [cost accounting](COST.md), [claim audit](CLAIM-AUDIT.md), [artifact-removal review](evidence-removal/REVIEW.md) and [handoff](HANDOFF.md).

The budget gate refused a [ninth fit](commands/21-extra-fit-refused.md). Closure refused [repeated final evaluation](commands/23-repeat-final-refused.md) and a [post-final fit](commands/24-post-final-fit-refused.md). None performed training. All eight actual fits succeeded; rejected model proposals remain in the traces.

## What the result means

The revised improver governed a later **candidate trial** and retained a better model in this one comparison. I1 was accepted afterward; no third, post-acceptance generation ran. This is an author-guided demonstration of a changed improvement procedure and its later use. It does not establish autonomous RSI, general improver superiority, lower total research cost or acceleration. The weak baseline, small fixed menu, familiar dataset and shared author context matter.

The 992 evaluation rows were scored only after the choices froze. Their files are public and locally accessible; the boundary is procedural, not private access control. No fresh-task effectiveness comparison, learner assessment, independent agent or cluster test occurred.

The [original concept illustration](../../../assets/illustrations/capstone-recursion-v1.png) remains useful: connect its protocol, lineage, later-use and fair-comparison areas to the files above. Its contrasting-case instruction is an illustrative alternative; this executed change uses selection MAE. Its arrows do not imply a third generation. No new image was generated.

## Preservation

The [manifest](MANIFEST.csv) records 121 original files from the sibling author workspace; every archived byte was checked against its hash. It includes generated implementation, eight fitted models, data, readable skills, predictions, all command records and the audit. Python caches and installed dependencies are excluded; [versions](commands/00-environment.md) remain. This README and a [progress-message correction](PUBLICATION-ADDENDUM.md) were added after sealing and are outside that original manifest. The old per-fit progress message is stale; the top-level progress and final lock record closure. The [maintained driver](../../../../how-did-i-generate-it/rsi/scripts/run-capstone-recursion.mjs) preserves the phase boundaries; students use the tutor and natural language.
