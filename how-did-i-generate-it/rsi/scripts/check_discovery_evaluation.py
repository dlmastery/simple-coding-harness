"""Audit a completed paired evaluation from hashes, choices and prediction rows."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(work):
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise ValueError(name)

    for row in pd.read_csv(work / "SOURCE-FREEZE.csv").itertuples():
        require("source/" + row.path, sha(work / "source" / row.path) == row.sha256)
    for row in pd.read_csv(work / "DATA-FREEZE.csv").itertuples():
        require("data/" + row.path, sha(work / row.path) == row.sha256)
    results = pd.read_csv(work / "RESULTS.csv")
    order = pd.read_csv(work / "ORDER.csv")
    selected = pd.read_csv(work / "SELECTED.csv")
    require("choices_frozen", f"Selected table SHA256: {sha(work / 'SELECTED.csv')}" in
            (work / "SELECTION-CLOSED.md").read_text(encoding="utf-8"))
    require("unique_task_arm", not results.duplicated(["seed", "arm"]).any())
    require("all_planned_arms", set(zip(order.seed, order.arm)) == set(zip(results.seed, results.arm)))
    require("all_choices_reported", set(zip(selected.seed, selected.arm)) == set(zip(results.seed, results.arm)))
    recovery = work / "standby-recovery"
    if recovery.exists():
        for item in pd.read_csv(recovery / "EFFECTIVE-FREEZE.csv").itertuples():
            require("recovery/freeze/" + item.path, sha(work / item.path) == item.sha256)
        old_order = pd.read_csv(recovery / "original-ORDER.csv")
        reconstructed = order.copy()
        reconstructed.loc[reconstructed.seed == 8123, "seed"] = 8105
        require("recovery/single_task_replacement", reconstructed.equals(old_order))
        require("recovery/source_unchanged", sha(work / "SOURCE-FREEZE.csv") == sha(recovery / "original-SOURCE-FREEZE.csv"))
        old_data = dict(pd.read_csv(recovery / "original-DATA-FREEZE.csv").itertuples(index=False, name=None))
        new_data = dict(pd.read_csv(work / "DATA-FREEZE.csv").itertuples(index=False, name=None))
        require("recovery/original_data_preserved", all(new_data.get(k) == v for k, v in old_data.items()))
        require("recovery/only_replacement_data_added", set(new_data) - set(old_data) ==
                {"public/task-8123.npz", "evaluator/task-8123.npz"})
        require("recovery/task_pairing", 8105 not in set(results.seed) and 8123 in set(results.seed))
        exclusion = pd.read_csv(recovery / "EXCLUSION.csv").iloc[0]
        excluded_tree = work / "rollouts/8105/broad-stop/TREE.csv"
        require("recovery/failed_history_unchanged", sha(excluded_tree) == exclusion.original_tree_sha256)
        failed = pd.read_csv(excluded_tree)
        require("recovery/extra_cost_retained", len(failed) == exclusion.interrupted_attempts and
                np.isclose(failed.seconds.sum(), exclusion.recorded_worker_seconds))
        require("recovery/unused_task_not_scored", not (work / "scoring/8105").exists())
    for row in results.itertuples():
        label = f"{row.seed}/{row.arm}"
        rollout = work / "rollouts" / str(row.seed) / row.arm
        public_path = work / "public" / f"task-{row.seed}.npz"
        public = np.load(public_path, allow_pickle=False)
        final = np.load(work / "evaluator" / f"task-{row.seed}.npz", allow_pickle=False)
        require(label + "/same_public_data", sha(public_path) == sha(rollout / "data.npz"))
        require(label + "/final_absent_from_rollout", not any("final" in key for key in public.files))
        require(label + "/disjoint_rows", not (set(public["train_ids"]) & set(public["selection_ids"])) and
                not (set(final["final_ids"]) & (set(public["train_ids"]) | set(public["selection_ids"]))))
        require(label + "/fixed_sizes", len(public["y_train"]) == 1200 and len(public["y_selection"]) == 800
                and len(final["y_final"]) == 1000)
        tree = pd.read_csv(rollout / "TREE.csv")
        require(label + "/tree_identity", sha(rollout / "TREE.csv") == row.tree_sha256)
        valid = tree[tree.status == "ok"]
        require(label + "/selected_by_selection", valid.loc[valid.loss.idxmin(), "node"] == row.node)
        require(label + "/candidate_identity", sha(rollout / "nodes" / row.node / "workspace/candidate.py") == row.candidate_sha256)
        require(label + "/actual_attempts", len(tree) == row.attempts <= 12)
        require(label + "/charged_time", np.isclose(tree.seconds.sum(), row.worker_seconds))
        require(label + "/actual_failures", tree.status.ne("ok").sum() == row.failures)
        checks_path = rollout / "CHECKS.csv"
        require(label + "/online_checks", checks_path.exists() and pd.read_csv(checks_path).passed.all())
        scoring = work / "scoring" / str(row.seed) / row.arm
        process = pd.read_csv(scoring / "process.csv").iloc[0]
        require(label + "/refit_succeeded", process.returncode == 0 and (scoring / "COMPLETED.md").exists())
        require(label + "/separate_refit_charge", process.seconds > 0 and np.isclose(process.seconds, row.scoring_process_seconds))
        pred = pd.read_csv(scoring / "predictions.csv")
        require(label + "/final_row_ids", np.array_equal(pred.row_id, final["final_ids"]))
        require(label + "/final_targets", np.allclose(pred.actual, final["y_final"], atol=1e-12, rtol=1e-12))
        require(label + "/finite_predictions", np.isfinite(pred.predicted).all())
        y, p = final["y_final"], pred.predicted.to_numpy()
        if row.kind == "classification":
            recalls = [np.count_nonzero(p[y == c] == c) / np.count_nonzero(y == c) for c in np.unique(y)]
            score = sum(recalls) / len(recalls)
            loss = 2 * (1 - score)
        else:
            score = np.sum(np.abs(y - p)) / len(y)
            reference_error = np.sum(np.abs(y - np.median(public["y_train"]))) / len(y)
            loss = score / reference_error
        require(label + "/final_metric", np.isclose(score, row.final_score, atol=1e-12, rtol=1e-12))
        require(label + "/normalized_loss", np.isclose(loss, row.final_loss, atol=1e-12, rtol=1e-12))
        require(label + "/separate_utility", np.isclose(loss + .001 * row.worker_seconds, row.utility))
    for contrast in pd.read_csv(work / "PAIRED.csv").itertuples():
        left = results[results.arm == "evolved"].set_index("seed")[contrast.metric]
        right = results[results.arm == contrast.reference].set_index("seed")[contrast.metric]
        delta = left - right
        prefix = f"paired/{contrast.reference}/{contrast.metric}"
        require(prefix + "/count", len(delta) == contrast.tasks and delta.notna().all())
        require(prefix + "/mean", np.isclose(delta.mean(), contrast.mean_evolved_minus_reference))
        require(prefix + "/outcomes", int((delta < -1e-10).sum()) == contrast.lower and
                int((delta > 1e-10).sum()) == contrast.higher and int((delta.abs() <= 1e-10).sum()) == contrast.tied)
    pd.DataFrame(checks).to_csv(work / "EVALUATION-CHECKS.csv", index=False)
    print(f"{len(checks)} independent evaluation checks passed; {len(results)} actual paired arms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
