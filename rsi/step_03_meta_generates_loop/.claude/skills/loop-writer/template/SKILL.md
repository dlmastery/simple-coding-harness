---
name: {{task_slug}}-loop
description: Train a classifier for the {{title}} problem by running the counted loop declared in loop.json over recipes.json - 24 fits, a freeze, one test score - with helpers you build from the contracts in tools.md. Use in the lesson that landed it, when the pack has loop.json and no graph or memory file.
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# Loop harness: the loop is a file

Run every helper through the Bash tool from this lesson's directory. This pack's directory
is `.claude/skills/{{task_slug}}-loop` (`P`); the problem is `../tasks/{{task_dir}}` (`T`);
the one arm is `control`.

## Boot order
1. This file. 2. `tools.md`. 3. `loop.json`: the loop - its kind, `N`, the counter, the body, the exit and what is illegal. 4. `recipes.json`: the 24 recipes the counter walks. 5. `schema.json`: the recipe space and the budget. 6. `T/intent.md`.

## Procedure
1. Build the helpers of `tools.md` under `runs/{{task_slug}}-loop/helpers/` if they are not there yet.
2. Open the arm: `load_splits P T --arm control --memory off`.
3. Run the loop exactly as `loop.json` declares it: `kind: counted_while`, the counter `t` from 1 to `N`, and for each `t` the body - the recipe is `recipes.json[t - 1]`, `fit_recipe` fits it (an errored fit still counts: `error_still_counts`), `write_loop_log` appends the audit line. You may fit in four calls of six recipes each (`fit_recipe P T --arm control --recipes <recipes 1-6>`, then 7-12, 13-18, 19-24) and log the six after each call; the counter is `fits_used` in `state.json`, not a number you keep in your head.
4. The exit, in the order `loop.json` lists it: the result says `FREEZE`; `score_test P T --arm control --recipe <best val recipe>` once; `save_model`; `scorecard`.
5. Answer in text with `N`, the best val_score, the test score and the number of loop-log lines. Stop.

## Rules
- Everything under `illegal` in `loop.json` is illegal: do not change `N`, reorder the recipes, open a second loop, score the test before FREEZE, write a memory file, or read `loop.log` back.
- The log is an audit trail and nothing else: no step of this procedure and no helper reads it. Generation n+1 loads the same `loop.json` and makes the same 24 fits. That is why this is not RSI yet.
- Never run `score_test` before FREEZE, never twice: the hook and the helper refuse it.

## Off switch
None: no memory. `loop.json` is `mutable: false` in spirit - a run never changes it, and a test asserts the pack is byte-identical after one.

## Done when
`t` reached `N`, `score_test` answered once, `save_model` once.
