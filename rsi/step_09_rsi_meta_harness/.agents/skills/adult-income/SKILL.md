---
name: adult-income
description: "Train a classifier for a curriculum problem under a 24-fit budget, proposing recipes shaped by the memory cards in memory.json (the memory arm), or walking the static list with the memory off (the control arm), with helpers you build from the contracts in tools.md. Use in rsi/step_09_rsi_meta_harness, when the pack has memory.json, a verifier writes to it and a meta pack patches its Search policy line, its schema.json forbid list or its cards."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# RSI harness: the inner pack (the actor)

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/adult-income` (`P`); the problem's directory is `T` (for example
`../tasks/01_adult_income`); the arm is `memory` (the default) or `control`, and a lesson may
name another (`memory-r2`, a seed). Every helper prints one JSON object; an `error` key is a
refusal you read.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space (`fields`), the budget and the static list (`recipes`). 4. `memory.schema.json`: what a card is. 5. `config.md`: the off switches. 6. `memory.json`: the cards - unless the arm is the control arm (`--memory off`) or `config.md` says `memory: off`; then there are none and you search as if the file were empty. 7. `T/intent.md`.
The trace log is not yours to read: the verifier reads it, you do not.

## Procedure
1. Build the helpers of `tools.md` under `runs/adult-income/helpers/` if they are not there yet.
2. Open the arm and keep the profile and the applicable cards it prints:
   control arm: `load_splits P T --arm control --memory off`; memory arm: `load_splits P T --arm memory` (the seed with `--seed <s>` when the lesson names one).
3. Search, until a result says `FREEZE`, under the policy the line below names - the one line of this file a meta pack may patch:
   Search policy: static
   - `static`: walk `schema.json -> recipes` in order, in one call, cards or no cards.
   - `obey-memory`: no applicable card - the static walk; otherwise take, per field, the `preferred` value `read_memory` prints and, in calls of up to eight recipes until `FREEZE`: a. the probe, one recipe per model, the preferred model first, with the preferred `scale` / `encode` / `class_weight` (defaults `yes` / `onehot` / `none`) at the middle hyper value; b. the probe winner's family - static recipes, then hyper variants, the recipes carrying the most preferred values first (`class_weight` and `encode` count 2, `scale` and `hyper` 1), then grid order; c. the rest of the grid in grid order. Skip a fitted recipe; a forbidden one is refused and costs no fit. `read_memory P T --arm memory --order obey-memory` prints the next eight.
   `fit_recipe P T --arm <arm> --recipes <the list>`.
4. When a result says `FREEZE`, pick the recipe with the highest `val_score` over the arm's fits, then, after FREEZE: `score_test P T --arm <arm> --recipe <that recipe>`; in a lesson whose curriculum skill does not say otherwise, `save_model` too.
5. `scorecard P T --arm <arm>` and answer in text with the arm, the best val_score, the test score, the fits used and the wasted fits. Stop.

## Rules
- Recipes come from `schema.json -> fields` only. Never invent a value; `fit_recipe` refuses one.
- Never run `score_test` before FREEZE, never twice.
- Never write a card: that is the verifier's job, and `write_card` is forbidden to this pack. Only a meta pack may patch this pack - its `Search policy:` line, the `forbid` list of `schema.json`, the cards of `memory.json` - and every patch is snapshotted under `runs/adult-income/versions/` first, so `rollback` can undo it.
- The two arms share the helper, the seed, the split and the budget: that is what makes the comparison mean something.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `memory: off` in `config.md`. No card is read or written; you run the static order. Same 24 fits, so the numbers can be compared - and must be equal to the control arm's.

## Done when
`score_test` answered once for the arm.
