"""Plot saved evaluation counts, without running or tuning the learner."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo = Path(__file__).resolve().parents[3]
root = repo / "rsi/evidence/2026-09-20/self-play"
rows = list(csv.DictReader((root / "evaluation-counts.csv").open(encoding="utf-8")))
fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=True)
colors = ("#237c6f", "#d8ab42", "#b85352")
for ax, seat, title in zip(axes, ("all", "X", "O"), ("Both seats • 500 games", "As X • 250 games", "As O • 250 games")):
    selected = [r for r in rows if r["seat"] == seat]
    bottom = [0, 0]
    for category, color in zip(("wins", "draws", "losses"), colors):
        values = [int(r[category]) for r in selected]
        bars = ax.bar(["Untrained", "Trained"], values, bottom=bottom, color=color, label=category.title())
        for bar, value, base in zip(bars, values, bottom):
            if value >= 16:
                ax.text(bar.get_x() + bar.get_width()/2, base + value/2, str(value), ha="center", va="center", color="white" if category != "draws" else "#182b36", fontsize=10)
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.set_title(title, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.15)
axes[0].set_ylabel("Number of evaluation games")
axes[2].legend(frameon=False, loc="upper right")
fig.suptitle("A learned table wins more often against this random opponent", fontsize=14)
fig.text(0.5, 0.025, "One training seed • fixed Monte Carlo learner • no policy updates during evaluation • not evidence of RSI", ha="center", fontsize=9)
fig.tight_layout(rect=(0, 0.07, 1, 0.93))
fig.savefig(root / "evaluation-counts.png", dpi=170, facecolor="white")
print(root / "evaluation-counts.png")
