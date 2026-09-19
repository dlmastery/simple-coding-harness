---
name: adult-income-actor
description: RSIAgent's actor - run the experiments the planner wrote into plan.json under a 24-fit budget, proposing nothing of your own; the memory is frozen while you run and the verifier writes after your score. Use in rsi/step_11_rsi_agent, for the memory arm of a curriculum problem (the control arm walks the static list).
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# RSIAgent's actor: proposes nothing of its own, runs the plan

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income-actor` (`P`); the planner is
`.claude/skills/adult-income-planner` (`C`); the task file is `T`. Every
command takes `--arm memory` (the default) or `--arm control`, and `--seed <s>`
when the curriculum skill names a seed.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`. 4. `memory.schema.json` and `memory.json`: the cards, frozen while you run - no card lands before `score_test`. 5. `plan.json`: the experiments, in order. 6. `eval.md`.

## Procedure
1. Open the arm:
   memory arm: `python ../tools/load_splits.py --pack P --task T`
   control arm: `python ../tools/load_splits.py --pack P --task T --arm control --memory off`, then walk the static list in one call - `python ../tools/fit_recipe.py --pack P --task T --arm control --recipes @P/schema.json` - and go to step 4.
2. Ask the planner for the broad phase: follow `C/SKILL.md` (it writes `P/plan.json`). Then fit the plan's experiments, in order, in one call:
   `python ../tools/fit_recipe.py --pack P --task T --recipes @P/plan.json`
3. When the plan runs dry and fits remain, follow `C/SKILL.md` again for the deep phase (it rewrites `P/plan.json` from your fits so far), then fit that plan the same way. Repeat until a result says `FREEZE`.
4. Pick the recipe with the highest `val_score` over the arm's fits, then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
5. `python ../tools/scorecard.py --pack P --task T [--arm control]` and answer in text with the arm, the phases run, the best val_score, the test score and the fits used. Stop.

## Rules
- You propose no recipe of your own: every memory-arm fit is an experiment from `plan.json`. Never edit `plan.json` yourself; only `write_plan.py`, run for the planner, writes it.
- Never run `score_test.py` before FREEZE, never twice. Never write a card: the memory is frozen until the verifier's turn, after your score.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`: you ignore `plan.json` and walk `schema.json` -> `recipes` in order - lesson 01's control arm, same 24 fits.

## Done when
`score_test.py` answered once for the arm.
