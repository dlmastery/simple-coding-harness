# Tools

## Allowed
- read_traces - every fit row of the log so far (scope all) with the profile of the current problem
- read_memory - the actor pack's cards
- read_pack - every file of the actor pack
- patch_pack - one patch per visit: snapshot, then the human or the private gate decides, then land or roll back
- private_score - one recipe on the private split; twice per visit at most
- rollback - restore the actor pack from a version

## Forbidden
- fit_recipe, score_test, save_model, walk_path - the meta pack never trains and never touches the test split
- write_card - cards go through patch_pack, so they are versioned and approved like every other change
- propose, apply - a whole-pack proposal is a writer's move; a meta pack patches
