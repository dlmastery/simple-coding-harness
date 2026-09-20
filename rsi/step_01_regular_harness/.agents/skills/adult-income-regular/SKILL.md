---
name: adult-income-regular
description: "Train a classifier for the Adult income problem by walking a fixed list of 24 recipes, the same way every run, with helpers you build from the contracts in tools.md. Use in rsi/step_01_regular_harness, when the task is adult_income and the pack has no loop, graph or memory file."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# Regular harness: the same trainer, every run

Run every helper through the Bash tool from this lesson's directory. This pack's directory
is `.claude/skills/adult-income-regular` (`P` below); the problem is `../tasks/01_adult_income`
(`T`); the one arm is `control`. Every helper prints one JSON object; an `error` key is a
refusal you read, not a crash you retry.

## Boot order
1. This file. 2. `tools.md`: the helpers you build and their contracts. 3. `schema.json`: the task, the budget (`n_fits: 24`), the recipe space (`fields`) and the 24 recipes, in order. 4. `T/intent.md`: the data source and the metric.
Nothing else is read. Nothing is written except the helpers, the run state under `runs/` and the model file.

## Procedure
1. Build the helpers named under `## Allowed` in `tools.md` under `runs/adult-income-regular/helpers/` if they are not there yet (one file per tool, or one module with one function per tool: the names and the contracts are what matters, and the runtime section of `tools.md` says exactly how to read the table, split it and fit a recipe). Reuse them if they exist.
2. Open the arm and keep the profile it prints: `load_splits P T --arm control --memory off`.
3. Fit the 24 recipes of `schema.json -> recipes`, in order, in one call: `fit_recipe P T --arm control --recipes <the list>`. The first is the baseline. That is the whole budget: the helper counts each fit in `state.json` and refuses a 25th.
4. The result says `FREEZE` (`fits_left` is 0). Pick the recipe with the highest `val_score` from `results`.
5. Score it on the locked test split once, after FREEZE, then save it: `score_test P T --arm control --recipe <that recipe>`, then `save_model P T --arm control --recipe <that recipe>`.
6. Write the scorecard - `scorecard P T --arm control` - and answer in text with the best val_score, the test score and the number of fits. Stop.

## Rules
- Fit only the recipes that appear in `schema.json`, in their order. Never invent a field or a value; `fit_recipe` refuses a recipe outside `fields`.
- Never run `score_test` before FREEZE, and never twice: the lesson's hook blocks the command until a `state.json` says `"frozen": true`, and the helper refuses it by reading the state.
- Do not read or write any other file. The next run boots this same text and makes the same 24 fits.

## Off switch
None: this pack has no memory to switch off. It is the control arm every later lesson compares against.

## Done when
`score_test` has answered once and `save_model` once.
