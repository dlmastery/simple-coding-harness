"""Audit the paired harness development without fitting another model."""
import argparse
import ast
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

    source = work / "source"
    for item in pd.read_csv(work / "SOURCE-FREEZE.csv").itertuples():
        require(f"source/{item.path}", sha(source / item.path) == item.sha256)
    for item in pd.read_csv(work / "DATA-FREEZE.csv").itertuples():
        require(f"data/{item.path}", sha(work / item.path) == item.sha256)
    order = pd.read_csv(work / "ORDER.csv")
    result = pd.read_csv(work / "RESULTS.csv")
    require("six_paired_tasks", set(order.seed) == set(range(3101, 3107)) and len(order) == 12)
    require("unique_arms", not order.duplicated(["seed", "arm"]).any())
    require("all_planned_arms", set(zip(order.seed, order.arm)) == set(zip(result.seed, result.arm)) and len(result) == 12)
    require("no_final_data", not list(work.rglob("*final*.npz")))
    require("no_live_workers", not list(work.rglob(".running")))
    parent_source = source / "rsi/experiments/tabular-discovery"
    child_source = source / "rsi/experiments/harness-revision"
    for item in result.itertuples():
        prefix = f"{item.seed}/{item.arm}"
        rollout = work / "rollouts" / str(item.seed) / item.arm
        require(prefix + "/online_checks", pd.read_csv(rollout / "CHECKS.csv").passed.all())
        tree = pd.read_csv(rollout / "TREE.csv")
        require(prefix + "/tree_identity", sha(rollout / "TREE.csv") == item.tree_sha256)
        require(prefix + "/data_identity", sha(rollout / "data.npz") == sha(work / "data" / f"task-{item.seed}.npz"))
        require(prefix + "/policy_identical", sha(rollout / "policy.py") == sha(parent_source / "round_robin.py"))
        contract = dict(pd.read_csv(rollout / "contract.csv", dtype=str).itertuples(index=False, name=None))
        require(prefix + "/budget", contract["attempts"] == "12" and float(contract["worker_seconds"]) == 120)
        require(prefix + "/attempts", item.attempts == len(tree) and len(tree) <= 12)
        require(prefix + "/failures", item.failures == tree.status.ne("ok").sum())
        require(prefix + "/worker_cost", np.isclose(item.worker_seconds, tree.seconds.sum(), atol=1e-9))
        require(prefix + "/fit_cost", np.isclose(item.fit_seconds, tree.fit_seconds.sum(), atol=1e-9))
        valid = tree[tree.status == "ok"]
        require(prefix + "/has_result", len(valid) > 0)
        best = valid.loc[valid.loss.idxmin()]
        require(prefix + "/selection", item.node == best.node and np.isclose(item.score, best.score) and np.isclose(item.loss, best.loss))
        engine_source = child_source if item.arm == "child" else parent_source
        require(prefix + "/proposer", sha(rollout / "proposer.py") == sha(engine_source / "proposer.py"))
        candidates = []
        for directory in [rollout / "root"] + list((rollout / "nodes").glob("*/workspace")):
            require(prefix + f"/engine/{directory.parent.name}", sha(directory / "engine.py") == sha(engine_source / "engine.py"))
            if item.arm == "child":
                require(prefix + f"/parent_engine/{directory.parent.name}", sha(directory / "parent_engine.py") == sha(parent_source / "engine.py"))
            constants = {}
            for node in ast.parse((directory / "candidate.py").read_text()).body:
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                    for name in node.targets:
                        if isinstance(name, ast.Name):
                            constants[name.id] = node.value.value
            candidates.append(constants)
        if item.arm == "child":
            require(prefix + "/new_basis_executed", any(x.get("TRANSFORM") == "quadratic-splines" for x in candidates))
        else:
            require(prefix + "/new_basis_absent", all(x.get("TRANSFORM") != "quadratic-splines" for x in candidates))

    paired = pd.read_csv(work / "PAIRED.csv").set_index("seed")
    parent = result[result.arm == "parent"].set_index("seed")
    child = result[result.arm == "child"].set_index("seed").loc[parent.index]
    delta = child.loss - parent.loss
    require("paired_identity", set(paired.index) == set(parent.index))
    require("paired_parent", np.allclose(paired.loc[parent.index].parent_loss, parent.loss, atol=1e-12))
    require("paired_child", np.allclose(paired.loc[parent.index].child_loss, child.loss, atol=1e-12))
    require("paired_delta", np.allclose(paired.loc[parent.index].child_minus_parent, delta, atol=1e-12))
    kinds = {kind: float(delta[parent.kind == kind].mean()) for kind in parent.kind.unique()}
    passed = bool(np.isfinite(delta).all() and delta.mean() <= -.01
                  and all(value <= 0 for value in kinds.values())
                  and child.failures.sum() <= parent.failures.sum())
    require("gate_recomputed", f"Passed: {passed}\n" in (work / "GATE.md").read_text())
    pd.DataFrame(checks).to_csv(work / "EVALUATION-CHECKS.csv", index=False)
    (work / "REPORT.md").write_text(
        "# Paired inner-harness development\n\n"
        f"Independent checks passed: {len(checks)}.\n\n"
        + (work / "GATE.md").read_text()
        + "\nThe changed builder and proposer were inherited by actual candidate workspaces. "
        "Both arms kept the same broad search policy, public task, split, model seed and budget. "
        "The coding agent authored the revision from development evidence and the public generator. "
        "The inner proposer is deterministic, not an LLM.\n\n"
        "This result concerns six development instances from a known synthetic grammar. "
        "Selection scores are not independent final scores. A passing gate authorizes a separate "
        "frozen comparison; it does not establish RSI, unseen-family transfer or net research-cost savings.\n",
        encoding="utf-8")
    print(f"{len(checks)} independent checks passed; development gate: {passed}; zero additional fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
