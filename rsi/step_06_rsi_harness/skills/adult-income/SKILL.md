---
name: adult-income
description: Train a classifier for a curriculum problem under a 24-fit budget, proposing one recipe at a time shaped by the memory cards. Use when the pack has memory.json and a verifier pack writes to it.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# RSI harness: the inner pack (the actor)

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space and the budget. 4. `memory.schema.json`: what a card is.
5. `memory.json`: the cards, unless the harness says MEMORY_OFF - then there are none and you search as if the file were empty.
The trace log is not in your prompt; the verifier reads it, you do not.

## Procedure
1. Call `load_splits` once and keep the profile it returns.
2. For t in 1..24: read the cards that apply (an `if` the profile satisfies, `evidence` >= 2, `counter` < `evidence`), propose ONE recipe from `schema.json` -> `fields`, and call `fit_recipe`. A recipe a forbid card rules out is refused by the tool and costs no fit; do not propose it again.
   Search policy: obey-memory
   (obey-memory: order the grid by how many applicable prefer cards a recipe satisfies; ties in the order of `schema.json` -> `recipes`, then the rest of the grid. With no applicable card that is the static order.)
3. When a fit result says `FREEZE`, pick the recipe with the highest `val_score`. Call `score_test` once with it, after FREEZE, then `save_model`.
4. Answer in text with the best val_score, the test score and the fits used. Stop.

## Rules
- One recipe per `fit_recipe` call, always from the schema. Never invent a value.
- Never call `score_test` before FREEZE, never twice.
- Never write a card: that is the verifier's job and `write_card` is not in your tools.md. Only a meta pack may patch this pack.

## Off switch
MEMORY_OFF: the harness does not load `memory.json`; you run the static order. Same 24 fits, so the numbers can be compared.

## Done when
`score_test` was called once and `save_model` once.
