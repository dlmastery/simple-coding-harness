# Tools

## Allowed
- validate_intent - task.json against the task schema, acceptance.md against the scorecard fields
- lint_pack - every reason a pack may not run for a task; refuses a pack that widens the intent

## Forbidden
- load_splits, fit_recipe, score_test, save_model - nothing is trained in this lesson
- write_card, propose, apply, patch_pack - nothing is written or changed
