---
name: adult-income-regular
description: Train a classifier for the Adult income problem by walking a fixed list of 24 recipes. Use when the task is adult_income and the pack has no loop, graph or memory file.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Regular harness: the same trainer, every run

## Boot order
1. This file. 2. `tools.md`: the only tools you may call. 3. `schema.json`: the task, the budget and the 24 recipes.
Nothing else is read. Nothing is written except the model file.

## Procedure
1. Call `load_splits` once.
2. The first recipe of `schema.json` -> `recipes` is the baseline. Call `fit_recipe` on every recipe of the list, in order, one call per recipe. That is 24 fits: the budget. A 25th is refused.
3. When a fit result says `FREEZE` (`fits_left` is 0), pick the recipe with the highest `val_score`.
4. Call `score_test` once with that recipe, after FREEZE. Then call `save_model` with it.
5. Answer in text: the best val_score, the test score and the number of fits. Stop.

## Rules
- Propose only recipes that appear in `schema.json`. Never invent a field or a value.
- Never call `score_test` before FREEZE, and never twice.
- Do not read or write any other file. The next run boots this same text.

## Done when
`score_test` has been called once and `save_model` once.
