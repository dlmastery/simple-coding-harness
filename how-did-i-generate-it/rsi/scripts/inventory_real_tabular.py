"""Collect OpenML task metadata, not dataset rows or model results."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import urllib.request


def inventory(out):
    if out.exists():
        raise ValueError("Use a fresh inventory directory")
    out.mkdir(parents=True)
    raw_dir = out / "api-responses"
    raw_dir.mkdir()
    manifest = []
    request_ids = itertools.count(1)

    def fetch(route):
        url = "https://www.openml.org/api/v1/json/" + route
        request = urllib.request.Request(url, headers={"User-Agent": "RSI-course-metadata-audit/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read()
        name = route.replace("/", "-") + f"-{next(request_ids):04d}.json"
        (raw_dir / name).write_bytes(raw)
        manifest.append(dict(path="api-responses/" + name, url=url, bytes=len(raw),
                             sha256=hashlib.sha256(raw).hexdigest(), retrieved_utc=datetime.now(timezone.utc).isoformat()))
        return json.loads(raw)

    jobs = []
    for suite in (99, 353):
        study = fetch(f"study/{suite}")["study"]
        for task in study["tasks"]["task_id"]:
            jobs.append((suite, int(task)))

    def task_metadata(job):
        suite, task_id = job
        try:
            task = fetch(f"task/{task_id}")["task"]
            definition = next(x["data_set"] for x in task["input"] if x["name"] == "source_data")
            dataset_id = int(definition["data_set_id"])
            description = fetch(f"data/{dataset_id}")["data_set_description"]
            quality = {x["name"]: x.get("value") for x in fetch(f"data/qualities/{dataset_id}")["data_qualities"]["quality"]}
            rows, columns = int(float(quality["NumberOfInstances"])), int(float(quality["NumberOfFeatures"]))
            license_text = description.get("licence", "")
            clear_license = bool(re.search(r"CC[ -]?BY|CC0|PUBLIC DOMAIN|CREATIVE COMMONS ATTRIBUTION", license_text, re.I))
            reason = []
            if not 750 <= rows <= 30000:
                reason.append("row count outside laptop range")
            if not 5 <= columns <= 65:
                reason.append("column count outside laptop range")
            if not clear_license:
                reason.append("license needs review")
            return dict(suite=suite, task=task_id, dataset=dataset_id, name=description["name"],
                version=description.get("version", ""), kind=task["task_type"], target=definition["target_feature"],
                rows=rows, columns=columns, symbolic_columns=quality.get("NumberOfSymbolicFeatures", ""),
                missing_values=quality.get("NumberOfMissingValues", ""), license=license_text,
                eligible=not reason, reason="; ".join(reason) or "metadata candidate; raw review pending",
                data_url=description.get("url", ""))
        except Exception as error:
            return dict(suite=suite, task=task_id, eligible=False, reason=f"metadata retrieval unresolved: {type(error).__name__}: {error}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(task_metadata, jobs))
    records.sort(key=lambda r: (r["suite"], r["task"]))
    selected = []
    for suite in (99, 353):
        selected.extend([r for r in records if r["suite"] == suite and r["eligible"]][:6])
    fields = ["suite", "task", "dataset", "name", "version", "kind", "target", "rows", "columns", "symbolic_columns", "missing_values", "license", "eligible", "reason", "data_url"]
    for name, rows, columns in (("INVENTORY.csv", records, fields), ("CANDIDATE-PANEL.csv", selected, fields),
                                ("API-MANIFEST.csv", sorted(manifest, key=lambda x: x["path"]), list(manifest[0]))):
        with (out / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
    text = ("# Real tabular task inventory\n\n"
            f"Collected metadata for {len(records)} tasks from OpenML studies 99 and 353. "
            "Zero dataset rows downloaded; zero model fits; no model scores requested.\n\n"
            "This is a candidate panel from the declared metadata rule. Raw data, provenance, "
            "group/duplicate structure, license terms and experiment roles still need checking.\n\n"
            "| Suite | Task | Dataset | Rows | Columns | License |\n|---|---:|---|---:|---:|---|\n")
    for row in selected:
        text += f"| {row['suite']} | {row['task']} | {row['name']} | {row['rows']} | {row['columns']} | {row['license']} |\n"
    text += "\nINVENTORY.csv keeps all exclusions and retrieval failures. API-MANIFEST.csv records the original response identities. No success claim follows from selection into this panel.\n"
    (out / "README.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    inventory(parser.parse_args().destination.resolve())
