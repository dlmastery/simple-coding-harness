---
name: adult-income-curriculum
description: "Run the actor pack adult-income-skills over the six curriculum problems in order with the skill-memory-meta pack visiting between problems (one validated card update per problem, snapshotted; nobody is asked); print the learning curve, then run the frozen pack on the exam over five seeds and print the exam report. Use in rsi/step_13_rsi_skill_memory."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

You orchestrate; the helpers measure. Run every helper through the Bash tool from this
lesson's directory. The actor pack is `.claude/skills/adult-income-skills` (`P`); there is no verifier pack - the meta pack `skill-memory-meta` (`M`) writes the memory; the meta pack is `.claude/skills/skill-memory-meta` (`M`); the curriculum is `../tasks/01_adult_income` ..
`../tasks/06_synth_shift_b`, in that order, and the exam is `../tasks/07_exam`.

## Boot order
1. This file. 2. `tools.md`. 3. `P/eval.md`: how the pack is judged. 4. `P/SKILL.md` and `M/SKILL.md`: the procedures you follow for each arm and for the meta visit. Re-read `P/SKILL.md` before every memory arm: a meta visit may have changed its `Search policy:` line, and the next generation boots what the last one wrote.

## Procedure
1. Build the helpers once: the actor's set under `runs/adult-income-skills/helpers/` (as `P/SKILL.md` says), the meta pack's under `runs/skill-memory-meta/helpers/`, and `curve` and `exam` under `runs/adult-income-curriculum/helpers/`. Reuse what exists. A helper may run a whole arm in one call (open, `read_memory --order`, fit, repeat until FREEZE, score once, scorecard) as long as every step writes what its contract says.
2. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open, `skill_memory --action tags` then `--action need`, obey-memory with the selected cards, fit them, repeat until FREEZE, score once, scorecard).
   d. Meta visit: follow `M/SKILL.md` on `T` with `--visit <n>` (`n` = the problem's index). one validated card update per problem, snapshotted; nobody is asked. With `meta: off` in `M/config.md` nothing is proposed (META_OFF).
   Do not run `save_model` in this lesson; the models are not the deliverable.
3. The learning curve: `curve P --tasks ../tasks`. Show the table. The claim of `eval.md`: `gap_val` never negative, larger on problem 6 than on problem 2.
4. The exam, on `../tasks/07_exam`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off`, then the memory arm with `--seed s` (both as in step 2, `--seed s` on every command; the arm directories are `control-s<s>` and `memory-s<s>` for s > 0). No meta visit: a card update on the exam problem is refused, and you do not ask for one. Record the sha256 of `P/memory.json` before the first exam arm.
5. The exam report: `exam P ../tasks/07_exam --seeds 0,1,2,3,4`. Show the table: wins out of 5, the mean test gap, the cards that did not transfer, `pack_unchanged` and `no_card_written` (both must be true).
6. `read_pack P --checksums` lists the versions under `runs/adult-income-skills/versions/`: one `gen_NNN` per patch that was proposed, kept or rolled back. Answer in text with the curve table, the exam table, the list of meta decisions (problem, proposal, decision, version) and one sentence per claim of `eval.md` saying whether it held - including a claim that did not. Stop.

## Rules
- The same budget on both arms of every problem; the test split scored once per arm, after FREEZE.
- You never edit a card file, `working.md`, `schema.json`, `SKILL.md` or any pack file yourself: the meta pack updates one card through `skill_memory --action update`, and nothing else changes the pack.
- Report the numbers the helpers print, including a claim that did not hold. Wine and digits saturate this recipe space; a gap of 0 there is the honest number.

## Off switch
`memory: off` in `P/config.md` turns every memory arm into the control arm; the curve is then all zeros by construction, which is the delete-the-file check.

## Done when
`curve.json` and `exam.json` exist under `runs/adult-income-skills/` and both tables were shown.
