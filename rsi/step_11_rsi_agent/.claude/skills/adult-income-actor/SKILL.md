---
name: adult-income-actor
description: "RSIAgent's actor - train a classifier for a curriculum problem under a 24-fit budget by running the experiments the planner wrote to plan.json (a broad phase, then a deep phase), with the memory frozen before the test is scored; the control arm walks the static list. Use in rsi/step_11_rsi_agent when the pack has plan.json."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# RSI harness: the inner pack (the actor)

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/adult-income-actor` (`P`); the problem's directory is `T` (for example
`../tasks/01_adult_income`); the arm is `memory` (the default) or `control`, and a lesson may
name another (`memory-r2`, a seed). Every helper prints one JSON object; an `error` key is a
refusal you read.

## Boot order
1. This file. 2. `tools.md`. 3. `plan.json`: the experiments the planner chose (empty until it writes). 4. `schema.json`: the recipe space (`fields`), the budget and the static list (`recipes`). 4. `memory.schema.json`: what a card is. 5. `config.md`: the off switches. 6. `memory.json`: the cards - unless the arm is the control arm (`--memory off`) or `config.md` says `memory: off`; then there are none and you search as if the file were empty. 7. `T/intent.md`.
The trace log is not yours to read: the verifier reads it, you do not.

## Procedure
1. Build the helpers of `tools.md` under `runs/adult-income-actor/helpers/` if they are not there yet.
2. Open the arm and keep the profile and the applicable cards it prints:
   control arm: `load_splits P T --arm control --memory off`; memory arm: `load_splits P T --arm memory` (the seed with `--seed <s>` when the lesson names one).
3. Search, in two phases the planner writes:
   - control arm: walk `schema.json -> recipes` in order, in one call.
   - memory arm: ask the planner (`.claude/skills/adult-income-planner/SKILL.md`) for the broad plan; fit the 12 experiments of `plan.json` in order (`fit_recipe P T --arm memory --recipes <the 12>`); ask the planner again for the deep plan; fit its 12. A recipe a `forbid` card rules out is refused and costs no fit. When `plan.json` holds no untried experiment and fits remain, take the static list's next untried recipe. The 24th fit says `FREEZE`.
   Search policy: planned
   Freeze the memory before the test: `freeze_memory P T --arm memory` sets `"memory": "frozen"` in the arm's state; from then on a card write refuses on this arm; the verifier, run afterwards by the curriculum skill, writes to `memory.json` for the *next* problem, never for the arm that was just scored.
4. When a result says `FREEZE`, pick the recipe with the highest `val_score` over the arm's fits, then, after FREEZE: `score_test P T --arm <arm> --recipe <that recipe>`; in a lesson whose curriculum skill does not say otherwise, `save_model` too.
5. `scorecard P T --arm <arm>` and answer in text with the arm, the best val_score, the test score, the fits used and the wasted fits. Stop.

## Rules
- Recipes come from `schema.json -> fields` only. Never invent a value; `fit_recipe` refuses one.
- Never run `score_test` before FREEZE, never twice.
- Never write a card: that is the verifier's job, and `write_card` is forbidden to this pack. Only a meta pack may patch this pack.
- The two arms share the helper, the seed, the split and the budget: that is what makes the comparison mean something.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `memory: off` in `config.md`. No card is read or written; you run the static order. Same 24 fits, so the numbers can be compared - and must be equal to the control arm's.

## Done when
`score_test` answered once for the arm.
