"""Plot checked parent/child scores; distinguish development from final results."""
import argparse
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot(work):
    if not pd.read_csv(work / "EVALUATION-CHECKS.csv").passed.all():
        raise ValueError("Check the comparison first")
    data = pd.read_csv(work / "RESULTS.csv")
    final = "final_score" in data
    metric = "final_score" if final else "score"
    parent = data[data.arm == "parent"].set_index("seed").sort_index()
    child = data[data.arm == "child"].set_index("seed").loc[parent.index]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                        "axes.spines.right": False, "axes.labelcolor": "#203448", "text.color": "#203448"})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.2), gridspec_kw={"height_ratios": [1.2, 1]})
    fig.subplots_adjust(left=.095, right=.965, bottom=.20, top=.84, hspace=.67, wspace=.34)
    phase = "Final rows" if final else "Development selection rows"
    fig.suptitle(f"A changed inner harness · {len(parent)} paired tasks", x=.07, y=.965, ha="left", fontsize=21, fontweight="bold")
    fig.text(.07, .908, f"{phase}. Same broad policy and per-task allocation; new builder and proposer.", fontsize=12)
    for axis, kind in zip(axes[0], ("classification", "regression")):
        a, b = parent[parent.kind == kind], child[child.kind == kind]
        gain = (b[metric] - a[metric]) * 100 if kind == "classification" else (a[metric] - b[metric]) / a[metric] * 100
        axis.barh(np.arange(len(a)), gain, color=["#12877f" if v >= 0 else "#b5523b" for v in gain])
        axis.set_yticks(np.arange(len(a)), [str(seed) for seed in a.index])
        axis.axvline(0, color="#80919c", linewidth=.8)
        axis.set_title("Classification" if kind == "classification" else "Regression", loc="left", fontweight="bold")
        axis.set_xlabel("Balanced accuracy change (percentage points)" if kind == "classification" else "MAE reduction (%)")
        axis.set_ylabel("Task seed")
        axis.invert_yaxis()
        axis.grid(axis="x", alpha=.15)
        axis.set_axisbelow(True)
    colors = ["#75889b", "#12877f"]
    for axis, column, title in ((axes[1, 0], "attempts", "Actual search attempts"),
                                 (axes[1, 1], "worker_seconds", "Search worker-process seconds")):
        values = [parent[column].sum(), child[column].sum()]
        bars = axis.bar(["Parent harness", "Child harness"], values, color=colors, width=.55)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_ylim(0, max(values) * 1.2)
        for bar, value in zip(bars, values):
            axis.text(bar.get_x() + bar.get_width() / 2, value + max(values) * .03,
                      f"{value:.0f}" if column == "attempts" else f"{value:.1f}", ha="center", fontsize=12)
    fig.text(.07, .116, "Positive top-panel values favor the child. Every task is shown; the report gives the declared gate.", fontsize=10)
    fig.text(.07, .078, "Known synthetic grammar, new instances. An agent-authored harness edit; no improved-updater or ignition claim.", fontsize=9)
    cost_note = f"Costs omit {len(data)} separate scoring refits, development and unmetered agent inference." if final else "Development scores are used for selection, not independent final evidence. No final rows were generated."
    fig.text(.07, .043, cost_note, fontsize=9, color="#5d6c7d")
    for suffix in ("png", "svg"):
        fig.savefig(work / f"quality-and-cost.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)
    (work / "FIGURE-SOURCE.md").write_text(
        "# Measured figure source\n\n"
        f"RESULTS.csv SHA256: {hashlib.sha256((work / 'RESULTS.csv').read_bytes()).hexdigest()}\n"
        f"Plot source SHA256: {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}\n"
        f"Phase: {phase}\nNo image generator supplied numeric results.\n", encoding="utf-8")
    print(f"Saved checked {phase.lower()} chart")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    plot(parser.parse_args().workspace.resolve())
