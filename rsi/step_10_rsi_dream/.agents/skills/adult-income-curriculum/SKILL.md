---
name: adult-income-curriculum
description: Run the actor pack adult-income over the six curriculum problems in order with the verifier writing after each and the Dream-RSI meta pack adult-income-meta-dream ranking search policies on the log between problems; print the learning curve, then run the frozen pack on the exam over five seeds and print the exam report. Use in rsi/step_10_rsi_dream.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

You orchestrate; the scripts measure. Run every command through the Bash
tool from this lesson's directory. The actor pack is
`.claude/skills/adult-income` (`P`), the verifier pack
`.claude/skills/adult-income-verifier` (`V`); the meta pack is
`.claude/skills/adult-income-meta-dream` (`M`, approval: gate); the curriculum is
`../tasks/01_adult_income.json` .. `../tasks/06_synth_shift_b.json`, in
that order, and the exam is `../tasks/07_exam.json`.

## Boot order
1. This file. 2. `P/eval.md`: how the pack is judged. 3. `P/SKILL.md`, `V/SKILL.md` and `M/SKILL.md`: the procedures you follow for each arm, for the verifier and for the meta visit. Re-read `P/SKILL.md` before every memory arm: a meta visit may have changed its `Search policy:` line, and the next generation boots what the last one wrote.

## Procedure
1. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open the arm, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open, `read_memory.py --order obey-memory` for the next recipes, fit them, repeat until FREEZE, score once, scorecard).
   c. Verifier: follow `V/SKILL.md` on `T` (the tally, then the cards, written with `--as V`).
   d. Meta visit: follow `M/SKILL.md` on `T` with `--visit <n>` (`n` = the problem's index): rank the policies on the log with zero fits, and if the winner differs from the actor's line, propose it; the private gate decides. With `{"meta": "off"}` in `M/config.json` the script proposes nothing (META_OFF).
   Do not run `save_model.py` in this lesson; the models are not the deliverable.
2. The learning curve:
   `python ../tools/curve.py --pack P --tasks ../tasks`
   Show the `table`. The claim of `eval.md`: `gap_val` never negative, larger on problem 6 than on problem 2.
3. The exam, on `../tasks/07_exam.json`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off --freeze-memory`, then the memory arm with `--seed s --freeze-memory` (both as in step 1, with `--seed s` on every command). No verifier: the memory is frozen and `write_card.py` refuses.
4. The exam report:
   `python ../tools/exam.py --pack P --task ../tasks/07_exam.json --seeds 0,1,2,3,4`
   Show the `table`: wins out of 5, the mean test gap, the cards that did not transfer, `pack_unchanged` and `no_card_written` (both must be true).
5. `python ../tools/read_pack.py --pack P --checksums` lists the versions under `runs/adult-income/versions/`: one `gen_NNN` per patch that was proposed, kept or rolled back.
6. Answer in text with the curve table, the exam table, the list of meta decisions (problem, proposal, decision, version) and one sentence per claim of `eval.md` saying whether it held. Stop.

## Rules
- The same budget on both arms of every problem; the test split scored once per arm, after FREEZE.
- You never edit `memory.json`, `schema.json`, `SKILL.md` or any pack file yourself: the verifier writes cards through `write_card.py`, the meta pack patches through `patch_pack.py`, and nothing else changes the pack.
- Report the numbers the scripts print, including a claim that did not hold.

## Done when
`curve.json` and `exam.json` exist under `runs/adult-income/` and both tables were shown.
