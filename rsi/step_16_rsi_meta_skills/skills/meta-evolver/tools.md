# Tools

## Allowed
- read_traces - every fit row of the log so far (scope all)
- read_memory - the actor's cards (the target of the fast loop; empty for this pack's own target)
- read_pack - every file of the task-skills-meta pack, roles/*.md included
- patch_pack - one change to one roles/*.md file per visit; the human decides

## Forbidden
- fit_recipe, score_test, save_model - the slow loop never trains and never touches the test split
- write_card, archive, rank_policies - not this pack's
