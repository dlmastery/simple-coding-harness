# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- fit_recipe - one fit (or a slice of recipes.json) on train scored on val; counted against the budget of {{n_fits}}
- write_loop_log - one audit line per iteration; nothing reads it back
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline
- scorecard - the numbers of this arm

## Forbidden
- read_memory, write_card, read_traces - this pack has no memory and no verifier
- propose, apply, patch_pack, rollback - this pack changes no file
