---
name: adult-income-loop
description: Train a classifier for the Adult income problem by running the counted loop in loop.json over recipes.json. Use when the pack has loop.json and no memory file.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Loop harness: the loop is a file

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space, the budget and the test rule. 4. `loop.json`: the loop. 5. `recipes.json`: what the loop iterates over.
Nothing else is read. `loop_log.jsonl` is written and never read: no tool reads it.

## Procedure
Run `loop.json` exactly as written:
1. Call `load_splits` once.
2. `counted_while` with counter `t` from 0 to `N` - 1: the body fits `recipes[t]` with `fit_recipe`, then writes one audit line with `write_loop_log` (`t`, the recipe, the val_score). An error still counts: `t` advances.
3. `exit`: when the fit result says `FREEZE`, pick the highest `val_score`, call `score_test` once with it, after FREEZE, then `save_model`.
4. Answer in text with the best val_score, the test score and the fits used. Stop.

## Rules
The `illegal` list of `loop.json` is binding: do not change `N`, do not reorder the recipes, do not open a second loop, never call `score_test` before FREEZE, never write `memory.json`. The tools refuse the ones they can see; the rest you refuse yourself.

## Done when
`t` reached `N`, `score_test` was called once and `save_model` once.
