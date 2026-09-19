# Eval: how this pack is judged

Read by the agent at boot, enforced by the scripts, reported by `curve.py` and `exam.py`.

## The comparison
- Two arms per problem, same seed, same split, same budget of 24 fits: the memory arm (this pack as it is) and the control arm (`--arm control --memory off`: `memory.json` not read, which is lesson 01's static walk).
- The test split is locked: scored once per arm, after FREEZE, never before. `test_touched_before_freeze` must be `false` on every scorecard; `score_test.py` and the hook refuse anything else.
- The delete-the-file check: `{"memory": "off"}` in `config.json` must give the control arm's numbers exactly; a difference means something other than the cards changed.

## The learning curve
Problems 1 to 6 in order, the pack carried forward, the verifier writing after each memory arm. Per problem: `gap_val` = memory best val - control best val; `wasted` = fits before reaching the control arm's best (within 0.005), plus every fit that errored; cards added / demoted / active. The claim: the gap is never negative, and larger on the last problem than on the second.

## The exam
Problem 7 is never written to: both arms open with `--freeze-memory` (`write_card.py` refuses), and the exam is run over five seeds. The claim: the memory arm beats the control arm on at least 3 of 5 seeds (a higher test score, or the same score reached with fewer wasted fits), and the report names every applicable card that did not transfer.

## The scorecard
problem, arm, seed, n_fits, fits_used, wasted_fits, best_val_score, best_recipe, test_score, test_scored_once, test_touched_before_freeze, cards_active, cards_added, cards_demoted - the fields of lesson 00's acceptance.md, no more, no fewer.
