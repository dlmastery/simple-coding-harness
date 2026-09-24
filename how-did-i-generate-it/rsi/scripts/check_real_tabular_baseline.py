"""Recompute portfolio losses from saved predictions and check allocation/source identity."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def check(work):
    results = []

    def require(name, condition):
        results.append(dict(check=name, passed=bool(condition)))
        if not condition:
            pd.DataFrame(results).to_csv(work / "BASELINE-CHECKS.csv", index=False)
            raise AssertionError(name)

    require("terminal", (work / "COMPLETE.md").exists() and not list(work.rglob(".running")))
    freeze = pd.read_csv(work / "SOURCE-AND-INPUT-FREEZE.csv")
    for item in freeze.itertuples():
        raw = (work / item.path).read_bytes()
        require("source/" + item.path, len(raw) == item.bytes and hashlib.sha256(raw).hexdigest() == item.sha256)
    require("no_final_copies", not list(work.rglob("final.csv")))
    panel = pd.read_csv(work / "PANEL.csv")
    require("development_tasks", set(panel.task) == {3, 16, 28, 361234, 361236, 361244} and (panel.role == "development").all())
    planned = pd.read_csv(work / "PLANNED.csv")
    ledger = pd.read_csv(work / "LEDGER.csv")
    require("all_attempts_charged", len(ledger) == 48 and ledger.attempt.tolist() == list(range(1, 49)))
    require("planned_identity", ledger[planned.columns].equals(planned))
    require("eight_per_task", (ledger.groupby("task").size() == 8).all())
    require("worker_budget", (ledger.worker_seconds > 0).all() and (ledger.worker_seconds <= 32).all())
    for task in panel.itertuples():
        directory = work / "public" / str(task.task)
        schema = pd.read_csv(directory / "SCHEMA.csv")
        dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
        train = pd.read_csv(directory / "train.csv", dtype=dtype)
        target = task.target
        scale = np.mean(np.abs(train[target] - np.median(train[target]))) if task.kind == "regression" else 1.
        for attempt in ledger[ledger.task == task.task].itertuples():
            output = work / "attempts" / f"{attempt.attempt:03d}"
            require(f"{attempt.attempt}/admission", (output / "ADMITTED.md").exists())
            require(f"{attempt.attempt}/outputs", (output / "stdout.txt").exists() and (output / "stderr.txt").exists())
            if attempt.status != "success":
                require(f"{attempt.attempt}/failure_charged", attempt.status in {"timeout", "failed"} and attempt.exit_code != 0)
                continue
            require(f"{attempt.attempt}/exit", attempt.exit_code == 0)
            metrics = pd.read_csv(output / "METRICS.csv").set_index("split")
            for split in ("train", "selection"):
                original = pd.read_csv(directory / f"{split}.csv", dtype=dtype)
                prediction = pd.read_csv(output / f"{split}-predictions.csv",
                                         dtype={"truth": str, "prediction": str} if task.kind == "classification" else None)
                require(f"{attempt.attempt}/{split}/rows", prediction.row_id.tolist() == original.row_id.tolist())
                require(f"{attempt.attempt}/{split}/labels", np.array_equal(prediction.truth.to_numpy(), original[target].to_numpy()))
                if task.kind == "classification":
                    recalls = [np.mean(prediction.loc[prediction.truth == label, "prediction"] == label) for label in sorted(prediction.truth.unique())]
                    score = float(np.mean(recalls))
                    loss = 1 - score
                    require(f"{attempt.attempt}/{split}/classes", set(prediction.prediction) <= set(train[target]))
                else:
                    require(f"{attempt.attempt}/{split}/finite", np.isfinite(prediction.prediction).all())
                    score = float(np.mean(np.abs(prediction.truth - prediction.prediction)))
                    loss = score / scale
                require(f"{attempt.attempt}/{split}/score", np.isclose(score, metrics.loc[split, "score"], atol=1e-12, rtol=1e-12))
                require(f"{attempt.attempt}/{split}/loss", np.isclose(loss, metrics.loc[split, "loss"], atol=1e-12, rtol=1e-12))
                require(f"{attempt.attempt}/{split}/scale", np.isclose(scale, metrics.loc[split, "training_scale"], atol=1e-12, rtol=1e-12))
                if split == "selection":
                    require(f"{attempt.attempt}/ledger", np.isclose(loss, attempt.selection_loss, atol=1e-12, rtol=1e-12))
    winners = ledger[ledger.status == "success"].sort_values(["task", "selection_loss", "attempt"]).groupby("task", as_index=False).first()
    require("one_winner_per_task", set(winners.task) == set(panel.task))
    winners.to_csv(work / "WINNERS.csv", index=False)
    pd.DataFrame(results).to_csv(work / "BASELINE-CHECKS.csv", index=False)
    lines = ["# Conventional portfolio development results", "", "These are selection scores. No final partition was scored. This is model selection, not RSI.", "",
             "| Task | Selected model | Metric | Selection score | Normalized loss |", "|---|---|---|---:|---:|"]
    for row in winners.itertuples():
        lines.append(f"| {row.task} | {row.candidate} | {'Balanced accuracy' if row.kind == 'classification' else 'MAE'} | {row.selection_score:.6f} | {row.selection_loss:.6f} |")
    lines.extend(["", f"48 attempts; {(ledger.status == 'success').sum()} succeeded; {(ledger.status != 'success').sum()} failed or timed out. "
                  f"Total worker-process time {ledger.worker_seconds.sum():.3f} seconds. {len(results)} checks passed.", "",
                  "The fixed portfolio is the development reference for the next agent-authored proposal. "
                  "No runtime-independent or total-cost gain follows from this baseline. Agent inference time/cost is unmetered.", ""])
    (work / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(results)} checks passed; 48 attempts; no final scoring")
    print(winners[["task", "candidate", "selection_score", "selection_loss"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
