"""Check metadata identities and the declared candidate ordering; zero fits."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


def read(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def check(work):
    checks, documents = [], {}

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    for row in read(work / "API-MANIFEST.csv"):
        path = work / row["path"]
        raw = path.read_bytes()
        require(row["path"] + "/identity", hashlib.sha256(raw).hexdigest() == row["sha256"] and len(raw) == int(row["bytes"]))
        route = row["url"].removeprefix("https://www.openml.org/api/v1/json/")
        require(row["path"] + "/metadata_only", re.fullmatch(r"(?:study|task|data|data/qualities)/\d+", route) is not None)
        documents[route] = json.loads(raw)
    inventory = read(work / "INVENTORY.csv")
    for row in inventory:
        prefix = f"{row['suite']}/{row['task']}"
        study = documents["study/" + row["suite"]]["study"]
        require(prefix + "/member", row["task"] in [str(x) for x in study["tasks"]["task_id"]])
        if row["reason"].startswith("metadata retrieval unresolved"):
            require(prefix + "/failure_ineligible", row["eligible"] == "False")
            continue
        task = documents["task/" + row["task"]]["task"]
        data = next(x["data_set"] for x in task["input"] if x["name"] == "source_data")
        require(prefix + "/dataset_identity", str(data["data_set_id"]) == row["dataset"] and data["target_feature"] == row["target"])
        description = documents["data/" + row["dataset"]]["data_set_description"]
        qualities = {x["name"]: x.get("value") for x in documents["data/qualities/" + row["dataset"]]["data_qualities"]["quality"]}
        require(prefix + "/description", description["name"] == row["name"] and description.get("licence", "") == row["license"])
        count, width = int(float(qualities["NumberOfInstances"])), int(float(qualities["NumberOfFeatures"]))
        require(prefix + "/dimensions", count == int(row["rows"]) and width == int(row["columns"]))
        license_ok = bool(re.search(r"CC[ -]?BY|CC0|PUBLIC DOMAIN|CREATIVE COMMONS ATTRIBUTION", row["license"], re.I))
        require(prefix + "/eligibility", (row["eligible"] == "True") == (750 <= count <= 30000 and 5 <= width <= 65 and license_ok))
    expected = []
    for suite in ("99", "353"):
        expected += sorted([r for r in inventory if r["suite"] == suite and r["eligible"] == "True"], key=lambda r: int(r["task"]))[:6]
    require("panel_exact_rule", read(work / "CANDIDATE-PANEL.csv") == expected)
    require("all_members_inventoried", len(inventory) == sum(len(documents["study/" + suite]["study"]["tasks"]["task_id"]) for suite in ("99", "353")))
    with (work / "CHECKS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("check", "passed"))
        writer.writeheader()
        writer.writerows(checks)
    print(f"{len(checks)} metadata identity and selection checks passed; {len(expected)} candidates; no data rows or fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
