"""Step 01 - the one loop every step reuses: propose, fit through the budget,
log, tell the observer, until the budget is gone. A policy is a function
`propose(rng, history) -> recipe`; random search is the first one.

An arm is one run of this loop with one seed. Paired seeds give paired arms:
the control arm and the memory arm with seed 3 draw from the same random
stream, so what differs between them is the memory and nothing else.
"""

import json
import time

import numpy as np

from common.recipe import SCHEMA, fit_recipe, validate

SEEDS = [0, 1, 2, 3, 4]
REDRAWS = 20   # attempts to find a recipe this arm has not tried yet


def key(recipe):
    return json.dumps(recipe, sort_keys=True)


def uniform_space(schema=SCHEMA):
    """Every value of every field with weight 1: the space random search draws from."""
    return {field: {value: 1.0 for value in values} for field, values in schema.items()}


def sample_recipe(space, rng, visited=()):
    """One weighted draw per field. A recipe the arm has already fitted is redrawn: a repeat is a wasted fit."""
    for _ in range(REDRAWS):
        recipe = {}
        for field, weights in space.items():
            values = list(weights)
            p = np.array([weights[v] for v in values], dtype=float)
            recipe[field] = values[rng.choice(len(values), p=p / p.sum())]
        if key(recipe) not in visited:
            return recipe
    return recipe


def random_policy(rng, history):
    return sample_recipe(uniform_space(), rng, {key(row["recipe"]) for row in history})


def run_arm(policy, budget, seed, split, log, arm="control", observe=None):
    """The loop. Returns the arm's rows, which are also appended to the log one by one."""
    rng = np.random.default_rng(seed)
    history, strikes = [], 0
    while budget.left > 0:
        recipe = policy(rng, history)
        started = time.perf_counter()
        try:
            validate(recipe)
        except ValueError as e:   # not a recipe: logged as an error, costs no fit
            result = {"val_auc": None, "error": f"Error: {e}"}
            strikes += 1
        else:
            result = budget.fit(fit_recipe, recipe, split["train"], split["val"])
        row = {"recipe": recipe, **result, "seconds": round(time.perf_counter() - started, 3), "seed": seed, "arm": arm}
        log.append(**row)
        history.append(row)
        if observe is not None:
            observe(row)
        if strikes >= budget.n:   # a policy that only produces junk does not run forever
            break
    return history


def best_of(rows):
    """The best validation AUC in a list of rows, and its recipe. None when every row errored."""
    scored = [row for row in rows if row["val_auc"] is not None]
    if not scored:
        return None, None
    best = max(scored, key=lambda row: row["val_auc"])
    return best["val_auc"], best["recipe"]


def wasted(rows):
    return sum(1 for row in rows if row["error"] is not None)


def mean_std(values):
    values = [v for v in values if v is not None]
    if not values:
        return None, None
    return round(float(np.mean(values)), 4), round(float(np.std(values)), 4)
