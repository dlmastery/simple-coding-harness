"""Check all charged revision attempts and recompute their metrics from predictions."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]


def check(stage):
    work = ROOT.parent / f"rsi-work-2026-09-22-real-tabular-revision-{stage}"
    parent = ROOT / "rsi/evidence/2026-09-22/real-tabular-baseline"
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            pd.DataFrame(checks).to_csv(work / "REVISION-CHECKS.csv", index=False)
            raise AssertionError(name)

    require("terminal", (work / "COMPLETE.md").exists() and not list(work.rglob(".running")))
    for item in pd.read_csv(work / "SOURCE-AND-INPUT-FREEZE.csv").itertuples():
        raw = (work / item.path).read_bytes()
        require("frozen/" + item.path, len(raw) == item.bytes and hashlib.sha256(raw).hexdigest() == item.sha256)
    require("unchanged_parent", (work / "source/parent_engine.py").read_bytes() == (parent / "source/engine.py").read_bytes())
    require("parent_ledger", (work / "PARENT-LEDGER.csv").read_bytes() == (parent / "LEDGER.csv").read_bytes())
    require("no_final_copies", not list(work.rglob("final.csv")))
    panel = pd.read_csv(work / "PANEL.csv")
    require("development_only", set(panel.task) == {3, 16, 28, 361234, 361236, 361244} and (panel.role == "development").all())
    planned = pd.read_csv(work / "PLANNED.csv")
    ledger = pd.read_csv(work / "LEDGER.csv")
    require("charged_slots", len(ledger) == 24 and ledger.attempt.tolist() == list(range(1, 25)))
    require("planned_identity", ledger[planned.columns].equals(planned))
    require("four_per_task", (ledger.groupby("task").size() == 4).all())
    require("process_budget", (ledger.worker_seconds > 0).all() and (ledger.worker_seconds <= 32).all())
    if stage == 2:
        previous = ROOT.parent / "rsi-work-2026-09-22-real-tabular-revision-1"
        old = pd.read_csv(previous / "LEDGER.csv")
        require("total_budget", len(old) + len(ledger) == 48 and (old.groupby("task").size() + ledger.groupby("task").size() == 8).all())
        require("inherited_revision", (work / "source/revision_one_engine.py").read_bytes() == (previous / "source/engine.py").read_bytes())
    for task in panel.itertuples():
        schema = pd.read_csv(work / "public" / str(task.task) / "SCHEMA.csv")
        dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
        train = pd.read_csv(work / "public" / str(task.task) / "train.csv", dtype=dtype)
        scale = np.mean(np.abs(train[task.target] - np.median(train[task.target]))) if task.kind == "regression" else 1.
        for row in ledger[ledger.task == task.task].itertuples():
            directory = work / "attempts" / f"{row.attempt:03d}"
            require(f"{row.attempt}/admission", (directory / "ADMITTED.md").exists())
            require(f"{row.attempt}/logs", (directory / "stdout.txt").exists() and (directory / "stderr.txt").exists())
            if row.status != "success":
                require(f"{row.attempt}/failure_charged", row.status in {"failed", "timeout"} and row.exit_code != 0)
                continue
            require(f"{row.attempt}/exit", row.exit_code == 0)
            metrics = pd.read_csv(directory / "METRICS.csv").set_index("split")
            for split in ("train", "selection"):
                source = work / "public" / str(task.task) / f"{split}.csv"
                require(f"{row.attempt}/{split}/input_identity", source.read_bytes() == (parent / "public" / str(task.task) / f"{split}.csv").read_bytes())
                frame = pd.read_csv(source, dtype=dtype)
                predictions = pd.read_csv(directory / f"{split}-predictions.csv", dtype={"truth": str, "prediction": str} if task.kind == "classification" else None)
                require(f"{row.attempt}/{split}/row_ids", predictions.row_id.tolist() == frame.row_id.tolist())
                require(f"{row.attempt}/{split}/truth", np.array_equal(predictions.truth, frame[task.target]))
                if task.kind == "classification":
                    score = np.mean([np.mean(predictions.loc[predictions.truth == label, "prediction"] == label) for label in sorted(predictions.truth.unique())])
                    loss = 1 - score
                    require(f"{row.attempt}/{split}/classes", set(predictions.prediction) <= set(train[task.target]))
                else:
                    score = np.mean(np.abs(predictions.truth - predictions.prediction))
                    loss = score / scale
                    require(f"{row.attempt}/{split}/finite", np.isfinite(predictions.prediction).all())
                require(f"{row.attempt}/{split}/metric", np.isclose(score, metrics.loc[split, "score"], rtol=1e-12, atol=1e-12))
                require(f"{row.attempt}/{split}/loss", np.isclose(loss, metrics.loc[split, "loss"], rtol=1e-12, atol=1e-12))
                require(f"{row.attempt}/{split}/scale", np.isclose(scale, metrics.loc[split, "training_scale"], rtol=1e-12, atol=1e-12))
                if split == "selection":
                    require(f"{row.attempt}/ledger", np.isclose(loss, row.selection_loss, rtol=1e-12, atol=1e-12))
    successful = ledger[ledger.status == "success"]
    winners = successful.sort_values(["task", "selection_loss", "attempt"]).groupby("task", as_index=False).first()
    baseline = pd.read_csv(parent / "WINNERS.csv").set_index("task")
    report = winners.copy()
    report["parent_loss"] = report.task.map(baseline.selection_loss)
    report["candidate_minus_parent"] = report.selection_loss - report.parent_loss
    report["incumbent_loss"] = report.parent_loss
    if stage == 2:
        first = pd.read_csv(previous / "COMPARISON.csv").set_index("task")
        require("first_stage_checked", pd.read_csv(previous / "REVISION-CHECKS.csv").passed.all())
        report["incumbent_loss"] = report.task.map(first.retained_loss)
    report["candidate_minus_incumbent"] = report.selection_loss - report.incumbent_loss
    report["retained_loss"] = report[["incumbent_loss", "selection_loss"]].min(axis=1)
    report.to_csv(work / "COMPARISON.csv", index=False)
    pd.DataFrame(checks).to_csv(work / "REVISION-CHECKS.csv", index=False)
    lines = [f"# Revision {stage}: development comparison", "", "These selection results used extra development fits. They do not establish an equal-budget improvement or RSI.", "",
             "| Task | Best new candidate | Native score | Original loss | Incumbent loss | New loss | Decision against incumbent |", "|---|---|---:|---:|---:|---:|---|"]
    for row in report.itertuples():
        lines.append(f"| {row.task} | {row.candidate} | {row.selection_score:.6f} | {row.parent_loss:.6f} | {row.incumbent_loss:.6f} | {row.selection_loss:.6f} | {'Keep candidate for further study' if row.candidate_minus_incumbent < -1e-12 else 'Retain incumbent'} |")
    lines.extend(["", f"24 attempts, {len(successful)} successes, {24-len(successful)} failures/timeouts. Worker-process time: {ledger.worker_seconds.sum():.3f} seconds. {len(checks)} checks pass.", "",
                  "No final score was read. A median reference is a conventional control, not an RSI gain. Further development and later comparison costs must remain separate.", ""])
    (work / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(checks)} checks passed")
    print(report[["task", "candidate", "selection_score", "candidate_minus_parent"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=int, choices=[1, 2])
    check(parser.parse_args().stage)
