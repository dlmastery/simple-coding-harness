# Tools

## Allowed
- lint_pack - both generated packs, linted against the task; the verifier contract included
- propose - write the proposal and the text the user must see (the contract first); nothing lands
- apply - land a proposal with the user's exact words; refuses without them

## Forbidden
- fit_recipe, score_test, save_model - the writer never trains anything
- write_card, read_traces, read_memory - there is no memory here and no feedback from the generated packs
