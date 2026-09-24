# Two rules can agree on recorded outcomes and still differ

This author walkthrough of [capstone 11.04](../../../11_capstones/step_04_external_audit/README.md) audits a recently revised primary source, then runs one small arithmetic check. It uses no model fits and makes no reproduction claim.

Read the [short audit](CLAIM-AUDIT.md) first. It begins with the strongest reasonable interpretation, identifies a consequential protocol distinction, and proposes the smallest follow-up that could resolve the remaining uncertainty. The [source trail](SEARCH-AND-READING.md) records exact date-bounded queries, versions, reading depth, artifact inspection and failed access attempts.

The local check compares two explicit statistical acceptance rules over all 441 possible pairs of success counts. At nineteen successes in each twenty-case group, the split-rule endpoint is 0.854481 and the pooled-rule endpoint is 0.834958. Against a threshold of 0.85, their decisions differ. These are our calculator outputs; they are not the source authors' raw candidate outcomes.

| Open | What it establishes |
|---|---|
| [Declared protocol](PROTOCOL.md) | One bounded numerical check; no source-system execution |
| [All count pairs](ALL-COUNT-PAIRS.csv) and [disagreement](RULE-DISAGREEMENTS.csv) | Exact numeric inputs, endpoints and decisions |
| [Six checks](CHECKS.csv), [result](RESULT.md), [command exit](COMMAND-OUTPUT.txt) and [runtime](RUN.md) | Executed arithmetic and its cost boundary |
| [Repository identity](REPOSITORY-IDENTITY.md), [tree](REPOSITORY-TREE.csv) and [inspected-file metadata](REPOSITORY-READS.csv) | Pinned read-only artifact inspection, not package execution |
| [Lab note](LAB-NOTE.md) and [progress](PROGRESS.md) | Interpretation, unattempted learner/peer checks and next step |

The useful distinction is simple: agreement on one set of records is weaker than equality of two rules. Finding a possible disagreement does not prove that the authors' actual records contain it. The proposed follow-up therefore asks for the versioned records and recomputes both decisions, without new model sampling.

The existing [source-audit illustration](../../../assets/illustrations/capstone-audit-v1.png) was inspected and preserved. It maps cleanly to this activity: versioned source, traced claim, focused check. No image was generated. Two attempts to inspect PDF screenshots failed; the reading record relies on successful primary text access instead.

The [manifest](MANIFEST.csv) preserves fifteen original files, each copied with a matching SHA-256 hash. This README was added afterward and is outside that original manifest. The [calculator source](check-admission-rules.mjs) and [maintained copy](../../../../how-did-i-generate-it/rsi/scripts/check-admission-rules.mjs) are agent implementation artifacts; students use the tutor and ordinary language.
