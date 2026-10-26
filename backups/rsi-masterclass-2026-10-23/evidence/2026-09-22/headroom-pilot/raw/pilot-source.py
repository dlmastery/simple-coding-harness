"""Development-only search-headroom pilot. Coding-agent operated, no final test.

Run prepare, run, then summarize with the same fresh sibling workspace.
Short-budget comparisons are replay of real fit results, not new experiments.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.datasets import load_breast_cancer, load_digits, make_friedman1
from sklearn.ensemble import (ExtraTreesClassifier, ExtraTreesRegressor,
                             HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                             RandomForestClassifier, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR
from threadpoolctl import threadpool_limits

REPO = Path(__file__).resolve().parents[3]
TASKS = ("bike", "wine", "cancer", "digits", "friedman", "interactions")
FAMILIES = ("linear", "forest", "boost", "kernel", "neighbors", "extra")
RESULT_FIELDS = ("task", "recipe", "status", "metric", "score", "normalized_loss",
                 "fit_seconds", "predict_seconds", "process_seconds", "note")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def recipes():
    # Index zero is a conventional default in every family, not a weak control.
    values = {
        "linear": [{"alpha": a} for a in (1, .01, .1, 10, 100, 1000, .001, 10000)],
        "kernel": [{"C": c, "gamma": g} for c, g in
                   ((1, "scale"), (10, "scale"), (100, "scale"), (.1, "scale"),
                    (1, .01), (10, .01), (100, .01), (10, 1.0))],
        "neighbors": [{"n_neighbors": n, "weights": w} for n, w in
                      ((5, "distance"), (3, "distance"), (11, "distance"), (25, "distance"),
                       (5, "uniform"), (11, "uniform"), (25, "uniform"), (51, "distance"))],
        "forest": [{"max_depth": d, "min_samples_leaf": n, "max_features": f}
                   for d, n, f in ((None, 1, 1.), (None, 3, .7), (8, 1, 1.),
                                   (8, 5, .7), (4, 1, 1.), (4, 5, .7),
                                   (None, 10, 1.), (None, 1, .3))],
        "extra": [{"max_depth": d, "min_samples_leaf": n, "max_features": f}
                  for d, n, f in ((None, 1, 1.), (None, 3, .7), (8, 1, 1.),
                                  (8, 5, .7), (4, 1, 1.), (4, 5, .7),
                                  (None, 10, 1.), (None, 1, .3))],
        "boost": [{"max_leaf_nodes": n, "learning_rate": r, "l2_regularization": l}
                  for n, r, l in ((31, .1, 0), (15, .1, 1), (7, .1, 1), (63, .1, 1),
                                  (15, .03, 0), (31, .03, 1), (7, .3, 1), (31, .1, 10))],
    }
    return [(f"{family}-{index}", family, params)
            for index in range(8) for family in FAMILIES
            for params in [values[family][index]]]


def task_data(name):
    categories = []
    kind = "regression"
    if name in ("bike", "wine"):
        sys.path.insert(0, str(REPO / "rsi/tools"))
        from lab import read_data, partitions, CALENDAR, WEATHER, CATEGORICAL
        frame = read_data(name)
        split = partitions(frame, name)
        if name == "bike":
            columns = CALENDAR + WEATHER
            categories = [columns.index(c) for c in CATEGORICAL]
            x, y = frame[columns].to_numpy(), frame.cnt.to_numpy()
        else:
            x, y = frame.drop(columns="quality").to_numpy(), frame.quality.to_numpy()
        train, selection = np.flatnonzero(split["train"]), np.flatnonzero(split["selection"])
        # Bound CPU cost using fixed samples chosen without target values.
        rng = np.random.default_rng(20260922)
        train = np.sort(rng.choice(train, min(1200, len(train)), replace=False))
        selection = np.sort(rng.choice(selection, min(1200, len(selection)), replace=False))
    else:
        if name == "cancer":
            x, y = load_breast_cancer(return_X_y=True)
            kind = "classification"
        elif name == "digits":
            x, y = load_digits(return_X_y=True)
            kind = "classification"
        elif name == "friedman":
            x, y = make_friedman1(n_samples=2000, n_features=20, noise=1., random_state=917)
        elif name == "interactions":
            rng = np.random.default_rng(918)
            x = rng.normal(size=(2000, 12))
            y = (x[:, 0] * x[:, 1] + .6 * x[:, 2] - .4 * x[:, 3]
                 + .25 * rng.normal(size=len(x)) > .3).astype(int)
            kind = "classification"
        else:
            raise ValueError(name)
        train, selection = train_test_split(np.arange(len(y)), test_size=.4, random_state=731,
                                           stratify=y if kind == "classification" else None)
    return dict(x_train=x[train], y_train=y[train], x_selection=x[selection],
                y_selection=y[selection], train_ids=train, selection_ids=selection,
                categories=np.asarray(categories, dtype=int), kind=np.asarray(kind))


def prepare(work):
    if work.exists():
        raise ValueError("Use a fresh workspace; preparation cannot replace prior evidence.")
    work.mkdir(parents=True)
    (work / "pilot-source.py").write_bytes(Path(__file__).read_bytes())
    records = []
    for name in TASKS:
        data = task_data(name)
        path = work / f"{name}.npz"
        np.savez_compressed(path, **data)
        assert not set(data["train_ids"]) & set(data["selection_ids"])
        records.append(dict(task=name, kind=str(data["kind"]), train_rows=len(data["y_train"]),
                            selection_rows=len(data["y_selection"]), features=data["x_train"].shape[1],
                            data_sha256=sha(path)))
    write_csv(work / "tasks.csv", records)
    write_csv(work / "recipes.csv", [dict(recipe=rid, family=family, parameters=repr(params))
                                     for rid, family, params in recipes()])
    (work / "ENVIRONMENT.md").write_text(
        f"# Development headroom pilot\n\nPython: {platform.python_version()}\n"
        f"scikit-learn: {sklearn.__version__}\nNumPy: {np.__version__}\nPandas: {pd.__version__}\n"
        f"Script SHA256: {sha(__file__)}\nPrepared at Unix time: {time.time()}\n"
        "288 attempts maximum; 60-second timeout per attempt; one library thread.\n"
        "All tasks are development tasks. No final performance is measured.\n"
        "Agent inference cost: unknown. Process time includes Python startup.\n", encoding="utf-8")
    print(f"Prepared {len(TASKS)} development tasks and {len(recipes())} recipes", flush=True)


def model(data, family, params):
    classification = str(data["kind"]) == "classification"
    categorical = data["categories"].tolist()
    numeric = [i for i in range(data["x_train"].shape[1]) if i not in categorical]
    transform = ColumnTransformer([
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")),
                              ("scale", StandardScaler())]), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ])
    if family == "linear":
        estimator = (LogisticRegression(C=1 / params["alpha"], max_iter=1500, class_weight="balanced")
                     if classification else Ridge(**params))
    elif family == "kernel":
        estimator = SVC(**params, class_weight="balanced") if classification else SVR(**params)
    elif family == "neighbors":
        estimator = KNeighborsClassifier(**params) if classification else KNeighborsRegressor(**params)
    elif family in ("forest", "extra"):
        cls = ((RandomForestClassifier if classification else RandomForestRegressor)
               if family == "forest" else (ExtraTreesClassifier if classification else ExtraTreesRegressor))
        estimator = cls(**params, n_estimators=64, random_state=41, n_jobs=1,
                        **({"class_weight": "balanced"} if classification else {}))
    elif family == "boost":
        cls = HistGradientBoostingClassifier if classification else HistGradientBoostingRegressor
        estimator = cls(**params, max_iter=100, early_stopping=False, random_state=41,
                        **({"class_weight": "balanced"} if classification else {}))
    else:
        raise ValueError(family)
    if not classification:
        estimator = TransformedTargetRegressor(regressor=estimator, transformer=StandardScaler())
    return Pipeline([("prepare", transform), ("model", estimator)])


def fit(work, task, recipe):
    data = np.load(work / f"{task}.npz", allow_pickle=False)
    family, params = next((family, params) for rid, family, params in recipes() if rid == recipe)
    estimator = model(data, family, params)
    with threadpool_limits(limits=1):
        started = time.perf_counter()
        estimator.fit(data["x_train"], data["y_train"])
        fit_seconds = time.perf_counter() - started
        started = time.perf_counter()
        prediction = estimator.predict(data["x_selection"])
        predict_seconds = time.perf_counter() - started
    y = data["y_selection"]
    if str(data["kind"]) == "regression":
        score = mean_absolute_error(y, prediction)
        baseline = mean_absolute_error(y, np.full(len(y), np.median(data["y_train"])))
        normalized = score / baseline
        metric = "MAE"
    else:
        score = balanced_accuracy_score(y, prediction)
        labels, counts = np.unique(data["y_train"], return_counts=True)
        baseline = balanced_accuracy_score(y, np.full(len(y), labels[np.argmax(counts)]))
        normalized = (1 - score) / (1 - baseline)
        metric = "balanced_accuracy"
    trial = work / "attempts" / task / recipe
    pd.DataFrame({"row_id": data["selection_ids"], "actual": y, "predicted": prediction}).to_csv(
        trial / "predictions.csv", index=False)
    write_csv(trial / "result.csv", [dict(task=task, recipe=recipe, status="ok", metric=metric,
                                        score=score, normalized_loss=normalized,
                                        fit_seconds=fit_seconds, predict_seconds=predict_seconds,
                                        process_seconds="", note="")], RESULT_FIELDS)


def run(work):
    if sha(__file__) != sha(work / "pilot-source.py"):
        raise ValueError("Pilot source changed; preserve this workspace and declare a new protocol.")
    for row in csv.DictReader((work / "tasks.csv").open(encoding="utf-8")):
        if sha(work / f"{row['task']}.npz") != row["data_sha256"]:
            raise ValueError("Prepared data changed")
    for task in TASKS:
        for recipe, _, _ in recipes():
            trial = work / "attempts" / task / recipe
            if trial.exists():
                # Interrupted attempts remain charged. They are not silently re-run.
                continue
            trial.mkdir(parents=True)
            (trial / "STARTED.md").write_text(f"Started at Unix time {time.time()}\n", encoding="utf-8")
            started = time.perf_counter()
            status, note = "failed", ""
            try:
                completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), "fit",
                                            "--workspace", str(work), "--task", task, "--recipe", recipe],
                                           capture_output=True, text=True, timeout=60)
                (trial / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
                (trial / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
                status = "ok" if completed.returncode == 0 else "failed"
                note = f"exit={completed.returncode}"
            except subprocess.TimeoutExpired as error:
                status, note = "timeout", "60-second timeout; attempt charged"
                (trial / "stderr.txt").write_text(str(error), encoding="utf-8")
            elapsed = time.perf_counter() - started
            if status == "ok" and (trial / "result.csv").exists():
                row = next(csv.DictReader((trial / "result.csv").open(encoding="utf-8")))
            else:
                row = {key: "" for key in RESULT_FIELDS}
                row.update(task=task, recipe=recipe)
            row.update(status=status, note=note, process_seconds=elapsed)
            write_csv(trial / "result.csv", [row], RESULT_FIELDS)
            print(f"{task} {recipe} {status} score={row['score']} process={elapsed:.2f}s", flush=True)


def summarize(work):
    rows = []
    for task in TASKS:
        for recipe, _, _ in recipes():
            result = work / "attempts" / task / recipe / "result.csv"
            if result.exists():
                rows.append(next(csv.DictReader(result.open(encoding="utf-8"))))
            else:
                raise ValueError(f"Missing terminal result: {task}/{recipe}; reconcile before analysis")
    write_csv(work / "results.csv", rows, RESULT_FIELDS)
    results = pd.DataFrame(rows)
    trials, summary = [], []
    ids = [rid for rid, _, _ in recipes()]
    for task in TASKS:
        table = results[results.task == task].set_index("recipe")
        losses = pd.to_numeric(table.normalized_loss, errors="coerce").fillna(np.inf)
        costs = pd.to_numeric(table.process_seconds)
        reference = float(losses.min())
        if not np.isfinite(reference):
            raise ValueError(f"All candidates failed: {task}")
        for budget in (4, 8, 16):
            for policy in ("fixed_diverse", "uniform_random"):
                for seed in range(32 if policy == "uniform_random" else 1):
                    order = ids if policy == "fixed_diverse" else np.random.default_rng(seed + 602).permutation(ids).tolist()
                    visited = order[:budget]
                    best = losses.loc[visited].idxmin()
                    trials.append(dict(task=task, budget=budget, policy=policy, seed=seed,
                                       best_recipe=best, normalized_loss=float(losses[best]),
                                       reference_recipe=losses.idxmin(), reference_loss=reference,
                                       headroom=float(losses[best] - reference),
                                       charged_process_seconds=float(costs.loc[visited].sum())))
        summary.append(dict(task=task, reference_recipe=losses.idxmin(),
                            reference_score=table.loc[losses.idxmin(), "score"],
                            metric=table.loc[losses.idxmin(), "metric"],
                            successful_fits=int((table.status == "ok").sum()),
                            failed_fits=int((table.status != "ok").sum())))
    write_csv(work / "headroom-replays.csv", trials)
    write_csv(work / "reference.csv", summary)
    replay = pd.DataFrame(trials)
    groups = replay.groupby(["task", "budget", "policy"]).agg(
        mean_headroom=("headroom", "mean"), min_headroom=("headroom", "min"),
        max_headroom=("headroom", "max"), mean_loss=("normalized_loss", "mean"),
        mean_process_seconds=("charged_process_seconds", "mean")).reset_index()
    groups.to_csv(work / "headroom-summary.csv", index=False)
    print(groups.to_string(index=False))
    print(f"Executed attempts: {len(rows)}; replay trajectories: {len(trials)}; final evaluations: 0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "fit", "summarize"))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--recipe")
    arguments = parser.parse_args()
    workspace = arguments.workspace.resolve()
    if workspace.is_relative_to(REPO):
        raise ValueError("Experiment workspace must be outside the source repository")
    if arguments.action == "fit":
        fit(workspace, arguments.task, arguments.recipe)
    else:
        {"prepare": prepare, "run": run, "summarize": summarize}[arguments.action](workspace)
