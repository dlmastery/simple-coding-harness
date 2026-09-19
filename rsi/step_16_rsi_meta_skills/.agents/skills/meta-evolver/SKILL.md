---
name: meta-evolver
description: The slow loop of MetaSkill-Evolve - every k problems, propose one change to one meta-skill file (roles/*.md) of the task-skills-meta pack, by the same evidence pipeline, and land it only with the human's approval. Use in rsi/step_16_rsi_meta_skills on the slow clock (k in config.json), never after every problem.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: human
  patches: ["roles/*.md"]
---
# The slow loop: the improver's own skills, rarely, with a human

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/meta-evolver` (`E`); the target is the
fast loop's pack `.claude/skills/task-skills-meta` (`M`) - its `roles/*.md`;
the actor pack is `.claude/skills/adult-income` (`P`); the task file of the
problem just finished is `T`. The clock is `k` in `E/config.json`: this pack
visits after problems `k`, `2k`, ... and never otherwise.

## Boot order
1. This file. 2. `tools.md`. 3. `E/config.json`: the clock. The log, the cards and the fast loop's pack come through scripts.

## Procedure
1. Check the clock: the problem's index must be a multiple of `k`; otherwise say so and stop.
2. Read the evidence the fast loop itself uses:
   `python ../tools/read_traces.py --pack P --task T --scope all`
   `python ../tools/read_memory.py --pack P --task T`
   `python ../tools/read_pack.py --pack M`
   `python ../tools/curve.py --pack P --tasks ../tasks` (the problems run so far; the others are listed as missing)
3. Judge the fast loop by that evidence: the number of active cards the last `k` problems added, and whether the memory arm's best val beat the control's on them. Decide ONE change, one file, one line:
   - the fast loop is adding cards but the gap is not growing: raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster);
   - the actor's policy line is still `static` after `k` problems: lower `Policy flip threshold` in `roles/allocator.md` by one;
   - otherwise nothing: say so and stop.
4. Write the changed role file under `runs/meta-evolver/patch/roles/<file>` (use your Write tool) and propose it:
   `python ../tools/patch_pack.py --pack E --task T --target M --files @runs/meta-evolver/patch --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c> --summary "<role>: <old> -> <new>" --visit <index / k>`
   with the last problem's best val recipe as the evidence recipe. `patches: ["roles/*.md"]`: the script refuses any other file. `approval: human`: show the user the diff, ask **approve / edit / reject**, wait, then
   `python ../tools/patch_pack.py --pack E --task T --target M --proposal <id> --approved "<the user's exact words>"`
   Nothing lands on a no. Every proposal snapshots `M` under `runs/task-skills-meta/versions/gen_NNN/`: the meta pack's version history is a directory you can diff.
5. Answer in text with the change, the decision and the version label. Stop.

## Rules
- Only on the slow clock, only one role file per visit, only with the human. The fast loop's `patch_pack` under the gate never touches `roles/`, and this pack never touches the actor.
- You never fit and never score the test split.

## Done when
`patch_pack.py` answered the second time, or it was not the slow clock, or there was nothing to change.
