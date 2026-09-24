"""Prepare declared OpenML rows and grouped partitions; never fit a model."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

import numpy as np
import pandas as pd
from scipy.io import arff

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = ROOT / "rsi/evidence/2026-09-22/real-tabular-inventory"
DEVELOPMENT = {3, 16, 28, 361234, 361236, 361244}
TASKS = [3, 6, 16, 23, 28, 31, 361234, 361235, 361236, 361237, 361244, 361247]
SALT = "rsi-real-tabular-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(work, reuse=None):
    if work.exists():
        raise ValueError("Use a fresh workspace; preserve any acquisition failure")
    work.mkdir(parents=True)
    source = work / "source"
    source.mkdir()
    for path in (Path(__file__), ROOT / "how-did-i-generate-it/rsi/validation/REAL-TABULAR-DATA-PROTOCOL.md"):
        shutil.copyfile(path, source / path.name)
    (work / "SOURCE-FREEZE.md").write_text("# Preparation sources before acquisition\n\n" +
        "\n".join(f"{p.name}: {digest(p)}" for p in sorted(source.iterdir())) + "\n", encoding="utf-8")
    catalog = pd.read_csv(INVENTORY / "INVENTORY.csv").set_index("task")
    manifest = pd.read_csv(INVENTORY / "API-MANIFEST.csv")
    descriptions = {}
    for item in manifest.itertuples():
        parts = item.url.rsplit("/", 2)
        if parts[-2] == "data":
            descriptions[int(parts[-1])] = json.loads((INVENTORY / item.path).read_text())["data_set_description"]
    summaries = []
    for task in TASKS:
        row = catalog.loc[task]
        directory = work / "tasks" / str(task)
        directory.mkdir(parents=True)
        descriptor = descriptions[int(row.dataset)]
        url = str(row.data_url)
        raw_path = directory / "original.arff"
        previous = reuse / "tasks" / str(task) if reuse else None
        copied = previous is not None and (previous / "original.arff").exists()
        if copied:
            shutil.copyfile(previous / "original.arff", raw_path)
            shutil.copyfile(previous / "SOURCE.md", directory / "ORIGINAL-ACQUISITION.md")
            if digest(raw_path) != digest(previous / "original.arff"):
                raise ValueError("Cached source identity changed")
        else:
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "RSI-course-data-audit/1.0"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    raw_path.write_bytes(response.read())
            except Exception as error:
                (directory / "ACQUISITION-FAILURE.md").write_text(f"# Acquisition failure\n\nURL: {url}\n{type(error).__name__}: {error}\n")
                raise
        raw_md5 = hashlib.md5(raw_path.read_bytes()).hexdigest()
        expected_md5 = descriptor.get("md5_checksum", "")
        if expected_md5 and expected_md5 != raw_md5:
            raise ValueError(f"OpenML raw MD5 differs for {task}")
        (directory / "SOURCE.md").write_text(
            f"# Dataset acquisition\n\nTask: {task}\nDataset: {row.dataset}, version {row.version}\n"
            f"Name: {row['name']}\nTarget: {row.target}\nURL: {url}\n"
            f"{'Copied cached bytes' if copied else 'Retrieved'} UTC: {datetime.now(timezone.utc).isoformat()}\nSHA256: {digest(raw_path)}\n"
            f"MD5: {raw_md5}\nOpenML MD5: {expected_md5 or 'not supplied'}\n"
            f"Metadata license: {row.license}\n"
            f"Cached source: {previous if copied else 'none'}\n"
            "Classification licenses and original attribution are resolved in the inventory REVIEW.md.\n", encoding="utf-8")
        records, schema = arff.loadarff(raw_path)
        frame = pd.DataFrame(records)
        ignored = []
        for key in ("ignore_attribute", "row_id_attribute"):
            declared = descriptor.get(key, [])
            if isinstance(declared, str):
                declared = [name.strip() for name in declared.split(",") if name.strip()]
            for name in declared or []:
                if name == row.target or name not in frame:
                    raise ValueError(f"Invalid declared exclusion {name} for {task}")
                ignored.append(dict(column=name, reason=key))
        pd.DataFrame(ignored, columns=["column", "reason"]).to_csv(directory / "IGNORED-COLUMNS.csv", index=False)
        frame = frame.drop(columns=list(dict.fromkeys(item["column"] for item in ignored)))
        if frame.shape != (int(row.rows), int(row.columns)) or row.target not in frame:
            raise ValueError(f"Metadata schema mismatch for {task}")
        kinds = []
        for name in frame:
            declared_type, categories = schema[name]
            nominal = declared_type == "nominal"
            if nominal:
                frame[name] = frame[name].map(lambda value: value.decode("utf-8") if isinstance(value, bytes) else value)
                frame[name] = frame[name].replace("?", np.nan)
            kinds.append(dict(column=name, role="target" if name == row.target else "feature", kind="categorical" if nominal else "numeric",
                              categories=" | ".join(categories) if categories else ""))
        pd.DataFrame(kinds).to_csv(directory / "SCHEMA.csv", index=False)
        if frame[row.target].isna().any():
            raise ValueError(f"Missing target in task {task}; preserve and review")
        feature_names = frame.columns.drop(row.target).tolist()
        groups = []
        for values in frame[feature_names].itertuples(index=False, name=None):
            canonical = [None if pd.isna(value) else float(value) if isinstance(value, (int, float)) else str(value) for value in values]
            groups.append(hashlib.sha256(json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest())
        group_table = pd.DataFrame(dict(row_id=np.arange(len(frame)), group=groups))
        unique = group_table.groupby("group", sort=True).size().rename("size").to_frame()
        unique["salted"] = [hashlib.sha256((SALT + ":" + key).encode()).hexdigest() for key in unique.index]
        unique["bucket"] = [int(value, 16) % 10 for value in unique.salted]
        unique["split"] = np.where(unique.bucket < 6, "train", np.where(unique.bucket < 8, "selection", "final"))
        unique["included"] = False
        for split, cap in (("train", 2400), ("selection", 800), ("final", 800)):
            used = 0
            for group, item in unique[unique.split == split].sort_values("salted").iterrows():
                if used + item["size"] > cap:
                    break
                unique.loc[group, "included"] = True
                used += item["size"]
        group_table = group_table.join(unique[["split", "included"]], on="group")
        group_table.to_csv(directory / "ROW-ROLES.csv", index=False)
        unique.to_csv(directory / "GROUPS.csv", index_label="group")
        classification = row.kind == "Supervised Classification"
        labels = set(frame[row.target].unique()) if classification else set()
        counts, label_support = {}, True
        for split in ("train", "selection", "final"):
            ids = group_table.loc[(group_table.split == split) & group_table.included, "row_id"].to_numpy()
            part = frame.iloc[ids].copy()
            part.insert(0, "row_id", ids)
            target_dir = directory / ("evaluator" if split == "final" else "public")
            target_dir.mkdir(exist_ok=True)
            part.to_csv(target_dir / f"{split}.csv", index=False)
            counts[split] = len(part)
            label_support &= not classification or set(part[row.target].unique()) == labels
        conflicts = pd.DataFrame(dict(group=groups, target=frame[row.target])).groupby("group").target.nunique()
        summary = dict(task=task, dataset=int(row.dataset), name=row["name"],
            role="development" if task in DEVELOPMENT else "procedure-comparison", kind="classification" if classification else "regression",
            target=row.target, rows=len(frame), features=len(feature_names), categorical_inputs=sum(k["kind"] == "categorical" and k["role"] == "feature" for k in kinds),
            missing_inputs=int(frame[feature_names].isna().sum().sum()), constant_inputs=int(frame[feature_names].nunique(dropna=False).le(1).sum()),
            duplicate_rows=int(len(frame) - len(unique)), conflicting_groups=int(conflicts.gt(1).sum()),
            all_classes_in_each_split=bool(label_support), raw_sha256=digest(raw_path), **counts)
        summaries.append(summary)
        pd.DataFrame([summary]).to_csv(directory / "PROFILE.csv", index=False)
        pd.DataFrame(summaries).to_csv(work / "DATASET-PANEL.csv", index=False)
        print(f"Prepared {task}: {row['name']}; counts {counts}; duplicate rows {summary['duplicate_rows']}; classes supported {label_support}", flush=True)
    files = []
    for path in sorted(work.rglob("*")):
        if path.is_file():
            files.append(dict(path=path.relative_to(work).as_posix(), bytes=path.stat().st_size, sha256=digest(path)))
    pd.DataFrame(files).to_csv(work / "PREPARATION-MANIFEST.csv", index=False)
    print("Prepared twelve tasks; zero model fits. Independent data checks and provenance review still required.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--reuse-raw-workspace", type=Path)
    args = parser.parse_args()
    path = args.workspace.resolve()
    if path.is_relative_to(ROOT):
        raise ValueError("Use a sibling workspace for preparation")
    prepare(path, args.reuse_raw_workspace.resolve() if args.reuse_raw_workspace else None)
