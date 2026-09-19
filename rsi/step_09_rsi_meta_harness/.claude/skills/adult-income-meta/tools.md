# Tools

## Allowed
- read_traces - the whole log (scope all) or one problem's rows with the tally
- read_memory - the cards, which apply, the preferred values
- read_pack - every file of the actor pack, with checksums and the versions on disk
- patch_pack - one patch per visit: snapshot, diff, the user's answer, land or reject
- rollback - restore the actor pack from a version (the human's tool too)

## Forbidden
- fit_recipe, score_test, save_model, load_splits - the meta pack never fits and never touches the test split
- write_card - cards land through a patch to memory.json, not through the verifier's pen
