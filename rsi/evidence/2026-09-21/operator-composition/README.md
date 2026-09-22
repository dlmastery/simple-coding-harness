# Order, evidence, and an inherited scheduler

Author walkthrough for lab 10.35, executed on 21 September 2026. The driver exited 0. Every score below is synthetic, not measured model accuracy.

The model stub copies the harness's current format. The fixed evaluator gives 50 points for a compatible harness and 50 for a compatible model. This constructed dependency makes the order visible.

| Check | Actual outcome |
|---|---|
| [Data → harness → model](01-harness-before-model/RESULT.md) | 100 synthetic points |
| [Data → model → harness](02-model-before-harness/RESULT.md), identical start | 50 synthetic points: model copied the old format |
| [Old evidence after harness change](03-stale-evidence/RESULT.md) | Model update rejected; state preserved |
| [Data operator tries to write evaluator](04-forbidden-write/RESULT.md) | Entire patch rejected; state preserved |
| [Saved scheduler on a later task](05-inherited-scheduler/RESULT.md) | Interface check moved harness before model; 100 synthetic points |

The [proposal](PROPOSAL.md) changed one rule. The original scheduler remains in [Q0](scheduler-q0.md); [Q1](scheduler-q1.md) adds a check before model. It passed the [static policy gate](POLICY-GATE.md), was [frozen](POLICY-FREEZE.md), and was actually [loaded when compatibility failed](05-inherited-scheduler/POLICY-USE-2.md). The later task requests format 2, carrying forward the released system's versions and format-1 content. This is an explicit author-constructed task change, not blinded transfer.

That trace supports structural inheritance: the saved revision governed later work. It does not establish a generally better improver. The first comparison contrasts two schedules, while the later task executes Q1 only. The [source audit](SOURCE-AUDIT.md) explains the stronger same-start comparison and the difference between cumulative and per-term gains.

Used: five schedule checks, twelve operator attempts including two rejections, one static policy gate, three synthetic evaluator calls, zero fits. [Actions](ACTIONS.csv) and [operator wall times](COST.csv) are retained. These timings exclude the full authoring process and agent inference cost. No learner prediction, teach-back, or quiz was tested.

See the [protocol](PROTOCOL.md), [frozen contracts](FREEZE.md), [results](RESULTS.md), and maintained [author driver](../../../../how-did-i-generate-it/rsi/scripts/run-operator-composition.mjs). Each attempt has saved before/after state and evidence. All original run files were copied and hash-verified. The manifest covers run files other than itself; this README and source audit were added afterward.
