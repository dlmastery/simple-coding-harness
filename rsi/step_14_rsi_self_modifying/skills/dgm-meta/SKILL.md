---
name: dgm-meta
description: Rewrite the actor pack's own source - its SKILL.md and loop.json - one generation deep, from a parent chosen in an archive of variants scored on a fixed held-out benchmark, behind the private gate and the human cycle. Use after a problem's actor and verifier runs are done.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: both
  patches: ["SKILL.md", "loop.json"]
  held_out: held-out
---
# The Darwin Goedel Machine lineage: the agent's own source, with an archive of stepping stones

## Boot order
1. This file. 2. `tools.md`. 3. `memory.json` of the actor (appended by the harness). The log, the pack and the archive come through tools.

## Procedure
1. Call `read_traces` (scope `all`), `read_memory`, `read_pack`.
2. Call `archive` with action `add`: `{label: "<problem>-<current policy>", arm: <the held-out arm the runner names in its first message>}`. The tool stores the current pack as a variant with its held-out score: over the fixed benchmark under `held-out/` (two synthetic tables no curriculum or exam problem uses), the private score of the variant's best recipe minus the static walk's, averaged.
3. Call `archive` with action `parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If the parent is not the latest, call `archive` with action `restore` and that label, then `read_pack` again: you now stand on the parent.
4. Propose ONE rewrite with `patch_pack`: the `Search policy:` line of `SKILL.md` and the `policy` field of `loop.json` set to the first of `static`, `obey-memory`, `neighbours-of-top-3`, `prefer-untried-family` that no variant in the archive carries; the evidence recipe is the parent's best. `patches:` allows those two files only. `approval: both`: the private gate decides keep-or-rollback first, then the human sees the diff and answers y / n / edit.
5. Answer in text with the parent, the rewrite and the tool's verdict. Stop.

## Rules
- One generation deep: a rewrite of the parent, never of a rewrite that has not run.
- A variant that lowered the held-out score is in the archive with its score; the parent rule never picks it over a better one.
- You never fit and never score the test split.

## Done when
`archive` holds this generation's variant and `patch_pack` has answered once, or every variant is in the archive.
