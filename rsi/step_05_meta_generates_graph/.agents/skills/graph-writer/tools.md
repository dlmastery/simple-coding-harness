# Tools

## Allowed
- lint_pack - the rendered pack, linted against the task
- propose - write the proposal and the text the user must see; nothing lands
- apply - land a proposal with the user's exact words; refuses without them

## Forbidden
- fit_recipe, score_test, save_model - the writer never trains anything
- write_card, read_traces, read_memory - there is no memory here and no feedback from the generated pack
