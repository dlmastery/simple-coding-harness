"""A deterministic synthetic table: four numeric columns, one categorical that
matters, one high-cardinality categorical that does not, a class-imbalance knob
and a `shift` knob that changes which recipe fields matter.

shift=0 puts interactions and thresholds in the signal, so trees win and a
linear model cannot follow. shift=1 draws a straight line through the same
columns, so the linear model wins. Problems 5 and 6 of the curriculum flip
the shift so a card learned as "trees always win" meets its counterexample;
the exam problem is a third seed no pack ever wrote to.
"""

import numpy as np
import pandas as pd

from _lib.recipe import TARGET

COLOUR_EFFECT = {"red": 1.0, "green": 0.0, "blue": -1.0, "grey": 0.3}


def make_table(n=600, seed=0, shift=0, imbalance=0.25, n_classes=2, noise=1.0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 4))
    colour = rng.choice(list(COLOUR_EFFECT), size=n)
    size = rng.choice([f"s{i:02d}" for i in range(12)], size=n)   # 12 levels, no effect
    effect = np.array([COLOUR_EFFECT[c] for c in colour])
    if shift == 0:   # XOR-shaped and V-shaped terms: no line separates them
        logit = 2.0 * np.sign(x[:, 0] * x[:, 1]) + 1.5 * (np.abs(x[:, 2]) - 0.8) + effect
    else:            # the same columns, one straight line
        logit = 1.5 * x[:, 0] - 1.0 * x[:, 1] + 0.5 * x[:, 2] + effect
    logit += rng.normal(scale=noise, size=n)   # 1.0 leaves the best recipe short of a perfect score
    df = pd.DataFrame({f"x{i}": x[:, i] for i in range(4)})
    df["colour"] = colour.astype(object)
    df["size"] = size.astype(object)
    if n_classes == 2:
        threshold = np.quantile(logit, 1 - imbalance)   # the top `imbalance` share is the positive class
        df[TARGET] = (logit > threshold).astype(int)
    else:            # equal-width bands of the logit: an ordinal multiclass target
        edges = np.quantile(logit, np.linspace(0, 1, n_classes + 1)[1:-1])
        df[TARGET] = np.digitize(logit, edges).astype(int)
    return df
