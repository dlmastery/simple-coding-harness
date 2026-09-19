---
name: task-skills-meta
description: Improve the actor pack's task skills - its search-policy line, its schema.json forbid list, its memory cards - one patch per problem under the private gate, following the five role files under roles/ that a slower loop may rewrite. Use after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: gate
---
# The fast loop: task skills, one patch per problem

## Boot order
1. This file. 2. `tools.md`. 3. `roles/*.md`: the five meta-skills - analyzer, retriever, allocator, proposer, evolver - that say how this pack works. They are files, they carry the numbers this procedure uses, and only the slow loop (`meta-evolver`, with the human) may change them. 4. `memory.json` of the actor (appended by the harness).

## Procedure
1. Call `read_traces` (scope `all`), `read_memory`, `read_pack` - the analyzer and retriever roles.
2. Decide ONE change, the first that applies, with the numbers of the allocator and proposer roles:
   a. The actor's `Search policy:` line says `static` and at least `Policy flip threshold` active cards exist: change the line to `obey-memory`.
   b. A field value lost every comparison one field apart it was in, at least three times across the log, and never won: add it to `schema.json` -> `forbid` (`hyper` excluded).
   c. Otherwise: merge at most `Cards per visit` new cards from the last problem's pairs into `memory.json`.
3. Call `patch_pack` once with the changed files, the evidence recipe (the best val recipe of the last problem) and a summary. `approval: gate`: the private split decides keep-or-rollback.
4. Answer in text with the tool's result. Stop.

## Rules
- One proposal per visit; a patch changes at most 20 % of the pack; the test rule stays.
- You never fit, never score the test split, never touch `roles/`: those are the slow loop's.

## Off switch
META_OFF: the runner does not boot this pack.

## Done when
`patch_pack` has answered once, or there was nothing to propose.
