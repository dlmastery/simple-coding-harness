"""Frozen, paired online evaluation of five tabular discovery policies.

Agent-operated implementation; students request the workflow in plain language.
Prepare, search and final scoring are separate actions. Final rows never enter
the online runner. Local filesystem separation is not a security boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rsi/tools"))
import discovery_run as runner

EXPERIMENT = ROOT / "rsi/experiments/tabular-discovery"
ARMS = {
    "broad": EXPERIMENT / "round_robin.py",
    "greedy": EXPERIMENT / "greedy.py",
    "lineage": EXPERIMENT / "policies/probe_lineage.py",
    "evolved": EXPERIMENT / "policies/quality_stop.py",
    "broad-stop": EXPERIMENT / "policies/broad_stop.py",
}
PHASES = {"shakedown": range(2101, 2105), "final": range(8101, 8117)}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public_and_final(seed):
    """Preserve the original 2,000-row generator, then draw independent rows."""
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(2000, 10))
    coefficients = rng.uniform(.6, 1.4, 4) * rng.choice([-1., 1.], 4)
    family = (seed - 1101) % 3

    def signal(values):
        if family == 0:
            return (coefficients[0] * values[:, 0] * values[:, 1] + coefficients[1] * values[:, 2]
                    + coefficients[2] * values[:, 3] + .4 * coefficients[3] * values[:, 4] * values[:, 5])
        if family == 1:
            return values[:, :4] @ coefficients
        return (coefficients[0] * (values[:, 0] ** 2 - 1) + coefficients[1] * values[:, 1]
                + coefficients[2] * np.sin(values[:, 2]) + coefficients[3] * values[:, 3] * values[:, 4])

    noisy = signal(raw) + rng.normal(scale=.3, size=len(raw))
    kind = "classification" if seed % 2 else "regression"
    y = (noisy > .25).astype(int) if kind == "classification" else noisy
    scale, shift = rng.uniform(.3, 4., 10), rng.normal(size=10)
    x = raw * scale + shift
    public = dict(x_train=x[:1200], y_train=y[:1200], x_selection=x[1200:],
                  y_selection=y[1200:], train_ids=np.arange(1200),
                  selection_ids=np.arange(1200, 2000), kind=np.asarray(kind))
    final_rng = np.random.default_rng(seed + 100000)
    raw_final = final_rng.normal(size=(1000, 10))
    final_noisy = signal(raw_final) + final_rng.normal(scale=.3, size=len(raw_final))
    final = dict(x_final=raw_final * scale + shift,
                 y_final=(final_noisy > .25).astype(int) if kind == "classification" else final_noisy,
                 final_ids=np.arange(2000, 3000))
    return public, final


def files_to_freeze():
    return list(dict.fromkeys([Path(__file__).resolve(), ROOT / "rsi/tools/discovery_run.py",
        ROOT / "rsi/tools/discovery.py", EXPERIMENT / "proposer.py", EXPERIMENT / "engine.py",
        ROOT / "how-did-i-generate-it/rsi/scripts/check_online_discovery.py", *ARMS.values()]))


def check_freeze(work):
    for row in pd.read_csv(work / "SOURCE-FREEZE.csv").itertuples():
        if digest(ROOT / row.path) != row.sha256 or digest(work / "source" / row.path) != row.sha256:
            raise ValueError(f"Frozen evaluation source changed: {row.path}")
    for row in pd.read_csv(work / "DATA-FREEZE.csv").itertuples():
        if digest(work / row.path) != row.sha256:
            raise ValueError(f"Frozen evaluation data changed: {row.path}")


def prepare(work, phase):
    if work.exists():
        raise ValueError("Use a new workspace; preserve prior evaluation")
    if phase == "final":
        previous = work.parent / "shakedown"
        if not (previous / "REPORT.md").exists():
            raise ValueError("Complete shakedown before final task generation")
        check_freeze(previous)
    # Exact per-array bytes, independent of ZIP metadata, against all six old tasks.
    original = ROOT.parent / "rsi-work-2026-09-22-discovery/data"
    for seed in range(1101, 1107):
        stored = np.load(original / f"dev-{seed}.npz", allow_pickle=False)
        generated, _ = public_and_final(seed)
        if set(stored.files) != set(generated) or any(
                stored[key].dtype != generated[key].dtype or stored[key].shape != generated[key].shape
                or stored[key].tobytes() != generated[key].tobytes() for key in generated):
            raise ValueError(f"Generator mismatch at development seed {seed}")
    work.mkdir(parents=True)
    sources = []
    for source in files_to_freeze():
        relative = source.relative_to(ROOT)
        target = work / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sources.append(dict(path=relative.as_posix(), sha256=digest(source)))
    pd.DataFrame(sources).to_csv(work / "SOURCE-FREEZE.csv", index=False)
    (work / "FREEZE.md").write_text(
        f"# Evaluation source frozen\n\nPhase: {phase}\nUnix time: {time.time()}\n"
        "All six development tasks reproduce identical public array bytes.\n"
        "Source freeze precedes generation of this phase's tasks.\n", encoding="utf-8")
    order, data_hashes = [], []
    names = list(ARMS)
    for index, seed in enumerate(PHASES[phase]):
        public, final = public_and_final(seed)
        for role, content in (("public", public), ("evaluator", final)):
            target = work / role / f"task-{seed}.npz"
            target.parent.mkdir(exist_ok=True)
            np.savez_compressed(target, **content)
            data_hashes.append(dict(path=target.relative_to(work).as_posix(), sha256=digest(target)))
        rotation = index % len(names)
        for position, arm in enumerate(names[rotation:] + names[:rotation]):
            order.append(dict(seed=seed, family=(seed - 1101) % 3, kind=str(public["kind"]),
                              position=position, arm=arm))
    pd.DataFrame(order).to_csv(work / "ORDER.csv", index=False)
    pd.DataFrame(data_hashes).to_csv(work / "DATA-FREEZE.csv", index=False)
    print(f"Prepared {phase}: {len(order)} paired arms; zero fits; sources frozen first", flush=True)


def search(work):
    check_freeze(work)
    if (work / "SELECTED.csv").exists():
        raise ValueError("Phase selection is closed")
    for row in pd.read_csv(work / "ORDER.csv").itertuples():
        rollout = work / "rollouts" / str(row.seed) / row.arm
        if not rollout.exists():
            runner.initialize(rollout, work / "public" / f"task-{row.seed}.npz", ARMS[row.arm], 12, 120)
        if not (rollout / "CLOSED.md").exists():
            print(f"Task {row.seed}; arm {row.arm}", flush=True)
            runner.run(rollout)
        checker = ROOT / "how-did-i-generate-it/rsi/scripts/check_online_discovery.py"
        completed = subprocess.run([sys.executable, str(checker), str(rollout)], capture_output=True, text=True)
        (rollout / "independent-check.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise ValueError(f"Independent rollout check failed: {rollout}")
    check_freeze(work)
    selected = []
    for row in pd.read_csv(work / "ORDER.csv").itertuples():
        rollout = work / "rollouts" / str(row.seed) / row.arm
        table = pd.read_csv(rollout / "TREE.csv")
        valid = table[table.status == "ok"]
        if valid.empty:
            raise ValueError("No valid candidate: retain failure and stop for review")
        best = valid.loc[valid.loss.idxmin()]
        candidate = rollout / "nodes" / best.node / "workspace/candidate.py"
        selected.append(dict(seed=row.seed, family=row.family, kind=row.kind, arm=row.arm,
            node=best.node, candidate_sha256=digest(candidate), tree_sha256=digest(rollout / "TREE.csv"),
            attempts=len(table), failures=int(table.status.ne("ok").sum()),
            worker_seconds=table.seconds.sum(), fit_seconds=table.fit_seconds.sum(),
            policy_seconds=table.policy_seconds.sum(), proposal_seconds=table.proposal_seconds.sum(),
            selection_score=best.score, selection_loss=best.loss))
    pd.DataFrame(selected).to_csv(work / "SELECTED.csv", index=False)
    (work / "SELECTION-CLOSED.md").write_text(
        f"# All choices frozen before final scoring\n\nUnix time: {time.time()}\n"
        f"Selected table SHA256: {digest(work / 'SELECTED.csv')}\n"
        f"Arms completed: {len(selected)}\n", encoding="utf-8")
    print(f"Search closed: {len(selected)} selected candidates; final rows not scored", flush=True)


def score_worker(work, seed, arm, out):
    chosen = pd.read_csv(work / "SELECTED.csv").query("seed == @seed and arm == @arm").iloc[0]
    rollout = work / "rollouts" / str(seed) / arm
    candidate_path = rollout / "nodes" / chosen.node / "workspace/candidate.py"
    if digest(candidate_path) != chosen.candidate_sha256 or digest(rollout / "TREE.csv") != chosen.tree_sha256:
        raise ValueError("Selected source or history changed")
    sys.path.insert(0, str(candidate_path.parent))
    candidate = runner.load_module(candidate_path, "selected_candidate")
    public = np.load(work / "public" / f"task-{seed}.npz", allow_pickle=False)
    final = np.load(work / "evaluator" / f"task-{seed}.npz", allow_pickle=False)
    model = candidate.build(str(public["kind"]), 41)
    with threadpool_limits(limits=1):
        start = time.perf_counter()
        model.fit(public["x_train"], public["y_train"])
        fit_seconds = time.perf_counter() - start
        selection_prediction = model.predict(public["x_selection"])
        original = pd.read_csv(rollout / "nodes" / chosen.node / "predictions.csv")
        if not np.allclose(selection_prediction, original.predicted, atol=1e-10, rtol=1e-10):
            raise ValueError("Selected model did not reproduce its selection predictions")
        start = time.perf_counter()
        prediction = model.predict(final["x_final"])
        predict_seconds = time.perf_counter() - start
    if not np.isfinite(prediction).all():
        raise ValueError("Nonfinite final predictions")
    y = final["y_final"]
    if str(public["kind"]) == "classification":
        score = np.mean([(prediction[y == label] == label).mean() for label in np.unique(y)])
        loss = 2 * (1 - score)
    else:
        score = np.abs(y - prediction).mean()
        loss = score / np.abs(y - np.median(public["y_train"])).mean()
    pd.DataFrame(dict(row_id=final["final_ids"], actual=y, predicted=prediction)).to_csv(out / "predictions.csv", index=False)
    pd.DataFrame([dict(final_score=score, final_loss=loss, scoring_fit_seconds=fit_seconds,
                       scoring_predict_seconds=predict_seconds, selection_reproduced=True)]).to_csv(out / "result.csv", index=False)


def score(work):
    check_freeze(work)
    closed = (work / "SELECTION-CLOSED.md").read_text(encoding="utf-8")
    if f"Selected table SHA256: {digest(work / 'SELECTED.csv')}" not in closed:
        raise ValueError("Selection freeze changed")
    for row in pd.read_csv(work / "SELECTED.csv").itertuples():
        out = work / "scoring" / str(row.seed) / row.arm
        if out.exists():
            if not (out / "COMPLETED.md").exists():
                raise ValueError("Interrupted scoring attempt needs review; do not retry silently")
            continue
        out.mkdir(parents=True)
        (out / "STARTED.md").write_text(f"# Scoring refit admitted\n\nUnix time: {time.time()}\n", encoding="utf-8")
        start = time.perf_counter()
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "score-worker",
                "--workspace", str(work), "--seed", str(row.seed), "--arm", row.arm],
                capture_output=True, text=True, timeout=60)
            (out / "stdout.txt").write_text(process.stdout, encoding="utf-8")
            (out / "stderr.txt").write_text(process.stderr, encoding="utf-8")
            returncode = process.returncode
        except subprocess.TimeoutExpired as error:
            (out / "stderr.txt").write_text(str(error), encoding="utf-8")
            returncode = -1
        elapsed = time.perf_counter() - start
        pd.DataFrame([dict(returncode=returncode, seconds=elapsed)]).to_csv(out / "process.csv", index=False)
        if returncode != 0:
            raise ValueError(f"Scoring failed: {out}; attempt remains charged")
        (out / "COMPLETED.md").write_text("# Scoring completed\n\nSelection predictions reproduced before final scoring.\n", encoding="utf-8")
        print(f"Scored task {row.seed}, {row.arm}; selection reproduced", flush=True)
    analyze(work)


def analyze(work):
    check_freeze(work)
    results = []
    for row in pd.read_csv(work / "SELECTED.csv").to_dict("records"):
        out = work / "scoring" / str(row["seed"]) / row["arm"]
        result = pd.read_csv(out / "result.csv").iloc[0].to_dict()
        process = pd.read_csv(out / "process.csv").iloc[0]
        results.append({**row, **result, "scoring_process_seconds": process.seconds})
    table = pd.DataFrame(results)
    table["utility"] = table.final_loss + .001 * table.worker_seconds
    table.to_csv(work / "RESULTS.csv", index=False)
    paired = []
    evolved = table[table.arm == "evolved"].set_index("seed")
    for arm in ARMS:
        if arm == "evolved":
            continue
        reference = table[table.arm == arm].set_index("seed").loc[evolved.index]
        rng = np.random.default_rng(20260922)
        for metric in ("final_loss", "attempts", "worker_seconds", "utility"):
            delta = (evolved[metric] - reference[metric]).to_numpy()
            boot = delta[rng.integers(0, len(delta), size=(10000, len(delta)))].mean(axis=1)
            paired.append(dict(reference=arm, metric=metric, mean_evolved_minus_reference=delta.mean(),
                ci_low=np.quantile(boot, .025), ci_high=np.quantile(boot, .975),
                lower=int((delta < -1e-10).sum()), tied=int((np.abs(delta) <= 1e-10).sum()),
                higher=int((delta > 1e-10).sum()), tasks=len(delta)))
    pd.DataFrame(paired).to_csv(work / "PAIRED.csv", index=False)
    columns = ["arm", "tasks", "attempts", "failures", "mean_final_loss", "worker_seconds"]
    summary = [dict(arm=arm, tasks=len(part), attempts=part.attempts.sum(), failures=part.failures.sum(),
                    mean_final_loss=part.final_loss.mean(), worker_seconds=part.worker_seconds.sum())
               for arm, part in table.groupby("arm", sort=False)]
    report = "# Paired discovery-policy evaluation\n\n"
    report += "Same synthetic grammar, new instances and separate final rows. Lower loss is better.\n\n"
    report += "| " + " | ".join(columns) + " |\n|" + "---|" * len(columns) + "\n"
    for row in summary:
        report += "| " + " | ".join(f"{row[c]:.6f}" if isinstance(row[c], float) else str(row[c]) for c in columns) + " |\n"
    report += (f"\nSearch attempts: {table.attempts.sum()}; separate scoring refits: {len(table)}.\n"
               "Fit, worker-process, proposal and scoring costs are separate in RESULTS.csv.\n"
               "PAIRED.csv reports task-bootstrap intervals; final_loss contrasts separate quality from cost.\n"
               "No inference-cost or unseen-family generalization claim. Other RSI methods remain pending.\n")
    (work / "REPORT.md").write_text(report, encoding="utf-8")
    print(report, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "search", "score", "score-worker", "analyze"))
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--phase", choices=tuple(PHASES))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--arm", choices=tuple(ARMS))
    args = parser.parse_args()
    work = args.workspace.resolve()
    if work.is_relative_to(ROOT):
        raise ValueError("Use an external sibling workspace")
    if args.action == "prepare":
        prepare(work, args.phase)
    elif args.action == "search":
        search(work)
    elif args.action == "score":
        score(work)
    elif args.action == "analyze":
        analyze(work)
    else:
        score_worker(work, args.seed, args.arm, work / "scoring" / str(args.seed) / args.arm)
