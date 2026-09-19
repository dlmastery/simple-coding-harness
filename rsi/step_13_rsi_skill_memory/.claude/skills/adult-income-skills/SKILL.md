---
name: adult-income-skills
description: Recuris's actor - train a classifier for a curriculum problem under a 24-fit budget, with the memory as a skill package (markdown cards under skill-memory/) selected by the situation the working memory names, not by recency. Use in rsi/step_13_rsi_skill_memory when the pack has a skill-memory/ directory.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# Recuris's actor: a working memory, and skill cards chosen by need

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income-skills` (`P`); the task file
is `T`. Commands take `--arm memory` (default) or `--arm control`, and
`--seed <s>` when the curriculum skill names a seed.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `eval.md`. 4. `skill-memory/manifest.yaml` and every card it lists: the experiential memory. 5. `working.md`: what the last run was doing; you rewrite it now.

## Procedure
1. Open the arm: `python ../tools/load_splits.py --pack P --task T` (control arm: `--arm control --memory off`, then walk the static list in one call - `python ../tools/fit_recipe.py --pack P --task T --arm control --recipes @P/schema.json` - and go to step 4).
2. Name the situation. The need tags are `small` (fewer than 1000 rows), `categorical` (any categorical column), `imbalanced` (rarest class under 0.35), `multiclass` (more than two classes); `python ../tools/skill_memory.py --pack P --task T --action tags` prints them from the profile. Then select the cards by need:
   `python ../tools/skill_memory.py --pack P --task T --action need --need <tag,tag,...>`
   The script selects every validated card whose `when` tags all hold for this need - by the situation, never by which card is newest - rewrites `working.md` with the need and the cards, and returns the cards' `then` values as `prefer`.
3. Search policy: obey-memory, with `prefer` as the preferences: probe one recipe per model (the preferred model first, each with the preferred `scale` / `encode` / `class_weight`, defaults `yes` / `onehot` / `none`, at its middle hyper value), then the probe winner's family (static recipes, then hyper variants, the recipes carrying the most preferred values first), then the rest of the grid; in calls of up to eight recipes until a result says `FREEZE`. With no card selected, the static order.
   `python ../tools/fit_recipe.py --pack P --task T --recipes '[{"model": ..., "hyper": ..., "scale": ..., "encode": ..., "class_weight": ...}, ...]'`
4. When a result says `FREEZE`, pick the highest `val_score`, then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
5. `python ../tools/scorecard.py --pack P --task T [--arm control]` and answer in text with the arm, the best val_score, the test score, the fits used and the cards that applied. Stop.

## Rules
- You never update a card: that is the meta pack's move, one card per visit, validated against the log first (`skill_memory.py --action update` refuses to act for this pack).
- Never run `score_test.py` before FREEZE, never twice.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`: you skip step 2 and walk `schema.json` -> `recipes` in order.

## Done when
`score_test.py` answered once for the arm.
