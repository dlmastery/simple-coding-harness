# A process becomes a reusable skill

This author walkthrough fills the trace and extension gaps in labs 01.01–01.03. Two new one-fit executions produce byte-identical predictions to the historical baseline. Each follows five recorded actions: frame, inspect, split, fit and check. There is no search or final evaluation.

| Lesson activity | Inspect the evidence |
|---|---|
| 01.01: define observable actions | [Process](PROCESS.md) names inputs, products and completion checks |
| 01.01: trace a result backward | [Gap review](GAP-REVIEW.md) connects source row 8645 to target, inputs, split and MAE |
| 01.01: move split design after fitting | [Counterexample](GAP-REVIEW.md#put-split-design-after-fitting-a-counterexample) explains selection bias; no contaminated fit is implied |
| 01.02: execute the fixed process | [Actual trace](01-02/TRACE.md), [timed rows](01-02/TRACE.csv), [fit command](01-02/fit-command.txt), [prediction check](01-02/trial-001/CHECK.md) |
| 01.02: compare runs and diagnose a missing report | [Repeatability](REPEATABILITY.md), [comparison values](COMPARISON.csv), [missing-report diagnosis](MISSING-REPORT-DIAGNOSIS.md) |
| 01.03: save and use a skill | [Baseline skill](BASELINE-SKILL.md), [instruction-to-action record](01-03/DECISION.md), [actual trace](01-03/TRACE.md), [checked result](01-03/trial-001/CHECK.md) |
| 01.03: remove ambiguity | [Ambiguous copy](AMBIGUOUS-SKILL.md), [two readings](AMBIGUITY-REVIEW.md), [repaired text](REPAIRED-SKILL.md); these variants were not executed |

All three compared prediction files have the same hash and MAE 159.94791188618632. The current source tool and one-attempt contracts differ from the older tool and shared twelve-attempt ceiling. [The comparison](REPEATABILITY.md) explains the difference rather than claiming identical software histories.

The [protocol](PROTOCOL.md) precedes execution. [Six artifact checks](CHECKS.csv), [source identities](INPUT-IDENTITIES.csv), [environment](ENVIRONMENT.md), [review and costs](REVIEW.md), and [manifest](MANIFEST.csv) preserve the boundary. Fresh output folders share the existing dependency environment and author context. Learner assessment, independent contexts and autonomous improvement remain untested.

The missing-report directory contains copied artifacts, not another execution. Its original report is preserved as [REMOVED-REPORT.md](REMOVED-REPORT.md). Do not count that copy as a third fit. This navigation page was added after sealing the original files.
