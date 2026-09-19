"""A deterministic synthetic table: four numeric columns, one categorical that
matters, one high-cardinality categorical that does not, a class-imbalance knob
and a `shift` knob that changes which recipe fields matter.

shift=0 puts interactions and thresholds in the signal, so trees win and a
linear model cannot follow. shift=1 draws a straight line through the same
columns and balances the classes, so the linear model wins and class weights
stop mattering. The tests learn on shift=0 and transfer to shift=1; step 03
does the same after learning on Adult.
"""

import numpy as np
import pandas as pd

from common.data import TARGET

COLOUR_EFFECT = {"red": 1.0, "green": 0.0, "blue": -1.0, "grey": 0.3}


def make_table(n=600, seed=0, shift=0, imbalance=None):
    rng = np.random.default_rng(seed)
    if imbalance is None:
        imbalance = 0.25 if shift == 0 else 0.5   # the shifted table is balanced
    x = rng.normal(size=(n, 4))
    colour = rng.choice(list(COLOUR_EFFECT), size=n)
    size = rng.choice([f"s{i:02d}" for i in range(12)], size=n)   # 12 levels, no effect
    effect = np.array([COLOUR_EFFECT[c] for c in colour])
    if shift == 0:   # XOR-shaped and V-shaped terms: no line separates them
        logit = 2.0 * np.sign(x[:, 0] * x[:, 1]) + 1.5 * (np.abs(x[:, 2]) - 0.8) + effect
    else:            # the same columns, one straight line
        logit = 1.5 * x[:, 0] - 1.0 * x[:, 1] + 0.5 * x[:, 2] + effect
    logit += rng.normal(scale=0.7, size=n)
    threshold = np.quantile(logit, 1 - imbalance)   # the top `imbalance` share is the positive class
    df = pd.DataFrame({f"x{i}": x[:, i] for i in range(4)})
    df["colour"] = colour.astype(object)
    df["size"] = size.astype(object)
    df[TARGET] = (logit > threshold).astype(int)
    return df
