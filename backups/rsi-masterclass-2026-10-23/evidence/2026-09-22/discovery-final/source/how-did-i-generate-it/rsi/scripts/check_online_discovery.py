"""Recompute scores and verify actual parent workspace inheritance; no fits."""
import argparse
import csv
import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "rsi/tools"))
from discovery import World, replay
from discovery_run import load_module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(work):
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    limits = dict(pd.read_csv(work / "contract.csv", dtype=str).itertuples(index=False, name=None))
    for name, key in (("data.npz", "data_sha256"), ("policy.py", "policy_sha256"), ("proposer.py", "proposer_sha256")):
        require(f"frozen/{name}", digest(work / name) == limits[key])
    data = np.load(work / "data.npz", allow_pickle=False)
    require("split_disjoint", not set(data["train_ids"]) & set(data["selection_ids"]))
    table = pd.read_csv(work / "TREE.csv", keep_default_na=False)
    require("closed", (work / "CLOSED.md").exists())
    require("attempt_limit", len(table) <= int(limits["attempts"]))
    require("worker_budget", table.seconds.sum() <= float(limits["worker_seconds"]) + .5)
    require("no_pending_or_hidden_attempt", len(list((work / "nodes").glob("node-*"))) == len(table))
    require("unique_nodes", not table.node.duplicated().any())
    seen, expanded = {"root"}, set()
    for row in table.itertuples():
        trial = work / "nodes" / row.node
        require(row.node + "/parent_seen", row.parent in seen)
        require(row.node + "/parent_eligible", row.parent == "root" or row.parent not in expanded)
        require(row.node + "/charged_cost", row.seconds > 0)
        require(row.node + "/source_used", digest(trial / "workspace/candidate.py") == row.candidate_sha256)
        parent_manifest = (work / "root-manifest.csv" if row.parent == "root"
                           else work / "nodes" / row.parent / "workspace-manifest.csv")
        parent_workspace = work / "root" if row.parent == "root" else work / "nodes" / row.parent / "workspace"
        require(row.node + "/inherited_manifest", (trial / "inherited-manifest.csv").read_bytes() == parent_manifest.read_bytes())
        for item in pd.read_csv(parent_manifest).itertuples():
            require(f"{row.node}/parent/{item.path}", digest(parent_workspace / item.path) == item.sha256)
        for item in pd.read_csv(trial / "workspace-manifest.csv").itertuples():
            require(f"{row.node}/snapshot/{item.path}", digest(trial / "workspace" / item.path) == item.sha256)
        seen.add(row.node)
        expanded.add(row.parent)
        if row.status != "ok":
            require(row.node + "/no_failure_score", row.loss == "" and row.score == "")
            continue
        predictions = pd.read_csv(trial / "predictions.csv")
        require(row.node + "/row_ids", np.array_equal(predictions.row_id, data["selection_ids"]))
        require(row.node + "/target_identity", np.allclose(predictions.actual, data["y_selection"], rtol=1e-12, atol=1e-12))
        y, predicted = data["y_selection"], predictions.predicted.to_numpy()
        require(row.node + "/finite", np.isfinite(predicted).all())
        if str(data["kind"]) == "classification":
            score = np.mean([(predicted[y == label] == label).mean() for label in np.unique(y)])
            loss = 2 * (1 - score)
        else:
            score = np.abs(y - predicted).mean()
            loss = score / np.abs(y - np.median(data["y_train"])).mean()
        require(row.node + "/score", np.isclose(float(row.score), score, rtol=1e-10, atol=1e-10))
        require(row.node + "/normalized_loss", np.isclose(float(row.loss), loss, rtol=1e-10, atol=1e-10))
    # Replaying the executed policy for its full allocation must recover the same realized history.
    policy = load_module(work / "policy.py", "checked_policy")
    result = replay(World.read(work / "TREE.csv"), policy.choose, int(limits["attempts"]))
    require("replay_recovers_online_order", [item.node for item in result.observations] == table.node.tolist())
    require("replay_has_no_unknown_requests", result.unknown_requests == 0)
    require("replay_cost_matches", np.isclose(result.represented_seconds, table.seconds.sum()))
    valid = table[table.status == "ok"].copy()
    selected = valid.loc[pd.to_numeric(valid.loss).idxmin(), "node"] if len(valid) else "none"
    require("selection_matches_report", f"Selected node: {selected}\n" in (work / "CLOSED.md").read_text())
    pd.DataFrame(checks).to_csv(work / "CHECKS.csv", index=False)
    print(f"{len(checks)} checks passed; {len(table)} actual attempts; selected {selected}; online/replay order matches")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
