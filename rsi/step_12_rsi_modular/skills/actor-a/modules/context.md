# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: static
  (static: walk `schema.json` -> `recipes` in order, cards or no cards.)
- MEMORY_OFF: the harness does not load `memory.json`; you run the static order.
