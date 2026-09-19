# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile, its budget
- read_memory - the cards, and the next recipes of the operators (--order aide-tree or aide-tree-top-3)
- fit_recipe - fits on train scored on val; counted against the budget of 24; marks a suspicious score
- score_test - the locked test split, once, after FREEZE
- scorecard - the numbers of this arm

## Forbidden
- write_card, read_traces - the verifier's tools
- meter, patch_pack, rollback - the outer loop's tools; only it rewrites operators.md
