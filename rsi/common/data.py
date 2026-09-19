"""The data: the bundled Adult sample, the sklearn built-ins, the profile a card
may condition on, and the one four-way split every arm shares.

The bundled 6,000-row Adult sample keeps every lesson offline. RSI_FULL=1 asks
for the full 48,842-row table from the cache under ~/.simple-harness/rsi/, or
from OpenML (network) once, which fills the cache.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd

from common.recipe import TARGET

# plain-Python strings: pandas 3 otherwise backs text with pyarrow, whose DLLs crash
# on some Windows machines when scikit-learn was imported first
pd.options.mode.string_storage = "python"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE = DATA_DIR / "adult_sample.csv"
CACHE = Path.home() / ".simple-harness" / "rsi" / "adult_full.csv"

PROFILE_KEYS = ("n_rows", "n_features", "n_classes", "imbalance", "has_categorical")


def load_adult():
    """The Adult table with a 0/1 `target` column (1 = income above 50K)."""
    if os.environ.get("RSI_FULL") == "1":
        if not CACHE.exists():
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            fetch_full().to_csv(CACHE, index=False, lineterminator="\n", encoding="utf-8")
        return clean(pd.read_csv(CACHE, encoding="utf-8"))
    return clean(pd.read_csv(SAMPLE, encoding="utf-8"))


def fetch_full():
    """OpenML "adult" version 2 (UCI Adult Census Income), 48,842 rows. Network."""
    from sklearn.datasets import fetch_openml

    frame = fetch_openml("adult", version=2, as_frame=True).frame
    frame[TARGET] = (frame.pop("class").astype(str) == ">50K").astype(int)
    return frame


def load_sklearn(name):
    """One of the sklearn built-ins as a frame with an integer `target`: breast_cancer, wine, digits."""
    from sklearn import datasets

    bunch = getattr(datasets, f"load_{name}")()
    df = pd.DataFrame(bunch.data, columns=[str(c).replace(" ", "_") for c in bunch.feature_names])
    df[TARGET] = bunch.target.astype(int)
    return df


def clean(df):
    """Categoricals as plain strings with "missing" for NaN, the target as int.
    Cleaning is fixed here on purpose: it is not a recipe field and no pack searches it."""
    df = df.copy()
    for col in df.columns:
        if col != TARGET and not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), "missing").astype(str).astype(object)
    df[TARGET] = df[TARGET].astype(int)
    return df


def profile(df):
    """What a card is allowed to condition on: five numbers about the table, nothing about the signal."""
    counts = df[TARGET].value_counts(normalize=True)
    return {
        "n_rows": int(len(df)),
        "n_features": int(df.shape[1] - 1),
        "n_classes": int(df[TARGET].nunique()),
        "imbalance": round(float(counts.min()), 3),          # share of the rarest class
        "has_categorical": int(any(df[c].dtype == object for c in df.columns if c != TARGET)),
    }


def split_frame(df, seed=0):
    """One shuffle, four disjoint parts: train 55 %, val 15 %, private 10 %, test 20 %.
    The same seed gives the same rows in the same order on every machine: the split is a constant.
    The private part is the gate's split (step 09); no inner pack ever sees it."""
    order = np.random.default_rng(seed).permutation(len(df))
    n = len(df)
    parts = np.split(order, [int(n * 0.55), int(n * 0.70), int(n * 0.80)])
    names = ["train", "val", "private", "test"]
    return {name: df.iloc[idx].reset_index(drop=True) for name, idx in zip(names, parts)}
