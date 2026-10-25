"""Inspect constructed estimators for recipe collisions; never fit a model."""
import hashlib
from pathlib import Path
import re
import shutil
import sys

import pandas as pd
from sklearn import config_context

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"


def main():
    if not (WORK / "SCORING-COMPLETE.md").exists():
        raise ValueError("Inspect construction after the timed study is terminal")
    sys.path.insert(0, str(WORK / "source"))
    from study_engine import build_recipe
    destination = WORK / "composition"
    destination.mkdir(exist_ok=False)
    shutil.copyfile(Path(__file__), destination / Path(__file__).name)
    records = []
    for row in pd.read_csv(WORK / "SEARCH-LEDGER.csv").itertuples():
        schema = pd.read_csv(WORK / "public" / str(row.task) / "SCHEMA.csv", keep_default_na=False)
        model = build_recipe(schema, row.kind, row.template, row.factor)
        # Full estimator repr includes nested preprocessing and all constructor
        # settings. Remove only nondeterministic object addresses for comparison.
        with config_context(print_changed_only=False):
            description = model.__repr__(N_CHAR_MAX=1000000)
        description = re.sub(r" at 0x[0-9a-fA-F]+", "", description)
        signature = hashlib.sha256(description.encode()).hexdigest()
        path = destination / "constructors" / str(row.task) / row.arm / f"{row.step:02d}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(description+"\n", encoding="utf-8")
        records.append(dict(task=row.task, arm=row.arm, step=row.step, template=row.template,
                            factor=row.factor, constructor_sha256=signature, candidate_sha256=row.candidate_sha256))
    frame = pd.DataFrame(records)
    frame.to_csv(destination / "CONSTRUCTORS.csv", index=False)
    collisions = []
    for (task, arm, signature), group in frame.groupby(["task", "arm", "constructor_sha256"]):
        if len(group) > 1:
            collisions.append(dict(task=task, arm=arm, steps=";".join(group.step.astype(str)),
                                   templates=";".join(group.template), constructor_sha256=signature))
    pd.DataFrame(collisions, columns=["task", "arm", "steps", "templates", "constructor_sha256"]).to_csv(destination / "WITHIN-PROCEDURE-COLLISIONS.csv", index=False)
    left = frame[frame.arm == "parent"].set_index(["task", "step"])
    right = frame[frame.arm == "harness"].set_index(["task", "step"])
    comparisons = []
    for key in left.index:
        comparisons.append(dict(task=key[0], step=key[1], parent_template=left.loc[key, "template"],
                                harness_template=right.loc[key, "template"],
                                same_constructor=left.loc[key, "constructor_sha256"] == right.loc[key, "constructor_sha256"],
                                same_source=left.loc[key, "candidate_sha256"] == right.loc[key, "candidate_sha256"]))
    comparisons = pd.DataFrame(comparisons)
    comparisons.to_csv(destination / "PARENT-HARNESS-COMPOSITION.csv", index=False)
    cancelled = comparisons[(comparisons.step > 4) & comparisons.same_constructor & ~comparisons.same_source]
    (destination / "README.md").write_text(
        "# Does a different recipe build a different estimator?\n\n"
        f"Post-run inspection constructed {len(frame)} estimators and performed **zero fits**. "
        "Complete constructor representations include nested preprocessing and all parameters. "
        "Object addresses are removed before hashing. Identical representations are evidence "
        "of identical constructor settings in this frozen implementation, not a universal proof "
        "of semantic equivalence for arbitrary programs.\n\n"
        f"Found {len(collisions)} within-procedure groups of repeated constructor settings and "
        f"{len(cancelled)} later parent/harness pairs with different candidate source but identical settings. "
        "For example, a template can change a tree's minimum leaf size, then the capacity operator "
        "can overwrite that setting. A unique template/factor pair does not guarantee a distinct model. "
        "All executed attempts still count. This diagnosis does not change the frozen procedure, "
        "replace outcomes, authorize retries or create a repaired-study claim.\n\n"
        "Inspect CONSTRUCTORS.csv, WITHIN-PROCEDURE-COLLISIONS.csv and "
        "PARENT-HARNESS-COMPOSITION.csv alongside the saved constructor text. Different settings "
        "can also produce the same predictions; this audit does not classify those cases.\n",
        encoding="utf-8")
    print(f"{len(frame)} constructions, zero fits; {len(collisions)} collision groups; {len(cancelled)} cancelled source changes")


if __name__ == "__main__":
    main()
