"""Independent prediction and accounting checks for the operator pilot."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def check(work):
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    for row in pd.read_csv(work / "SOURCE-IDENTITIES.csv").itertuples():
        actual = hashlib.sha256((work / row.path).read_bytes()).hexdigest()
        require(f"source/{row.path}", actual == row.sha256)
    records = pd.read_csv(work / "extension-results.csv")
    tasks = pd.read_csv(work / "tasks.csv")
    require("72_attempts", len(records) == 72)
    require("unique_attempts", not records.duplicated(["task", "recipe"]).any())
    for task in tasks.itertuples():
        data = np.load(work / f"{task.task}.npz", allow_pickle=False)
        require(f"{task.task}/split_disjoint", not set(data["train_ids"]) & set(data["selection_ids"]))
        y = data["y_selection"]
        for row in records[records.task == task.task].itertuples():
            key = f"{task.task}/{row.recipe}"
            require(key + "/terminal", row.status in ("ok", "failed", "timeout"))
            require(key + "/charged_cost", row.process_seconds > 0)
            if row.status != "ok":
                require(key + "/no_failure_score", pd.isna(row.score))
                continue
            frame = pd.read_csv(work / "attempts" / task.task / row.recipe / "predictions.csv")
            require(key + "/row_ids", np.array_equal(frame.row_id, data["selection_ids"]))
            require(key + "/targets", np.allclose(frame.actual, y, rtol=1e-12, atol=1e-12))
            predictions = frame.predicted.to_numpy()
            require(key + "/finite", np.isfinite(predictions).all())
            if task.task == "bike":
                require(key + "/count_domain", (predictions >= 0).all())
            if task.kind == "regression":
                score = np.abs(y - predictions).mean()
                loss = score / np.abs(y - np.median(data["y_train"])).mean()
            else:
                labels = np.unique(y)
                score = np.mean([(predictions[y == label] == label).mean() for label in labels])
                loss = (1 - score) / (1 - 1 / len(labels))
            require(key + "/score", np.isclose(row.score, score, rtol=1e-10, atol=1e-10))
            require(key + "/normalized_loss", np.isclose(row.normalized_loss, loss, rtol=1e-10, atol=1e-10))
    combined = pd.read_csv(work / "combined-results.csv")
    require("360_combined_attempts", len(combined) == 360)
    require("60_candidates_per_task", combined.groupby("task").recipe.nunique().eq(60).all())
    old = pd.read_csv(work / "base-results.csv")
    require("base_scores_unchanged", np.array_equal(combined.iloc[:288].score, old.score))
    original = pd.read_csv(work / "base-recipes.csv").recipe.tolist()[:8]
    expanded = [f"{family}-0" for family in ("linear", "forest", "boost", "kernel", "neighbors", "extra")]
    expanded += ["linear-0-pairwise", "linear-0-quantile"]
    for row in pd.read_csv(work / "headroom.csv").itertuples():
        table = combined[combined.task == row.task].set_index("recipe")
        permitted = original if row.control == "original_diverse" else expanded
        losses = table.normalized_loss.fillna(np.inf)
        key = f"comparison/{row.task}/{row.control}"
        require(key + "/candidate_allowed", row.selected in permitted)
        require(key + "/best_within_budget", losses[row.selected] == losses.loc[permitted].min())
        require(key + "/reference", losses[row.reference] == losses.min())
        require(key + "/headroom", np.isclose(row.normalized_headroom, losses[row.selected] - losses.min()))
    pd.DataFrame(checks).to_csv(work / "CHECKS.csv", index=False)
    print(f"{len(checks)} checks passed; 72 new attempts; base records remain unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
