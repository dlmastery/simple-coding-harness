---
name: task-skills-meta
description: "MetaSkill-Evolve's fast loop - improve the actor pack adult-income's task skills (its Search policy line, its schema.json forbid list, its memory cards), one patch per problem under the private gate, following the five role files under roles/ that only the slow loop may rewrite. Use in rsi/step_16_rsi_meta_skills after a problem's actor and verifier runs are done, before the next problem boots."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: gate
  patches: ["SKILL.md", "schema.json", "memory.json"]
---
# The fast loop: task skills, one patch per problem

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/task-skills-meta` (`M`); the target is the actor pack `.claude/skills/adult-income`
(`P`); the problem just finished is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `M/roles/analyzer.md`, `M/roles/retriever.md`, `M/roles/allocator.md`, `M/roles/proposer.md`, `M/roles/evolver.md`: the five meta-skills that say how this pack works. They are files, they carry the numbers this procedure uses, and only the slow loop (`meta-evolver`, with the human) may change them. 4. `M/config.md`. The log, the cards and the actor pack come through helpers.

## Procedure
1. Build `read_traces`, `read_memory`, `read_pack`, `propose`, `gate`, `private_score` and `rollback` under `runs/task-skills-meta/helpers/` if they are not there yet. Read everything a meta pack may see, as `roles/analyzer.md` and `roles/retriever.md` say: `read_traces P T --scope all`, `read_memory P T`, `read_pack P`.
2. Decide ONE change, in the order `roles/allocator.md` gives, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least `Policy flip threshold` (from `roles/allocator.md`) cards are active: change that line to `Search policy: obey-memory` (the whole `SKILL.md`, with that one line changed).
   b. A field value lost every comparison one field apart it was in, at least three times across the whole log, and never won: add `{"field": ..., "value": ...}` to `schema.json -> forbid` (`hyper` values are excluded: they belong to one model each).
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet (`read_traces P T --scope problem --tally` lists `cards_by_rule`); merge at most `Cards per visit` (from `roles/proposer.md`) of them into `memory.json`.
   If none applies, say so and stop: nothing is proposed this visit.
3. Write the changed file(s) - and only those - under `runs/task-skills-meta/patch/` at their paths in the pack (your Write tool), then `propose M T --target adult-income --files runs/task-skills-meta/patch --recipe <the best val recipe of the last problem> --summary "<what and why>" --visit <n>`.
4. `gate M T <id>`: the helper snapshots the actor pack under `runs/adult-income/versions/gen_NNN/`, lands the patch, scores the evidence recipe against the incumbent on the private split and keeps the patch only if it did not score lower; otherwise it restores the snapshot.
5. Answer in text with the proposal id, the gate's numbers, whether it landed and the version label. Nobody is asked. Stop.

## Rules
- One proposal per visit; a patch changes at most 20 % of the pack's text and never removes the test rule.
- You never fit for yourself, never score the test split, never touch the verifier pack, `eval.md` or `roles/`: those are the slow loop's.

## Off switch
META_OFF: `meta: off` in `M/config.md`. Nothing is proposed and the actor pack stays byte-identical between problems.

## Done when
`gate` answered (kept or rolled back), or there was nothing to propose.
