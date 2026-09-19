---
name: skill-memory-meta
description: Turn one problem's execution evidence into ONE localised, validated update of the actor's skill memory - a card for the situation the problem was in. Use after the actor's run on a problem is frozen and scored.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# Recuris's meta agent: evidence becomes a card, one at a time

## Boot order
1. This file. 2. `tools.md`. 3. The actor's `skill-memory/manifest.yaml`, its cards and `working.md` (appended by the harness from the target pack).

## Procedure
1. Call `read_traces` (scope `problem`), `read_memory`, `read_pack`.
2. Name the situation of this problem with the same need tags the actor uses. Tally the problem's pairs one field apart: per field, the value with the most wins net of losses.
3. Take the first field of `model`, `class_weight`, `encode`, `scale` whose winning value the situation's card does not already hold (a card holds one `then`). Call `skill_memory` with action `update` once: `{card, then, when, body}` - the existing card's name when the situation has one for that field, else a new name. The tool refuses an update whose `then` did not win its comparisons on this problem, keeps one file per card, snapshots the pack under `versions/` first, and raises the card's `horizon` (the number of problems it was updated on).
4. Answer in text with the tool's result. Stop.

## Rules
- One update per visit; the tool refuses a second.
- An update is localised to one card file (plus a manifest line for a new card) and validated before it lands.
- You never fit and never score the test split.

## Done when
`skill_memory` has answered once, or there was nothing to update.
