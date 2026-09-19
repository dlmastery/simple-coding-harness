---
name: adult-income-planner
description: RSIAgent's curriculum module - choose the actor's next experiments by uncertainty (a broad phase that touches every model family, then a deep phase that goes where the faults are) and write them to the actor's plan.json. Use in rsi/step_11_rsi_agent before the actor's first fit on a problem and again when its plan runs dry.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# RSIAgent's curriculum: the next experiment, chosen on purpose

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income-planner` (`C`); the actor
pack is `.claude/skills/adult-income-actor` (`P`); the task file is `T`.

## Boot order
1. This file. 2. `tools.md`. The actor's fits so far come through `write_plan.py --uncertainty`; the cards through `read_memory.py`; the plan goes out through `write_plan.py`.

## Procedure
1. Read the numbers:
   `python ../tools/write_plan.py --pack C --task T --target P --uncertainty --c <c>`
   `python ../tools/read_memory.py --pack P --task T`
   No fits yet: this is the broad phase, `c` = 2.0. Fits: the deep phase, `c` = 0.25.
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far and `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline). The script prints these per family; check them.
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
   In the broad phase every family starts equal and the large `c` makes the plan round-robin: every family is touched before any is repeated. In the deep phase the small `c` lets `1 - success` dominate: the family with the most faults (fits below the baseline, or errors) comes first.
3. Build the plan greedily: 12 times, take the family with the highest `u` (ties: the family the cards prefer, then schema order), give it its next untried recipe (static recipes of `schema.json` -> `recipes` before hyper variants; inside those, the recipes carrying the most card-preferred values first), and count that experiment as one more fit for the family (recompute `u` with `n + 1` and the same success).
4. Write the plan once:
   `python ../tools/write_plan.py --pack C --task T --target P --plan '{"phase": "broad" | "deep", "c": <c>, "experiments": [ ...12 recipes... ]}'`
   (PowerShell: write the plan to a file and pass `--plan '@plan.json'`.)
5. Answer in text with the phase and the families in order. Stop.

## Rules
- You never fit and never score: `fit_recipe.py` and `score_test.py` are not in your `tools.md`. One plan per visit.
- The memory is not yours: the verifier writes cards after the actor's `score_test`, not you.

## Done when
`write_plan.py` has answered.
