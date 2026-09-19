# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- fit_recipe - one fit on train scored on val; counted against the budget of {{n_fits}}; refuses a recipe a forbid card rules out
- read_memory - the cards as they are on disk (the same cards are in your prompt)
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline

## Forbidden
- write_card, read_traces - the verifier's tools; the actor never grades its own homework
- propose, apply, patch_pack, rollback - only a meta pack changes this pack
