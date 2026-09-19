# Eval: how this pack is judged

Read by the model at boot, enforced by the harness, reported by `run.py`.

## The comparison
- Two arms per problem, same seed, same split, same budget of 24 fits: the memory arm (this pack as it is) and the `MEMORY_OFF` arm (the same pack with `memory.json` not loaded, which is lesson 01's static walk).
- The test split is locked: scored once per arm, after FREEZE, never before. `test_touched_before_freeze` must be `no` on every scorecard.
- The delete-the-file check: deleting `memory.json` must give the `MEMORY_OFF` numbers exactly; a difference means something other than the cards changed.

## The learning curve
Problems 1 to 6 in order, the pack carried forward, the verifier writing after each. Per problem: `gap_val` = memory best val - `MEMORY_OFF` best val; `wasted` = fits before reaching the `MEMORY_OFF` arm's best (within 0.005); cards activated / demoted / active. The claim: the gap is never negative, and larger on the last problem than on the second.

## The exam
Problem 7 is never written to: the pack is frozen (`write_card` refuses), and the exam is run over five seeds. The claim: the memory arm beats `MEMORY_OFF` on at least 3 of 5 seeds (a higher test score, or the same score reached with fewer wasted fits), and the report names every applicable card that did not transfer.

## The scorecard
problem, arm, seed, n_fits, fits_used, wasted_fits, best_val_score, best_recipe, test_score, test_scored_once, test_touched_before_freeze, cards_active, cards_added, cards_demoted - the fields of lesson 00's acceptance.md, no more, no fewer.
