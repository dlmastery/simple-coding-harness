---
name: meta-evolver
description: The slow loop of MetaSkill-Evolve - every k problems, propose one change to one meta-skill file (roles/*.md) of the task-skills-meta pack, by the same evidence pipeline, and land it only with the human's y. Use on the slow clock, never after every problem.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: human
  patches: ["roles/*.md"]
---
# The slow loop: the improver's own skills, rarely, with a human

## Boot order
1. This file. 2. `tools.md`. The target is the `task-skills-meta` pack: its `roles/*.md` come through `read_pack`.

## Procedure
1. Call `read_traces` (scope `all`), `read_memory`, `read_pack`.
2. Judge the fast loop by the same evidence it uses: the number of active cards the last k problems added, and whether the memory arm's best val beat the control's on them. If the fast loop is adding cards but the gap is not growing, raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster); if the policy line is still `static` after k problems, lower `Policy flip threshold` in `roles/allocator.md` by one. One file, one line.
3. Call `patch_pack` once with that role file. `approval: human`: the human sees the diff and answers y / n / edit; nothing lands on `n`. `patches:` allows `roles/*.md` only.
4. Answer in text with the change and the decision. Stop.

## Rules
- Only on the slow clock (the runner boots this pack every k problems), only one role file per visit, only with the human.
- You never fit, never score the test split, never touch the actor pack.

## Done when
`patch_pack` has answered once, or there was nothing to change.
