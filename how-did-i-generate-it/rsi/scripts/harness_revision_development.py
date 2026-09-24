"""Agent-operated paired development of the proposed inner-harness revision."""
from __future__ import annotations

import argparse
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rsi/tools"))
import discovery_run as runner

PARENT = ROOT / "rsi/experiments/tabular-discovery"
CHILD = ROOT / "rsi/experiments/harness-revision"


def public_task(seed):
    # Exact original public generator; this function creates no final rows.
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
    kind = "classification" if seed % 2 else "regression"
    y = (noisy > .25).astype(int) if kind == "classification" else noisy
    x = raw * rng.uniform(.3, 4., 10) + rng.normal(size=10)
    return dict(x_train=x[:1200], y_train=y[:1200], x_selection=x[1200:],
                y_selection=y[1200:], train_ids=np.arange(1200),
                selection_ids=np.arange(1200, 2000), kind=np.asarray(kind))


def prepare(work):
    if work.exists():
        raise ValueError("Use a fresh development workspace")
    for seed in range(1101, 1107):
        archive = ROOT / "rsi/evidence/2026-09-22/online-discovery/data" / f"dev-{seed}.npz"
        known = np.load(archive, allow_pickle=False)
        generated = public_task(seed)
        if set(known.files) != set(generated) or any(known[k].tobytes() != generated[k].tobytes() for k in generated):
            raise ValueError("Generator changed from the declared family")
    work.mkdir(parents=True)
    sources = [Path(__file__).resolve(), ROOT / "rsi/tools/discovery_run.py", ROOT / "rsi/tools/discovery.py",
        PARENT / "engine.py", PARENT / "proposer.py", PARENT / "round_robin.py",
        CHILD / "engine.py", CHILD / "proposer.py", CHILD / "CHANGE-PROPOSAL.md",
        ROOT / "how-did-i-generate-it/rsi/validation/HARNESS-REVISION-DEVELOPMENT-PROTOCOL.md",
        ROOT / "how-did-i-generate-it/rsi/scripts/check_online_discovery.py"]
    records = []
    for source in sources:
        relative = source.relative_to(ROOT)
        target = work / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append(dict(path=relative.as_posix(), sha256=runner.sha(source)))
    pd.DataFrame(records).to_csv(work / "SOURCE-FREEZE.csv", index=False)
    (work / "FREEZE.md").write_text(
        f"# Development harness sources frozen\n\nUnix time: {time.time()}\n"
        "Source freeze precedes new task generation. Six archived tasks match the public generator.\n"
        "At most 144 attempts; no final rows or scoring refits.\n", encoding="utf-8")
    order, data_records = [], []
    (work / "data").mkdir()
    for index, seed in enumerate(range(3101, 3107)):
        task = public_task(seed)
        path = work / "data" / f"task-{seed}.npz"
        np.savez_compressed(path, **task)
        data_records.append(dict(path=path.relative_to(work).as_posix(), sha256=runner.sha(path)))
        for arm in (("parent", "child") if index % 2 == 0 else ("child", "parent")):
            order.append(dict(seed=seed, kind=str(task["kind"]), family=(seed - 1101) % 3, arm=arm))
    pd.DataFrame(order).to_csv(work / "ORDER.csv", index=False)
    pd.DataFrame(data_records).to_csv(work / "DATA-FREEZE.csv", index=False)
    print("Prepared six paired development tasks and source freezes; zero fits; no final arrays")


def verify(work):
    for row in pd.read_csv(work / "SOURCE-FREEZE.csv").itertuples():
        if runner.sha(ROOT / row.path) != row.sha256 or runner.sha(work / "source" / row.path) != row.sha256:
            raise ValueError(f"Source changed: {row.path}")
    for row in pd.read_csv(work / "DATA-FREEZE.csv").itertuples():
        if runner.sha(work / row.path) != row.sha256:
            raise ValueError("Task data changed")


def assemble(work, data, arm):
    runner.initialize(work, data, PARENT / "round_robin.py", 12, 120)
    if arm == "child":
        # This constructor is still assembling a new, unscored workspace.
        # Preserve the initial base assembly before freezing the child files.
        if runner.read_csv(work / "TREE.csv"):
            raise ValueError("Never revise assembly after an attempt")
        shutil.copyfile(work / "contract.csv", work / "base-assembly-contract.csv")
        shutil.copyfile(work / "root-manifest.csv", work / "base-assembly-manifest.csv")
        shutil.copyfile(PARENT / "engine.py", work / "root/parent_engine.py")
        shutil.copyfile(CHILD / "engine.py", work / "root/engine.py")
        shutil.copyfile(CHILD / "proposer.py", work / "proposer.py")
        values = dict(pd.read_csv(work / "contract.csv", dtype=str).itertuples(index=False, name=None))
        values["proposer_sha256"] = runner.sha(work / "proposer.py")
        runner.write_csv(work / "contract.csv", [dict(key=k, value=v) for k, v in values.items()], ["key", "value"])
        runner.write_csv(work / "root-manifest.csv", runner.snapshot_manifest(work / "root"), ["path", "sha256"])
    (work / "ASSEMBLY.md").write_text(
        f"# Harness assembled before fitting\n\nArm: {arm}\nUnix time: {time.time()}\n"
        f"Final root manifest SHA256: {runner.sha(work / 'root-manifest.csv')}\n"
        f"Final contract SHA256: {runner.sha(work / 'contract.csv')}\n"
        "Every child inherits all builder files. No existing experiment was reopened or given a larger allowance.\n",
        encoding="utf-8")


