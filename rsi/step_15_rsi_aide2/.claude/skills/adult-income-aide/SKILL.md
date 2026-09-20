---
name: adult-income-aide
description: "AIDE2's inner agent - train a classifier for a curriculum problem under a 24-fit budget as an AIDE-style tree search over solutions, with the operators of operators.md (draft, debug, improve, review) and their guards, with helpers you build from the contracts in tools.md. Use in rsi/step_15_rsi_aide2 when the pack has operators.md; the arm name is the outer loop's version (v1, v2, ...)."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# AIDE2's inner agent: a tree search over solutions, one operator at a time

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/adult-income-aide` (`P`); the problem is `T`; the arm is the outer loop's version
name (`--arm v1`, `--arm v2`, ...) on every command - the outer loop compares versions arm against arm.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space and the budget. 4. `operators.md`: draft, debug, improve, review - each with its guard. 5. `memory.schema.json`, `memory.json`, `config.md`. 6. `eval.md`.

## Procedure
1. Build the helpers of `tools.md` under `runs/adult-income-aide/helpers/` if they are not there yet; `fit_recipe` here also marks a result `suspicious: true` as the review operator says.
2. Open the arm: `load_splits P T --arm <v>`.
3. Search policy: aide-tree - the operators of `operators.md`, applied to the tree of solutions you have fitted:
   a. draft: one solution per model family, in one call.
   b. review each result as the review operator says; a result marked `suspicious: true` is fitted again once before it is believed.
   c. improve, until a result says `FREEZE`: the untried neighbours (one field away, nearest first) of what the improve operator says to expand; debug a solution that errored as the debug operator says. `read_memory P T --arm <v> --order aide-tree` prints the next eight recipes of the current operators (`aide-tree-top-3` when the improve operator says "top three"); fit them in one call and repeat: `fit_recipe P T --arm <v> --recipes <the list>`.
4. When a result says `FREEZE`, pick the highest `val_score`, then, after FREEZE: `score_test P T --arm <v> --recipe <that recipe>`.
5. `scorecard P T --arm <v>` and answer in text with the arm, the best val_score, the test score, the fits used and how many results were suspicious. Stop.

## Rules
- Recipes come from `schema.json -> fields` only; never invent a value.
- Never run `score_test` before FREEZE, never twice.
- Never write a card: that is the verifier's job. Only the outer loop may rewrite `operators.md` - and only that file; every operator keeps its guard line word for word, or `lint_pack` refuses the pack.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `memory: off` in `config.md`: the static order, same 24 fits.

## Done when
`score_test` answered once for the arm.
