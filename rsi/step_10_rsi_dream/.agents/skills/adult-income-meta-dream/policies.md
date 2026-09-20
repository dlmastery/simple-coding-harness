# Search policies the actor may be told to run

Each is one line of the actor's SKILL.md (`Search policy: <name>`); the actor follows the description, and `read_memory --order <name>` walks it.

- `static`: walk `schema.json -> recipes` in order, cards or no cards.
- `obey-memory`: probe one recipe per model (the preferred model first) with the preferred preprocessing; then the believed family - its static recipes, then its hyper variants - ranked by the cards; then the rest of the grid.
- `random`: the 72-recipe grid in a seeded shuffle (`numpy.random.default_rng(seed)`).
- `neighbours-of-top-3`: six static fits, then the untried neighbours (one field away, a model change taking the new model's middle hyper value) of the three best so far, then the static list.
- `prefer-untried-family`: at every step the model family with the fewest fits so far, static recipes before hyper variants.
