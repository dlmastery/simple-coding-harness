"""Plot checked native scores; all six procedures and tasks remain visible."""
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"
ARMS = ["fixed", "random", "memory", "parent", "harness", "updater"]
COLORS = ["#203C55", "#718496", "#9DCBC7", "#9B94B8", "#C49A56", "#087E83"]


def main():
    checks = pd.read_csv(WORK / "FINAL-CHECKS.csv")
    if checks.empty or not checks.passed.eq(True).all():
        raise ValueError("Checked final results required")
    scores = pd.read_csv(WORK / "NATIVE-SCORES.csv").set_index("task")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(3, 2, figsize=(15, 11))
    for ax, (task, row) in zip(axes.flat, scores.iterrows()):
        values = [row[arm] for arm in ARMS]
        bars = ax.bar(ARMS, values, color=COLORS, width=.65)
        classification = row.metric == "balanced_accuracy"
        ax.set_title(f"{row.task_name} · task {task}", loc="left", weight="bold", color="#203C55")
        ax.set_ylabel("Balanced accuracy · higher is better" if classification else "MAE · lower is better")
        ax.set_ylim(0, 1.12 if classification else max(values)*1.25)
        for bar, value in zip(bars, values):
            if pd.notna(value):
                ax.text(bar.get_x()+bar.get_width()/2, value, f"{value:.4f}", ha="center", va="bottom", fontsize=10)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
    fig.suptitle("Final scores after the same eight search attempts", fontsize=23, weight="bold", color="#203C55", y=.98)
    fig.text(.055, .925, "Six frozen procedures. Six reserved public tasks. All 36 choices fixed before final scoring.", fontsize=13)
    fig.text(.055, .028, "Source: checked SCORES.csv and NATIVE-SCORES.csv. One split and model seed per task; no general-superiority claim.\nClassification and regression use different native metrics. Search cost is equal in fit count; development and scoring cost are additional.", fontsize=10, color="#42566B")
    fig.tight_layout(rect=[.025, .08, .99, .90], h_pad=3)
    for suffix in ("png", "svg"):
        fig.savefig(WORK / f"native-score-comparison.{suffix}", dpi=160, facecolor="white")
    plt.close(fig)
    destination = WORK / "analysis-source"
    destination.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__), destination / Path(__file__).name)
    print("Rendered native-score-comparison.png and .svg from checked results; zero fits")


if __name__ == "__main__":
    main()
