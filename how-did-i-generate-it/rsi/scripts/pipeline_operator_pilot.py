"""Bounded development-only operator pilot, extending saved base fits."""
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

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures, QuantileTransformer, StandardScaler
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("base_pilot", HERE / "benchmark_headroom.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
MODES = ("pairwise", "quantile")


def prepare(source, work):
    if work.exists():
        raise ValueError("Fresh sibling workspace required")
    if not (source / "CORRECTION.md").exists():
        raise ValueError("Use the independently checked count-corrected base records")
    if not pd.read_csv(source / "CHECKS.csv").passed.all():
        raise ValueError("Base prediction audit did not pass")
    work.mkdir(parents=True)
    identities = []
    for name in [f"{task}.npz" for task in base.TASKS] + ["tasks.csv", "results.csv", "recipes.csv"]:
        target = work / ("base-" + name if name in ("results.csv", "recipes.csv") else name)
        shutil.copyfile(source / name, target)
        identities.append(dict(path=target.name, sha256=base.sha(target)))
    for path in (Path(__file__), HERE / "benchmark_headroom.py"):
        shutil.copyfile(path, work / path.name)
        identities.append(dict(path=path.name, sha256=base.sha(path)))
    base.write_csv(work / "SOURCE-IDENTITIES.csv", identities)
    base.write_csv(work / "operators.csv", [dict(recipe=f"{family}-0-{mode}", family=family, mode=mode)
                                            for family in base.FAMILIES for mode in MODES])
    (work / "CONTRACT.md").write_text(
        "# Development-only operator pilot\n\n72 new attempts maximum; six tasks; twelve extensions per task.\n"
        "Each attempt: one library thread; 60-second subprocess timeout. No automatic retry.\n"
        "The base table contains 288 previous fits, not new executions. No final evaluation.\n"
        "Count predictions clipped at zero. Agent inference cost unknown.\n"
        "Fixed controls: original first eight recipes; six raw defaults plus linear pairwise and quantile.\n",
        encoding="utf-8")
    print("Prepared 72 extension attempts; no fitting yet")


def fit(work, task, recipe):
    family, _, mode = recipe.split("-")
    data = np.load(work / f"{task}.npz", allow_pickle=False)
    params = next(params for rid, fam, params in base.recipes() if rid == f"{family}-0")
    estimator = base.model(data, family, params)
    if mode == "quantile":
        numeric = estimator.named_steps["prepare"].transformers[0][1]
        numeric.steps[-1] = ("quantile", QuantileTransformer(
            n_quantiles=min(200, len(data["y_train"])), output_distribution="normal", random_state=41))
    elif mode == "pairwise":
        estimator.steps[1:1] = [("interactions", PolynomialFeatures(degree=2, interaction_only=True,
                                                                  include_bias=False)),
                                ("interaction_scale", StandardScaler())]
    else:
        raise ValueError(mode)
    with threadpool_limits(limits=1):
        started = time.perf_counter()
        estimator.fit(data["x_train"], data["y_train"])
        fit_seconds = time.perf_counter() - started
        started = time.perf_counter()
        prediction = estimator.predict(data["x_selection"])
        if task == "bike":
            prediction = np.maximum(prediction, 0)
        predict_seconds = time.perf_counter() - started
    y = data["y_selection"]
    if str(data["kind"]) == "regression":
        score = base.mean_absolute_error(y, prediction)
        normalized = score / base.mean_absolute_error(y, np.full(len(y), np.median(data["y_train"])))
        metric = "MAE"
    else:
        score = base.balanced_accuracy_score(y, prediction)
        normalized = (1 - score) / (1 - 1 / len(np.unique(data["y_train"])))
        metric = "balanced_accuracy"
    trial = work / "attempts" / task / recipe
    pd.DataFrame(dict(row_id=data["selection_ids"], actual=y, predicted=prediction)).to_csv(
        trial / "predictions.csv", index=False)
    base.write_csv(trial / "result.csv", [dict(task=task, recipe=recipe, status="ok", metric=metric,
        score=score, normalized_loss=normalized, fit_seconds=fit_seconds, predict_seconds=predict_seconds,
        process_seconds="", note="")], base.RESULT_FIELDS)


def run(work):
    for row in pd.read_csv(work / "SOURCE-IDENTITIES.csv").itertuples():
        if base.sha(work / row.path) != row.sha256:
            raise ValueError("Prepared source changed")
    if base.sha(__file__) != base.sha(work / Path(__file__).name):
        raise ValueError("Runner changed after preparation")
    if base.sha(HERE / "benchmark_headroom.py") != base.sha(work / "benchmark_headroom.py"):
        raise ValueError("Base pipeline source changed")
    for task in base.TASKS:
        for recipe in pd.read_csv(work / "operators.csv").recipe:
            trial = work / "attempts" / task / recipe
            if trial.exists():
                continue
            trial.mkdir(parents=True)
            (trial / "STARTED.md").write_text(f"Started at Unix time {time.time()}\n", encoding="utf-8")
            started = time.perf_counter()
            try:
                completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), "fit",
                    "--workspace", str(work), "--task", task, "--recipe", recipe],
                    capture_output=True, text=True, timeout=60)
                (trial / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
                (trial / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
                status, note = ("ok" if completed.returncode == 0 else "failed"), f"exit={completed.returncode}"
            except subprocess.TimeoutExpired as error:
                status, note = "timeout", "60-second timeout; charged"
                (trial / "stderr.txt").write_text(str(error), encoding="utf-8")
            elapsed = time.perf_counter() - started
            path = trial / "result.csv"
            if status == "ok" and path.exists():
                row = next(csv.DictReader(path.open(encoding="utf-8")))
            else:
                if status == "ok":
                    status, note = "failed", "Missing result despite exit 0"
                row = {key: "" for key in base.RESULT_FIELDS}
                row.update(task=task, recipe=recipe)
            row.update(status=status, note=note, process_seconds=elapsed)
            base.write_csv(path, [row], base.RESULT_FIELDS)
            print(f"{task} {recipe} {status} score={row['score']} process={elapsed:.2f}s", flush=True)


def summarize(work):
    records = []
    for task in base.TASKS:
        for recipe in pd.read_csv(work / "operators.csv").recipe:
            path = work / "attempts" / task / recipe / "result.csv"
            if not path.exists():
                raise ValueError(f"Unfinished attempt: {task}/{recipe}")
            records.append(pd.read_csv(path))
    extensions = pd.concat(records, ignore_index=True)
    extensions.to_csv(work / "extension-results.csv", index=False)
    combined = pd.concat([pd.read_csv(work / "base-results.csv"), extensions], ignore_index=True)
    combined.to_csv(work / "combined-results.csv", index=False)
    first = pd.read_csv(work / "base-recipes.csv").recipe.tolist()[:8]
    enhanced = [f"{family}-0" for family in base.FAMILIES] + ["linear-0-pairwise", "linear-0-quantile"]
    summary = []
    for task in base.TASKS:
        table = combined[combined.task == task].set_index("recipe")
        losses = table.normalized_loss.fillna(np.inf)
        reference = losses.idxmin()
        for name, ids in (("original_diverse", first), ("expanded_diverse", enhanced)):
            selected = losses.loc[ids].idxmin()
            summary.append(dict(task=task, control=name, budget=8, selected=selected,
                                score=table.loc[selected, "score"], reference=reference,
                                reference_score=table.loc[reference, "score"],
                                normalized_headroom=float(losses[selected] - losses[reference])))
    base.write_csv(work / "headroom.csv", summary)
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "fit", "summarize"))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--task", choices=base.TASKS)
    parser.add_argument("--recipe")
    args = parser.parse_args()
    work = args.workspace.resolve()
    if work.is_relative_to(base.REPO):
        raise ValueError("Use a sibling workspace")
    if args.action == "prepare":
        prepare(args.source.resolve(), work)
    elif args.action == "fit":
        fit(work, args.task, args.recipe)
    else:
        {"run": run, "summarize": summarize}[args.action](work)
