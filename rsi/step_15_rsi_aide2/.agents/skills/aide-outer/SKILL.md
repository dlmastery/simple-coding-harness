---
name: aide-outer
description: "AIDE2's outer loop - rewrite the inner agent's operator text and keep the rewrite only if it beats the previous version across the whole heterogeneous curriculum under one metered budget of fits and helper calls. Use in rsi/step_15_rsi_aide2 after the inner pack has run every curriculum problem once as version v1."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: metered
  patches: ["operators.md"]
---
# Autoresearch on autoresearch: the outer loop rewrites the researcher

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/aide-outer` (`M`); the inner pack is `.claude/skills/adult-income-aide` (`P`); the
verifier is `.claude/skills/adult-income-verifier` (`V`); the curriculum is `../tasks/01_adult_income`
.. `../tasks/06_synth_shift_b`; `T` is `../tasks/01_adult_income`.

## Boot order
1. This file. 2. `tools.md`. 3. `M/config.md`. The log, the pack and the meter come through helpers.

## Procedure - one outer step
1. Build `meter`, `read_pack`, `propose`, `lint_pack` and `rollback` under `runs/aide-outer/helpers/` if they are not there yet.
2. Version 1: for each curriculum task in order, follow `P/SKILL.md` with `--arm v1`, then `V/SKILL.md` on that task (the cards carry forward; the verifier reads the `v1` arm: `read_traces --of v1`). Then meter it: `meter M T --target P --of v1`.
3. Propose ONE rewrite of `operators.md`: the `improve` operator changed from expanding the best solution to expanding the top three ("Improve: expand the top three solutions - fit their untried neighbours, one field away, nearest first."). Every operator keeps its guard line word for word (`lint_pack` refuses an operator without it; `propose` refuses any other file). Write the whole file under `runs/aide-outer/patch/operators.md` and `propose M T --target adult-income-aide --files runs/aide-outer/patch --recipe <v1's best recipe on T> --summary "improve: top-1 -> top-3" --visit 1`. `approval: metered`: snapshot the pack under `runs/adult-income-aide/versions/gen_NNN/`, land the rewrite now (`landed: pending`) and leave the decision to step 5.
4. Version 2: the same curriculum, same order, same budget, under the rewrite - `P/SKILL.md` with `--arm v2` on every task, the verifier after each (`--of v2`). Then `meter M T --target P --of v2`.
5. Decide, across the whole set: `meter M T --target P --decide --proposal <id> --before v1 --after v2 --tasks ../tasks`. Per problem, v2's best val minus v1's; the statistical layer discards a gain more than 3 MADs above the median; the rewrite is kept only if the remaining total gain is positive and it loses on at most half the problems - otherwise the helper restores `operators.md` from the snapshot. Both arms must have spent the same fits.
6. Answer in text with both meter readings, the per-problem gains, the outliers discarded, and the verdict. Stop.

## Rules
- One rewrite per outer step. The three guards stay in every operator: the anti-overfitting line, the re-run of a suspicious score, the statistical layer.
- You never fit for yourself and never score the test split; the inner arms are run as the inner pack.
- The budget is metered in fits and helper calls; there is no token count, because no helper sees your transcript - say so when you report.

## Off switch
META_OFF: `meta: off` in `M/config.md`; v1 runs and nothing is rewritten.

## Done when
`meter --decide` has answered.
