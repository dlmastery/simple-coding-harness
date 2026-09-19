# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: static
  (static: walk `schema.json` -> `recipes` in order, cards or no cards: `--recipes @P/schema.json`.)
- MEMORY_OFF (`--memory off` on the arm, or `config.json`): no card is read; you run the static order.
