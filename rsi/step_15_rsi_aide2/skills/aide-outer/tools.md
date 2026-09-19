# Tools

## Allowed
- read_traces - every fit row of the log so far (scope all)
- read_memory - the inner pack's cards
- read_pack - every file of the inner pack
- meter - the fits and tokens spent so far, per arm or in all
- patch_pack - one rewrite per outer step of operators.md; the human decides, the runner's keep-if-better is the second gate

## Forbidden
- fit_recipe, score_test, save_model - the outer loop never trains and never touches the test split
- write_card - the verifier's tool
