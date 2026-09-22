# Remove duplicate work while keeping the check

[Lab 10.30](../../../10_research_studio/09_efficient_harnesses/step_30_cost_quality/README.md) compares two reporting variants around the same regression and classification recipes. Four real fits ran. Both task pairs produced identical prediction files and passed the predeclared quality floor.

| Task | Quality in both variants | H0 summary calls | H1 summary calls |
|---|---|---:|---:|
| Bike regression | MAE 99.175924 | 3 | 1 |
| Wine classification | Balanced accuracy 0.744955; recalls 0.733813 and 0.756098 | 3 | 1 |

H1 removes two identical derived reports per task. It retains the model result, predictions, prediction check, and one complete summary. The [paired decision](COMPARISON.csv) retains H1 under the fixed rule. The [checker-removal counterexample](stub/QUALITY.md) fails: a supplied stub score cannot replace missing evidence.

Read the [quality and cost contract](QUALITY-COST.md), [proposal](PROPOSAL.md), [measured outcomes](OUTCOMES.csv), [command ledger](COMMANDS.csv), [cost boundaries](COST.md), and [interpretation](INTERPRETATION.md). Report bytes measure only the added summaries. The one-shot wall times and unknown inference/design costs do not justify a broad speed or total-cost claim.

Inspect a [bike summary](H1/bike/report-1.md), [wine summary](H1/wine/report-1.md), and the [wine prediction check](H1/wine/experiment/trial-001/CHECK.md). [H0](H0.md) and [H1](H1.md) differ only in duplicate summary work. The [SoL-Pi audit](SOURCE-AUDIT.md) and [VideoHarness cost comparison](CONTEXT-COST-COMPARISON.md) distinguish this local exercise from the source mechanisms and from recursive compounding.

The [manifest](MANIFEST.csv) preserves 85 original files, checked against the sibling workspace and this archive. The manifest itself and this guide are publication additions. [Inputs and procedures](FROZEN.csv), raw tool sources, every subprocess output, rejected stub, and learner [assessment limits](LAB-NOTE.md) remain inspectable. No process is running and the four-fit budget is exhausted.

Start a new learner run through the lesson's natural-language prompt. The agent can use the canonical [execution driver](../../../../how-did-i-generate-it/rsi/scripts/run-efficient-harnesses.mjs) in a new sibling workspace. This deterministic report-consolidation example uses the shared course runtime; it is not an autonomous harness-search system.
