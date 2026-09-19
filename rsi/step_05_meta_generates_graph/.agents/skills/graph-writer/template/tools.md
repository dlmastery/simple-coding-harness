# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- walk_path - walk one path (or six) of graph.json by id: fit its recipe, or skip and count if the path is illegal; counted against the budget of {{n_fits}}
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline
- scorecard - the numbers of this arm

## Forbidden
- fit_recipe - a recipe reaches the fitter only as a path of the graph
- read_memory, write_card, read_traces - this pack has no memory and no verifier
- propose, apply, patch_pack, rollback - graph.json and paths.json are mutable: false
