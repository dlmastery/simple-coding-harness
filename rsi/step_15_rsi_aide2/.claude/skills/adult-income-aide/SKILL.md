---
name: adult-income-aide
description: AIDE2's inner agent - train a classifier for a curriculum problem under a 24-fit budget as an AIDE-style tree search over solutions, with the operators of operators.md (draft, debug, improve, review) and their guards. Use in rsi/step_15_rsi_aide2 when the pack has operators.md; the arm name is the outer loop's version (v1, v2, ...).
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# AIDE2's inner agent: a tree search over solutions, one operator at a time

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income-aide` (`P`); the task file
is `T`; the arm is the outer loop's version name (`--arm v1`, `--arm v2`, ...)
on every command - the outer loop compares versions arm against arm.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space and the budget. 4. `operators.md`: draft, debug, improve, review - each with its guard. 5. `memory.schema.json`, `memory.json`: the cards. 6. `eval.md`.

## Procedure
1. Open the arm: `python ../tools/load_splits.py --pack P --task T --arm <v>`.
2. Search policy: aide-tree - the operators of `operators.md`, applied to the tree of solutions you have fitted:
   Search policy: aide-tree
   a. draft: one solution per model family, in one call.
   b. review each result as the review operator says; a result marked `suspicious: true` is fitted again once before it is believed.
   c. improve, until a result says `FREEZE`: the untried neighbours (one field away, nearest first) of what the improve operator says to expand; debug a solution that errored as the debug operator says. `python ../tools/read_memory.py --pack P --task T --arm <v> --order aide-tree` prints the next eight recipes of the current operators (`aide-tree-top-3` when the improve operator says "top three"); fit them in one call and repeat:
   `python ../tools/fit_recipe.py --pack P --task T --arm <v> --recipes '[...]'`
3. When a result says `FREEZE`, pick the highest `val_score`, then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T --arm <v> --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
4. `python ../tools/scorecard.py --pack P --task T --arm <v>` and answer in text with the arm, the best val_score, the test score, the fits used and how many results were suspicious. Stop.

## Rules
- Recipes come from `schema.json` -> `fields` only; never invent a value.
- Never run `score_test.py` before FREEZE, never twice.
- Never write a card: that is the verifier's job. Only the outer loop may rewrite `operators.md` - and only that file; every operator keeps its guard line word for word, or `lint_pack.py` refuses the pack.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`: the static order, same 24 fits.

## Done when
`score_test.py` answered once for the arm.
