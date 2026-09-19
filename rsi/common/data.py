"""Step 00 - the data: the bundled Adult sample, the full table on request, the
dataset profile the memory cards condition on, and the one split every step shares.

The bundled 6,000-row sample keeps every step offline. RSI_FULL=1 asks for the
full 48,842-row table: from the cache under ~/.simple-harness/rsi/ when it is
there, else from OpenML (network), which fills the cache.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd

# plain-Python strings: pandas 3 otherwise backs text with pyarrow, whose DLLs crash
# on some Windows machines when scikit-learn was imported first
pd.options.mode.string_storage = "python"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE = DATA_DIR / "adult_sample.csv"
CACHE = Path.home() / ".simple-harness" / "rsi" / "adult_full.csv"
TARGET = "target"


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


def clean(df):
    """Categoricals as plain strings with "missing" for NaN, the target as int.
    Cleaning is fixed here on purpose: it is not a recipe field and no step searches it."""
    df = df.copy()
    for col in df.columns:
        if col != TARGET and not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), "missing").astype(str).astype(object)
    df[TARGET] = df[TARGET].astype(int)
    return df


def categorical_columns(df):
    return [c for c in df.columns if c != TARGET and not pd.api.types.is_numeric_dtype(df[c])]


def profile(df):
    """What a card is allowed to condition on: five numbers about the table, nothing about the signal."""
    cats = categorical_columns(df)
    share = float(df[TARGET].mean())
    return {
        "rows": int(len(df)),
        "cols": int(df.shape[1] - 1),
        "categorical": len(cats),
        "max_cardinality": int(max((df[c].nunique() for c in cats), default=0)),
        "minority_share": round(min(share, 1 - share), 3),
    }


def split_frame(df, seed=0):
    """One shuffle, four disjoint parts: train 55 %, val 15 %, private 10 %, test 20 %.
    The same seed gives the same rows in the same order on every machine: the split is a constant."""
    order = np.random.default_rng(seed).permutation(len(df))
    n = len(df)
    parts = np.split(order, [int(n * 0.55), int(n * 0.70), int(n * 0.80)])
    names = ["train", "val", "private", "test"]
    return {name: df.iloc[idx].reset_index(drop=True) for name, idx in zip(names, parts)}
