---
name: adult-income-curriculum
description: "Run the actor pack adult-income-actor over the six curriculum problems in order with the verifier writing after each and the adult-income-planner pack visiting between problems (the planner writes the actor's plan.json before the memory arm's first fit (broad) and when it runs dry (deep); the verifier writes after the test is scored, for the next problem); print the learning curve, then run the frozen pack on the exam over five seeds and print the exam report. Use in rsi/step_11_rsi_agent."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

You orchestrate; the helpers measure. Run every helper through the Bash tool from this
lesson's directory. The actor pack is `.claude/skills/adult-income-actor` (`P`), the verifier pack
`.claude/skills/adult-income-verifier` (`V`); the planner pack is `.claude/skills/adult-income-planner` (`C`); the curriculum is `../tasks/01_adult_income` ..
`../tasks/06_synth_shift_b`, in that order, and the exam is `../tasks/07_exam`.

## Boot order
1. This file. 2. `tools.md`. 3. `P/eval.md`: how the pack is judged. 4. `P/SKILL.md`, `C/SKILL.md` and `V/SKILL.md`: the procedures you follow for each arm, for the planner and for the verifier.

## Procedure
1. Build the helpers once: the actor's set under `runs/adult-income-actor/helpers/` (as `P/SKILL.md` says), the verifier's under `runs/adult-income-verifier/helpers/`, and `curve` and `exam` under `runs/adult-income-curriculum/helpers/`. Reuse what exists. A helper may run a whole arm in one call (open, `read_memory --order`, fit, repeat until FREEZE, score once, scorecard) as long as every step writes what its contract says.
2. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open, `read_memory --order <the policy the actor's Search policy line names>` for the next recipes, fit them, repeat until FREEZE, score once, scorecard).
   c. Verifier: follow `V/SKILL.md` on `T` (the tally, then the cards, written with `--as V`).
   Do not run `save_model` in this lesson; the models are not the deliverable.
3. The learning curve: `curve P --tasks ../tasks`. Show the table. The claim of `eval.md`: `gap_val` never negative, larger on problem 6 than on problem 2.
4. The exam, on `../tasks/07_exam`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off`, then the memory arm with `--seed s` (both as in step 2, `--seed s` on every command; the arm directories are `control-s<s>` and `memory-s<s>` for s > 0). No verifier: a card write on the exam problem is refused, and you do not ask for one. Record the sha256 of `P/memory.json` before the first exam arm.
5. The exam report: `exam P ../tasks/07_exam --seeds 0,1,2,3,4`. Show the table: wins out of 5, the mean test gap, the cards that did not transfer, `pack_unchanged` and `no_card_written` (both must be true).
6. Answer in text with the curve table, the exam table, the plans per problem (phase, the families in order) and one sentence per claim of `eval.md` saying whether it held - including a claim that did not. Stop.

## Rules
- The same budget on both arms of every problem; the test split scored once per arm, after FREEZE.
- You never edit `memory.json`, `schema.json`, `SKILL.md` or any pack file yourself: the planner writes `plan.json` through `write_plan`, the verifier writes cards through `write_card`, and nothing else changes the pack.
- Report the numbers the helpers print, including a claim that did not hold. Wine and digits saturate this recipe space; a gap of 0 there is the honest number.

## Off switch
`memory: off` in `P/config.md` turns every memory arm into the control arm; the curve is then all zeros by construction, which is the delete-the-file check.

## Done when
`curve.json` and `exam.json` exist under `runs/adult-income-actor/` and both tables were shown.
