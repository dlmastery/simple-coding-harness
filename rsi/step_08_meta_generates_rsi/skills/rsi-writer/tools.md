# Tools

## Allowed
- read_task - the task.json this writer was booted for
- lint_pack - both generated packs, linted against the task (the verifier contract included) and booted dry
- propose - show the pack to the human and get y / n / edit
- apply - land an approved proposal

## Forbidden
- fit_recipe, score_test, save_model - the writer never trains anything
- write_card, read_traces, read_memory - there is no memory here and no feedback from the generated pack
