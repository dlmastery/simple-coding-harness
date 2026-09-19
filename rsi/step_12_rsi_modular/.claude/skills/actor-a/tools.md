# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile, its budget
- read_memory - the cards, and the next recipes of the policy the context module names
- fit_recipe - fits on train scored on val; counted against the budget of 24
- score_test - the locked test split, once, after FREEZE
- scorecard - the numbers of this arm

## Forbidden
- write_card, read_traces - the verifier's tools
- contrast, patch_pack, rollback - the meta pack's tools; only it patches a module
