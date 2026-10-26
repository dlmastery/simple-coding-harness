"""Small deterministic experiment tools, operated by a coding agent.

The agent decides hypotheses and writes skills. This module does not implement
an LLM, autonomous skill evolution, a sandbox, or a secret evaluator.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
DATA = {
    "bike": (ROOT / "examples/bike-demand/source/hour.csv", "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"),
    "wine": (ROOT / "examples/wine-quality/source/winequality-red.csv", "4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e"),
}
CALENDAR = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday"]
WEATHER = ["weathersit", "temp", "atemp", "hum", "windspeed"]
CATEGORICAL = CALENDAR + ["weathersit"]
MODELS = ("constant", "linear", "tree", "forest")
FIELDS = ["candidate", "status", "task", "model", "features", "seed", "score", "seconds", "policy_sha256", "note"]
MAX_ATTEMPTS = 12
MAX_SECONDS = 120


class Refusal(ValueError):
    """An invalid request; it must not turn into a successful experiment."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_data(task: str) -> pd.DataFrame:
    path, expected = DATA[task]
    if digest(path) != expected:
        raise Refusal("Source data changed. Restore the pinned source; use a new task for different data.")
    return pd.read_csv(path, sep=";" if task == "wine" else ",")


def partitions(data: pd.DataFrame, task: str) -> dict[str, np.ndarray]:
    if task == "bike":
        date = data["dteday"]
        return {"train": (date < "2012-01-01").to_numpy(),
                "selection": ((date >= "2012-01-01") & (date < "2012-07-01")).to_numpy(),
                "final": (date >= "2012-07-01").to_numpy()}
    # The same feature vector always has the same group, independent of its label.
    keys = data.drop(columns="quality").astype(str).agg("|".join, axis=1)
    bucket = keys.map(lambda key: int(hashlib.sha256(("wine-v1|" + key).encode()).hexdigest()[:8], 16) % 100)
    return {"train": (bucket < 60).to_numpy(),
            "selection": ((bucket >= 60) & (bucket < 80)).to_numpy(),
            "final": (bucket >= 80).to_numpy()}


def target(data: pd.DataFrame, task: str) -> pd.Series:
    return data.cnt if task == "bike" else (data.quality >= 7).astype(int)


def feature_names(task: str, choice: str, data: pd.DataFrame) -> list[str]:
    if task == "wine":
        if choice != "all":
            raise Refusal("Wine uses 'all' physicochemical inputs. The label and quality are excluded.")
        return list(data.drop(columns="quality").columns)
    choices = {"calendar": CALENDAR, "weather": WEATHER, "all": CALENDAR + WEATHER}
    if choice not in choices:
        raise Refusal("Use calendar, weather, or all. Count components and the target are forbidden features.")
    return choices[choice]


def pipeline(task: str, model: str, columns: list[str], seed: int) -> Pipeline:
    if model not in MODELS:
        raise Refusal("Unknown model family. An extension requires a new, documented tool contract.")
    cat = [c for c in columns if c in CATEGORICAL] if task == "bike" else []
    num = [c for c in columns if c not in cat]
    transform = ColumnTransformer([
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num),
        ("category", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), cat),
    ])
    if task == "bike":
        estimator = {"constant": lambda: DummyRegressor(strategy="median"),
                     "linear": lambda: Ridge(alpha=10),
                     "tree": lambda: DecisionTreeRegressor(max_depth=8, min_samples_leaf=15, random_state=seed),
                     "forest": lambda: RandomForestRegressor(n_estimators=40, max_depth=12, min_samples_leaf=5, n_jobs=1, random_state=seed)}[model]()
    else:
        estimator = {"constant": lambda: DummyClassifier(strategy="most_frequent"),
                     "linear": lambda: LogisticRegression(C=1, max_iter=500, class_weight="balanced", random_state=seed),
                     "tree": lambda: DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, class_weight="balanced", random_state=seed),
                     "forest": lambda: RandomForestClassifier(n_estimators=40, max_depth=8, min_samples_leaf=5, class_weight="balanced", n_jobs=1, random_state=seed)}[model]()
    return Pipeline([("prepare", transform), ("model", estimator)])


def specification(task: str) -> dict:
    return {"version": 1, "task": task, "data_sha256": DATA[task][1],
            "tool_sha256": digest(Path(__file__)), "max_attempts": MAX_ATTEMPTS,
            "max_fit_seconds": MAX_SECONDS, "metric": "MAE" if task == "bike" else "balanced accuracy",
            "split": "2011 / 2012-H1 / 2012-H2" if task == "bike" else "feature-group hash wine-v1: 60/20/20",
            "label": "cnt" if task == "bike" else "quality >= 7"}


