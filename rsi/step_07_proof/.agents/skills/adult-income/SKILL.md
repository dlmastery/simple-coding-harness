---
name: adult-income
description: Train a classifier for a curriculum problem under a 24-fit budget, proposing recipes shaped by the memory cards in memory.json (the memory arm), or walking the static list with the memory off (the control arm). Use in rsi/step_06_rsi_harness and later, when the pack has memory.json and a verifier pack writes to it.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# RSI harness: the inner pack (the actor)

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income` (`P` below); the task file
of the problem you are given is `T` (e.g. `../tasks/01_adult_income.json`).
Every command below takes `--arm memory` (the default) or `--arm control`, and `--seed <s>` when the curriculum skill names a seed.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space (`fields`), the budget and the static list (`recipes`). 4. `memory.schema.json`: what a card is. `eval.md`: how this pack is judged.
5. `memory.json`: the cards - unless the arm is the control arm (`--memory off`) or `config.json` says `{"memory": "off"}`; then there are none and you search as if the file were empty.
The trace log is not yours: the verifier reads it, you do not.

## Procedure
1. Open the arm and keep the profile and the applicable cards it returns:
   memory arm: `python ../tools/load_splits.py --pack P --task T`
   control arm: `python ../tools/load_splits.py --pack P --task T --arm control --memory off`
2. Search policy: obey-memory.
   - No applicable card (every control arm; a memory arm with an empty memory): walk `schema.json` -> `recipes` in order, in one call:
     `python ../tools/fit_recipe.py --pack P --task T [--arm control] --recipes @P/schema.json`
   - Otherwise take, per field, the applicable `prefer` card with the most `evidence` minus `counter` as the preferred value (`python ../tools/read_memory.py --pack P --task T` lists them under `preferred`; a tie is no preference). Then, in calls of up to eight recipes each, in this order until a result says `FREEZE`:
     a. Probe: one recipe per model of `schema.json` -> `models`, the preferred model first, each with the preferred `scale` / `encode` / `class_weight` (defaults `yes` / `onehot` / `none`) at its middle hyper value (`logreg` 1, `rf` 16, `hgb` 0.1). The probe winner is the model belief.
     b. The believed model's family: its recipes from `recipes` (middle hyper value) first, then its hyper variants; inside each group the recipes carrying the most preferred values first (`class_weight` and `encode` count 2, `scale` and `hyper` 1), then grid order.
     c. The rest of the grid of `fields`, grid order (model, hyper, scale, encode, class_weight).
     Skip a recipe already fitted. A recipe a `forbid` card rules out is refused by the script and costs no fit; do not propose it again.
     `python ../tools/read_memory.py --pack P --task T --order obey-memory` prints `next`: the next eight recipes this rule gives, from the cards and the arm's fits so far; check your order against it (or take it).
     `python ../tools/fit_recipe.py --pack P --task T --recipes '[{"model": ..., "hyper": ..., "scale": ..., "encode": ..., "class_weight": ...}, ...]'`
3. When a result says `FREEZE`, pick the recipe with the highest `val_score` over the arm's fits, then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
   `python ../tools/save_model.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
4. `python ../tools/scorecard.py --pack P --task T [--arm control]` and answer in text with the arm, the best val_score, the test score, the fits used and the wasted fits. Stop.

## Rules
- Recipes come from `schema.json` -> `fields` only. Never invent a value; the script refuses one.
- Never run `score_test.py` before FREEZE, never twice.
- Never write a card: that is the verifier's job, and `write_card` is not in your `tools.md`. Only a meta pack may patch this pack.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`. No card is read or written; you run the static order. Same 24 fits, so the numbers can be compared.

## Done when
`score_test.py` answered once for the arm and `save_model.py` once.
