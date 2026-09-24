# Improve the report without changing the builder

[Lab 10.31](../../../10_research_studio/09_efficient_harnesses/step_31_harness_builders/README.md) revises an existing generated wine harness. The original brief asks for both class recalls. The parent reports a correct confusion matrix and balanced accuracy, but leaves the recalls for the reader to calculate.

Two matched executions ran, one fit per arm. The report-only child states both recalls explicitly. Its prediction file is byte-identical to the parent's, and balanced accuracy remains 0.744955.

| Required behavior | Parent | Child |
|---|---|---|
| Predictions agree with source rows and reported metric | [Pass](parent/experiment/trial-001/CHECK.md) | [Pass](child/experiment/trial-001/CHECK.md) |
| Explicit, correct class recalls | [Fail: fields absent](parent/REPORT-CHECK.md) | [Pass](child/REPORT-CHECK.md) |
| Prediction quality | Balanced accuracy 0.744955 | Same score and prediction bytes |

The [child result](child/experiment/trial-001/RESULT.md) gives class-0 recall 0.733813 and class-1 recall 0.756098. This is a reporting repair, not a gain in predictive quality. Read the [observed failure and repair decision](REPAIR-DECISION.md), [component change](child/CHANGE.md), and [comparison](COMPARISON.md).

The [historical builder](BUILDER.md) has SHA-256 `5a1e076b9c58cfed745ee2e29823eb6a090cfa664d974893188996625506a649`, matching the original package's generation record. It was recovered from Git; the [current reference](CURRENT-BUILDER-REFERENCE.md) is a later version. Neither builder ran or changed in this study. The [identity record](BUILDER-IDENTITY.md) and [child provenance addendum](CHILD-PROVENANCE.md) prevent the revised artifact from inheriting a misleading entry-point identity. The child package's inherited PROVENANCE.md still describes its parent generation and must be read with the addendum.

The [two-source map](SOURCE-MAP.md) distinguishes HarnessDev's evolving harness from Harness-of-Harness's evolving software under a fixed agent configuration. The [two-brief builder comparison](BUILDER-COMPARISON-PROPOSAL.md) is a proposed separate experiment, not an executed extension. One repaired artifact does not establish a better generator.

Inspect the [protocol](PROTOCOL.md), [interpretation](INTERPRETATION.md), [cost record](COST.md), and [learner limits](LAB-NOTE.md). Both fits used the shared course runtime in one author context. The historical controller has a two-attempt ceiling, but this study allocated only one fit to each arm and refused repeat arm execution. No independent creator/executor context, fresh-task generator test, or paper reproduction occurred.

The [manifest](MANIFEST.csv) contains 66 original files, checked against both the sibling workspace and this archive. Parent code, child code, source snapshots, frozen identities, commands, predictions, and the failed check remain intact. The manifest itself and this guide are publication additions. Two raw Markdown records put a hash or timing on the next line with a trailing space; narrow per-file attributes preserve those sealed bytes. Their values are also visible in the linked command and identity records.

Start a new run with the lesson's prompt. The canonical [driver](../../../../how-did-i-generate-it/rsi/scripts/run-harness-builder.mjs) prepares, executes the parent, then permits the child only after the report failure. It requires the recorded historical package, Git history, and shared course runtime; it is not a standalone portable builder benchmark.
