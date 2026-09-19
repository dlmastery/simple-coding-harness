---
name: adult-income-verifier
description: Turn the fit log of one problem into memory cards for the actor pack adult-income-aide. Use after the actor's memory arm on a problem is frozen and scored; input is the log and the profile, nothing else.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

Run every command through the Bash tool from this lesson's directory. The
actor pack is `.claude/skills/adult-income-aide` (`P` below: its memory is where
your cards go); your own pack is `.claude/skills/adult-income-verifier`
(`V` below); the task file is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `memory.schema.json`: the only shape a card may have. 4. The actor's `memory.json`: the cards so far.
You never read the actor's messages, its reasoning or its intent. Your input is `{recipe, val_score, error}` rows and the profile, from one script.

## Procedure
1. Read the fits of this problem's version arm (`v1`, `v2`, ...: the arm the outer loop named), with the pairwise tally:
   `python ../tools/read_traces.py --pack P --task T --scope problem --tally --of <v>`
2. Tally every pair of rows whose recipes differ in exactly one field (two models at their default hyper value count as differing in `model` only): the higher `val_score` is a win for its value of that field and a loss for the other; a pair where one side errored marks the erroring value. The script's `tally` is the same count; check yours against it.
3. Per field, write ONE `prefer` card for the value with the most wins net of losses (`evidence` 1) - if it has any net wins at all - and a `counter` 1 card (same `if`/`then`, `evidence` 0) for every value that lost more than it won. Write a `forbid` card (`evidence` 1) for a value that errored. A card's `if` is the side of the field's threshold this profile is on (`class_weight` -> `imbalance` 0.35; `encode` -> `has_categorical` == 0/1; `scale` -> `n_features` 10; `model` -> `n_rows` 1000; `hyper` -> `n_classes` 3), written `{"key": ..., "op": ">=" or "<" (== for has_categorical), "value": <the threshold>}`. The script's `cards_by_rule` is this list; write it in one call:
   `python ../tools/write_card.py --pack P --task T --arm <v> --as V --cards '[{"if": {...}, "then": {...}, "evidence": 1, "counter": 0}, ...]'`
   The script merges the counts into the actor's `memory.json`: one problem is one piece of evidence, a card is active from its first, and it is demoted as soon as its counters reach half its evidence (`demoted: true` in the result).
4. Answer in text with how many cards you wrote, how many were new and how many were demoted. Stop.

## Rules
- A card has exactly `if`, `then`, `evidence`, `counter`. No note, no reason, no mention of the test split or of the intent: `write_card.py` refuses them.
- You do not fit, you do not score the test split, you do not read the actor's messages: `fit_recipe.py` and `score_test.py` are not in your `tools.md`.

## Done when
Every pair one field apart has been counted and written.
