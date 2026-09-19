"""Write adult_sample.csv: 6,000 rows of OpenML "adult" v2, stratified by the target, seed 0.

    python rsi/data/make_sample.py     # network; fills ~/.simple-harness/rsi/adult_full.csv too
"""

import sys
from pathlib import Path

from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # rsi/, for common

from common.data import CACHE, SAMPLE, TARGET, fetch_full  # noqa: E402

if __name__ == "__main__":
    full = fetch_full()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(CACHE, index=False, lineterminator="\n", encoding="utf-8")
    sample, _ = train_test_split(full, train_size=6000, stratify=full[TARGET], random_state=0)
    sample = sample.sort_index()   # row order from the source table, not from the shuffle
    sample.to_csv(SAMPLE, index=False, lineterminator="\n", encoding="utf-8")
    print(f"wrote {SAMPLE} ({len(sample)} rows, {sample[TARGET].mean():.3f} positive)")
