"""Frozen parent/child harness comparison, conditional on its development gate."""
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

import evaluate_discovery as evaluation
import harness_revision_development as development

ROOT = evaluation.ROOT


def prepare(work, prior):
    if work.exists():
        raise ValueError("Use a new workspace")
    if "Passed: True\n" not in (prior / "GATE.md").read_text():
        raise ValueError("Development gate did not pass")
    if not pd.read_csv(prior / "EVALUATION-CHECKS.csv").passed.all():
        raise ValueError("Check development before proceeding")
    development.verify(prior)
    work.mkdir(parents=True)
    sources = list(dict.fromkeys(evaluation.files_to_freeze() + [
        Path(__file__).resolve(), Path(development.__file__).resolve(),
        development.CHILD / "engine.py", development.CHILD / "proposer.py",
        development.CHILD / "CHANGE-PROPOSAL.md",
        ROOT / "how-did-i-generate-it/rsi/validation/HARNESS-REVISION-FINAL-PROTOCOL.md",
    ]))
    frozen = []
    for path in sources:
        relative = path.relative_to(ROOT)
        target = work / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        frozen.append(dict(path=relative.as_posix(), sha256=evaluation.digest(path)))
    pd.DataFrame(frozen).to_csv(work / "SOURCE-FREEZE.csv", index=False)
    (work / "prior-gate").mkdir()
    for name in ("GATE.md", "RESULTS.csv", "PAIRED.csv", "EVALUATION-CHECKS.csv", "SOURCE-FREEZE.csv"):
        shutil.copyfile(prior / name, work / "prior-gate" / name)
    (work / "FREEZE.md").write_text(
        f"# Harness evaluation frozen before new data\n\nUnix time: {time.time()}\n"
        f"Passing development workspace: {prior}\nMaximum 288 search attempts and 24 scoring refits.\n", encoding="utf-8")
    order, hashes = [], []
    for index, seed in enumerate(range(9101, 9113)):
        public, final = evaluation.public_and_final(seed)
        for role, content in (("public", public), ("evaluator", final)):
            path = work / role / f"task-{seed}.npz"
            path.parent.mkdir(exist_ok=True)
            np.savez_compressed(path, **content)
            hashes.append(dict(path=path.relative_to(work).as_posix(), sha256=evaluation.digest(path)))
        for arm in (("parent", "child") if index % 2 == 0 else ("child", "parent")):
            order.append(dict(seed=seed, kind=str(public["kind"]), family=(seed - 1101) % 3, arm=arm))
    pd.DataFrame(order).to_csv(work / "ORDER.csv", index=False)
    pd.DataFrame(hashes).to_csv(work / "DATA-FREEZE.csv", index=False)
    print("Prepared 12 paired tasks; 24 arms; zero fits", flush=True)


def search(work):
    evaluation.check_freeze(work)
    if (work / "SELECTED.csv").exists():
        raise ValueError("Selection is already closed")
    chosen = []
    for row in pd.read_csv(work / "ORDER.csv").itertuples():
        rollout = work / "rollouts" / str(row.seed) / row.arm
        if not rollout.exists():
            development.assemble(rollout, work / "public" / f"task-{row.seed}.npz", row.arm)
        if not (rollout / "CLOSED.md").exists():
            print(f"Task {row.seed}, {row.arm} harness", flush=True)
            evaluation.runner.run(rollout)
        checked = subprocess.run([sys.executable, str(ROOT / "how-did-i-generate-it/rsi/scripts/check_online_discovery.py"),
                                  str(rollout)], capture_output=True, text=True)
        (rollout / "independent-check.txt").write_text(checked.stdout + checked.stderr, encoding="utf-8")
        if checked.returncode:
            raise ValueError(f"Independent check refused {rollout}")
        tree = pd.read_csv(rollout / "TREE.csv")
        valid = tree[tree.status == "ok"]
        if valid.empty:
            raise ValueError("No valid candidate; preserve failed task")
        best = valid.loc[valid.loss.idxmin()]
        chosen.append(dict(seed=row.seed, kind=row.kind, family=row.family, arm=row.arm, node=best.node,
            candidate_sha256=evaluation.digest(rollout / "nodes" / best.node / "workspace/candidate.py"),
            tree_sha256=evaluation.digest(rollout / "TREE.csv"), attempts=len(tree),
            failures=int(tree.status.ne("ok").sum()), worker_seconds=tree.seconds.sum(),
            fit_seconds=tree.fit_seconds.sum(), policy_seconds=tree.policy_seconds.sum(),
            proposal_seconds=tree.proposal_seconds.sum(), selection_score=best.score, selection_loss=best.loss))
    evaluation.check_freeze(work)
    pd.DataFrame(chosen).to_csv(work / "SELECTED.csv", index=False)
    (work / "SELECTION-CLOSED.md").write_text(
        f"# All selections frozen before final scoring\n\nUnix time: {time.time()}\n"
        f"Selected table SHA256: {evaluation.digest(work / 'SELECTED.csv')}\nArms completed: {len(chosen)}\n", encoding="utf-8")
    print("All 24 choices frozen; final rows unscored", flush=True)


