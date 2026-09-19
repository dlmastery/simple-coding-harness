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
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space and the budget. 4. `loop.json`: the counted loop; its `policy` field mirrors the `Search policy:` line below. 5. `memory.schema.json`: what a card is.
5. `memory.json`: the cards, unless the harness says MEMORY_OFF - then there are none and you search as if the file were empty.
The trace log is not in your prompt; the verifier reads it, you do not.

## Procedure
1. Call `load_splits` once and keep the profile it returns.
2. For t in 1..24: read the cards that apply (an `if` the profile satisfies, `evidence` >= 1, `counter` at most half the `evidence`), propose ONE recipe from `schema.json` -> `fields`, and call `fit_recipe`. A recipe a forbid card rules out is refused by the tool and costs no fit; do not propose it again.
   Search policy: static
   (policies: `static` walks `schema.json` -> `recipes` in order, cards or no cards; `obey-memory` is the card-shaped order below. Only a meta pack may change this line.)
   (obey-memory: with no applicable card, walk `schema.json` -> `recipes` in order. Otherwise take, per field, the applicable prefer card with the most evidence minus counter as the preferred value - a tie is no preference. Probe first: one fit per model, the believed model first, each with the preferred `scale` / `encode` / `class_weight` (defaults `yes` / `onehot` / `none`) at its middle hyper value. The probe winner is the model belief. Then walk the grid of `fields` in this order: the believed model's family first; inside a family the recipes of `recipes` (middle hyper value) before the hyper variants; inside those, the weighted count of preferred values a recipe carries - `class_weight` 2, `encode` 2, `scale` 1, `hyper` 1 - highest first; then grid order.)
3. When a fit result says `FREEZE`, pick the recipe with the highest `val_score`. Call `score_test` once with it, after FREEZE, then `save_model`.
4. Answer in text with the best val_score, the test score and the fits used. Stop.

## Rules
- One recipe per `fit_recipe` call, always from the schema. Never invent a value.
- Never call `score_test` before FREEZE, never twice.
- Never write a card: that is the verifier's job and `write_card` is not in your tools.md. Only a meta pack may rewrite this pack - and in this lesson only this file and `loop.json`, the harness source - one generation deep, from a parent chosen in the archive, behind the private gate and the human.

## Off switch
MEMORY_OFF: the harness does not load `memory.json`; you run the static order. Same 24 fits, so the numbers can be compared.

## Done when
`score_test` was called once and `save_model` once.
