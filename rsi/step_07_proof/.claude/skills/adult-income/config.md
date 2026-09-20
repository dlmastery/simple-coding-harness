---
memory: "on"
meta: "on"
---
# Off switches

`memory: off` is MEMORY_OFF: no card is read or written on any arm of this pack; the memory
arm runs the static order and must reproduce the control arm's numbers exactly (the
delete-the-file check). `memory: frozen` reads the cards but refuses every `write_card` (the
exam). `meta: off` is META_OFF: a meta pack proposes nothing and the actor pack stays
byte-identical between problems. Flip a line, rerun, compare.
