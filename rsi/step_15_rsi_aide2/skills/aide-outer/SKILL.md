---
name: aide-outer
description: AIDE2's outer loop - rewrite the inner agent's operator text and keep the rewrite only if it beats the previous best across the whole curriculum under one metered budget of fits and tokens. Use after the inner pack has run every curriculum problem once.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: human
  patches: ["operators.md"]
---
# Autoresearch on autoresearch: the outer loop rewrites the researcher

## Boot order
1. This file. 2. `tools.md`. 3. `memory.json` of the inner pack (appended by the harness). The log, the pack and the meter come through tools.

## Procedure
1. Call `read_traces` (scope `all`), `read_memory`, `read_pack`, then `meter` with arm `""`: the fits and tokens spent so far across every problem.
2. Propose ONE rewrite of `operators.md` with `patch_pack`: the `improve` operator changed from expanding the best solution to expanding the top three. Every operator keeps its guard line word for word: `lint_pack` refuses an operator without it and `patch_pack` refuses any other file.
3. Answer in text with the meter reading and the rewrite. Stop. The runner then evaluates the rewrite across every curriculum problem under the same fits budget and keeps it only if it is better on the set after the statistical layer drops outlier successes; otherwise it rolls the operators back.

## Rules
- One rewrite per outer step. The three guards stay in every operator: the anti-overfitting line, the re-run of a suspicious score, the statistical layer.
- You never fit and never score the test split.

## Done when
`patch_pack` has answered once, or the operator already reads as the rewrite would make it.