def run(work):
    verify(work)
    if (work / "GATE.md").exists():
        raise ValueError("Development comparison is closed")
    power = None
    if os.name == "nt":
        power = ctypes.windll.kernel32.SetThreadExecutionState
        power.argtypes, power.restype = [ctypes.c_uint], ctypes.c_uint
        if not power(0x80000001):
            raise OSError("Cannot request temporary idle-sleep prevention")
    try:
        (work / "POWER.md").write_text(
            f"# Execution power request\n\nStarted: {time.time()}\n"
            f"Windows temporary idle-sleep prevention: {power is not None}\n"
            "No persistent system setting is changed.\n", encoding="utf-8")
        for row in pd.read_csv(work / "ORDER.csv").itertuples():
            rollout = work / "rollouts" / str(row.seed) / row.arm
            if not rollout.exists():
                assemble(rollout, work / "data" / f"task-{row.seed}.npz", row.arm)
            if not (rollout / "CLOSED.md").exists():
                print(f"Task {row.seed}, {row.arm} harness", flush=True)
                runner.run(rollout)
            checker = ROOT / "how-did-i-generate-it/rsi/scripts/check_online_discovery.py"
            checked = subprocess.run([sys.executable, str(checker), str(rollout)], capture_output=True, text=True)
            (rollout / "independent-check.txt").write_text(checked.stdout + checked.stderr, encoding="utf-8")
            if checked.returncode:
                raise ValueError(f"Independent check refused {rollout}")
        verify(work)
        report(work)
    finally:
        if power is not None:
            power(0x80000000)
        with (work / "POWER.md").open("a", encoding="utf-8") as stream:
            stream.write(f"\nPower request released / run ended: {time.time()}\n")


def report(work):
    records = []
    for row in pd.read_csv(work / "ORDER.csv").itertuples():
        rollout = work / "rollouts" / str(row.seed) / row.arm
        tree = pd.read_csv(rollout / "TREE.csv")
        valid = tree[tree.status == "ok"]
        best = valid.loc[valid.loss.idxmin()] if len(valid) else None
        records.append(dict(seed=row.seed, kind=row.kind, family=row.family, arm=row.arm,
            node=best.node if best is not None else "none", loss=best.loss if best is not None else np.inf,
            score=best.score if best is not None else np.nan, attempts=len(tree), failures=int(tree.status.ne("ok").sum()),
            worker_seconds=tree.seconds.sum(), fit_seconds=tree.fit_seconds.sum(),
            tree_sha256=runner.sha(rollout / "TREE.csv")))
    results = pd.DataFrame(records)
    results.to_csv(work / "RESULTS.csv", index=False)
    parent = results[results.arm == "parent"].set_index("seed")
    child = results[results.arm == "child"].set_index("seed").loc[parent.index]
    deltas = child.loss - parent.loss
    kinds = {kind: float(deltas[parent.kind == kind].mean()) for kind in parent.kind.unique()}
    pass_gate = (np.isfinite(deltas).all() and deltas.mean() <= -.01 and all(value <= 0 for value in kinds.values())
                 and child.failures.sum() <= parent.failures.sum())
    pd.DataFrame(dict(seed=parent.index, kind=parent.kind.values, parent_loss=parent.loss.values,
                      child_loss=child.loss.values, child_minus_parent=deltas.values)).to_csv(work / "PAIRED.csv", index=False)
    (work / "GATE.md").write_text(
        f"# Exploratory harness gate\n\nPassed: {pass_gate}\n"
        f"Mean normalized selection-loss change, child minus parent: {deltas.mean()}\n"
        f"Task-kind changes: {kinds}\nSearch attempts: {results.attempts.sum()}\n"
        f"Parent failures: {parent.failures.sum()}\nChild failures: {child.failures.sum()}\n"
        "This is a development gate, not significance or final transfer evidence. No final rows were created.\n",
        encoding="utf-8")
    print((work / "GATE.md").read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    work = args.workspace.resolve()
    if work.is_relative_to(ROOT):
        raise ValueError("Use a new sibling learner workspace")
    if args.action == "prepare":
        prepare(work)
    else:
        run(work)
