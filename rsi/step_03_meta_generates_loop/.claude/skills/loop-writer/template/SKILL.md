---
name: {{slug}}-loop
description: Train a classifier for {{title}} by running the counted loop in loop.json over recipes.json. Generated from task.json by loop-writer. Use when the pack has loop.json and no memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Loop harness for {{name}}: the loop is a file

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/{{slug}}-loop`; below, `P` stands for
that path and `T` for the task file of {{name}} under `../tasks/`.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space, the budget and the test rule. 4. `loop.json`: the loop. 5. `recipes.json`: what the loop iterates over.
Nothing else is read. `loop_log.jsonl` is written and never read: no script reads it back.

## Procedure
Run `loop.json` exactly as written:
1. `python ../tools/load_splits.py --pack P --task T` once.
2. `counted_while` with counter `t` from 0 to `N` - 1 (`N` is {{n_fits}}): the body fits `recipes[t]` and writes one audit line with `t`, the recipe and the `val_score`. Execute the body for six consecutive values of `t` per pair of commands:
   `python ../tools/fit_recipe.py --pack P --task T --recipes @P/recipes.json --range 0:6`
   `python ../tools/write_loop_log.py --pack P --task T --entries '[{"t": 0, "recipe": {...}, "val_score": ...}, ...]'`
   then the next slices of six, each followed by its log call. An error still counts: `t` advances.
3. `exit`: when the last fit result says `FREEZE`, pick the highest `val_score` ({{metric}}) over all fits, then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
   `python ../tools/save_model.py --pack P --task T --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
4. `python ../tools/scorecard.py --pack P --task T` and answer in text with the best val_score, the test score and the fits used. Stop.

## Rules
The `illegal` list of `loop.json` is binding: do not change `N`, do not reorder the recipes, do not open a second loop, never run `score_test.py` before FREEZE, never write `memory.json`. The scripts refuse the ones they can see; the rest you refuse yourself.

## Done when
`t` reached `N` ({{n_fits}}), `score_test.py` answered once and `save_model.py` once.