def contract_text(task: str) -> str:
    values = specification(task)
    return "# Frozen experiment contract\n\n" + "\n".join(f"- {k}: {v}" for k, v in values.items()) + "\n\n" + (
        "The agent can read the public source. This workspace is not a secret evaluation service.\n"
        "The fit budget excludes agent inference costs; record those separately when available.\n"
        "Keep rejected and interrupted attempts. Final evaluation closes this workspace to search.\n")


@contextmanager
def workspace_lock(workspace: Path):
    workspace.mkdir(parents=True, exist_ok=True)
    lock = workspace / ".running"
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise Refusal("Workspace busy or interrupted. Check its recorded process before removing .running.") from error
    try:
        with os.fdopen(handle, "w") as stream:
            stream.write(f"pid={os.getpid()}\nstarted={datetime.now(timezone.utc).isoformat()}\n")
        yield
    finally:
        lock.unlink(missing_ok=True)


def check_contract(workspace: Path, task: str) -> None:
    path = workspace / "CONTRACT.md"
    expected = contract_text(task)
    if path.exists() and path.read_text(encoding="utf-8") != expected:
        raise Refusal("Frozen contract differs from this tool/task. Keep this workspace; start a new one.")
    if not path.exists():
        write(path, expected)
    if (workspace / "FINAL-LOCK.md").exists():
        raise Refusal("Final evaluation already started. This workspace is closed to further selection.")


def records(workspace: Path) -> list[dict]:
    path = workspace / "trials.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def save_records(workspace: Path, rows: list[dict]) -> None:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    temporary = workspace / "trials.csv.tmp"
    write(temporary, output.getvalue())
    temporary.replace(workspace / "trials.csv")


def environment() -> str:
    return f"Python {platform.python_version()}; scikit-learn {sklearn.__version__}; pandas {pd.__version__}; NumPy {np.__version__}; {platform.system()} {platform.machine()}"


