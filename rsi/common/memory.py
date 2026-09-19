"""Memory cards: the first RSI file, typed so a tool can enforce them.

A card is a constraint on the *next* proposal: when the profile satisfies
`if`, `then` prefers or forbids one field value. `evidence` counts the paired
comparisons that support it, `counter` the ones that contradict it; a card
whose counters reach half its evidence is demoted and no longer applies. There is no
free-text field, so there is no place for a reason, an intent or a diary
entry - and no way for the word "test" to get in.

`memory.schema.json` in a pack is the JSON Schema below; `write_card`
validates against the pack's copy, so a pack that loosens it is a diff you
can see. `compare` is the verifier's rule: over one problem's log, the value of a
field that won the most comparisons one field apart gets one evidence, the
values that lost more than they won get one counter - the rule the verifier
pack states in its SKILL.md, so the fake model and a real one write the same
cards from the same log. One problem is one piece of evidence: a pack that
saw trees win on one table has an anecdote, not a card.
"""

import json
import operator
from pathlib import Path

import jsonschema

from common.data import PROFILE_KEYS
from common.recipe import FIELDS, SCHEMA

MIN_EVIDENCE = 1     # one problem is one piece of evidence: a card acts after one, a counterexample demotes it
OPS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le, "==": operator.eq}

CARD_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "memory card: IF profile THEN prefer or forbid one field value",
    "type": "object",
    "additionalProperties": False,
    "required": ["if", "then", "evidence", "counter"],
    "properties": {
        "if": {
            "type": "object", "additionalProperties": False, "required": ["key", "op", "value"],
            "properties": {"key": {"enum": list(PROFILE_KEYS)}, "op": {"enum": list(OPS)}, "value": {"type": "number"}},
        },
        "then": {
            "type": "object", "additionalProperties": False, "required": ["field"],
            "properties": {
                "field": {"enum": list(FIELDS)},
                "prefer": {"type": ["string", "number", "null"]},
                "forbid": {"type": ["string", "number", "null"]},
            },
            "oneOf": [{"required": ["prefer"]}, {"required": ["forbid"]}],
        },
        "evidence": {"type": "integer", "minimum": 0},
        "counter": {"type": "integer", "minimum": 0},
    },
}

# which profile key a field's cards condition on, and the threshold that splits the condition.
# The profile sees the table, never the signal: a card about `model` is conditioned on `n_rows`
# because nothing in the profile can see whether the signal is linear. That is the superstition
# problem 5 is there to catch.
CONDITION = {
    "class_weight": ("imbalance", 0.35),
    "encode": ("has_categorical", 1),
    "scale": ("n_features", 10),
    "model": ("n_rows", 1000),
    "hyper": ("n_classes", 3),
}

FORBIDDEN_WORDS = ("test", "intent")


def validate_card(card, schema=CARD_SCHEMA):
    """A card is typed. Anything outside the type - a reason, an intent, the word test - is refused."""
    jsonschema.validate(card, schema)
    text = json.dumps(card).lower()
    for word in FORBIDDEN_WORDS:
        if word in text:
            raise ValueError(f"a card may not mention {word!r}")
    return card


def card_id(card):
    return json.dumps({"if": card["if"], "then": card["then"]}, sort_keys=True)


def active(card):
    """Some evidence, and at most half as many counterexamples: one counter demotes a one-evidence card."""
    return card["evidence"] >= MIN_EVIDENCE and card["evidence"] >= 2 * card["counter"]


def matches(card, profile):
    return OPS[card["if"]["op"]](profile[card["if"]["key"]], card["if"]["value"])


def applicable(cards, profile):
    """The active cards whose condition this profile satisfies: the ones that shape the next proposal."""
    return [c for c in cards if active(c) and matches(c, profile)]


def forbidden(recipe, cards, profile):
    """The first applicable forbid card this recipe violates, or None. `fit_recipe` refuses on it."""
    for card in applicable(cards, profile):
        if "forbid" in card["then"] and recipe[card["then"]["field"]] == card["then"]["forbid"]:
            return card
    return None


WEIGHT = {"model": 4, "class_weight": 2, "encode": 2, "scale": 1, "hyper": 1}   # how much a preferred value moves a recipe up


