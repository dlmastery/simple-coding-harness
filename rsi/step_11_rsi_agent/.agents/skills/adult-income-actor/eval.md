# Eval: how this pack is judged

Read by the agent at boot, implemented by the helpers it builds (`curve`, `exam`), reported by the curriculum skill.

## The comparison
- Two arms per problem, same seed, same split, same helper, same budget of 24 fits: the memory arm (this pack as it is) and the control arm (`--arm control --memory off`: `memory.json` not read, which is lesson 01's static walk).
- The test split is locked: scored once per arm, after FREEZE, never before. `test_touched_before_freeze` must be `false` on every scorecard; `score_test` and the hook refuse anything else.
- The delete-the-file check: `memory: off` in `config.md` must give the control arm's numbers exactly; a difference means something other than the cards changed.

## The learning curve
Problems 1 to 6 in order, the pack carried forward, the verifier writing after each memory arm. Per problem: `gap_val` = memory best val - control best val; `wasted` = fits before reaching the control arm's best (within 0.005), plus every fit that errored; cards added / demoted / active. The claim: the gap is never negative, and larger on the last problem than on the second. The numbers are this machine's - the agent wrote the fit helper - but both arms share it, so the gap is real.

## The exam
The memory is frozen before every `score_test` (`freeze_memory`) and problem 7 is never written to: `write_card` refuses on an exam problem, and the curriculum runs no verifier there. Five seeds of the split. The claim: the memory arm beats the control arm on at least 3 of 5 seeds (a higher test score, or the same score with fewer wasted fits), the pack's `memory.json` is byte-identical before and after, and the report names every applicable card that did not transfer.

## The scorecard
problem, arm, seed, n_fits, fits_used, wasted_fits, best_val_score, best_recipe, test_score, test_scored_once, test_touched_before_freeze, cards_active, cards_added, cards_demoted - the fields of lesson 00's acceptance.md, no more, no fewer.
