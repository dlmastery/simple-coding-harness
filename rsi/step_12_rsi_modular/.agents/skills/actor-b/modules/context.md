# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter * 2 < evidence`.
- Search policy: obey-memory
  (obey-memory: the probe, the believed family, the rest of the grid, as `read_memory --order obey-memory` prints it, eight recipes per call.)
- MEMORY_OFF (`--memory off` on the arm, or `config.md`): no card is read; you run the static order.
