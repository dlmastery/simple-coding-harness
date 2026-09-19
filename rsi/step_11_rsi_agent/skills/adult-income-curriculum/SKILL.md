---
name: adult-income-curriculum
description: Choose the actor's next experiments by uncertainty - a broad phase that touches every model family, then a deep phase that goes where the faults are - and write them to the actor's plan.json. Use before the actor's first fit on a problem and again when its plan runs dry.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# RSIAgent's curriculum: the next experiment, chosen on purpose

## Boot order
1. This file. 2. `tools.md`. The actor's fits so far come through `read_traces`; the plan goes out through `write_plan`.

## Procedure
1. Call `read_traces` with scope `problem`, then `read_memory`. No rows yet: this is the broad phase. Rows: the deep phase.
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far, `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline), and `c` is the phase's exploration weight:
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
   In the broad phase every family starts equal and the large `c` makes the plan round-robin: every family is touched before any is repeated. In the deep phase the small `c` lets `1 - success` dominate: the family with the most faults (fits below the baseline, or errors) comes first.
3. Build the plan greedily: 12 times, take the family with the highest `u` (ties: the family the cards prefer, then schema order), give it its next untried recipe (static recipes before hyper variants; inside those, the recipes carrying the most card-preferred values first), and count that experiment as one more fit for the family.
4. Call `write_plan` once with `{phase, c, experiments}`. Answer in text with the phase and the families in order. Stop.

## Rules
- You never fit and never score. One plan per visit.
- The memory is not yours: the verifier writes cards after the actor's `score_test`, not you.

## Done when
`write_plan` has answered.
