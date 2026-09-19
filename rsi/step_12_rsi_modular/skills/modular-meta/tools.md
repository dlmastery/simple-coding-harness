# Tools

## Allowed
- read_traces - every fit row of the pool runs (scope all)
- read_memory - the target pack's cards
- read_pack - every file of the target pack
- contrast - pair success and failure per pool task; name the module whose text differs; return both texts
- patch_pack - one patch per visit, modules/*.md only; the private gate of the pool task decides

## Forbidden
- fit_recipe, score_test, save_model - the meta pack never trains and never touches the test split
- write_card - the verifier's tool
