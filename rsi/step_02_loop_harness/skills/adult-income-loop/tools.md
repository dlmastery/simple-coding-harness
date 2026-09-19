# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- fit_recipe - one fit on train scored on val; counted against the budget of 24
- write_loop_log - one audit line per iteration; nothing reads it back
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline

## Forbidden
- read_memory, write_card, read_traces - this pack has no memory and no verifier
- propose, apply, patch_pack, rollback - this pack changes no file
