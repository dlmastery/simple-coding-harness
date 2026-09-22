"""Independently audit and analyze the frozen two-harness final comparison."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(work):
    checks = []

    def require(label, condition):
        checks.append(dict(check=label, passed=bool(condition)))
        if not condition:
            raise AssertionError(label)

    for row in pd.read_csv(work / "SOURCE-FREEZE.csv").itertuples():
        require("source/" + row.path, sha(work / "source" / row.path) == row.sha256)
    for row in pd.read_csv(work / "DATA-FREEZE.csv").itertuples():
        require("data/" + row.path, sha(work / row.path) == row.sha256)
    results = pd.read_csv(work / "RESULTS.csv")
    order = pd.read_csv(work / "ORDER.csv")
    selected = pd.read_csv(work / "SELECTED.csv")
    require("declared_tasks", set(order.seed) == set(range(9101, 9113)) and len(order) == 24)
    require("unique_arms", not results.duplicated(["seed", "arm"]).any() and len(results) == 24)
    require("all_planned", set(zip(order.seed, order.arm)) == set(zip(results.seed, results.arm)))
    require("choices_frozen", f"Selected table SHA256: {sha(work / 'SELECTED.csv')}" in (work / "SELECTION-CLOSED.md").read_text())
    require("all_choices_reported", len(selected) == len(results))
    for name in selected.columns:
        if pd.api.types.is_float_dtype(selected[name]):
            require("selected/" + name, np.allclose(selected[name], results[name], atol=1e-12, rtol=1e-12))
        else:
            require("selected/" + name, selected[name].equals(results[name]))
    require("no_live_workers", not list(work.rglob(".running")))
    parent_source = work / "source/rsi/experiments/tabular-discovery"
    child_source = work / "source/rsi/experiments/harness-revision"
    for row in results.itertuples():
        prefix = f"{row.seed}/{row.arm}"
        rollout = work / "rollouts" / str(row.seed) / row.arm
        require(prefix + "/online_checks", pd.read_csv(rollout / "CHECKS.csv").passed.all())
        require(prefix + "/data_identity", sha(rollout / "data.npz") == sha(work / "public" / f"task-{row.seed}.npz"))
        require(prefix + "/policy", sha(rollout / "policy.py") == sha(parent_source / "round_robin.py"))
        model_source = child_source if row.arm == "child" else parent_source
        require(prefix + "/proposer", sha(rollout / "proposer.py") == sha(model_source / "proposer.py"))
        tree = pd.read_csv(rollout / "TREE.csv")
        require(prefix + "/tree_identity", sha(rollout / "TREE.csv") == row.tree_sha256)
        valid = tree[tree.status == "ok"]
        require(prefix + "/selected_by_selection", valid.loc[valid.loss.idxmin(), "node"] == row.node)
        require(prefix + "/attempts", row.attempts == len(tree) <= 12)
        require(prefix + "/failures", row.failures == tree.status.ne("ok").sum())
        require(prefix + "/cost", np.isclose(row.worker_seconds, tree.seconds.sum()) and np.isclose(row.fit_seconds, tree.fit_seconds.sum()))
        candidate = rollout / "nodes" / row.node / "workspace"
        require(prefix + "/candidate_identity", sha(candidate / "candidate.py") == row.candidate_sha256)
        for directory in [rollout / "root"] + list((rollout / "nodes").glob("*/workspace")):
            require(prefix + f"/engine/{directory.parent.name}", sha(directory / "engine.py") == sha(model_source / "engine.py"))
            if row.arm == "child":
                require(prefix + f"/parent_engine/{directory.parent.name}", sha(directory / "parent_engine.py") == sha(parent_source / "engine.py"))
        public = np.load(work / "public" / f"task-{row.seed}.npz", allow_pickle=False)
        final = np.load(work / "evaluator" / f"task-{row.seed}.npz", allow_pickle=False)
        require(prefix + "/no_final_in_search", not any("final" in name for name in public.files))
        require(prefix + "/split_sizes", len(public["y_train"]) == 1200 and len(public["y_selection"]) == 800 and len(final["y_final"]) == 1000)
        require(prefix + "/disjoint_rows", not set(public["train_ids"]) & set(public["selection_ids"]) and
                not set(final["final_ids"]) & (set(public["train_ids"]) | set(public["selection_ids"])))
        scoring = work / "scoring" / str(row.seed) / row.arm
        process = pd.read_csv(scoring / "process.csv").iloc[0]
        require(prefix + "/scoring_complete", process.returncode == 0 and (scoring / "COMPLETED.md").exists())
        require(prefix + "/scoring_cost", process.seconds > 0 and np.isclose(process.seconds, row.scoring_process_seconds))
        require(prefix + "/selection_reproduced", bool(row.selection_reproduced))
        pred = pd.read_csv(scoring / "predictions.csv")
        require(prefix + "/row_ids", np.array_equal(pred.row_id, final["final_ids"]))
        require(prefix + "/targets", np.allclose(pred.actual, final["y_final"], atol=1e-12, rtol=1e-12))
        require(prefix + "/finite", np.isfinite(pred.predicted).all())
        y, p = final["y_final"], pred.predicted.to_numpy()
        if row.kind == "classification":
            score = np.mean([np.count_nonzero(p[y == c] == c) / np.count_nonzero(y == c) for c in np.unique(y)])
            loss = 2 * (1 - score)
        else:
            score = np.abs(y - p).mean()
            loss = score / np.abs(y - np.median(public["y_train"])).mean()
        require(prefix + "/score", np.isclose(score, row.final_score, atol=1e-12, rtol=1e-12))
        require(prefix + "/loss", np.isclose(loss, row.final_loss, atol=1e-12, rtol=1e-12))
    parent = results[results.arm == "parent"].set_index("seed")
    child = results[results.arm == "child"].set_index("seed").loc[parent.index]
    delta = child.final_loss - parent.final_loss
    rng = np.random.default_rng(20260923)
    boot = delta.to_numpy()[rng.integers(0, len(delta), size=(10000, len(delta)))].mean(axis=1)
    lower, upper = np.quantile(boot, [.025, .975])
    kinds = {kind: float(delta[parent.kind == kind].mean()) for kind in parent.kind.unique()}
    supportive = delta.mean() < 0 and upper < 0 and all(x <= 0 for x in kinds.values())
    pd.DataFrame(dict(seed=parent.index, kind=parent.kind.values, parent_final_score=parent.final_score.values,
        child_final_score=child.final_score.values, parent_final_loss=parent.final_loss.values,
        child_final_loss=child.final_loss.values, child_minus_parent=delta.values)).to_csv(work / "PAIRED.csv", index=False)
    pd.DataFrame(checks).to_csv(work / "EVALUATION-CHECKS.csv", index=False)
    report = ("# A changed inner harness on twelve new tasks\n\n"
        f"Independent checks: {len(checks)} passed.\n\n"
        f"Primary mean normalized final-loss difference, child minus parent: {delta.mean():.9f}.\n"
        f"Paired task-bootstrap 95% interval: [{lower:.9f}, {upper:.9f}].\n"
        f"Task-kind means: {kinds}.\n"
        f"Lower / tied / higher loss: {(delta < -1e-10).sum()} / {(delta.abs() <= 1e-10).sum()} / {(delta > 1e-10).sum()}.\n"
        f"Prespecified supportive-result rule met: {bool(supportive)}.\n\n"
        f"Search attempts: {results.attempts.sum()}; failures: {results.failures.sum()}; separate scoring refits: {len(results)}.\n"
        "See RESULTS.csv for all scores and separate fit, worker-process and scoring costs.\n\n"
        "The child is an agent-authored builder/proposer revision selected on earlier development tasks. "
        "The deterministic inner search inherited its code and ran real model fits. This known synthetic "
        "grammar tests new instances, not new domains. The same coding agent authored and evaluated the method. "
        "No AIDE2 reproduction, improved-updater, ignition or net total-cost claim follows.\n")
    (work / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
