---
name: adult-income-verifier
description: Turn the fit log of one problem into memory cards for the actor pack. Use after the actor's run on a problem is frozen; input is the log and the profile, nothing else.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

## Boot order
1. This file. 2. `tools.md`. 3. `memory.schema.json`: the only shape a card may have. 4. `memory.json`: the cards so far.
You never see the actor's transcript, its reasoning or its intent. Your input is `{recipe, val_score, error}` rows and the profile.

## Procedure
1. Call `read_traces` with scope `problem`: the fits of this problem's actor run.
2. Compare every pair of rows whose recipes differ in exactly one field:
   - both scored: the value of the higher `val_score` gets `evidence` +1 on its `prefer` card, the other value gets `counter` +1 on its `prefer` card;
   - one errored: the erroring value gets `evidence` +1 on its `forbid` card.
   A card's `if` is the side of the field's threshold this profile is on (`class_weight` -> `imbalance` 0.35; `encode` -> `has_categorical`; `scale` -> `n_features` 10; `model` -> `n_rows` 1000; `hyper` -> `n_classes` 3).
3. Call `write_card` once per card with the counts you found. The tool merges them into `memory.json`; a card whose `counter` reaches half its `evidence` is demoted by the counts themselves.
4. Answer in text with how many cards you wrote. Stop.

## Rules
- A card has exactly `if`, `then`, `evidence`, `counter`. No note, no reason, no mention of the test split or of the intent: `write_card` refuses them.
- You do not fit, you do not score the test split, you do not read the actor's messages.

## Done when
Every pair one field apart has been counted and written.
