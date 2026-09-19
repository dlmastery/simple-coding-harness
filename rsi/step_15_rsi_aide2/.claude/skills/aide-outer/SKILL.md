---
name: aide-outer
description: AIDE2's outer loop - rewrite the inner agent's operator text and keep the rewrite only if it beats the previous version across the whole heterogeneous curriculum under one metered budget of fits and script calls. Use in rsi/step_15_rsi_aide2 after the inner pack has run every curriculum problem once as version v1.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: metered
  patches: ["operators.md"]
---
# Autoresearch on autoresearch: the outer loop rewrites the researcher

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/aide-outer` (`M`); the inner pack is
`.claude/skills/adult-income-aide` (`P`); the verifier is
`.claude/skills/adult-income-verifier` (`V`); the curriculum is
`../tasks/01_*.json` .. `../tasks/06_*.json`; `T` is `../tasks/01_adult_income.json`.

## Boot order
1. This file. 2. `tools.md`. The log, the pack and the meter come through scripts.

## Procedure - one outer step
1. Version 1: for each curriculum task in order, follow `P/SKILL.md` with `--arm v1`, then `V/SKILL.md` on that task (the cards carry forward; the verifier reads the `v1` arm: `read_traces.py --of v1`). Then meter it:
   `python ../tools/meter.py --pack M --task T --target P --of v1`
2. Propose ONE rewrite of `operators.md`: the `improve` operator changed from expanding the best solution to expanding the top three ("Improve: expand the top three solutions - fit their untried neighbours, one field away, nearest first."). Every operator keeps its guard line word for word (`lint_pack.py` refuses an operator without it; `patch_pack.py` refuses any other file). Write the whole file under `runs/aide-outer/patch/operators.md` and:
   `python ../tools/patch_pack.py --pack M --task T --target P --files @runs/aide-outer/patch --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c> --summary "improve: top-1 -> top-3" --visit 1`
   with v1's best recipe on `T` as the evidence recipe. `approval: metered`: the script snapshots the pack, lands the rewrite now (`landed: pending`) and leaves the decision to step 4.
3. Version 2: the same curriculum, same order, same budget, under the rewrite - `P/SKILL.md` with `--arm v2` on every task, the verifier after each (`--of v2`). Then `python ../tools/meter.py --pack M --task T --target P --of v2`.
4. Decide, across the whole set:
   `python ../tools/meter.py --pack M --task T --target P --decide --proposal <id> --before v1 --after v2 --tasks ../tasks`
   Per problem, v2's best val minus v1's; the statistical layer discards a gain more than 3 MADs above the median; the rewrite is kept only if the remaining total gain is positive and it loses on at most half the problems - otherwise the script rolls `operators.md` back to the snapshot. Both arms must have spent the same fits.
5. Answer in text with both meter readings, the per-problem gains, the outliers discarded, and the verdict. Stop.

## Rules
- One rewrite per outer step. The three guards stay in every operator: the anti-overfitting line, the re-run of a suspicious score, the statistical layer.
- You never fit for yourself and never score the test split; the inner arms are run as the inner pack.
- The budget is metered in fits and script calls; there is no token count, because no harness sees your transcript - say so when you report.

## Done when
`meter.py --decide` has answered.
