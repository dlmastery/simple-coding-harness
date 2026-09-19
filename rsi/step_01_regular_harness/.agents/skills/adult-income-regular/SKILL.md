---
name: adult-income-regular
description: Train a classifier for the Adult income problem by walking a fixed list of 24 recipes, the same way every run. Use in rsi/step_01_regular_harness, when the task is adult_income and the pack has no loop, graph or memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Regular harness: the same trainer, every run

Run every command through the Bash tool from this lesson's directory. Every
script prints one JSON object; an `error` key is a refusal you read, not a
crash you retry. This pack's directory is `.claude/skills/adult-income-regular`.

## Boot order
1. This file. 2. `tools.md`: the only scripts you may run. 3. `schema.json`: the task, the budget (`n_fits: 24`) and the 24 recipes, in order.
Nothing else is read. Nothing is written except the run state under `runs/` and the model file.

## Procedure
1. Open the arm and read the profile:
   `python ../tools/load_splits.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json`
2. Fit the 24 recipes of `schema.json` -> `recipes`, in order, in one call; the first is the baseline. That is the whole budget: the script counts each fit and refuses a 25th.
   `python ../tools/fit_recipe.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-regular/schema.json`
3. The result's last line says `FREEZE` (`fits_left` is 0). Pick the recipe with the highest `val_score` from `results`.
4. Score it on the locked test split once, after FREEZE, then save it. Write the recipe as `k=v` pairs (no quoting problems in any shell):
   `python ../tools/score_test.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
   `python ../tools/save_model.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
5. Write the scorecard and answer in text with the best val_score, the test score and the number of fits:
   `python ../tools/scorecard.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json`
   Stop.

## Rules
- Fit only the recipes that appear in `schema.json`, in their order. Never invent a field or a value; the script refuses a recipe outside the schema.
- Never run `score_test.py` before FREEZE, and never twice: the hook blocks it and the script refuses it.
- Do not read or write any other file. The next run boots this same text and makes the same 24 fits.

## Done when
`score_test.py` has answered once and `save_model.py` once.
