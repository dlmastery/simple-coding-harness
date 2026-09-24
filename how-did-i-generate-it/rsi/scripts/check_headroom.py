"""Independently check pilot scores, partitions and replay accounting; no fits."""
import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(work):
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    tasks = pd.read_csv(work / "tasks.csv")
    results = pd.read_csv(work / "results.csv")
    recipes = pd.read_csv(work / "recipes.csv").recipe.tolist()
    require("exact_attempt_count", len(results) == len(tasks) * len(recipes))
    require("unique_attempts", not results.duplicated(["task", "recipe"]).any())
    for task in tasks.itertuples():
        require(f"{task.task}/prepared_data_identity", digest(work / f"{task.task}.npz") == task.data_sha256)
        data = np.load(work / f"{task.task}.npz", allow_pickle=False)
        require(f"{task.task}/partition_disjoint", not set(data["train_ids"]) & set(data["selection_ids"]))
        require(f"{task.task}/partition_count", len(data["selection_ids"]) == task.selection_rows)
        y = data["y_selection"]
        for row in results[results.task == task.task].itertuples():
            key = f"{task.task}/{row.recipe}"
            require(key + "/terminal_status", row.status in ("ok", "failed", "timeout"))
            require(key + "/charged_time", row.process_seconds > 0)
            if row.status != "ok":
                require(key + "/failure_has_no_score", pd.isna(row.score))
                continue
            predictions = pd.read_csv(work / "attempts" / task.task / row.recipe / "predictions.csv")
            require(key + "/row_ids", np.array_equal(predictions.row_id, data["selection_ids"]))
            require(key + "/targets", np.allclose(predictions.actual, y, rtol=1e-12, atol=1e-12))
            require(key + "/finite_predictions", np.isfinite(predictions.predicted).all())
            if task.kind == "regression":
                score = np.abs(y - predictions.predicted.to_numpy()).mean()
                normalization = np.abs(y - np.median(data["y_train"])).mean()
                loss = score / normalization
            else:
                classes = np.unique(y)
                score = np.mean([(predictions.predicted.to_numpy()[y == label] == label).mean()
                                 for label in classes])
                loss = (1 - score) / (1 - 1 / len(classes))
            require(key + "/score_from_predictions", np.isclose(row.score, score, rtol=1e-10, atol=1e-10))
            require(key + "/normalized_loss", np.isclose(row.normalized_loss, loss, rtol=1e-10, atol=1e-10))
    replays = pd.read_csv(work / "headroom-replays.csv")
    require("exact_replay_count", len(replays) == len(tasks) * 3 * 33)
    for row in replays.itertuples():
        table = results[results.task == row.task].set_index("recipe")
        order = recipes if row.policy == "fixed_diverse" else np.random.default_rng(row.seed + 602).permutation(recipes)
        visited = list(order[:row.budget])
        losses = table.normalized_loss.fillna(np.inf)
        expected = losses.loc[visited].min()
        prefix = f"replay/{row.task}/{row.policy}/{row.budget}/{row.seed}"
        require(prefix + "/chosen_candidate_visited", row.best_recipe in visited)
        require(prefix + "/best_observed_loss", np.isclose(row.normalized_loss, expected))
        require(prefix + "/headroom", np.isclose(row.headroom, expected - losses.min()))
        require(prefix + "/cost", np.isclose(row.charged_process_seconds, table.loc[visited].process_seconds.sum()))
    pd.DataFrame(checks).to_csv(work / "CHECKS.csv", index=False)
    print(f"{len(checks)} checks passed; {len(results)} real attempt records; {len(replays)} replay trajectories")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    check(args.workspace.resolve())
