"""Plot retained measured outcomes without running or changing an experiment."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("workspace", type=Path)
args = parser.parse_args()
results = pd.read_csv(args.workspace / "FINAL-RESULTS.csv")
fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), layout="constrained")
fig.set_facecolor("white")
for ax, task, title, unit in zip(axes, ["regression", "classification"],
                               ["Regression: reject the overfit edit", "Classification: keep a useful edit"],
                               ["Final MAE · lower is better", "Final balanced accuracy · higher is better"]):
    rows = results[results.task == task].set_index("improver")
    values = [rows.loc["v0", "parent_final"], rows.loc["v0", "retained_final"], rows.loc["v1", "retained_final"]]
    bars = ax.bar(["Starting\nskill", "v0 retains\nby training", "v1 retains\nby selection"], values,
                  color=["#64748b", "#b45309", "#0f766e"], width=.63)
    ax.set_title(title, fontsize=12, pad=16, weight="bold")
    ax.set_ylabel(unit, fontsize=10)
    ax.set_ylim(0, 100 if task == "regression" else 1.08)
    ax.bar_label(bars, fmt="%.2f", padding=5, fontsize=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, alpha=.15)
fig.suptitle("Changing the promotion rule changes what survives", fontsize=15, weight="bold")
fig.supxlabel("Measured synthetic teaching cases · one split per task · eight fits · same author context", fontsize=10)
fig.savefig(args.workspace / "retained-outcomes.png", dpi=170, facecolor="white")
