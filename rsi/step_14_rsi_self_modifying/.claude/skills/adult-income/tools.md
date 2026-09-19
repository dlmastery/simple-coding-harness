# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile, its budget and the cards that apply
- read_memory - the cards on disk, which apply to this profile, and the preferred value per field
- fit_recipe - one fit (or a list) on train scored on val; counted against the budget of 24; refuses a recipe a forbid card rules out
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline
- scorecard - the numbers of this arm

## Forbidden
- write_card, read_traces - the verifier's tools; the actor never grades its own homework
- propose, apply, patch_pack, rollback - only a meta pack changes this pack
