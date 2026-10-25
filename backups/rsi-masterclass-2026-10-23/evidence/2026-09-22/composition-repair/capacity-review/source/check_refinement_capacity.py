"""No-fit follow-up: greater capacity must not cap a previously unlimited tree."""
from pathlib import Path
import shutil
import sys

import pandas as pd

import run_composition_repair as checks

ROOT = checks.ROOT
WORK = ROOT.parent / "rsi-work-2026-09-22-composition-capacity-review"


def main():
    WORK.mkdir(exist_ok=False)
    source = WORK / "source"
    source.mkdir()
    previous = ROOT.parent / "rsi-work-2026-09-22-composition-repair-2"
    for name in checks.BUILDER_FILES[:-1] + ["run_tabular_comparison.py"]:
        shutil.copyfile(previous / "source" / name, source / name)
    shutil.copyfile(ROOT / "rsi/experiments/real-tabular/refinement-v2/refinement_engine.py", source / "refinement_engine.py")
    for path in (Path(__file__), Path(checks.__file__)):
        shutil.copyfile(path, source / path.name)
    checks.WORK = WORK
    helper = checks.executor()
    helper.manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    checks.preflight()
    from refinement_engine import build_recipe, constructor_signature
    from study_engine import build_recipe as old
    schema = pd.DataFrame([dict(column="x", role="feature", kind="numeric"),
                           dict(column="category", role="feature", kind="categorical"),
                           dict(column="target", role="target", kind="categorical")])
    rows = []
    for kind in ("classification", "regression"):
        for template in ("base:extra-trees", "base:random-forest"):
            for factor in (3., 20.):
                prior = old(schema, kind, template, factor)
                revised = build_recipe(schema, kind, template, factor)
                baseline = build_recipe(schema, kind, template, 1.)
                old_pipe = prior if kind == "classification" else prior.regressor
                new_pipe = revised if kind == "classification" else revised.regressor
                condition = (old_pipe.named_steps["model"].max_depth is not None and
                             new_pipe.named_steps["model"].max_depth is None and
                             constructor_signature(revised) == constructor_signature(baseline))
                rows.append(dict(check=f"{kind}/{template}/{factor}/unlimited_parent_preserved", passed=condition))
    # The four admitted integration fits used factor .3. Verify that this
    # upper-capacity correction leaves every fitted constructor unchanged.
    import importlib.util
    spec = importlib.util.spec_from_file_location("previous_refinement", previous / "source/refinement_engine.py")
    prior_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior_module)
    for task, kind, template in [(3, "classification", "one:extra-leaf2"), (361234, "regression", "two:extra-leaf5")]:
        actual_schema = pd.read_csv(previous / "public" / str(task) / "SCHEMA.csv")
        same = constructor_signature(prior_module.build_recipe(actual_schema, kind, template, .3)) == constructor_signature(build_recipe(actual_schema, kind, template, .3))
        rows.append(dict(check=f"prior_fit_constructor/{task}", passed=same))
    pd.DataFrame(rows).to_csv(WORK / "CAPACITY-CHECKS.csv", index=False)
    if not all(row["passed"] for row in rows):
        raise AssertionError("Capacity or earlier-fit constructor check failed")
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    print(f"{len(rows)} additional capacity/source-composition checks pass; zero new fits")


if __name__ == "__main__":
    main()
