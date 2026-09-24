"""Recompute a recorded teaching result from pinned rows and saved predictions."""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error

import lab


def check(candidate_dir):
    candidate_dir = Path(candidate_dir)
    rows = lab.records(candidate_dir.parent)
    matches = [row for row in rows if row["candidate"] == candidate_dir.name and row["status"] == "ok"]
    if len(matches) != 1:
        raise ValueError("Candidate identity does not match one successful trial.")
    row = matches[0]
    data = lab.read_data(row["task"])
    expected = np.flatnonzero(lab.partitions(data, row["task"])["selection"])
    predictions = pd.read_csv(candidate_dir / "predictions.csv")
    if list(predictions.source_row) != list(expected):
        raise ValueError("Prediction row identities or order differ from the selection partition.")
    actual = lab.target(data, row["task"]).iloc[expected].to_numpy()
    if not np.array_equal(predictions.actual.to_numpy(), actual):
        raise ValueError("Saved actual targets differ from the pinned data.")
    if not np.isfinite(predictions.predicted.to_numpy()).all():
        raise ValueError("Non-finite prediction.")
    if row["task"] == "wine" and not predictions.predicted.isin([0, 1]).all():
        raise ValueError("Invalid classification label.")
    score = (mean_absolute_error(actual, predictions.predicted) if row["task"] == "bike"
             else balanced_accuracy_score(actual, predictions.predicted))
    if abs(score - float(row["score"])) > 1e-9:
        raise ValueError("Ledger score does not match recomputed predictions.")
    report = (candidate_dir / "RESULT.md").read_text(encoding="utf-8")
    match = re.search(r"Score: ([0-9.eE+-]+)\.", report)
    if not match or abs(float(match[1]) - score) > 0.500001e-6:
        raise ValueError("Report score does not match recomputed predictions.")
    return float(score)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        score = check(args.candidate_dir)
        message = f"PASS: selection rows, targets, ledger, and report agree. Score: {score:.6f}."
        code = 0
    except (ValueError, OSError) as error:
        message = f"FAIL: {error}"
        code = 1
    if args.report:
        lab.write(args.report, f"# Result check\n\n{message}\n\nThis calculation is separate code in the same local trust boundary. It does not prove evaluator secrecy.\n")
    print(message)
    raise SystemExit(code)
