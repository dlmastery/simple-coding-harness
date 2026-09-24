# A faster proposal does not remove a slow check

[Lab 10.38](../../../10_research_studio/12_evidence_and_open_questions/step_38_economics/README.md) now has an executed calculator and an audit of the course's existing two-generation record. The calculator uses the five synthetic scenarios shown in the lesson's infographic. These are alternatives, not successive generations or forecasts.

| Synthetic scenario | Total minutes | Change from baseline |
|---|---:|---|
| Baseline: 1 proposal + 9 evaluation | 10 | Reference |
| Proposal twice as fast | 9.5 | 5% less time |
| Evaluation twice as fast | 5.5 | 45% less time |
| Faster proposal plus one-minute extra check | 10.5 | 5% more time |
| Faster proposal with costlier verifier | 12.5 | 25% more time |

Execution time is zero only in this calculation, and all stages run in series. Even instant proposals leave nine minutes. Read the [frozen assumptions](PROTOCOL.md), [inputs](SCENARIOS.csv), [outputs](TIMING-RESULTS.csv), and [arithmetic check](ARITHMETIC-CHECK.md). A separate [4, 2, 1 gain example](SYNTHETIC-GAINS.csv) shows rising cumulative gain with shrinking increments; its units are arbitrary.

The [local rate calculation](LOCAL-RATES.csv) uses copied historical results and costs, without running models again. Both paths achieve the same 10.631744 MAE reduction after two generations. The fixed path used 16.686200 recorded fit-process seconds; the improver-comparison path used 32.935724. Both proposed improver revisions were rejected, and the active improver stayed unchanged. Total research cost is unknown, so these are not total-resource efficiency estimates.

The [acceleration audit](ACCELERATION-AUDIT.md) accepts the measured task improvement but finds sustained acceleration unestablished. It separates cumulative gain, per-round gain, throughput, and the cost denominator. The [source-assumption audit](SOURCE-AUDIT.md) identifies the economic-model passages inspected and the optional criticality reading; this calculator implements neither source model.

The [manifest](MANIFEST.csv) contains 18 original files, verified against the sibling workspace and this archive. [Source identities](SOURCES.csv), calculator code, copied lineage, and raw numerical outputs are preserved. The manifest itself and this guide are publication additions. There were no new fits or paid compute jobs; [unknown author costs](COST.md) and [unattempted learner assessment](LAB-NOTE.md) remain explicit.

Use the lesson's natural-language prompt for a new learner run. The agent can run the canonical [calculator](../../../../how-did-i-generate-it/rsi/scripts/run-bottlenecks.mjs) in a new sibling workspace. The separate six-system matrix in lab 10.37 remains pending; this maintainer execution does not claim to complete that prerequisite.
