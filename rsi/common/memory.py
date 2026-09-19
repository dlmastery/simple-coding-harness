"""Step 02 - the memory: executable cards, the rule-based verifier that writes
them, and the policy that obeys them.

A card is a typed constraint on the next proposal: when the dataset profile
satisfies `if`, the sampling space is reshaped by `then` (one field value
preferred or forbidden). `evidence` counts the paired comparisons that support
it, `counter` the ones that contradict it; a card with counter >= evidence is
demoted and no longer applies. There is no free-text field, so there is no
place for a reason, an intent, or a diary entry.

The verifier receives an Observation and nothing else. It cannot be told what
the actor was thinking, because the type has no field for it.
"""

import json
import operator
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from common.arm import key, sample_recipe, uniform_space
from common.recipe import SCHEMA

PREFER = 3.0        # a preferred value is drawn three times as often
MIN_EVIDENCE = 2    # one comparison is a coincidence; two is a card
PROFILE_KEYS = ("rows", "cols", "categorical", "max_cardinality", "minority_share")
OPS = {">=": operator.ge, "<=": operator.le, "==": operator.eq}

# which profile key a field's cards condition on, and the threshold that splits the condition.
# The profile sees the table, never the signal: cards about `model` are conditioned on `rows`
# because nothing in the profile can see whether the signal is linear. Step 03 catches that.
CONDITION = {
    "class_weight": ("minority_share", 0.3),
    "encode": ("categorical", 1),
    "scale": ("rows", 2000),
    "model": ("rows", 2000),
    "capacity": ("rows", 2000),
}


@dataclass(frozen=True)
class Observation:
    recipe: dict
    val_auc: float | None
    error: str | None
    profile: dict


def memory_off():
    return os.environ.get("MEMORY_OFF", "").lower() in ("1", "true", "yes")


def empty_memory():
    return {"frozen": False, "cards": []}


def load_memory(path):
    """The cards on disk, validated one by one. No file, or MEMORY_OFF: no cards."""
    path = Path(path)
    if memory_off() or not path.exists():
        return empty_memory()
    with open(path, encoding="utf-8") as f:
        memory = json.load(f)
    for card in memory["cards"]:
        validate_card(card)
    return memory


def save_memory(path, memory):
    if memory_off() or memory["frozen"]:
        return
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        json.dump(memory, f, indent=1)
        f.write("\n")


def freeze(path, memory):
    """Read-only from here on: the flag the verifier honours, and the file mode for everyone else."""
    memory["frozen"] = True
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        json.dump(memory, f, indent=1)
        f.write("\n")
    os.chmod(path, stat.S_IREAD)
    return memory


def validate_card(card, schema=SCHEMA):
    """A card is typed. Anything outside the type - a reason, an intent, the word test - is refused."""
    if not isinstance(card, dict) or set(card) != {"if", "then", "evidence", "counter"}:
        raise ValueError("a card has exactly the keys if, then, evidence, counter")
    cond, then = card["if"], card["then"]
    if set(cond) != {"profile_key", "op", "value"} or cond["profile_key"] not in PROFILE_KEYS or cond["op"] not in OPS:
        raise ValueError(f"a condition is one of {PROFILE_KEYS} with one of {list(OPS)}")
    if not isinstance(cond["value"], (int, float)):
        raise ValueError("a condition value is a number")
    if set(then) not in ({"field", "prefer"}, {"field", "forbid"}):
        raise ValueError("a consequence is one field with one prefer or one forbid")
    value = then.get("prefer", then.get("forbid"))
    if then["field"] not in schema or value not in schema[then["field"]]:
        raise ValueError(f"{then['field']}={value!r} is not in the schema")
    if not all(isinstance(card[k], int) for k in ("evidence", "counter")):
        raise ValueError("evidence and counter are counts")
    if "test" in json.dumps(card).lower():
        raise ValueError("a card may not mention the test split")
    return card


def active(card):
    return card["evidence"] >= MIN_EVIDENCE and card["counter"] < card["evidence"]


def matches(cond, profile):
    return OPS[cond["op"]](profile[cond["profile_key"]], cond["value"])


