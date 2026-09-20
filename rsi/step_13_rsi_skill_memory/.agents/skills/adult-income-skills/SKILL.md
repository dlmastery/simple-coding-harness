---
name: adult-income-skills
description: "Recuris's actor - train a classifier for a curriculum problem under a 24-fit budget, with the memory as a skill package (markdown cards under skill-memory/) selected by the situation the working memory names, not by recency, with helpers you build from the contracts in tools.md. Use in rsi/step_13_rsi_skill_memory when the pack has a skill-memory/ directory."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# Recuris's actor: a working memory, and skill cards chosen by need

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/adult-income-skills` (`P`); the problem is `T`. Arms are `memory` (default) or
`control`, with `--seed <s>` when the curriculum skill names a seed.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `eval.md`, `config.md`. 4. `skill-memory/manifest.yaml` and every card it lists: the experiential memory. 5. `working.md`: what the last run was doing; you rewrite it now.

## Procedure
1. Build the helpers of `tools.md` under `runs/adult-income-skills/helpers/` if they are not there yet.
2. Open the arm: `load_splits P T` (control arm: `--arm control --memory off`, then walk the static list in one call and go to step 5).
3. Name the situation. The need tags are `small` (fewer than 1000 rows), `categorical` (any categorical column), `imbalanced` (rarest class under 0.35), `multiclass` (more than two classes); `skill_memory P T --action tags` prints them from the profile. Then select the cards by need: `skill_memory P T --action need --need <tag,tag,...>`. The helper selects every validated card whose `when` tags all hold for this need - by the situation, never by which card is newest - rewrites `working.md` with the need and the cards, and prints the cards' `then` values as `prefer`.
4. Search policy: obey-memory, with `prefer` as the preferences: the probe (one recipe per model, the preferred model first, each with the preferred `scale` / `encode` / `class_weight`, defaults `yes` / `onehot` / `none`, at its middle hyper value), then the probe winner's family (static recipes, then hyper variants, the recipes carrying the most preferred values first), then the rest of the grid; in calls of up to eight recipes until a result says `FREEZE`: `fit_recipe P T --recipes <the list>`. With no card selected, the static order.
5. When a result says `FREEZE`, pick the highest `val_score`, then, after FREEZE: `score_test P T [--arm control] --recipe <that recipe>`.
6. `scorecard P T [--arm control]` and answer in text with the arm, the best val_score, the test score, the fits used and the cards that applied. Stop.

## Rules
- You never update a card: that is the meta pack's move, one card per visit, validated against the log first (`skill_memory --action update` refuses for this pack).
- Never run `score_test` before FREEZE, never twice.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `memory: off` in `config.md`: you skip step 3 and walk `schema.json -> recipes` in order.

## Done when
`score_test` answered once for the arm.
