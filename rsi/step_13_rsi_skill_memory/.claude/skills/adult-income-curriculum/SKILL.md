---
name: adult-income-curriculum
description: Run Recuris's actor pack adult-income-skills over the six curriculum problems in order with the skill-memory meta pack updating one card after each, print the learning curve, then run the frozen pack on the exam problem over five seeds and print the exam report. Use in rsi/step_13_rsi_skill_memory.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

You orchestrate; the scripts measure. Run every command through the Bash
tool from this lesson's directory. The actor pack is
`.claude/skills/adult-income-skills` (`P`), the meta pack
`.claude/skills/skill-memory-meta` (`M`); the curriculum is
`../tasks/01_adult_income.json` .. `../tasks/06_synth_shift_b.json`, in
that order, and the exam is `../tasks/07_exam.json`.

## Boot order
1. This file. 2. `P/eval.md`: how the pack is judged. 3. `P/SKILL.md` and `M/SKILL.md`: the procedures you follow for each arm and for the meta update.

## Procedure
1. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open the arm, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open; the need tags; `skill_memory.py --action need`; fit by the preferences until FREEZE; score once; scorecard).
   c. Meta update: follow `M/SKILL.md` on `T` with `--visit <n>` (`n` = the problem's index): one validated card update, or nothing.
   Do not run `save_model.py` in this lesson; the models are not the deliverable.
2. The learning curve:
   `python ../tools/curve.py --pack P --tasks ../tasks`
   Show the `table`. The claim of `eval.md`: `gap_val` never negative, larger on problem 6 than on problem 2.
3. The exam, on `../tasks/07_exam.json`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off --freeze-memory`, then the memory arm with `--seed s --freeze-memory` (both as in step 1, with `--seed s` on every command). No meta update on the exam: the skill memory stays as the curriculum left it (do not run `M/SKILL.md`).
4. The exam report:
   `python ../tools/exam.py --pack P --task ../tasks/07_exam.json --seeds 0,1,2,3,4`
   Show the `table`: wins out of 5, the mean test gap, the cards that did not transfer, `pack_unchanged` and `no_card_written` (both must be true).
5. Answer in text with the curve table, the exam table, and one sentence per claim of `eval.md` saying whether it held. Stop.

## Rules
- The same budget on both arms of every problem; the test split scored once per arm, after FREEZE.
- You never edit a card, `working.md` or any pack file yourself: cards change through `skill_memory.py --action update`, run for the meta pack, and nothing else changes the pack. The horizon report: after the curriculum, `skill_memory.py --action list` shows each card's `horizon` - the number of problems it was updated on.
- Report the numbers the scripts print, including a claim that did not hold.

## Done when
`curve.json` and `exam.json` exist under `runs/adult-income-skills/` and both tables were shown.
