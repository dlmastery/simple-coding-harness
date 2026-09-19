---
name: adult-income-curriculum
description: Run RSIAgent's actor pack adult-income-actor over the six curriculum problems in order - the planner choosing its experiments, the verifier writing after each - print the learning curve, then run the frozen pack on the exam problem over five seeds and print the exam report. Use in rsi/step_11_rsi_agent.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

You orchestrate; the scripts measure. Run every command through the Bash
tool from this lesson's directory. The actor pack is
`.claude/skills/adult-income-actor` (`P`), the planner `.claude/skills/adult-income-planner` (`C`), the verifier pack
`.claude/skills/adult-income-verifier` (`V`); the curriculum is
`../tasks/01_adult_income.json` .. `../tasks/06_synth_shift_b.json`, in
that order, and the exam is `../tasks/07_exam.json`.

## Boot order
1. This file. 2. `P/eval.md`: how the pack is judged. 3. `P/SKILL.md`, `C/SKILL.md` and `V/SKILL.md`: the procedures you follow for each arm, for the planner and for the verifier.

## Procedure
1. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open the arm, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open; the planner's broad phase, fit it; the planner's deep phase, fit it; score once; scorecard).
   c. Verifier: follow `V/SKILL.md` on `T` (the tally, then the cards, written with `--as V`).
   Do not run `save_model.py` in this lesson; the models are not the deliverable.
2. The learning curve:
   `python ../tools/curve.py --pack P --tasks ../tasks`
   Show the `table`. The claim of `eval.md`: `gap_val` never negative, larger on problem 6 than on problem 2.
3. The exam, on `../tasks/07_exam.json`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off --freeze-memory`, then the memory arm with `--seed s --freeze-memory` (planner and actor as in step 1, with `--seed s` on every command). No verifier: the memory is frozen and `write_card.py` refuses - the transfer table is scored with the memory exactly as the curriculum left it.
4. The exam report:
   `python ../tools/exam.py --pack P --task ../tasks/07_exam.json --seeds 0,1,2,3,4`
   Show the `table`: wins out of 5, the mean test gap, the cards that did not transfer, `pack_unchanged` and `no_card_written` (both must be true).
5. Answer in text with the curve table, the exam table, and one sentence per claim of `eval.md` saying whether it held. Stop.

## Rules
- The same budget on both arms of every problem; the test split scored once per arm, after FREEZE.
- You never edit `memory.json`, `schema.json` or any pack file: the verifier writes cards through `write_card.py`, and nothing else changes the pack.
- Report the numbers the scripts print, including a claim that did not hold.

## Done when
`curve.json` and `exam.json` exist under `runs/adult-income/` and both tables were shown.