def score(work):
    evaluation.check_freeze(work)
    if f"Selected table SHA256: {evaluation.digest(work / 'SELECTED.csv')}" not in (work / "SELECTION-CLOSED.md").read_text():
        raise ValueError("Choices changed")
    rows = []
    for row in pd.read_csv(work / "SELECTED.csv").to_dict("records"):
        out = work / "scoring" / str(row["seed"]) / row["arm"]
        if out.exists() and not (out / "COMPLETED.md").exists():
            raise ValueError("Interrupted scoring needs explicit review")
        if not out.exists():
            out.mkdir(parents=True)
            (out / "STARTED.md").write_text(f"# Scoring refit admitted\n\nUnix time: {time.time()}\n")
            start = time.perf_counter()
            try:
                process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "score-worker", "--workspace", str(work),
                    "--seed", str(row["seed"]), "--arm", row["arm"]], capture_output=True, text=True, timeout=60)
                (out / "stdout.txt").write_text(process.stdout, encoding="utf-8")
                (out / "stderr.txt").write_text(process.stderr, encoding="utf-8")
                returncode = process.returncode
            except subprocess.TimeoutExpired as error:
                (out / "stderr.txt").write_text(str(error), encoding="utf-8")
                returncode = 124
            pd.DataFrame([dict(seconds=time.perf_counter() - start, returncode=returncode)]).to_csv(out / "process.csv", index=False)
            if returncode:
                raise ValueError(f"Scoring failed: {out}")
            (out / "COMPLETED.md").write_text(f"Completed at {time.time()}\n")
        rows.append({**row, **pd.read_csv(out / "result.csv").iloc[0].to_dict(),
                     "scoring_process_seconds": pd.read_csv(out / "process.csv").iloc[0].seconds})
    pd.DataFrame(rows).to_csv(work / "RESULTS.csv", index=False)
    print("All 24 final scoring refits complete; run independent analysis next", flush=True)


def powered(action, work):
    record = work / f"POWER-{action}.md"
    if record.exists():
        raise ValueError("Preserve prior power-session record; review before resume")
    power = None
    if os.name == "nt":
        power = ctypes.windll.kernel32.SetThreadExecutionState
        power.argtypes, power.restype = [ctypes.c_uint], ctypes.c_uint
        if not power(0x80000001):
            raise OSError("Cannot request idle-sleep protection")
    record.write_text(f"# Temporary power request\n\nAction: {action}\nStarted: {time.time()}\nWindows guard: {power is not None}\n")
    try:
        {"search": search, "score": score}[action](work)
    finally:
        if power is not None:
            power(0x80000000)
        with record.open("a") as stream:
            stream.write(f"Released / ended: {time.time()}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "search", "score", "score-worker"))
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--development", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--arm", choices=("parent", "child"))
    args = parser.parse_args()
    work = args.workspace.resolve()
    if work.is_relative_to(ROOT):
        raise ValueError("Use a separate sibling workspace")
    if args.action == "prepare":
        prepare(work, args.development.resolve())
    elif args.action == "score-worker":
        evaluation.score_worker(work, args.seed, args.arm, work / "scoring" / str(args.seed) / args.arm)
    else:
        powered(args.action, work)
