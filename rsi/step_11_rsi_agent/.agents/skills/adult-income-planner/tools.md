# Tools

## Allowed
- write_plan - the per-family numbers (--uncertainty), and the next phase's experiments into the actor's plan.json
- read_memory - the actor's cards: the believed family goes first at ties, and the recipes that carry the preferred values go first inside a family

## Forbidden
- fit_recipe, score_test, save_model - the planner never trains
- write_card - the verifier's tool
