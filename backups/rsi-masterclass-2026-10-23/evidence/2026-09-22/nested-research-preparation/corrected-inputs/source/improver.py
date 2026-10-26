"""Bounded source-rewriting improvers; no model fitting and no final-task access."""
import ast
import hashlib
from pathlib import Path
import re

import pandas as pd


REVISED_PROPOSER = '''def adaptive(history, kind, serial, nonnegative, unavailable):
    used = {row["template"] for row in history} | unavailable
    if len(history) < 8 + BREADTH:
        alternatives = [name for name in RANKING[kind] + sorted(pool(kind, nonnegative))
                        if name not in used and name in pool(kind, nonnegative)]
        if not alternatives:
            raise ValueError("No unused applicable representation alternative")
        return plan(alternatives[0], reason="retain coverage; test a different representation or objective")
    valid = sorted([row for row in history if row["status"] == "success" and "median" not in row["template"]],
                   key=lambda row: (row["selection_loss"], row["step"]))
    parents, families = [], set()
    for row in valid:
        label = family(row["template"])
        if label not in families:
            parents.append(row)
            families.add(label)
    if not parents:
        raise ValueError("No successful tunable family")
    parent = parents[(serial - 9 - BREADTH) % min(2, len(parents))]
    gap = parent["selection_loss"] - parent["train_loss"]
    direction = .5 if gap > .15 else 2.
    collision_scale = (1., .5, 2., .25, 4.)[((serial-9-BREADTH)//2) % 5]
    return plan(parent["template"], parent["factor"]*direction*collision_scale,
                parent["step"], "alternate two checked families; use observed generalization gap")'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def setting(source, name):
    assignments = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(assignments) != 1:
        raise ValueError("Ambiguous inherited researcher setting")
    return ast.literal_eval(assignments[0].value)


def replace_setting(source, name, value):
    result, count = re.subn(r"^" + re.escape(name) + r" = .+$", lambda _: name + " = " + repr(value), source, flags=re.M)
    if count != 1:
        raise ValueError("Expected one inherited setting")
    return result


def rewrite(parent, evidence, version, generation, rejected, destination):
    if version not in {"i0", "i1"} or generation not in {1, 2}:
        raise ValueError("Undeclared generation")
    destination.mkdir(parents=True, exist_ok=False)
    source = parent.read_text(encoding="utf-8")
    rows = pd.read_csv(evidence)
    probe_count = 8 if rows.step.max() > 8 else 4
    valid = rows[(rows.status == "success") & (rows.step > probe_count)].copy()
    if valid.empty or not {"kind", "task", "template", "train_loss", "selection_loss"} <= set(valid):
        raise ValueError("Completed checked evidence required")
    reason = ""
    if version == "i0":
        valid = valid[(valid.factor != 1) & (valid.parent_step > 0)]
        if valid.empty:
            raise ValueError("No checked local refinement outcomes")
        prior = float(setting(source, "FIRST_FACTOR"))
        gap = float((valid.selection_loss-valid.train_loss).mean())
        factor = max(.125, prior/2) if gap > .15 else min(8., prior*2)
        source = replace_setting(source, "FIRST_FACTOR", factor)
        reason = f"Observed mean post-probe gap {gap:.12g}; inherited first factor {prior}; new factor {factor}."
    else:
        ranking = {}
        for kind in ("classification", "regression"):
            subset = valid[valid.kind == kind].copy()
            subset["rank"] = subset.groupby("task").selection_loss.rank(method="average")
            ranking[kind] = subset.groupby("template")["rank"].mean().sort_values(kind="stable").index.tolist()
        breadth = 4 if rejected else 2
        source = replace_setting(source, "BREADTH", breadth)
        source = replace_setting(source, "RANKING", ranking)
        before, rest = source.split("# BEGIN REWRITABLE PROPOSER\n", 1)
        _, after = rest.split("# END REWRITABLE PROPOSER", 1)
        source = before + "# BEGIN REWRITABLE PROPOSER\n" + REVISED_PROPOSER + "\n# END REWRITABLE PROPOSER" + after
        reason = f"Preserve eight broad probes; allocate {breadth} unused alternatives; rejected previous child: {rejected}."
    compile(source, str(destination / "researcher.py"), "exec")
    (destination / "researcher.py").write_text(source, encoding="utf-8")
    (destination / "PARENT.py").write_bytes(parent.read_bytes())
    (destination / "GENERATION.md").write_text(
        f"# Researcher generation {generation}, {version}\n\n"
        f"Parent SHA256: {sha(parent)}\n\nImprover SHA256: {sha(Path(__file__))}\n\n"
        f"Evidence SHA256: {sha(evidence)}\n\n{reason}\n\n"
        "This is a bounded programmatic source rewrite, not an independent LLM agent or a weight update.\n",
        encoding="utf-8")
    return destination / "researcher.py"