def condition_for(field, profile):
    """The condition the verifier writes: the side of the threshold this dataset is on."""
    profile_key, threshold = CONDITION[field]
    op = ">=" if profile[profile_key] >= threshold else "<="
    return {"profile_key": profile_key, "op": op, "value": threshold}


def apply_cards(space, cards, profile):
    """Reshape a sampling space by the active cards whose condition this profile satisfies.
    Returns the new space and the cards that applied. A forbid never empties a field."""
    space = {field: dict(weights) for field, weights in space.items()}
    applied = []
    for card in cards:
        if not active(card) or not matches(card["if"], profile):
            continue
        then = card["then"]
        weights = space[then["field"]]
        if "prefer" in then:
            weights[then["prefer"]] *= PREFER
        elif any(w > 0 for v, w in weights.items() if v != then["forbid"]):
            weights[then["forbid"]] = 0.0
        applied.append(card)
    return space, applied


def card_id(card):
    return json.dumps({"if": card["if"], "then": card["then"]}, sort_keys=True)


def differing_field(a, b):
    """The one field two recipes differ in, or None when they differ in zero or several."""
    diff = [field for field in a if a[field] != b[field]]
    return diff[0] if len(diff) == 1 else None


class Verifier:
    """Rule-based, no model. Sees Observations only; writes cards from paired comparisons in what it saw;
    demotes by counterexample. Honours the frozen flag and MEMORY_OFF by writing nothing."""

    def __init__(self, memory, path=None):
        self.memory = memory
        self.path = path
        self.seen = []

    def observe(self, obs):
        if not isinstance(obs, Observation):
            raise TypeError("the verifier takes an Observation and nothing else")
        if self.memory["frozen"] or memory_off():
            return
        for past in self.seen:
            field = differing_field(past.recipe, obs.recipe)
            if field is not None:
                self.compare(past, obs, field)
        if obs.error is None:   # a success is a counterexample to every forbid on its values
            for field, value in obs.recipe.items():
                self.bump(self.find(field, "forbid", value, obs.profile), "counter")
        self.seen.append(obs)
        if self.path is not None:
            save_memory(self.path, self.memory)

    def compare(self, a, b, field):
        """Two recipes one field apart: the better value gets evidence, the worse one a counter."""
        if a.error is None and b.error is None:
            if a.val_auc == b.val_auc:
                return
            win, lose = (a, b) if a.val_auc > b.val_auc else (b, a)
            self.bump(self.card(field, "prefer", win.recipe[field], win.profile), "evidence")
            self.bump(self.find(field, "prefer", lose.recipe[field], lose.profile), "counter")
        elif (a.error is None) != (b.error is None):
            bad = a if a.error is not None else b
            self.bump(self.card(field, "forbid", bad.recipe[field], bad.profile), "evidence")

    def find(self, field, kind, value, profile):
        wanted = card_id({"if": condition_for(field, profile), "then": {"field": field, kind: value}})
        return next((c for c in self.memory["cards"] if card_id(c) == wanted), None)

    def card(self, field, kind, value, profile):
        found = self.find(field, kind, value, profile)
        if found is None:
            found = validate_card({"if": condition_for(field, profile), "then": {"field": field, kind: value},
                                   "evidence": 0, "counter": 0})
            self.memory["cards"].append(found)
        return found

    @staticmethod
    def bump(card, count):
        if card is not None:
            card[count] += 1


def observer(verifier, profile):
    """The only bridge from the loop to the verifier: a row becomes an Observation, nothing more can pass."""
    return lambda row: verifier.observe(Observation(row["recipe"], row["val_auc"], row["error"], profile))


def memory_policy(memory, profile, counts=None):
    """Sampling shaped by the active cards that match this profile. With no cards it is random search."""
    def propose(rng, history):
        space, applied = apply_cards(uniform_space(), memory["cards"], profile)
        if counts is not None:
            for card in applied:
                counts[card_id(card)] = counts.get(card_id(card), 0) + 1
        return sample_recipe(space, rng, {key(row["recipe"]) for row in history})
    return propose
