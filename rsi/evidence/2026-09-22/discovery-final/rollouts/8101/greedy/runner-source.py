"""Agent-operated online discovery with actual workspace inheritance.

Developer task generation, online runs and replay are separate operations.
All local code is trusted cooperative course code, not a security sandbox.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

import numpy as np
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error
from threadpoolctl import threadpool_limits

from discovery import Observation, View, World, replay

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "rsi/experiments/tabular-discovery"
TREE_FIELDS = ("node", "parent", "status", "loss", "seconds", "score", "metric",
               "fit_seconds", "predict_seconds", "policy_seconds", "proposal_seconds", "candidate_sha256")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot_manifest(workspace):
    return [dict(path=p.relative_to(workspace).as_posix(), sha256=sha(p))
            for p in sorted(workspace.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]


def verify_manifest(workspace, rows):
    actual = snapshot_manifest(workspace)
    if actual != rows:
        raise ValueError("Saved workspace identity changed")


def task(path, seed, kind):
    # Restrict this initial command to declared development tasks.
    if seed not in range(1101, 1107) or kind != ("classification" if seed % 2 else "regression"):
        raise ValueError("Only the six declared development tasks are enabled here")
    if path.exists():
        raise ValueError("Preserve existing task")
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(2000, 10))
    coefficients = rng.uniform(.6, 1.4, 4) * rng.choice([-1., 1.], 4)
    family = (seed - 1101) % 3
    if family == 0:
        signal = (coefficients[0] * raw[:, 0] * raw[:, 1] + coefficients[1] * raw[:, 2]
                  + coefficients[2] * raw[:, 3] + .4 * coefficients[3] * raw[:, 4] * raw[:, 5])
    elif family == 1:
        signal = raw[:, :4] @ coefficients
    else:
        signal = (coefficients[0] * (raw[:, 0] ** 2 - 1) + coefficients[1] * raw[:, 1]
                  + coefficients[2] * np.sin(raw[:, 2]) + coefficients[3] * raw[:, 3] * raw[:, 4])
    noisy = signal + rng.normal(scale=.3, size=len(raw))
    y = (noisy > .25).astype(int) if kind == "classification" else noisy
    x = raw * rng.uniform(.3, 4., 10) + rng.normal(size=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, x_train=x[:1200], y_train=y[:1200], x_selection=x[1200:],
                        y_selection=y[1200:], train_ids=np.arange(1200),
                        selection_ids=np.arange(1200, 2000), kind=np.asarray(kind))
    path.with_suffix(".md").write_text(
        f"# Development task {seed}\n\nKind: {kind}\nSignal family index: {family}\n"
        "1,200 training rows; 800 selection rows; ten numeric inputs. No final rows.\n"
        f"Generator SHA256: {sha(__file__)}\nData SHA256: {sha(path)}\n",
        encoding="utf-8")
    print(f"Prepared development task {seed}; no fits or final cases")


def initialize(work, data_path, policy_path, attempts, seconds):
    if work.exists():
        raise ValueError("Use a fresh sibling workspace")
    if not 1 <= attempts <= 24 or not 1 <= seconds <= 600:
        raise ValueError("Unsupported allocation")
    data = np.load(data_path, allow_pickle=False)
    if set(data.files) != {"x_train", "y_train", "x_selection", "y_selection", "train_ids", "selection_ids", "kind"}:
        raise ValueError("Unexpected data roles; final rows must not enter development")
    if set(data["train_ids"]) & set(data["selection_ids"]):
        raise ValueError("Overlapping data roles")
    if data["x_train"].shape[1] > 16:
        raise ValueError("This small pipeline builder is limited to 16 numeric inputs")
    work.mkdir(parents=True)
    shutil.copyfile(data_path, work / "data.npz")
    shutil.copyfile(policy_path, work / "policy.py")
    shutil.copyfile(EXPERIMENT / "proposer.py", work / "proposer.py")
    shutil.copyfile(__file__, work / "runner-source.py")
    shutil.copyfile(Path(__file__).with_name("discovery.py"), work / "replay-source.py")
    root = work / "root"
    root.mkdir()
    shutil.copyfile(EXPERIMENT / "engine.py", root / "engine.py")
    (root / "candidate.py").write_text(
        "FAMILY = 'linear'\nTRANSFORM = 'raw'\nSTRENGTH = 1.0\nSTAGE = -1\n", encoding="utf-8")
    (root / "README.md").write_text("# Initial unscored workspace\n\nNo model has been fitted.\n", encoding="utf-8")
    write_csv(work / "root-manifest.csv", snapshot_manifest(root), ["path", "sha256"])
    contract = dict(data_sha256=sha(work / "data.npz"), policy_sha256=sha(work / "policy.py"),
                    proposer_sha256=sha(work / "proposer.py"), runner_sha256=sha(__file__),
                    replay_sha256=sha(Path(__file__).with_name("discovery.py")),
                    attempts=str(attempts), worker_seconds=str(seconds), model_seed="41")
    write_csv(work / "contract.csv", [dict(key=k, value=v) for k, v in contract.items()], ["key", "value"])
    (work / "CONTRACT.md").write_text(
        f"# Frozen online discovery allocation\n\n{attempts} attempts; {seconds} worker-process seconds; "
        "at most 60 seconds per worker. Failed attempts count.\n"
        "The policy and proposer stay fixed during this rollout. Only observations from completed attempts "
        "enter the policy view. Parent workspace copies are checked before proposal.\n"
        "Policy and proposal time are reported separately. Agent inference costs are unknown. "
        "Local file access is cooperative, not a protected evaluation service.\n", encoding="utf-8")
    write_csv(work / "TREE.csv", [], TREE_FIELDS)
    print(f"Initialized {work.name}; no fits yet")


def contract(work):
    values = {row["key"]: row["value"] for row in read_csv(work / "contract.csv")}
    for name, key in (("data.npz", "data_sha256"), ("policy.py", "policy_sha256"),
                      ("proposer.py", "proposer_sha256")):
        if sha(work / name) != values[key]:
            raise ValueError(f"Frozen input changed: {name}")
    if sha(__file__) != values["runner_sha256"] or sha(Path(__file__).with_name("discovery.py")) != values["replay_sha256"]:
        raise ValueError("Runtime changed; retain the matching source checkout to resume")
    return values


def execute_worker(work, node):
    trial = work / "nodes" / node
    workspace = trial / "workspace"
    data = np.load(work / "data.npz", allow_pickle=False)
    sys.path.insert(0, str(workspace))
    candidate = load_module(workspace / "candidate.py", "candidate")
    model = candidate.build(str(data["kind"]), 41)
    with threadpool_limits(limits=1):
        start = time.perf_counter()
        model.fit(data["x_train"], data["y_train"])
        fit_seconds = time.perf_counter() - start
        start = time.perf_counter()
        prediction = np.asarray(model.predict(data["x_selection"]))
        predict_seconds = time.perf_counter() - start
    if prediction.shape != data["y_selection"].shape or not np.isfinite(prediction).all():
        raise ValueError("Invalid predictions")
    if str(data["kind"]) == "classification":
        score = balanced_accuracy_score(data["y_selection"], prediction)
        loss, metric = 2 * (1 - score), "balanced_accuracy"
    else:
        score = mean_absolute_error(data["y_selection"], prediction)
        denominator = mean_absolute_error(data["y_selection"],
                                          np.full(len(prediction), np.median(data["y_train"])))
        loss, metric = score / denominator, "MAE"
    write_csv(trial / "predictions.csv", [dict(row_id=int(rid), actual=float(y), predicted=float(p))
        for rid, y, p in zip(data["selection_ids"], data["y_selection"], prediction)],
        ["row_id", "actual", "predicted"])
    write_csv(trial / "worker-result.csv", [dict(score=score, loss=loss, metric=metric,
        fit_seconds=fit_seconds, predict_seconds=predict_seconds)],
        ["score", "loss", "metric", "fit_seconds", "predict_seconds"])


def run(work):
    limits = contract(work)
    if (work / "CLOSED.md").exists():
        raise ValueError("Rollout already closed")
    lock = work / ".running"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\nstarted={time.time()}\n")
    try:
        rows = read_csv(work / "TREE.csv")
        folders = list((work / "nodes").glob("node-*")) if (work / "nodes").exists() else []
        if len(folders) != len(rows):
            raise ValueError("Interrupted attempt needs explicit reconciliation; no automatic retry")
        policy = load_module(work / "policy.py", "policy")
        proposer = load_module(work / "proposer.py", "proposer")
        reason = "attempt_limit"
        while len(rows) < int(limits["attempts"]):
            remaining_seconds = float(limits["worker_seconds"]) - sum(float(row["seconds"]) for row in rows)
            if remaining_seconds <= .01:
                reason = "worker_time_limit"
                break
            world = World.read(work / "TREE.csv")
            view = View(world.observations, int(limits["attempts"]) - len(rows))
            started = time.perf_counter()
            parent = policy.choose(view)
            policy_seconds = time.perf_counter() - started
            if parent is None:
                reason = "policy_stop"
                break
            if parent not in view.eligible:
                raise ValueError("Policy requested an unobserved or non-leaf parent")
            node = f"node-{len(rows) + 1:03d}"
            parent_workspace = work / "root" if parent == "root" else work / "nodes" / parent / "workspace"
            parent_manifest = (work / "root-manifest.csv" if parent == "root"
                               else work / "nodes" / parent / "workspace-manifest.csv")
            inherited = read_csv(parent_manifest)
            verify_manifest(parent_workspace, inherited)
            trial = work / "nodes" / node
            trial.mkdir(parents=True)
            (trial / "STARTED.md").write_text(
                f"# Admitted attempt\n\nParent: {parent}\nUnix time: {time.time()}\n"
                f"Worker timeout: {min(60., remaining_seconds)} seconds\n", encoding="utf-8")
            started = time.perf_counter()
            shutil.copytree(parent_workspace, trial / "workspace", ignore=shutil.ignore_patterns("__pycache__"))
            verify_manifest(trial / "workspace", inherited)
            write_csv(trial / "inherited-manifest.csv", inherited, ["path", "sha256"])
            proposer.propose(trial / "workspace", parent == "root", sum(row["parent"] == "root" for row in rows))
            proposal_seconds = time.perf_counter() - started
            candidate_hash = sha(trial / "workspace/candidate.py")
            started = time.perf_counter()
            try:
                result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "worker",
                    "--workspace", str(work), "--node", node], capture_output=True, text=True,
                    timeout=min(60., remaining_seconds))
                (trial / "stdout.txt").write_text(result.stdout, encoding="utf-8")
                (trial / "stderr.txt").write_text(result.stderr, encoding="utf-8")
                status = "ok" if result.returncode == 0 and (trial / "worker-result.csv").exists() else "failed"
            except subprocess.TimeoutExpired as error:
                status = "timeout"
                (trial / "stderr.txt").write_text(str(error), encoding="utf-8")
            elapsed = time.perf_counter() - started
            if sha(trial / "workspace/candidate.py") != candidate_hash:
                raise ValueError("Candidate source changed during execution")
            row = {field: "" for field in TREE_FIELDS}
            row.update(node=node, parent=parent, status=status, seconds=elapsed,
                       policy_seconds=policy_seconds, proposal_seconds=proposal_seconds,
                       candidate_sha256=candidate_hash)
            if status == "ok":
                row.update(read_csv(trial / "worker-result.csv")[0])
            (trial / "workspace/OBSERVATION.md").write_text(
                f"# Latest attempt\n\nNode: {node}\nParent: {parent}\nStatus: {status}\n"
                f"Selection loss: {row['loss']}\nWorker seconds: {elapsed}\n", encoding="utf-8")
            write_csv(trial / "workspace-manifest.csv", snapshot_manifest(trial / "workspace"), ["path", "sha256"])
            rows.append(row)
            write_csv(work / "TREE.csv", rows, TREE_FIELDS)
            contract(work)
            print(f"{node} from {parent}: {status}; score={row['score']}; worker={elapsed:.3f}s", flush=True)
        valid = [row for row in rows if row["status"] == "ok"]
        best = min(valid, key=lambda row: float(row["loss"]))["node"] if valid else "none"
        (work / "CLOSED.md").write_text(
            f"# Rollout closed\n\nReason: {reason}\nAttempts: {len(rows)}\nSelected node: {best}\n"
            f"Worker seconds: {sum(float(row['seconds']) for row in rows)}\n"
            "Selection used development rows only. No final result or policy improvement is implied.\n", encoding="utf-8")
        print(f"Closed: {reason}; selected {best}")
    finally:
        lock.unlink()


def replay_policy(work, policy_path, worlds, rounds):
    if work.exists():
        raise ValueError("Preserve prior replay")
    work.mkdir(parents=True)
    shutil.copyfile(policy_path, work / "policy.py")
    summaries = []
    for index, world_path in enumerate(worlds):
        policy = load_module(work / "policy.py", f"replay_policy_{index}")
        start = time.perf_counter()
        result = replay(World.read(world_path), policy.choose, rounds)
        elapsed = time.perf_counter() - start
        utility = None if result.best_loss is None or result.unknown_requests else result.best_loss + .001 * result.represented_seconds
        summaries.append(dict(world=str(world_path), world_sha256=sha(world_path),
            best_loss=result.best_loss, represented_seconds=result.represented_seconds,
            revealed_attempts=len(result.observations), decisions=len(result.decisions),
            unknown_requests=result.unknown_requests, terminal=result.terminal,
            utility=utility, replay_seconds=elapsed))
        write_csv(work / f"world-{index:02d}-decisions.csv",
                  [dict(parent=p, child=c) for p, c in result.decisions], ["parent", "child"])
    write_csv(work / "REPLAY.csv", summaries, list(summaries[0]))
    valid = all(row["utility"] is not None for row in summaries)
    mean = sum(row["utility"] for row in summaries) / len(summaries) if valid else None
    (work / "RESULT.md").write_text(
        f"# Replay result\n\nEligible: {valid}\nMean utility: {mean}\n"
        f"Policy SHA256: {sha(work / 'policy.py')}\n"
        "Lower utility is better. Represented worker cost is historical; replay executed no ML fits.\n",
        encoding="utf-8")
    print(f"Replay eligible={valid}; mean utility={mean}; {len(worlds)} worlds; zero fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("task", "init", "run", "worker", "replay"))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--kind", choices=("classification", "regression"))
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--node")
    parser.add_argument("--world", type=Path, action="append")
    parser.add_argument("--rounds", type=int, default=8)
    args = parser.parse_args()
    work = args.workspace.resolve()
    if work.is_relative_to(ROOT):
        raise ValueError("Use an external sibling experiment workspace")
    if args.action == "task":
        task(work, args.seed, args.kind)
    elif args.action == "init":
        initialize(work, args.data, args.policy, args.attempts, args.seconds)
    elif args.action == "run":
        run(work)
    elif args.action == "worker":
        execute_worker(work, args.node)
    else:
        replay_policy(work, args.policy, args.world, args.rounds)
