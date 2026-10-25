"""Plot the four declared decision replays; these are not four new model fits."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("workspace", type=Path)
args = parser.parse_args()
with (args.workspace / "08-04/FOUR-ARMS.csv").open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
values = {(r["skill"], r["memory"]): float(r["cached_balanced_accuracy"]) for r in rows}
assert len(values) == 4
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
fig, ax = plt.subplots(figsize=(7.5, 5.4), constrained_layout=True)
x = np.arange(2)
for memory, label, offset, color in [("False", "Without memory", -0.18, "#3A718F"), ("True", "With restrictive memory", 0.18, "#B56538")]:
    bars = ax.bar(x + offset, [values[(skill, memory)] for skill in ("parent", "child")], 0.34, color=color, label=label)
    ax.bar_label(bars, fmt="%.3f", padding=5, fontsize=12)
ax.set(xticks=x, xticklabels=["Parent skill", "Changed skill"], ylim=(0, 1), ylabel="Selected candidate's balanced accuracy")
ax.spines[["right", "top"]].set_visible(False)
ax.axhline(0.5, color="#999999", linewidth=0.8, linestyle=":")
ax.legend(loc="upper left", frameon=False, fontsize=10)
ax.set_title("A saved rule blocks a useful choice", fontsize=16, pad=28)
fig.text(0.5, 0.905, "Four deterministic choices over checked wine predictions; no new fits", ha="center", fontsize=10, color="#555555")
fig.savefig(args.workspace / "08-04/memory-interaction.png", dpi=160, facecolor="white")
