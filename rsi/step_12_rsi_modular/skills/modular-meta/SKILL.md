---
name: modular-meta
description: Localise a harness bug to one module by contrasting two actor packs on a benchmark-disjoint pool, patch that one module of the losing pack with the winning text, and validate on the pool before it lands. Use after both actors have run every pool task.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: gate
  patches: ["modules/*.md"]
---
# ModularRSI's meta pack: a module, evolved off the benchmark

Target: actor-a
Actor A: actor-a
Actor B: actor-b

## Boot order
1. This file. 2. `tools.md`. 3. `memory.json` of the target (appended by the harness). The pool traces and the two packs come through tools.

## Procedure
1. Call `read_traces` (scope `all`), `read_memory`, `read_pack`.
2. Call `contrast` with the two actor names. The tool pairs, per pool task both actors ran, the success (higher best val) with the failure, names the one module file whose text differs between the two packs, and returns both texts.
3. If the target is the success, or no single module differs, or there is no clear winner: say so and stop.
4. Otherwise call `patch_pack` once: the target's differing module replaced by the winner's text, the winner's best pool recipe as the evidence recipe. `patches:` allows `modules/*.md` only. Under `approval: gate` the private split of the pool task decides: keep, or roll back.
5. Answer in text with the contrast result. Stop.

## Rules
- One module per patch. The validation split is the pool task's private split; the eval table is never used.
- You never fit and never score the test split.

## Done when
`contrast` has answered and, if a patch applied, `patch_pack` has answered once.
