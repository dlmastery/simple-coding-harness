"""Check the starting bike baseline report; no imports from the course solver."""
import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
import sys


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check(reference, source, report):
    require(hashlib.sha256(source.read_bytes()).hexdigest() ==
            "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f", "Source changed")
    registry = read_rows(reference / "trials.csv")
    require(len(registry) == 1, "Expected one trial")
    for key, value in {"candidate":"trial-001", "status":"ok", "task":"bike",
                       "model":"constant", "features":"calendar", "seed":"17"}.items():
        require(registry[0][key] == value, f"Wrong {key}")
    contract = (reference / "CONTRACT.md").read_text(encoding="utf-8")
    for field in ["- metric: MAE", "- label: cnt", "- split: 2011 / 2012-H1 / 2012-H2"]:
        require(field in contract.splitlines(), "Wrong task contract")
    data = read_rows(source)
    expected = {i for i,row in enumerate(data) if "2012-01-01" <= row["dteday"] < "2012-07-01"}
    predictions = read_rows(reference / "predictions.csv")
    ids = [int(row["source_row"]) for row in predictions]
    require(len(ids) == len(set(ids)) and set(ids) == expected, "Wrong row set")
    errors = []
    for index,row in zip(ids,predictions):
        actual, predicted = float(row["actual"]), float(row["predicted"])
        require(math.isfinite(predicted) and actual == float(data[index]["cnt"]), "Wrong numeric evidence")
        errors.append(abs(actual-predicted))
    score = math.fsum(errors)/len(errors)
    require(math.isclose(score,float(registry[0]["score"]),rel_tol=0,abs_tol=1e-10), "Registry mismatch")
    text = report.read_text(encoding="utf-8")
    require(text.startswith("# trial-001: selection result\n"), "Wrong report identity")
    matches = re.findall(r"^Score: (\d+\.\d{6})\.$",text,re.M)
    require(len(matches) == 1, "Expected one six-decimal claim")
    print(f"Evidence: {len(ids)} selection rows; MAE {score:.17g} rentals per hour")
    print(f"Report: {report.name}; claimed MAE {matches[0]}")
    require(abs(float(matches[0])-score) <= 0.000000500001, "Report disagrees at declared six-decimal precision")
    print("PASS: report matches the saved prediction evidence")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["reference","source","report"]:
        parser.add_argument("--"+name,type=Path,required=True)
    args = parser.parse_args()
    try:
        check(args.reference,args.source,args.report)
    except (ValueError,KeyError,OSError,csv.Error) as exc:
        print(f"REFUSED: {exc}",file=sys.stderr)
        sys.exit(2)
