"""Acquire six pinned datasets, then prepare entity/feature-group partitions; zero fits."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import re
import urllib.request

import numpy as np
import pandas as pd
from scipy.io import arff

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-nested-data-2"
INVENTORY = ROOT / "rsi/evidence/2026-09-22/real-tabular-inventory"
TASKS = [43, 45, 2074, 361241, 361251, 361260]
SALT = "rsi-nested-public-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(destination):
    rows = [dict(path=p.relative_to(WORK).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(WORK.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p != destination]
    pd.DataFrame(rows).to_csv(destination, index=False)


def acquire(reuse=None):
    WORK.mkdir(exist_ok=False)
    source = WORK / "source"
    source.mkdir()
    for path in (Path(__file__), ROOT / "how-did-i-generate-it/rsi/validation/NESTED-DATA-PROTOCOL.md",
                 ROOT / "how-did-i-generate-it/rsi/validation/NEXT-PROCEDURE-TASKS.md"):
        shutil.copyfile(path, source / path.name)
    catalog = pd.read_csv(INVENTORY / "INVENTORY.csv").set_index("task")
    api = pd.read_csv(INVENTORY / "API-MANIFEST.csv")
    selected = catalog.loc[TASKS].reset_index()
    selected.to_csv(WORK / "SELECTED-TASKS.csv", index=False)
    records = []
    for row in selected.itertuples():
        directory = WORK / "tasks" / str(row.task)
        directory.mkdir(parents=True)
        item, = list(api[api.url == f"https://www.openml.org/api/v1/json/data/{row.dataset}"].itertuples())
        original = INVENTORY / item.path
        if sha(original) != item.sha256:
            raise ValueError("Cached descriptor differs from its source manifest")
        descriptor_path = directory / "OPENML-DESCRIPTOR.json"
        shutil.copyfile(original, descriptor_path)
        descriptor = json.loads(descriptor_path.read_text())["data_set_description"]
        url = str(row.data_url)
        record = dict(task=row.task, url=url, started_utc=datetime.now(timezone.utc).isoformat())
        try:
            if reuse is not None:
                previous = pd.read_csv(reuse / "ACQUISITION.csv").set_index("task").loc[row.task]
                raw = (reuse / "tasks" / str(row.task) / "original.arff").read_bytes()
                if hashlib.sha256(raw).hexdigest() != previous.sha256:
                    raise ValueError("Cached raw bytes differ from prior acquisition")
                record.update(copied_from=str(reuse), original_started_utc=previous.started_utc)
            else:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "RSI-course-data-audit/1.0"}), timeout=60) as response:
                    raw = response.read()
            (directory / "original.arff").write_bytes(raw)
            md5 = hashlib.md5(raw).hexdigest()
            if md5 != descriptor["md5_checksum"]:
                raise ValueError("Downloaded MD5 does not match pinned metadata")
            record.update(status="success", bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), md5=md5)
        except Exception as error:
            record.update(status="failed", error=f"{type(error).__name__}: {error}")
            records.append(record)
            pd.DataFrame(records).to_csv(WORK / "ACQUISITION.csv", index=False)
            raise
        records.append(record)
        pd.DataFrame(records).to_csv(WORK / "ACQUISITION.csv", index=False)
        print(f"Acquired task {row.task}: {row.name}; {len(raw)} pinned bytes", flush=True)
    manifest(WORK / "ACQUISITION-MANIFEST.csv")
    print("All six raw files acquired; zero fits")


def read_source(directory):
    try:
        records, metadata = arff.loadarff(directory / "original.arff")
    except NotImplementedError:
        # The pinned grid file has numeric fields plus its excluded, string
        # alternate target. Parse only this verified dense CSV-compatible case.
        lines = (directory / "original.arff").read_text().splitlines()
        names, types, data_start = [], [], None
        for index, line in enumerate(lines):
            match = re.fullmatch(r"@attribute\s+'([^']+)'\s+(numeric|string)", line.strip(), re.I)
            if match:
                names.append(match[1])
                types.append(match[2].lower())
            if line.strip().lower() == "@data":
                data_start = index+1
                break
        expected = [f"tau{i}" for i in range(1, 5)] + [f"p{i}" for i in range(1, 5)] + [f"g{i}" for i in range(1, 5)] + ["stab", "stabf"]
        if names != expected or types != ["numeric"]*13 + ["string"] or data_start is None:
            raise ValueError("Unsupported string ARFF schema requires explicit review")
        values = list(csv.reader(lines[data_start:]))
        if not values or any(len(row) != 14 or row[-1] not in {"stable", "unstable"} for row in values):
            raise ValueError("Unexpected grid row width or alternate-target label")
        frame = pd.DataFrame(values, columns=names)
        for name in names[:-1]:
            frame[name] = frame[name].astype(float)
        metadata = {name: ("numeric", None) for name in names[:-1]}
        metadata["stabf"] = ("nominal", ("stable", "unstable"))
        return frame, metadata
    frame = pd.DataFrame(records)
    for name in frame:
        if metadata[name][0] == "nominal":
            frame[name] = frame[name].map(lambda value: value.decode() if isinstance(value, bytes) else value).replace("?", np.nan)
    return frame, metadata


def canonical(values):
    return json.dumps([None if pd.isna(v) else float(v) if isinstance(v, (int, float)) else str(v) for v in values],
                      ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def prepare():
    if (WORK / "PREPARATION-STARTED.md").exists():
        raise ValueError("Preserve prior preparation; do not overwrite a partial run")
    for item in pd.read_csv(WORK / "ACQUISITION-MANIFEST.csv").itertuples():
        if sha(WORK / item.path) != item.sha256:
            raise ValueError("Acquisition identity changed")
    if sha(Path(__file__)) != sha(WORK / "source" / Path(__file__).name):
        raise ValueError("Preparation source changed after acquisition")
    (WORK / "PREPARATION-STARTED.md").write_text("# Preparation admitted\n\nNo model fits.\n")
    summaries = []
    for row in pd.read_csv(WORK / "SELECTED-TASKS.csv").itertuples():
        directory = WORK / "tasks" / str(row.task)
        original, metadata = read_source(directory)
        descriptor = json.loads((directory / "OPENML-DESCRIPTOR.json").read_text())["data_set_description"]
        excluded = []
        for key in ("ignore_attribute", "row_id_attribute"):
            names = descriptor.get(key, [])
            if isinstance(names, str):
                names = [part.strip() for part in names.split(",") if part.strip()]
            for name in names:
                if name not in original or name == row.target:
                    raise ValueError(f"Invalid exclusion {name}")
                excluded.append(dict(column=name, reason=key))
        if row.task == 361251:
            for name in original:
                if name.lower() in {"stabf", "stability_class", "stable"} and name != row.target:
                    excluded.append(dict(column=name, reason="derived_stability_class"))
        pd.DataFrame(excluded, columns=["column", "reason"]).to_csv(directory / "IGNORED-COLUMNS.csv", index=False)
        names = list(dict.fromkeys(item["column"] for item in excluded))
        frame = original.drop(columns=names)
        if len(frame) != int(row.rows) or frame.shape[1] != int(row.columns) or row.target not in frame:
            raise ValueError(f"Unreconciled metadata shape for {row.task}: {frame.shape}")
        if frame[row.target].isna().any():
            raise ValueError("Missing targets require review")
        schema = pd.DataFrame([dict(column=name, role="target" if name == row.target else "feature",
                                    kind="categorical" if metadata[name][0] == "nominal" else "numeric") for name in frame])
        schema.to_csv(directory / "SCHEMA.csv", index=False)
        features = frame.columns.drop(row.target).tolist()
        feature_hashes = [hashlib.sha256(canonical(values).encode()).hexdigest() for values in frame[features].itertuples(index=False, name=None)]
        parents = list(range(len(frame)))

        def root(index):
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        def connect(first, second):
            a, b = root(first), root(second)
            parents[max(a, b)] = min(a, b)

        seen = {}
        identifiers = [name for name in names if name.lower() in {"parcelno", "instance_name"}]
        id_records = []
        for index, values in enumerate(original.itertuples(index=False, name=None)):
            keys = ["features:"+feature_hashes[index]]
            for name in identifiers:
                value = original.iloc[index][name]
                if pd.notna(value):
                    identity = canonical([value])
                    keys.append("identifier:"+name+":"+identity)
                    id_records.append(dict(row_id=index, column=name, identity=identity))
            for key in keys:
                if key in seen:
                    connect(index, seen[key])
                else:
                    seen[key] = index
        pd.DataFrame(id_records, columns=["row_id", "column", "identity"]).to_csv(directory / "ENTITY-KEYS.csv", index=False)
        components = {}
        for index, feature_hash in enumerate(feature_hashes):
            components.setdefault(root(index), []).append(feature_hash)
        identities = {key: hashlib.sha256("|".join(sorted(set(values))).encode()).hexdigest() for key, values in components.items()}
        roles = pd.DataFrame(dict(row_id=np.arange(len(frame)), feature_group=feature_hashes,
                                  group=[identities[root(index)] for index in range(len(frame))]))
        groups = roles.groupby("group").size().rename("size").to_frame()
        groups["salted"] = [hashlib.sha256(f"{SALT}:{row.task}:{key}".encode()).hexdigest() for key in groups.index]
        groups["bucket"] = [int(value, 16) % 10 for value in groups.salted]
        groups["split"] = np.where(groups.bucket < 6, "train", np.where(groups.bucket < 8, "selection", "final"))
        groups["included"] = False
        for split, cap in [("train", 2400), ("selection", 800), ("final", 800)]:
            used = 0
            for key, item in groups[groups.split == split].sort_values("salted").iterrows():
                if used + item["size"] <= cap:
                    groups.loc[key, "included"] = True
                    used += item["size"]
        roles = roles.join(groups[["split", "included"]], on="group")
        roles.to_csv(directory / "ROW-ROLES.csv", index=False)
        groups.to_csv(directory / "GROUPS.csv")
        classification = row.kind == "Supervised Classification"
        if (schema[schema.role == "target"].iloc[0].kind == "categorical") != classification:
            raise ValueError("Target type differs from the declared task kind")
        counts = {}
        for split in ("train", "selection", "final"):
            ids = roles.loc[(roles.split == split) & roles.included, "row_id"].tolist()
            part = frame.iloc[ids].copy()
            if part.empty or (classification and set(part[row.target]) != set(frame[row.target])):
                raise ValueError(f"Missing partition or class support: {row.task}/{split}")
            part.insert(0, "row_id", ids)
            target_directory = directory / ("evaluator" if split == "final" else "public")
            target_directory.mkdir(exist_ok=True)
            part.to_csv(target_directory / f"{split}.csv", index=False)
            counts[split] = len(part)
        conflicts = pd.DataFrame(dict(group=feature_hashes, target=frame[row.target])).groupby("group").target.nunique()
        summary = dict(task=row.task, dataset=row.dataset, name=row.name, kind="classification" if classification else "regression",
                       target=row.target, role="nested-procedure-comparison", rows=len(frame), features=len(features),
                       duplicate_feature_rows=len(frame)-len(set(feature_hashes)), entity_keys=len(id_records),
                       merged_components=len(groups), conflicting_feature_groups=int(conflicts.gt(1).sum()), **counts)
        summaries.append(summary)
        pd.DataFrame(summaries).to_csv(WORK / "PANEL.csv", index=False)
        print(f"Prepared {row.task}: {counts}; {len(groups)} groups; {len(id_records)} identifier records", flush=True)
    manifest(WORK / "PREPARATION-MANIFEST.csv")
    print("Prepared six tasks; zero fits; independent checks required")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["acquire", "prepare"])
    parser.add_argument("--reuse-acquisition-workspace", type=Path)
    args = parser.parse_args()
    if args.action == "acquire":
        acquire(args.reuse_acquisition_workspace)
    else:
        if args.reuse_acquisition_workspace is not None:
            raise ValueError("Raw reuse is an acquisition option only")
        prepare()
