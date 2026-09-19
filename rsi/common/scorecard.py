"""Step 01 - the scorecard: one JSON file with the numbers a claim is made of.

The search never reads it. It is written for the reader and for step 03, which
adds the locked test score and the transfer run to it.
"""

import json
from pathlib import Path

from common.arm import best_of, mean_std, wasted


def write_scorecard(path, card):
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        json.dump(card, f, indent=2)
        f.write("\n")


def read_scorecard(path):
    with open(Path(path), encoding="utf-8") as f:
        return json.load(f)


def arm_summary(per_seed):
    """per_seed: {seed: rows}. Mean and std of the best validation AUC, and the wasted fits, over seeds."""
    bests = {seed: best_of(rows)[0] for seed, rows in per_seed.items()}
    mean, std = mean_std(bests.values())
    return {
        "best_val_auc_per_seed": bests,
        "mean_best_val_auc": mean,
        "std_best_val_auc": std,
        "wasted_fits": sum(wasted(rows) for rows in per_seed.values()),
        "fits": sum(len(rows) for rows in per_seed.values()),
    }
