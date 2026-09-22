"""Plot measured development scores; no generated numbers, training or final tests."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot(work):
    results = pd.read_csv(work / "results.csv")
    ids = pd.read_csv(work / "recipes.csv").recipe.tolist()
    task_cards = pd.read_csv(work / "tasks.csv")
    titles = {"bike": "Bike demand", "wine": "Red wine quality", "cancer": "Breast cancer",
              "digits": "Handwritten digits", "friedman": "Friedman regression", "interactions": "Interaction classification"}
    fig, axes = plt.subplots(3, 2, figsize=(13, 11))
    fig.patch.set_facecolor("white")
    curve_records = []
    for ax, task in zip(axes.flat, task_cards.itertuples()):
        table = results[results.task == task.task].set_index("recipe")
        losses = table.normalized_loss.fillna(np.inf)
        reference = table.loc[losses.idxmin(), "score"]
        random_scores, fixed_scores = [], []
        for budget in range(1, 17):
            best = losses.loc[ids[:budget]].idxmin()
            fixed = table.loc[best, "score"]
            values = []
            for seed in range(32):
                visited = np.random.default_rng(seed + 602).permutation(ids)[:budget]
                values.append(table.loc[losses.loc[visited].idxmin(), "score"])
            mean, low, high = np.mean(values), np.quantile(values, .1), np.quantile(values, .9)
            random_scores.append((mean, low, high))
            fixed_scores.append(fixed)
            curve_records.append(dict(task=task.task, budget=budget, fixed_score=fixed,
                                      random_mean=mean, random_p10=low, random_p90=high,
                                      reference_score=reference))
        x = np.arange(1, 17)
        random = np.asarray(random_scores)
        ax.fill_between(x, random[:, 1], random[:, 2], color="#43a0a3", alpha=.17, linewidth=0)
        ax.plot(x, random[:, 0], color="#157b83", linewidth=2, label="Random search: mean")
        ax.plot(x, fixed_scores, color="#ce6b31", linewidth=2, label="Fixed diverse order")
        ax.axhline(reference, color="#243c52", linestyle="--", linewidth=1.5, label="48-fit reference")
        ax.set_title(titles[task.task], loc="left", fontweight="bold", fontsize=13, color="#172f44")
        ax.set_ylabel("Selection MAE (lower is better)" if task.kind == "regression"
                      else "Selection balanced accuracy (higher is better)", fontsize=9)
        ax.set_xlabel("Attempts available to the replayed search", fontsize=9)
        ax.set_xticks([1, 4, 8, 12, 16])
        ax.grid(axis="y", alpha=.2)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=9)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .952), ncol=3, frameon=False)
    fig.suptitle("Does the search budget leave room for better decisions?", x=.06, ha="left",
                 fontsize=20, color="#172f44", weight="bold", y=.99)
    fig.text(.06, .017,
             "Development selection scores only. Each task used 48 actual fits; shorter searches reuse their recorded outcomes.\n"
             "Shading is the 10th–90th percentile over 32 random orders, not a confidence interval. This does not measure RSI gains.",
             fontsize=10, color="#41566b")
    fig.tight_layout(rect=(.025, .065, .99, .925), h_pad=2.5, w_pad=2.5)
    fig.savefig(work / "headroom.png", dpi=160)
    fig.savefig(work / "headroom.svg")
    plt.close(fig)
    pd.DataFrame(curve_records).to_csv(work / "plotted-curves.csv", index=False)
    print("Saved headroom.png, headroom.svg and plotted-curves.csv from real selection scores")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    plot(parser.parse_args().workspace.resolve())