def inspect_data(task: str, workspace: Path) -> str:
    data = read_data(task)
    masks = partitions(data, task)
    y = target(data, task)
    lines = ["# Data inspection", "", environment(), "", f"Task: {task}. Rows: {len(data)}. Columns: {len(data.columns)}.",
             f"Missing cells: {int(data.isna().sum().sum())}. Exact duplicate rows: {int(data.duplicated().sum())}.", "",
             "| Partition | Rows | Target mean | Target minimum | Target maximum |", "|---|---:|---:|---:|---:|"]
    for name, mask in masks.items():
        part = y[mask]
        if part.empty or (task == "wine" and part.nunique() != 2):
            raise Refusal("A partition is empty or lacks a class. Review the task before training.")
        lines.append(f"| {name} | {len(part)} | {part.mean():.3f} | {part.min()} | {part.max()} |")
    if task == "bike":
        lines += ["", f"Dates: {data.dteday.min()} to {data.dteday.max()}.",
                  f"Rows where casual + registered = cnt: {int((data.casual + data.registered == data.cnt).sum())}.",
                  "Do not use either component count as an input. Weather is observed, so this is not an advance forecast."]
    else:
        groups = data.drop(columns="quality").astype(str).agg("|".join, axis=1)
        lines += ["", f"Repeated input vectors: {int(groups.duplicated().sum())}.",
                  "Identical input vectors stay together. Target mean is the positive class fraction."]
    lines += ["", "The source and partition summaries are public teaching data. This inspection is not independent evaluation.", ""]
    write(workspace / "DATA-REPORT.md", "\n".join(lines))
    data.head(8).to_csv(workspace / "sample.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4), facecolor="white")
    if task == "bike":
        means = data.groupby("hr").cnt.mean()
        ax.plot(means.index, means.values, color="#146a91", marker="o", markersize=3)
        ax.set(xlabel="Hour of day", ylabel="Mean rentals", title="Observed hourly demand — full public teaching data")
    else:
        counts = y.value_counts().sort_index()
        ax.bar(["Quality below 7", "Quality 7 or more"], counts.values, color=["#146a91", "#dc7d2a"])
        ax.set(ylabel="Rows", title="The derived label is imbalanced")
    fig.tight_layout()
    fig.savefig(workspace / "data-overview.png", dpi=150)
    plt.close(fig)
    return str(workspace / "DATA-REPORT.md")


def fit_once(task: str, model: str, features: str, seed: int, partition: str = "selection") -> tuple[float, pd.DataFrame, str]:
    data = read_data(task)
    masks = partitions(data, task)
    names = feature_names(task, features, data)
    y = target(data, task)
    for key in ("train", partition):
        if not masks[key].any() or (task == "wine" and y[masks[key]].nunique() < 2):
            raise Refusal("Invalid partition. A classification comparison needs both classes.")
    fitted = pipeline(task, model, names, seed)
    with threadpool_limits(limits=1):
        fitted.fit(data.loc[masks["train"], names], y[masks["train"]])
        predicted = fitted.predict(data.loc[masks[partition], names])
    actual = y[masks[partition]].to_numpy()
    if task == "bike":
        predicted = np.maximum(0, predicted)
        score = mean_absolute_error(actual, predicted)
        detail = "MAE is the mean of absolute prediction errors. Lower is better."
    else:
        score = balanced_accuracy_score(actual, predicted)
        matrix = confusion_matrix(actual, predicted, labels=[0, 1])
        detail = f"Balanced accuracy is mean class recall. Higher is better.\n\nConfusion matrix, true rows / predicted columns [0, 1]: {matrix.tolist()}."
    if not np.isfinite(score):
        raise Refusal("Non-finite score.")
    predictions = pd.DataFrame({"source_row": np.flatnonzero(masks[partition]), "actual": actual, "predicted": predicted})
    if task == "bike":
        predictions["hour"] = data.loc[masks[partition], "hr"].to_numpy()
    return float(score), predictions, detail


def experiment(workspace: Path, task: str, model: str, features: str, seed: int, hypothesis: str, policy: Path | None = None) -> dict:
    with workspace_lock(workspace):
        check_contract(workspace, task)
        rows = records(workspace)
        if len(rows) >= MAX_ATTEMPTS:
            raise Refusal("Attempt budget exhausted. Keep the evidence and stop.")
        if sum(float(row["seconds"] or 0) for row in rows) >= MAX_SECONDS:
            raise Refusal("Recorded local fit-time budget exhausted.")
        if any(row["status"] == "running" for row in rows):
            raise Refusal("Interrupted candidate needs review. Mark it interrupted; do not silently rerun it.")
        candidate = f"trial-{len(rows) + 1:03d}"
        folder = workspace / candidate
        folder.mkdir(exist_ok=False)
        policy_hash = digest(policy) if policy else "not supplied"
        if policy:
            write(folder / "POLICY-SNAPSHOT.md", policy.read_text(encoding="utf-8"))
        row = dict(candidate=candidate, status="running", task=task, model=model, features=features, seed=seed,
                   score="", seconds=0, policy_sha256=policy_hash, note=hypothesis)
        rows.append(row)
        save_records(workspace, rows)  # reserve attempt before training
        write(folder / "PROPOSAL.md", f"# {candidate}\n\n{hypothesis}\n\nModel: {model}. Features: {features}. Seed: {seed}.\n\nPolicy snapshot records provenance; it does not prove the agent followed that policy.\n")
        start = time.perf_counter()
        try:
            if not hypothesis.strip():
                raise Refusal("State the hypothesis before fitting.")
            score, predicted, detail = fit_once(task, model, features, seed)
            row.update(status="ok", score=score)
            predicted.to_csv(folder / "predictions.csv", index=False)
            write(folder / "RESULT.md", f"# {candidate}: selection result\n\n{detail}\n\nScore: {score:.6f}.\n\n{environment()}\n\nOnly training rows fit preprocessing and model parameters. Selection rows choose candidates.\n\nAgent inference cost: not measured by this tool.\n")
            if task == "bike":
                predicted["absolute_error"] = abs(predicted.actual - predicted.predicted)
                predicted.groupby("hour").absolute_error.agg(["size", "mean"]).to_csv(folder / "error-by-hour.csv")
        except Exception as error:
            row.update(status="failed", note=f"{hypothesis} | {type(error).__name__}: {error}")
            write(folder / "FAILURE.md", f"# Failed attempt\n\n{type(error).__name__}: {error}\n\nThe attempt remains in the budget and ledger.\n")
            raise
        finally:
            row["seconds"] = round(time.perf_counter() - start, 6)
            save_records(workspace, rows)
        return row


def compare(workspace: Path) -> str:
    rows = records(workspace)
    good = [r for r in rows if r["status"] == "ok"]
    if not good:
        raise Refusal("No successful candidates to compare.")
    task = good[0]["task"]
    best = min(good, key=lambda r: (float(r["score"]) * (1 if task == "bike" else -1), int(r["candidate"].split("-")[1])))
    lines = ["# Selection comparison", "", "| Candidate | State | Model | Features | Score | Local seconds |", "|---|---|---|---|---:|---:|"]
    lines += [f"| {r['candidate']} | {r['status']} | {r['model']} | {r['features']} | {r['score']} | {r['seconds']} |" for r in rows]
    lines += ["", f"Selected: {best['candidate']}. Ties retain the earlier candidate.",
              f"Attempts: {len(rows)} / {MAX_ATTEMPTS}. Local fit seconds: {sum(float(r['seconds']) for r in rows):.3f} / {MAX_SECONDS}.",
              "Agent proposal, reading, and review costs are additional. They are not measured here.",
              "A selection result does not show general improvement of an agent or its improver.", ""]
    write(workspace / "COMPARISON.md", "\n".join(lines))
    return best["candidate"]


def final_evaluation(workspace: Path, candidate: str) -> float:
    with workspace_lock(workspace):
        rows = records(workspace)
        matches = [r for r in rows if r["candidate"] == candidate and r["status"] == "ok"]
        if len(matches) != 1:
            raise Refusal("Choose one successful recorded candidate.")
        row = matches[0]
        check_contract(workspace, row["task"])
        # Lock before touching final labels. Failed final runs require a new reviewed protocol.
        write(workspace / "FINAL-LOCK.md", f"# Final evaluation started\n\nCandidate: {candidate}. No more selection in this workspace.\n")
        score, predicted, detail = fit_once(row["task"], row["model"], row["features"], int(row["seed"]), "final")
        predicted.to_csv(workspace / "final-predictions.csv", index=False)
        write(workspace / "FINAL.md", f"# Final public-data evaluation\n\nCandidate: {candidate}. Score: {score:.6f}.\n\n{detail}\n\nRefit the recorded recipe on the same training rows; selection rows are not added to training.\n\nThis is a reproducible teaching check, not a secret test against the host agent.\n")
        return score


def audit_domain(path: Path, output: Path) -> list[str]:
    """Validate a small human-readable relation table; no ontology engine required."""
    text = path.read_text(encoding="utf-8")
    triples = []
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(cells) == 3 and cells[0] != "Subject" and not cells[0].startswith("---"):
                triples.append(tuple(cells))
    if not triples:
        raise Refusal("No relation rows found. Use the supplied Markdown table with three columns.")
    facts = set(triples)
    errors = []
    for subject, relation, obj in triples:
        if relation == "uses feature" and (obj, "derived from", "target") in facts:
            errors.append(f"{subject} uses {obj}, which is derived from the target.")
        if relation == "fit on" and obj != "train":
            errors.append(f"{subject} is fit on {obj}; fitted transforms must use train only.")
        if relation == "selects on" and obj == "final":
            errors.append(f"{subject} selects on final; that consumes the final evaluation.")
    allowed = {"uses feature", "derived from", "fit on", "selects on", "measured by", "predicts", "evaluated on"}
    errors += [f"Unknown relation: {relation}. Define it before use." for _, relation, _ in triples if relation not in allowed]
    write(output, "# Domain check\n\n" + ("\n".join(f"- FAIL: {e}" for e in errors) if errors else "PASS: no violation of the supplied rules.") + "\n\nThis checks three declared invariants and relation names. It is not a complete scientific validator.\n")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "run", "compare", "final"):
        command = sub.add_parser(name)
        command.add_argument("--workspace", type=Path, required=True)
        if name in ("inspect", "run"):
            command.add_argument("--task", choices=DATA, default="bike")
        if name == "run":
            command.add_argument("--model", default="constant")
            command.add_argument("--features", default="all")
            command.add_argument("--seed", type=int, default=17)
            command.add_argument("--hypothesis", required=True)
            command.add_argument("--policy", type=Path)
        if name == "final":
            command.add_argument("--candidate", required=True)
    domain = sub.add_parser("audit-domain")
    domain.add_argument("--input", type=Path, required=True)
    domain.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            args.workspace.mkdir(parents=True, exist_ok=True)
            print(inspect_data(args.task, args.workspace))
        elif args.command == "run":
            print(json.dumps(experiment(args.workspace, args.task, args.model, args.features, args.seed, args.hypothesis, args.policy)))
        elif args.command == "compare":
            print(compare(args.workspace))
        elif args.command == "final":
            print(final_evaluation(args.workspace, args.candidate))
        else:
            return 1 if audit_domain(args.input, args.output) else 0
        return 0
    except (Refusal, OSError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
