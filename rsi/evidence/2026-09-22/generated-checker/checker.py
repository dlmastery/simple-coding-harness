"""Lab 01.04: generated separately from the supplied checker; no solver imports.

This checks a declared historical bike baseline, not arbitrary model provenance.
The caller and checker share host access. References are not a secret evaluator.
"""
import argparse
import csv
import hashlib
import math
import sys
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check(reference, predictions, source):
    contract = (reference / "CONTRACT.md").read_text(encoding="utf-8")
    fields = dict(line[2:].split(": ", 1) for line in contract.splitlines()
                  if line.startswith("- ") and ": " in line)
    for key, expected in {"task": "bike", "metric": "MAE", "label": "cnt",
                          "split": "2011 / 2012-H1 / 2012-H2"}.items():
        require(fields.get(key) == expected, f"Wrong contract field: {key}")
    expected_source = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
    require(fields.get("data_sha256") == expected_source, "Unexpected data identity")
    require(digest(source) == expected_source, "Source hash mismatch")
    registry = rows(reference / "trials.csv")
    require(len(registry) == 1, "Expected exactly one recorded candidate")
    candidate = registry[0]
    for key, expected in {"candidate": "trial-001", "status": "ok", "task": "bike",
                          "model": "constant", "features": "calendar", "seed": "17"}.items():
        require(candidate.get(key) == expected, f"Wrong candidate field: {key}")
    require(digest(reference / "POLICY-SNAPSHOT.md") == candidate["policy_sha256"],
            "Policy identity mismatch")
    proposal = (reference / "PROPOSAL.md").read_text(encoding="utf-8")
    require(proposal.startswith("# trial-001\n"), "Proposal candidate mismatch")
    require("Model: constant. Features: calendar. Seed: 17." in proposal,
            "Proposal recipe mismatch")
    data = rows(source)
    expected_ids = {i for i, row in enumerate(data)
                    if "2012-01-01" <= row["dteday"] < "2012-07-01"}
    observed = rows(predictions)
    require(bool(observed), "No predictions")
    ids = [int(row["source_row"]) for row in observed]
    require(len(ids) == len(set(ids)), "Duplicate row identity")
    unexpected = set(ids) - expected_ids
    require(not unexpected, f"Rows outside selection: {sorted(unexpected)[:5]}")
    require(set(ids) == expected_ids, "Selection row set is incomplete")
    errors = []
    for row, index in zip(observed, ids):
        actual, prediction = float(row["actual"]), float(row["predicted"])
        require(math.isfinite(actual) and math.isfinite(prediction), "Nonfinite number")
        target = float(data[index]["cnt"])
        require(actual == target, f"Wrong source target at row {index}")
        require(int(row["hour"]) == int(data[index]["hr"]), f"Wrong hour at row {index}")
        errors.append(abs(target - prediction))
    score = math.fsum(errors) / len(errors)
    recorded = float(candidate["score"])
    require(math.isfinite(recorded), "Nonfinite recorded score")
    require(math.isclose(score, recorded, rel_tol=0, abs_tol=1e-10), "MAE mismatch")
    print(f"PASS: trial-001, constant/calendar, seed 17; {len(ids)} selection rows")
    print(f"MAE recomputed from pinned targets: {score:.17g}")
    print(f"Predictions SHA256: {digest(predictions)}")
    print("Boundary: artifact consistency, not authenticated training provenance or isolated evaluation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    try:
        check(args.reference, args.predictions, args.source)
    except (ValueError, KeyError, OSError, csv.Error) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(2)
