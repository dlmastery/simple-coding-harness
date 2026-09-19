# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- fit_recipe - one experiment of the plan; counted against the budget of 24
- read_pack - your own files, to re-read plan.json after the curriculum pack rewrote it
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline

## Forbidden
- write_plan - the curriculum pack's tool
- write_card, read_traces - the verifier's tools
- propose, apply, patch_pack, rollback - only a meta pack changes this pack
