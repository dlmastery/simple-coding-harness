"""Independently reconstruct the six prepared datasets from dense ARFF; no fits."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(values):
    return json.dumps([None if pd.isna(v) else float(v) if isinstance(v, (int, float)) else str(v)
                       for v in values], ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def dense_arff(path):
    """Separate parser: retain original tokens, including opaque parcel identifiers."""
    fields, types, records = [], [], []
    in_data = False
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        if not in_data:
            if line.lower() == "@data":
                in_data = True
            elif line.lower().startswith("@attribute"):
                match = re.fullmatch(r"@attribute\s+(?:'([^']+)'|\"([^\"]+)\"|(\S+))\s+(.+)", line, re.I)
                if not match:
                    raise ValueError("Unrecognized attribute declaration")
                fields.append(next(value for value in match.groups()[:3] if value is not None))
                types.append(match[4].strip())
        else:
            if line.startswith("{"):
                raise ValueError("Sparse data requires separate review")
            values = next(csv.reader([line], skipinitialspace=True))
            if len(values) != len(fields):
                raise ValueError("ARFF width mismatch")
            records.append([value.strip().strip("'\"") for value in values])
    if not in_data or not records or len(set(fields)) != len(fields):
        raise ValueError("Incomplete or ambiguous ARFF")
    tokens = pd.DataFrame(records, columns=fields)
    frame, kinds = tokens.copy(), {}
    for name, declaration in zip(fields, types):
        if declaration.lower() in {"numeric", "real", "integer"}:
            frame[name] = [np.nan if v == "?" else float(v) for v in tokens[name]]
            kinds[name] = "numeric"
        elif declaration.lower() == "string" or declaration.startswith("{"):
            frame[name] = tokens[name].replace("?", np.nan)
            kinds[name] = "categorical"
            if declaration.startswith("{"):
                allowed = {v.strip().strip("'\"") for v in next(csv.reader([declaration[1:-1]]))}
                if not set(frame[name].dropna()).issubset(allowed):
                    raise ValueError("Undeclared categorical value")
        else:
            raise ValueError("Unsupported attribute type")
    return frame, tokens, kinds


def check(work):
    checks, reports = [], []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    try:
        for filename in ("ACQUISITION-MANIFEST.csv", "PREPARATION-MANIFEST.csv"):
            entries = pd.read_csv(work / filename)
            require(filename + "/unique_paths", not entries.path.duplicated().any())
            for item in entries.itertuples():
                raw = (work / item.path).read_bytes()
                require(filename + "/" + item.path, len(raw) == item.bytes and digest(raw) == item.sha256)
        panel = pd.read_csv(work / "PANEL.csv")
        selected = pd.read_csv(work / "SELECTED-TASKS.csv").set_index("task")
        acquired = pd.read_csv(work / "ACQUISITION.csv").set_index("task")
        require("six_selected_tasks", panel.task.tolist() == [43, 45, 2074, 361241, 361251, 361260])
        require("six_acquisitions", set(acquired.index) == set(panel.task) and acquired.status.eq("success").all())
        for item in panel.itertuples():
            prefix = str(item.task) + "/"
            directory = work / "tasks" / str(item.task)
            original, tokens, kinds = dense_arff(directory / "original.arff")
            raw = (directory / "original.arff").read_bytes()
            desc = json.loads((directory / "OPENML-DESCRIPTOR.json").read_text())["data_set_description"]
            require(prefix + "raw_identity", digest(raw) == acquired.loc[item.task, "sha256"] and hashlib.md5(raw).hexdigest() == desc["md5_checksum"])
            exclusions = []
            for key in ("ignore_attribute", "row_id_attribute"):
                names = desc.get(key, [])
                if isinstance(names, str):
                    names = [s.strip() for s in names.split(",") if s.strip()]
                exclusions.extend((name, key) for name in names)
            if item.task == 361251:
                exclusions.extend((name, "derived_stability_class") for name in original
                                  if name.lower() in {"stabf", "stability_class", "stable"} and name != item.target)
            saved = pd.read_csv(directory / "IGNORED-COLUMNS.csv")
            require(prefix + "exclusion_reasons", list(saved.itertuples(index=False, name=None)) == exclusions)
            excluded = list(dict.fromkeys(name for name, _ in exclusions))
            require(prefix + "target_retained", item.target not in excluded and original[item.target].notna().all())
            frame = original.drop(columns=excluded)
            features = [name for name in frame if name != item.target]
            require(prefix + "source_shape", frame.shape == (int(selected.loc[item.task, "rows"]), int(selected.loc[item.task, "columns"])))
            schema = pd.read_csv(directory / "SCHEMA.csv")
            expected_schema = [(name, "target" if name == item.target else "feature", kinds[name]) for name in frame]
            require(prefix + "schema", list(schema.itertuples(index=False, name=None)) == expected_schema)
            require(prefix + "task_kind", (kinds[item.target] == "categorical") == (item.kind == "classification"))
            hashes = [digest(packed(values).encode()) for values in frame[features].itertuples(index=False, name=None)]
            # Build an explicit undirected graph, independent of the producer's union-find.
            adjacency = [set() for _ in range(len(frame))]
            first, identity_records = {}, []
            identifier_columns = [name for name in excluded if name.lower() in {"parcelno", "instance_name"}]
            for index, feature_hash in enumerate(hashes):
                keys = [("features", feature_hash)]
                for name in identifier_columns:
                    value = original.at[index, name]
                    if pd.notna(value):
                        identity = packed([value])
                        identity_records.append((index, name, identity))
                        keys.append((name, identity))
                for key in keys:
                    if key in first:
                        other = first[key]
                        adjacency[index].add(other)
                        adjacency[other].add(index)
                    else:
                        first[key] = index
            actual_ids = pd.read_csv(directory / "ENTITY-KEYS.csv", keep_default_na=False)
            require(prefix + "recorded_identifiers", list(actual_ids.itertuples(index=False, name=None)) == identity_records)
            group_by_row, groups, unseen = {}, {}, set(range(len(frame)))
            while unseen:
                pending, members = [unseen.pop()], []
                while pending:
                    current = pending.pop()
                    members.append(current)
                    for neighbor in adjacency[current]:
                        if neighbor in unseen:
                            unseen.remove(neighbor)
                            pending.append(neighbor)
                identity = digest("|".join(sorted({hashes[i] for i in members})).encode())
                require(prefix + "distinct_component/" + identity, identity not in groups)
                salted = digest(f"rsi-nested-public-v1:{item.task}:{identity}".encode())
                bucket = int(salted, 16) % 10
                split = "train" if bucket < 6 else "selection" if bucket < 8 else "final"
                groups[identity] = dict(size=len(members), salted=salted, bucket=bucket, split=split, included=False)
                group_by_row.update((i, identity) for i in members)
            for split, cap in (("train", 2400), ("selection", 800), ("final", 800)):
                used = 0
                for entry in sorted(groups.values(), key=lambda r: r["salted"]):
                    if entry["split"] == split and used + entry["size"] <= cap:
                        entry["included"] = True
                        used += entry["size"]
            expected_groups = pd.DataFrame.from_dict(groups, orient="index").sort_index()
            stored_groups = pd.read_csv(directory / "GROUPS.csv", index_col="group").sort_index()
            require(prefix + "group_records", expected_groups.equals(stored_groups))
            roles = pd.read_csv(directory / "ROW-ROLES.csv")
            expected_roles = [(i, hashes[i], group_by_row[i], groups[group_by_row[i]]["split"], groups[group_by_row[i]]["included"]) for i in range(len(frame))]
            require(prefix + "all_row_roles", list(roles.itertuples(index=False, name=None)) == expected_roles)
            for split, cap in (("train", 2400), ("selection", 800), ("final", 800)):
                path = directory / ("evaluator" if split == "final" else "public") / (split + ".csv")
                dtype = {name: str if kinds[name] == "categorical" else float for name in frame}
                part = pd.read_csv(path, dtype=dtype, float_precision="round_trip", keep_default_na=False, na_values=[""])
                ids = roles.loc[(roles.split == split) & roles.included, "row_id"].tolist()
                require(prefix + split + "/identities", part.row_id.tolist() == ids and 0 < len(ids) <= cap and len(ids) == getattr(item, split))
                require(prefix + split + "/columns", part.columns.tolist() == ["row_id"] + frame.columns.tolist())
                for name in frame:
                    actual, expected = part[name].to_numpy(), frame.iloc[ids][name].to_numpy()
                    equal = np.array_equal(actual, expected, equal_nan=True) if kinds[name] == "numeric" else all((pd.isna(a) and pd.isna(b)) or a == b for a, b in zip(actual, expected))
                    require(prefix + split + "/" + name, equal)
                if item.kind == "classification":
                    require(prefix + split + "/classes", set(part[item.target]) == set(frame[item.target]))
            conflicts = pd.DataFrame({"features": hashes, "target": frame[item.target]}).groupby("features").target.nunique().gt(1).sum()
            require(prefix + "panel_counts", item.rows == len(frame) and item.features == len(features)
                    and item.duplicate_feature_rows == len(frame)-len(set(hashes)) and item.entity_keys == len(identity_records)
                    and item.merged_components == len(groups) and item.conflicting_feature_groups == conflicts)
            if item.task == 361251:
                require(prefix + "derived_label_removed", "stabf" not in features and "stabf" in excluded)
                require(prefix + "derived_label_relationship", ((original.stab > 0) == (original.stabf == "unstable")).all())
            for name in identifier_columns:
                mapping = pd.DataFrame({"token": tokens[name], "parsed": original[name].map(lambda v: packed([v])), "group": roles.group, "split": roles.split})
                require(prefix + name + "/no_parser_collisions", mapping.groupby("parsed").token.nunique().max() == 1)
                require(prefix + name + "/identity_isolation", mapping.groupby("token").group.nunique().max() == 1 and mapping.groupby("token").split.nunique().max() == 1)
                reports.append(dict(task=item.task, column=name, rows=len(mapping), distinct_raw_tokens=mapping.token.nunique(), distinct_parsed_values=mapping.parsed.nunique(), repeated_identifier_rows=len(mapping)-mapping.token.nunique(), cross_split_identifiers=int(mapping.groupby("token").split.nunique().gt(1).sum())))
            print(f"Checked task {item.task}: source, schema, groups and exact partition values", flush=True)
        pd.DataFrame(reports).to_csv(work / "IDENTIFIER-CHECKS.csv", index=False)
    finally:
        pd.DataFrame(checks).to_csv(work / "DATA-CHECKS.csv", index=False)
    print(f"{len(checks)} checks passed; six tasks; zero model fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    check(parser.parse_args().workspace.resolve())
