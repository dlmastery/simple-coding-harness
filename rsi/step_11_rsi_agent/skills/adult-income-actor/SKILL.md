---
name: adult-income-actor
description: Run the experiments the curriculum pack wrote into plan.json, one fit each, under the 24-fit budget; score the test split once after FREEZE. Use when plan.json exists and a curriculum pack is choosing the experiments.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# RSIAgent's actor: proposes nothing of its own, runs the plan

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`. 4. `memory.schema.json` and `memory.json`: the cards, frozen while you run - no card lands before `score_test`. 5. `plan.json`: the experiments, in order. 6. `eval.md`.

## Procedure
1. Call `load_splits` once.
2. Fit the experiments of `plan.json` in order with `fit_recipe`, one call each.
3. When the plan runs dry and fits remain, call `read_pack` to re-read `plan.json`: the curriculum pack may have written the next phase. If there is nothing new, answer in text that the plan is exhausted and wait; the harness resumes you when the plan changes.
4. When a fit result says `FREEZE`, pick the highest `val_score`. Call `score_test` once with it, after FREEZE, then `save_model`.
5. Answer in text with the best val_score, the test score and the fits used. Stop.

## Rules
- You propose no recipe of your own: every fit is an experiment from `plan.json`.
- Never call `score_test` before FREEZE, never twice. Never write a card; the memory is frozen until the verifier's turn.

## Off switch
MEMORY_OFF: the harness does not load `memory.json`; you ignore `plan.json` and walk `schema.json` -> `recipes` in order - lesson 01's control arm, same 24 fits.

## Done when
`score_test` was called once and `save_model` once.
