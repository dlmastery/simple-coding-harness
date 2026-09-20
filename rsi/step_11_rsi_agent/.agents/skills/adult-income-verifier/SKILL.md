---
name: adult-income-verifier
description: "Turn the fit log of one problem into memory cards for the actor pack adult-income, with helpers you build from the contracts in tools.md. Use after the actor's memory arm on a problem is frozen and scored; input is the log and the profile, nothing else."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

Run every helper through the Bash tool from this lesson's directory. The actor pack is
`.claude/skills/adult-income-actor` (`P`: its `memory.json` is where your cards go); your own pack
is `.claude/skills/adult-income-verifier` (`V`); the problem's directory is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `memory.schema.json`: the only shape a card may have. 4. The actor's `memory.json`: the cards so far.
You never read the actor's messages, its reasoning, its intent or its test score. Your input is `{recipe, val_score, error}` rows and the profile, from one helper.

## Procedure
1. Build `read_traces` and `write_card` under `runs/adult-income-verifier/helpers/` if they are not there yet (they may import the actor's runtime helpers for the table and the profile; never the test scorer).
2. Read the fits of this problem's memory arm with the pairwise tally: `read_traces P T --scope problem --tally` (the arm to read is `memory`, or the one the curriculum skill names with `--of`).
3. The tally: every pair of rows whose recipes differ in exactly one field (two models each at their middle hyper value differ in `model` only) - the higher `val_score` is a win for its value of that field and a loss for the other; a pair with one errored side marks the erroring value. The helper prints it; check a few pairs by hand the first time.
4. The rule, per field: ONE `prefer` card for the value with the most wins net of losses (`evidence` 1, `counter` 0) if that net is positive; a counter card (`evidence` 0, `counter` 1, the same `if` and `then`) for every value that lost more than it won; a `forbid` card (`evidence` 1) for a value that errored. A card's `if` is the side of the field's threshold this profile is on - `class_weight` -> `imbalance` 0.35; `encode` -> `has_categorical` == 0 / 1; `scale` -> `n_features` 10; `model` -> `n_rows` 1000; `hyper` -> `n_classes` 3 - written `{"key": ..., "op": ">=" or "<" (== for has_categorical), "value": <the threshold>}`. The helper's `cards_by_rule` is this list; write it in one call:
   `write_card P T --as V --cards <the list>`
   The helper merges the counts into the actor's `memory.json` (both mirrors): one problem is one piece of evidence, a card is active from its first, and it is demoted as soon as its counters reach half its evidence.
5. Answer in text with how many cards you wrote, how many were new and how many were demoted. Stop.

## Rules
- A card has exactly `if`, `then`, `evidence`, `counter`. No note, no reason, no mention of the test split or of the intent: `write_card` refuses them.
- You do not fit, you do not score the test split, you do not read the actor's messages: `fit_recipe` and `score_test` are forbidden to this pack.
- On a problem whose `role` is `exam`, or when the actor's `config.md` says `memory: frozen`, `write_card` refuses: the exam is never learned from.

## Off switch
MEMORY_OFF in the actor's `config.md`: there is no memory arm to read, and you write nothing.

## Done when
Every pair one field apart has been counted and written.