def preferred(cards, profile):
    """The pack's current belief, one value per field: the applicable prefer card with the most net evidence.
    A tie is no belief. `hyper` values belong to one model each, so the belief is per model: key ("hyper", model)."""
    best = {}
    for c in applicable(cards, profile):
        if "prefer" not in c["then"]:
            continue
        field, value = c["then"]["field"], c["then"]["prefer"]
        k = ("hyper", next(m for m, vs in SCHEMA["hyper"].items() if value in vs)) if field == "hyper" else field
        net = c["evidence"] - c["counter"]
        if k not in best or net > best[k][0]:
            best[k] = (net, value, False)
        elif net == best[k][0]:
            best[k] = (net, value, True)      # tied: nothing to prefer
    return {k: v for k, (_, v, tied) in best.items() if not tied}


def agreement(recipe, cards, profile, want=None):
    """The weighted number of fields of this recipe that carry the pack's preferred value: the sort key of the
    obey-memory order. The model weighs most, so a model belief ranks that whole family first."""
    want = preferred(cards, profile) if want is None else want
    total = 0
    for k, v in want.items():
        if isinstance(k, tuple):
            total += WEIGHT["hyper"] * (k[1] == recipe["model"] and recipe["hyper"] == v)
        else:
            total += WEIGHT[k] * (recipe[k] == v)
    return total


def condition_for(field, profile):
    """The condition the verifier writes: the side of the field's threshold this profile is on."""
    key, threshold = CONDITION[field]
    if key == "has_categorical":
        return {"key": key, "op": "==", "value": int(profile[key])}
    op = ">=" if profile[key] >= threshold else "<"
    return {"key": key, "op": op, "value": threshold}


def differing_field(a, b):
    """The one field two recipes differ in, or None when they differ in zero or several. Two models at their
    default hyper value differ in `model` only: the hyper value is the model's, not a second difference."""
    diff = [f for f in FIELDS if a[f] != b[f]]
    if diff == ["model", "hyper"] and all(r["hyper"] == SCHEMA["hyper"][r["model"]][1] for r in (a, b)):
        return "model"
    return diff[0] if len(diff) == 1 else None


def tally(rows):
    """Wins and losses per (field, value) over every pair of rows one field apart, and the values that errored."""
    wins, losses, errors = {}, {}, set()
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            field = differing_field(a["recipe"], b["recipe"])
            if field is None:
                continue
            if a["error"] is None and b["error"] is None:
                if a["val_score"] == b["val_score"]:
                    continue
                win, lose = (a, b) if a["val_score"] > b["val_score"] else (b, a)
                wins[(field, win["recipe"][field])] = wins.get((field, win["recipe"][field]), 0) + 1
                losses[(field, lose["recipe"][field])] = losses.get((field, lose["recipe"][field]), 0) + 1
            elif (a["error"] is None) != (b["error"] is None):
                bad = a if a["error"] is not None else b
                errors.add((field, bad["recipe"][field]))
    return wins, losses, errors


def compare(rows, profile):
    """The verifier's rule for one problem: per field, the value that won the most pairwise comparisons net of
    its losses gets evidence 1 on its prefer card; every value that lost more than it won gets counter 1; a value
    that errored gets evidence 1 on its forbid card. One problem is one piece of evidence, however many pairs it
    had: a card is active from its first problem, and demoted as soon as its counters reach half its evidence."""
    wins, losses, errors = tally(rows)
    deltas = []
    for field in FIELDS:
        values = {v for f, v in list(wins) + list(losses) if f == field}
        net = {v: wins.get((field, v), 0) - losses.get((field, v), 0) for v in values}
        if not net:
            continue
        best = max(sorted(values, key=str), key=lambda v: net[v])
        if net[best] > 0:
            deltas.append({"if": condition_for(field, profile), "then": {"field": field, "prefer": best}, "evidence": 1, "counter": 0})
        for v in sorted(values, key=str):
            if net[v] < 0:
                deltas.append({"if": condition_for(field, profile), "then": {"field": field, "prefer": v}, "evidence": 0, "counter": 1})
    for field, v in sorted(errors, key=str):
        deltas.append({"if": condition_for(field, profile), "then": {"field": field, "forbid": v}, "evidence": 1, "counter": 0})
    return deltas


def merge(cards, card):
    """Add a card's evidence and counter to the card with the same if/then, or append it. Returns (cards, added)."""
    for existing in cards:
        if card_id(existing) == card_id(card):
            existing["evidence"] += card["evidence"]
            existing["counter"] += card["counter"]
            return cards, False
    cards.append(dict(card))
    return cards, True


def load(path):
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, cards):
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        json.dump(cards, f, indent=1)
        f.write("\n")
