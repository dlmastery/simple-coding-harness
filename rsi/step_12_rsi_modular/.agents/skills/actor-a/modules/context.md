# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter * 2 < evidence`.
- Search policy: static
  (static: walk `schema.json -> recipes` in order, cards or no cards.)
- MEMORY_OFF (`--memory off` on the arm, or `config.md`): no card is read; you run the static order.
