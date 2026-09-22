"""Draw measured quality and cost separately from a checked evaluation table."""
import argparse
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot(work):
    checks = pd.read_csv(work / "EVALUATION-CHECKS.csv")
    if not checks.passed.all():
        raise ValueError("Independent checks must pass before plotting")
    data = pd.read_csv(work / "RESULTS.csv")
    names = ["broad", "greedy", "lineage", "evolved", "broad-stop"]
    labels = ["Broad", "Greedy", "Lineage", "Evolved", "Broad + stop"]
    palette = ["#8f9eae", "#afb9c6", "#687e9e", "#126f88", "#aabbb7"]
    baseline = data[data.arm == "broad"].set_index("seed")
    evolved = data[data.arm == "evolved"].set_index("seed")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": "#34465a", "text.color": "#172e46"})
    fig, axs = plt.subplots(2, 2, figsize=(13, 8.2))
    fig.subplots_adjust(top=.80, bottom=.17, hspace=.67, wspace=.28)
    fig.text(.07, .95, "Does a changed search policy help?", fontsize=23, weight="bold")
    phase = "Final evaluation" if len(evolved) == 16 else "Prospective shakedown"
    fig.text(.07, .90, f"{phase} · {len(evolved)} paired synthetic tasks · 1,000 separate final rows per task", fontsize=12)
    fig.text(.07, .857, "Quality and actual computation are separate outcomes. Every procedure has the same search allowance.", fontsize=10)
    for axis, kind, title in zip(axs[0], ("classification", "regression"),
                                 ("Classification: change in balanced accuracy", "Regression: reduction in MAE")):
        part = evolved[evolved.kind == kind]
        ref = baseline.loc[part.index]
        if kind == "classification":
            delta = 100 * (part.final_score - ref.final_score)
            ylabel, minimum = "Percentage points; positive is better", 5
        else:
            delta = 100 * (ref.final_score - part.final_score) / ref.final_score
            ylabel, minimum = "Percent of baseline MAE; positive is better", 10
        colors = ["#29866a" if x > 1e-8 else "#bf604e" if x < -1e-8 else "#8f9eae" for x in delta]
        bars = axis.bar([str(seed) for seed in part.index], delta, color=colors, width=.65)
        for bar, value in zip(bars, delta):
            axis.annotate(f"{value:+.2f}", (bar.get_x() + bar.get_width() / 2, value),
                          xytext=(0, 5 if value >= 0 else -12), textcoords="offset points",
                          ha="center", fontsize=8)
        limit = max(minimum, abs(delta).max() * 1.35)
        axis.set_ylim(-limit, limit)
        axis.axhline(0, color="#7f8d9c", linewidth=.8)
        axis.set_title(title, loc="left", fontsize=12, weight="bold", pad=14)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.set_xlabel("Task seed · evolved minus broad search", fontsize=9)
        axis.tick_params(axis="x", labelsize=9)
        axis.set_axisbelow(True)
        axis.grid(axis="y", alpha=.12)
    for axis, field, title, ylabel in zip(axs[1], ("attempts", "worker_seconds"),
        ("Search attempts actually executed", "Measured search worker time"),
        ("Total admitted attempts", "Seconds; includes process startup")):
        values = data.groupby("arm")[field].sum().reindex(names)
        bars = axis.bar(labels, values, color=palette, width=.65)
        axis.bar_label(bars, labels=[f"{x:.0f}" for x in values], padding=4, fontsize=10)
        axis.set_ylim(0, values.max() * 1.22)
        axis.set_title(title, loc="left", fontsize=12, weight="bold", pad=14)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.tick_params(axis="x", labelsize=9)
        axis.set_axisbelow(True)
        axis.grid(axis="y", alpha=.12)
    fig.text(.07, .085, "Known synthetic grammar, new instances. No claim of unseen-domain transfer or general RSI.", fontsize=10)
    fig.text(.07, .053, f"Costs shown exclude {len(data)} separate scoring refits, policy development and unmetered agent inference.", fontsize=9, color="#5d6c7d")
    fig.text(.07, .026, "Source: RESULTS.csv; independent prediction and identity checks: EVALUATION-CHECKS.csv.", fontsize=8, color="#5d6c7d")
    for suffix in ("png", "svg"):
        fig.savefig(work / f"quality-and-cost.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)
    sha = hashlib.sha256((work / "RESULTS.csv").read_bytes()).hexdigest()
    (work / "FIGURE-SOURCE.md").write_text(
        f"# Measured chart source\n\nRESULTS.csv SHA256: {sha}\n"
        "Generated with plot_discovery_evaluation.py after independent checks.\n"
        "Top panels compare evolved and broad search on the same task; bottom panels sum actual search cost.\n"
        "No image generator supplied numeric results.\n", encoding="utf-8")
    print(f"Saved measured PNG and SVG for {len(evolved)} paired tasks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    plot(parser.parse_args().workspace.resolve())
