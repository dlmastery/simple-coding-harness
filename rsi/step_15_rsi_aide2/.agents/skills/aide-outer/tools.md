# Tools

## Allowed
- meter - the fits and script calls spent per arm, and --decide: keep-if-better across the curriculum
- read_pack - every file of the inner pack
- patch_pack - one rewrite per outer step of operators.md; metered: landed now, decided after the curriculum
- load_splits, fit_recipe, read_memory, score_test, scorecard - the inner pack's tools, run as the inner pack on each version arm
- read_traces, write_card - the verifier's tools, run for the verifier pack after each arm

## Forbidden
- propose, apply - the outer loop rewrites, it does not generate
- save_model - the models are not the deliverable
