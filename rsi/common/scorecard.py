"""The scorecard: one JSON file with the numbers a claim is made of, the same
fields for every lesson from step 00's acceptance.md onwards.

The search never reads it. It is written for the reader, for the learning
curve and for the map. `SCORECARD_FIELDS` is the contract acceptance.md
states; a scorecard missing one is not a scorecard (step 07 asserts it).
"""

import json
from pathlib import Path

SCORECARD_FIELDS = (
    "problem", "arm", "seed", "n_fits", "fits_used", "wasted_fits",
    "best_val_score", "best_recipe", "test_score", "test_scored_once",
    "test_touched_before_freeze", "cards_active", "cards_added", "cards_demoted",
)


GOOD = 0.005   # within 0.005 of the bar counts as reaching it


def wasted_fits(rows, bar=None):
    """Fits spent before the first recipe that reaches the bar (within 0.005), plus every fit that errored.
    The bar is the MEMORY_OFF arm's best val score on the same problem and seed - the static grid's answer -
    or, for that arm itself and for a run with no control, the arm's own best. Experience is measured by
    how many fits it saved on the way to the same answer."""
    scored = [r for r in rows if r["val_score"] is not None]
    if not scored:
        return len(rows)
    target = (max(r["val_score"] for r in scored) if bar is None else bar) - GOOD
    first_good = next((i for i, r in enumerate(rows) if r["val_score"] is not None and r["val_score"] >= target), len(rows))
    return first_good + sum(1 for r in rows[first_good:] if r["val_score"] is None)


def best_of(rows):
    scored = [r for r in rows if r["val_score"] is not None]
    if not scored:
        return None, None
    best = max(scored, key=lambda r: r["val_score"])
    return best["val_score"], best["recipe"]


def make_scorecard(**fields):
    missing = set(SCORECARD_FIELDS) - set(fields)
    if missing:
        raise ValueError(f"a scorecard has every field of acceptance.md; missing {sorted(missing)}")
    return {k: fields[k] for k in SCORECARD_FIELDS}


def write_scorecard(path, card):
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        json.dump(card, f, indent=2)
        f.write("\n")


def read_scorecard(path):
    with open(Path(path), encoding="utf-8") as f:
        return json.load(f)
