---
name: adult-income-meta-gate
description: Improve the actor pack between two curriculum problems - one patch per visit to its search-policy line, its schema.json forbid list or its memory cards - and put it through the private gate - keep-or-rollback on a split the actor never sees. Use after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: gate
---
# The RSI meta harness: a pack that patches the pack

## Boot order
1. This file. 2. `tools.md`. 3. `memory.json` of the actor pack (appended by the harness). The trace and the pack come through tools.

## Procedure
1. Call `read_traces` with scope `all`, then `read_memory`, then `read_pack`: the whole log, the cards, every file of the actor pack.
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change the line to `obey-memory`.
   b. A field value lost every comparison one field apart it was in, at least three times across the log, and never won: add `{"field": ..., "value": ...}` to `schema.json` -> `forbid`. (`hyper` values are excluded: they belong to one model each.)
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet; merge at most three of them into `memory.json`.
3. Call `patch_pack` once with the changed files (`{path: {after: text}}`), the evidence recipe (the best val recipe of the last problem) and a one-line summary. Under `approval: human` the human answers y / n / edit; under `approval: gate` the private split decides keep-or-rollback. Either way the tool snapshots the pack under `versions/` first.
4. Answer in text with the tool's result. Stop.

## Rules
- One proposal per visit; the tool refuses a second.
- A patch changes at most 20 % of the pack's text and never removes the test rule from `SKILL.md`; the tool refuses more.
- You never fit, never score the test split, never touch the verifier pack or `eval.md`.

## Off switch
META_OFF: the runner does not boot this pack; the actor pack stays byte-identical between problems.

## Done when
`patch_pack` has answered once.
