---
name: adult-income-verifier
description: Turn the fit log of one problem into memory cards for the actor pack. Use after the actor's run on a problem is frozen; input is the log and the profile, nothing else.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

## Boot order
1. This file. 2. `tools.md`. 3. `memory.schema.json`: the only shape a card may have. 4. `memory.json`: the cards so far.
You never see the actor's transcript, its reasoning or its intent. Your input is `{recipe, val_score, error}` rows and the profile.

## Procedure
1. Call `read_traces` with scope `problem`: the fits of this problem's actor run.
2. Tally every pair of rows whose recipes differ in exactly one field (two models at their default hyper value count as differing in `model` only): the higher `val_score` is a win for its value of that field and a loss for the other; a pair where one side errored marks the erroring value.
3. Per field, write ONE prefer card for the value with the most wins net of losses (`evidence` 1) - if it has any net wins at all - and a `counter` 1 card for every value that lost more than it won. Write a `forbid` card (`evidence` 1) for a value that errored. A card's `if` is the side of the field's threshold this profile is on (`class_weight` -> `imbalance` 0.35; `encode` -> `has_categorical`; `scale` -> `n_features` 10; `model` -> `n_rows` 1000; `hyper` -> `n_classes` 3). Call `write_card` once per card; the tool merges the counts into `memory.json`. One problem is one piece of evidence: a card becomes active at two, and two problems against it demote it.
4. Answer in text with how many cards you wrote. Stop.

## Rules
- A card has exactly `if`, `then`, `evidence`, `counter`. No note, no reason, no mention of the test split or of the intent: `write_card` refuses them.
- You do not fit, you do not score the test split, you do not read the actor's messages.

## Done when
Every pair one field apart has been counted and written.
