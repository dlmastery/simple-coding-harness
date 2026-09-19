# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: obey-memory
  (obey-memory: probe one recipe per model, the believed model first, with the preferred preprocessing; then the believed family - its static recipes, then its hyper variants - ranked by the cards; then the rest of the grid. With no applicable card, the static order. `python ../tools/read_memory.py --pack P --task T --order obey-memory` prints the next eight; fit them and repeat.)
- MEMORY_OFF (`--memory off` on the arm, or `config.json`): no card is read; you run the static order.
