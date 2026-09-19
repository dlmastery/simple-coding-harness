"""Memory cards: the first RSI file, typed so a tool can enforce them.

A card is a constraint on the *next* proposal: when the profile satisfies
`if`, `then` prefers or forbids one field value. `evidence` counts the paired
comparisons that support it, `counter` the ones that contradict it; a card
whose counters reach half its evidence is demoted and no longer applies. There is no
free-text field, so there is no place for a reason, an intent or a diary
entry - and no way for the word "test" to get in.

`memory.schema.json` in a pack is the JSON Schema below; `write_card`
validates against the pack's copy, so a pack that loosens it is a diff you
can see. `compare` is the verifier's rule: two recipes one field apart, the
better value gets evidence, the worse one a counter - the same rule the
verifier pack states in its SKILL.md, so the fake model and a real one write
the same cards from the same log.
"""

import json
import operator
from pathlib import Path

import jsonschema

from common.data import PROFILE_KEYS
from common.recipe import FIELDS, SCHEMA

MIN_EVIDENCE = 2     # one comparison is a coincidence; two is a card
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
    """Enough evidence, and at most half as many counterexamples: two counters demote a two-evidence card."""
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


def preferred(cards, profile):
    """The pack's current belief, one value per field: the applicable prefer card with the most net evidence.
    `hyper` values belong to one model each, so the belief is per model: key ("hyper", model)."""
    best = {}
    for c in applicable(cards, profile):
        if "prefer" not in c["then"]:
            continue
        field, value = c["then"]["field"], c["then"]["prefer"]
        k = ("hyper", next(m for m, vs in SCHEMA["hyper"].items() if value in vs)) if field == "hyper" else field
        net = c["evidence"] - c["counter"]
        if k not in best or net > best[k][0]:
            best[k] = (net, value)
    return {k: v for k, (_, v) in best.items()}


def agreement(recipe, cards, profile):
    """How many fields of this recipe carry the pack's preferred value: the sort key a memory-shaped search uses."""
    want = preferred(cards, profile)
    return sum(1 for k, v in want.items()
               if (recipe["hyper"] == v if isinstance(k, tuple) and k[1] == recipe["model"] else not isinstance(k, tuple) and recipe[k] == v))


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


def compare(rows, profile):
    """The verifier's rule over a list of {recipe, val_score, error} rows: every pair one field apart
    gives evidence to the winning value's prefer card and a counter to the losing value's. Returns card
    deltas keyed by card id; the tool merges them into the memory file."""
    deltas = {}

    def bump(field, kind, value, count):
        card = {"if": condition_for(field, profile), "then": {"field": field, kind: value}, "evidence": 0, "counter": 0}
        card = deltas.setdefault(card_id(card), card)
        card[count] += 1

    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            field = differing_field(a["recipe"], b["recipe"])
            if field is None:
                continue
            if a["error"] is None and b["error"] is None:
                if a["val_score"] == b["val_score"]:
                    continue
                win, lose = (a, b) if a["val_score"] > b["val_score"] else (b, a)
                bump(field, "prefer", win["recipe"][field], "evidence")
                bump(field, "prefer", lose["recipe"][field], "counter")
            elif (a["error"] is None) != (b["error"] is None):
                bad = a if a["error"] is not None else b
                bump(field, "forbid", bad["recipe"][field], "evidence")
    return list(deltas.values())


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
