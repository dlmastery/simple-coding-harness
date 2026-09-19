---
name: adult-income-skills
description: Train a classifier for a curriculum problem under a 24-fit budget, with the memory as a skill package - markdown cards selected by the situation the working memory names, not by recency. Use when the pack has a skill-memory/ directory.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# Recuris's actor: a working memory, and skill cards chosen by need

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `eval.md`. 4. `skill-memory/manifest.yaml` and every card it lists: the experiential memory. 5. `working.md`: what the last run was doing; you rewrite it now.

## Procedure
1. Call `load_splits` once and keep the profile.
2. Name the situation: the need tags are `small` (fewer than 1000 rows), `categorical` (any categorical column), `imbalanced` (rarest class under 0.35), `multiclass` (more than two classes). Call `skill_memory` with action `need` and `{need: [tags]}`. The tool selects every validated card whose `when` tags all hold for this need - by the situation, never by which card is newest - rewrites `working.md` with the need and the cards, and returns the cards' `then` values as preferences.
3. For t in 1..24: propose ONE recipe from `schema.json` -> `fields` and call `fit_recipe`.
   Search policy: obey-memory
   (the preferences are the selected cards' `then` values; probe one recipe per model, the preferred model first, then that family - static recipes, then hyper variants - ranked by the preferences, then the rest of the grid. With no card selected, the static order.)
4. When a fit result says `FREEZE`, pick the highest `val_score`, call `score_test` once with it, after FREEZE, then `save_model`.
5. Answer in text with the best val_score, the test score, the fits used and the cards that applied. Stop.

## Rules
- You never update a card: that is the meta pack's move, one card per visit, validated against the log first.
- Never call `score_test` before FREEZE, never twice.

## Off switch
MEMORY_OFF: the harness loads no memory; you skip step 2 and walk `schema.json` -> `recipes` in order.

## Done when
`score_test` was called once and `save_model` once.
