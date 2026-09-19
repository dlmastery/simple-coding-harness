# Tools

## Allowed
- read_traces - the actor's fits on this problem so far (scope problem)
- read_memory - the actor's cards: the believed family goes first at ties, and the recipes that carry the preferred values go first inside a family
- write_plan - the next phase's experiments, into the actor's plan.json

## Forbidden
- fit_recipe, score_test, save_model - the curriculum pack never trains
- write_card - the verifier's tool
