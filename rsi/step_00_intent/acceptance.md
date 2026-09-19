# Acceptance: what counts as success, written before any pack exists

The intent is `intent.md`: improve ROC-AUC on Adult income (> 50k) under a budget of 24 fits
per arm, with the models it allows, the locked test rule it states and the profile keys a
card may condition on. Nothing downstream may widen it: the `lint_pack` checklist refuses a
pack whose `n_fits`, `test_rule`, `metric` or `models` differ from the intent's. The test
split is scored once, after FREEZE (the budget spent), never before and never twice. The
curriculum in `../tasks/` is the transfer table: the same intent, one `intent.md` per problem,
in the order the pack learns them; problem 7 is the exam and is never written to.

## The scorecard

Every arm of every later lesson reports exactly these fields, and a scorecard missing one is
not a scorecard:

- problem
- arm
- seed
- n_fits
- fits_used
- wasted_fits
- best_val_score
- best_recipe
- test_score
- test_scored_once
- test_touched_before_freeze
- cards_active
- cards_added
- cards_demoted

## The pass rule

A lesson claims a pack learned only when, on the same problem, seed and budget:

1. `test_scored_once` is true and `test_touched_before_freeze` is false for both arms (you
   did not peek);
2. the memory arm's `best_val_score` is at least the `MEMORY_OFF` arm's on every problem, the
   gap is larger on the last problem than on the second, and its `wasted_fits` (fits spent
   before reaching the `MEMORY_OFF` arm's best val score, within 0.005) are fewer in total
   over the curriculum;
3. on the exam problem the frozen pack beats `MEMORY_OFF` on at least 3 of 5 seeds (a higher
   test score, or the same score reached with fewer wasted fits), and the report names every
   applicable card that did not transfer.

The numbers are relative on purpose: the agent that runs a lesson writes its own fit helper
from the contract in `tools.md`, so two machines need not print the same validation score,
but on one machine the memory arm and the `MEMORY_OFF` arm share the helper, the seed, the
split and the budget - and that comparison is what the framework paper's evidence standard
asks for. Everything else - a nicer recipe, a lower loss this Monday - is B0 self-refinement
or AutoML, and the lessons say so.
