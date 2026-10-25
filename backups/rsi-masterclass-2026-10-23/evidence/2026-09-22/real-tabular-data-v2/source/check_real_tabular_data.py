"""Audit raw-to-partition identity, exclusions and feature-group isolation; zero fits."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.datasets import load_digits


def check(work):
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    for item in pd.read_csv(work / "PREPARATION-MANIFEST.csv").itertuples():
        raw = (work / item.path).read_bytes()
        require("identity/" + item.path, len(raw) == item.bytes and hashlib.sha256(raw).hexdigest() == item.sha256)
    panel = pd.read_csv(work / "DATASET-PANEL.csv")
    require("twelve_unique_tasks", len(panel) == 12 and not panel.task.duplicated().any())
    require("declared_development", set(panel[panel.role == "development"].task) == {3, 16, 28, 361234, 361236, 361244})
    digits_overlap = None
    for item in panel.itertuples():
        directory = work / "tasks" / str(item.task)
        raw, meta = arff.loadarff(directory / "original.arff")
        original = pd.DataFrame(raw)
        excluded = pd.read_csv(directory / "IGNORED-COLUMNS.csv")
        for name in original:
            if meta[name][0] == "nominal":
                original[name] = original[name].map(lambda v: v.decode() if isinstance(v, bytes) else v).replace("?", np.nan)
        usable = original.drop(columns=excluded.column.tolist())
        schema = pd.read_csv(directory / "SCHEMA.csv", keep_default_na=False)
        require(f"{item.task}/schema_columns", schema.column.tolist() == usable.columns.tolist())
        require(f"{item.task}/target", schema[schema.role == "target"].column.tolist() == [item.target])
        require(f"{item.task}/feature_count", len(usable.columns) - 1 == item.features)
        feature_names = usable.columns.drop(item.target)
        group_keys = []
        for values in usable[feature_names].itertuples(index=False, name=None):
            normalized = [None if pd.isna(v) else float(v) if isinstance(v, (int, float)) else str(v) for v in values]
            group_keys.append(hashlib.sha256(json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest())
        roles = pd.read_csv(directory / "ROW-ROLES.csv")
        require(f"{item.task}/row_identity", roles.row_id.tolist() == list(range(len(usable))))
        require(f"{item.task}/group_identity", roles.group.tolist() == group_keys)
        require(f"{item.task}/group_isolation", roles.groupby("group").split.nunique().max() == 1)
        require(f"{item.task}/group_wholeness", roles.groupby("group").included.nunique().max() == 1)
        salted = [hashlib.sha256(("rsi-real-tabular-v1:" + key).encode()).hexdigest() for key in group_keys]
        buckets = np.array([int(key, 16) % 10 for key in salted])
        expected_split = np.where(buckets < 6, "train", np.where(buckets < 8, "selection", "final"))
        require(f"{item.task}/declared_hash_split", np.array_equal(roles.split, expected_split))
        dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
        grouped = roles.groupby("group", sort=False).agg(size=("row_id", "size"), split=("split", "first"), included=("included", "first"))
        grouped["salted"] = [hashlib.sha256(("rsi-real-tabular-v1:" + key).encode()).hexdigest() for key in grouped.index]
        for split, cap in (("train", 2400), ("selection", 800), ("final", 800)):
            path = directory / ("evaluator" if split == "final" else "public") / f"{split}.csv"
            part = pd.read_csv(path, dtype=dtype)
            ids = roles.loc[(roles.split == split) & roles.included, "row_id"]
            require(f"{item.task}/{split}/rows", part.row_id.tolist() == ids.tolist() and 0 < len(part) <= cap)
            require(f"{item.task}/{split}/no_extra_columns", part.columns.tolist() == ["row_id"] + usable.columns.tolist())
            expected = usable.iloc[ids].reset_index(drop=True)
            for field in schema.itertuples():
                good = (part[field.column].fillna("<missing>").equals(expected[field.column].fillna("<missing>")) if field.kind == "categorical"
                        else np.allclose(part[field.column], expected[field.column], equal_nan=True, atol=1e-12, rtol=1e-12))
                require(f"{item.task}/{split}/{field.column}", good)
            kept, total = [], 0
            for key, entry in grouped[grouped.split == split].sort_values("salted").iterrows():
                if total + entry["size"] > cap:
                    break
                kept.append(key)
                total += entry["size"]
            require(f"{item.task}/{split}/cap_rule", set(kept) == set(grouped[(grouped.split == split) & grouped.included].index))
            if item.kind == "classification":
                require(f"{item.task}/{split}/classes", set(part[item.target]) == set(usable[item.target]))
        if item.task == 361236:
            require("auction/forbidden_outcome_removed", "verification.result" in excluded.column.tolist() and "verification.result" not in usable)
        if item.task == 28:
            digits = load_digits()
            source_rows = {tuple(r) + (str(y),) for r, y in zip(usable[feature_names].to_numpy(), usable[item.target])}
            digits_overlap = sum(tuple(r) + (str(y),) in source_rows for r, y in zip(digits.data, digits.target))
            require("digits/development_only", item.role == "development")
    pd.DataFrame(checks).to_csv(work / "DATA-CHECKS.csv", index=False)
    (work / "DIGITS-EXPOSURE.md").write_text(
        "# Earlier digits exposure\n\n"
        f"Exact feature-and-label overlap with scikit-learn load_digits: {digits_overlap} of 1797 rows.\n"
        "No fitting occurred. The full Optical Recognition task remains development-only. "
        "The grouped classroom split does not reproduce the source's writer-separated evaluation.\n", encoding="utf-8")
    print(f"{len(checks)} data checks passed; twelve tasks; zero model fits; prior digits overlap {digits_overlap}/1797")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
