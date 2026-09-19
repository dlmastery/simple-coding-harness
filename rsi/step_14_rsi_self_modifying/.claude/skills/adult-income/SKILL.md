---
name: adult-income
description: Train a classifier for a curriculum problem under a 24-fit budget, proposing recipes shaped by the memory cards in memory.json (the memory arm), or walking the static list with the memory off (the control arm). Use in rsi/step_14_rsi_self_modifying, when the pack has loop.json and a DGM meta pack may rewrite this file and loop.json.
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
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space (`fields`), the budget and the static list (`recipes`). 4. `loop.json`: the counted loop; its `policy` field mirrors the `Search policy:` line below. 5. `memory.schema.json`: what a card is. `eval.md`: how this pack is judged.
5. `memory.json`: the cards - unless the arm is the control arm (`--memory off`) or `config.json` says `{"memory": "off"}`; then there are none and you search as if the file were empty.
The trace log is not yours: the verifier reads it, you do not.

## Procedure
1. Open the arm and keep the profile and the applicable cards it returns:
   memory arm: `python ../tools/load_splits.py --pack P --task T`
   control arm: `python ../tools/load_splits.py --pack P --task T --arm control --memory off`
2. Search policy - the line below is this pack's search-policy line; only a meta pack may change it, and `python ../tools/read_memory.py --pack P --task T [--arm control] --order <policy>` prints `next`, the next eight recipes the named policy gives from the cards and the arm's fits so far:
   Search policy: static
   - static: walk `schema.json` -> `recipes` in order, in one call (the control arm always does this):
     `python ../tools/fit_recipe.py --pack P --task T [--arm control] --recipes @P/schema.json`
   - obey-memory: with no applicable card, the static order. Otherwise take, per field, the applicable `prefer` card with the most `evidence` minus `counter` as the preferred value (a tie is no preference); probe one recipe per model (the preferred model first, each with the preferred `scale` / `encode` / `class_weight`, defaults `yes` / `onehot` / `none`, at its middle hyper value); the probe winner is the model belief; then that family (its static recipes, then its hyper variants, the recipes carrying the most preferred values first - `class_weight` and `encode` count 2, `scale` and `hyper` 1), then the rest of the grid. In calls of up to eight recipes until a result says `FREEZE`; skip a recipe already fitted; a recipe a `forbid` card or `schema.json` -> `forbid` rules out is refused and costs no fit:
     `python ../tools/fit_recipe.py --pack P --task T --recipes '[{"model": ..., "hyper": ..., "scale": ..., "encode": ..., "class_weight": ...}, ...]'`
   - neighbours-of-top-3: six static fits, then the untried neighbours (one field away) of the three best so far, then the static list.
   - prefer-untried-family: at every step the model family with the fewest fits so far, static recipes before hyper variants.
   Whatever the line says, `read_memory.py --order <that policy>` prints the next eight recipes; fit them in one call and repeat until `FREEZE`.
3. When a result says `FREEZE`, pick the recipe with the highest `val_score` over the arm's fits, then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
   `python ../tools/save_model.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
4. `python ../tools/scorecard.py --pack P --task T [--arm control]` and answer in text with the arm, the best val_score, the test score, the fits used and the wasted fits. Stop.

## Rules
- Recipes come from `schema.json` -> `fields` only. Never invent a value; the script refuses one.
- Never run `score_test.py` before FREEZE, never twice.
- Never write a card: that is the verifier's job, and `write_card` is not in your `tools.md`. Only a meta pack may rewrite this pack - and in this lesson only this file and `loop.json`, the harness source - one generation deep, from a parent chosen in the archive, behind the private gate and the human.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`. No card is read or written; you run the static order. Same 24 fits, so the numbers can be compared.

## Done when
`score_test.py` answered once for the arm and `save_model.py` once.
