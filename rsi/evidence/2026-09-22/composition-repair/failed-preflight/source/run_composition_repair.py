"""Freeze and check refinement v2, then run its separately declared four-fit check."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-composition-repair"
ARCHIVE = ROOT / "rsi/evidence/2026-09-22/tabular-comparison"
BUILDER_FILES = ["study_engine.py", "parent_engine.py", "revision_one_engine.py", "revision_two_engine.py", "refinement_engine.py"]


def executor():
    spec = importlib.util.spec_from_file_location("frozen_executor", WORK / "source/run_tabular_comparison.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.WORK = WORK
    return module


def prepare():
    WORK.mkdir(exist_ok=False)
    source = WORK / "source"
    source.mkdir()
    for name in BUILDER_FILES[:-1] + ["study_worker.py", "run_tabular_comparison.py"]:
        shutil.copyfile(ARCHIVE / "source" / name, source / name)
    shutil.copyfile(ROOT / "rsi/experiments/real-tabular/refinement-v2/refinement_engine.py", source / "refinement_engine.py")
    shutil.copyfile(Path(__file__), source / Path(__file__).name)
    shutil.copyfile(ROOT / "how-did-i-generate-it/rsi/validation/COMPOSITION-REPAIR-PROTOCOL.md", source / "PROTOCOL.md")
    shutil.copyfile(ARCHIVE / "ENVIRONMENT.md", WORK / "ENVIRONMENT.md")
    data = ROOT / "rsi/evidence/2026-09-22/real-tabular-data-v2/tasks"
    for task in (3, 361234):
        public = WORK / "public" / str(task)
        public.mkdir(parents=True)
        for name in ("train.csv", "selection.csv"):
            shutil.copyfile(data / str(task) / "public" / name, public / name)
        shutil.copyfile(data / str(task) / "SCHEMA.csv", public / "SCHEMA.csv")
    plans = []
    for task, kind, template in [(3, "classification", "one:extra-leaf2"), (361234, "regression", "two:extra-leaf5")]:
        for version in ("original", "v2"):
            number = len(plans)+1
            builder = WORK / "candidates" / str(number)
            builder.mkdir(parents=True)
            for name in BUILDER_FILES:
                shutil.copyfile(source / name, builder / name)
            module = "study_engine" if version == "original" else "refinement_engine"
            (builder / "candidate.py").write_text(f"from {module} import build_recipe\n\ndef build(schema, kind, seed=41):\n    return build_recipe(schema, kind, {template!r}, .3, seed)\n")
            plans.append(dict(attempt=number, task=task, kind=kind, template=template, factor=.3, version=version))
    pd.DataFrame(plans).to_csv(WORK / "PLAN.csv", index=False)
    executor().manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    print("Prepared separate repair workspace, sources and four-attempt plan; zero fits")


def preflight():
    helper = executor()
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    output = WORK / "preflight"
    output.mkdir(exist_ok=False)
    sys.path.insert(0, str(WORK / "source"))
    from study_engine import build_recipe as old
    from refinement_engine import build_recipe as new, constructor_signature as signature, admit_distinct
    from refinement_engine import constructor_description
    rows = []

    def require(name, condition):
        rows.append(dict(check=name, passed=bool(condition)))
        pd.DataFrame(rows).to_csv(output / "CHECKS.csv", index=False)
        if not condition:
            raise AssertionError(name)

    experience = pd.read_csv(ARCHIVE / "memory/EXPERIENCE.csv")
    for kind in ("classification", "regression"):
        schema = pd.DataFrame([dict(column="x", role="feature", kind="numeric"),
                               dict(column="category", role="feature", kind="categorical"),
                               dict(column="target", role="target", kind="categorical" if kind == "classification" else "numeric")])
        for template in sorted(experience[experience.kind == kind].candidate.unique()):
            baseline = old(schema, kind, template, 1.)
            require(f"{kind}/{template}/factor_one_preserved", signature(baseline) == signature(new(schema, kind, template, 1.)))
            for factor in ([1.] if "median" in template else [.05, .3, .33, 1., 3., 20.]):
                model = new(schema, kind, template, factor)
                model._validate_params()
                pipe = model.regressor if isinstance(model, TransformedTargetRegressor) else model
                pipe.named_steps["model"]._validate_params()
                require(f"{kind}/{template}/{factor}/clone", signature(model) == signature(clone(model)))
                require(f"{kind}/{template}/{factor}/unfitted", not hasattr(pipe.named_steps["prepare"], "transformers_"))
        if kind == "classification":
            for factor in (.3, .33):
                require(f"old_cancellation/{factor}", signature(old(schema, kind, "base:extra-trees", factor)) == signature(old(schema, kind, "one:extra-leaf2", factor)))
                require(f"repair_preserves_difference/{factor}", signature(new(schema, kind, "base:extra-trees", factor)) != signature(new(schema, kind, "one:extra-leaf2", factor)))
            for name, proposals in [
                ("saturated_tree", [dict(template="base:extra-trees", factor=3.), dict(template="one:extra-leaf2", factor=3.)]),
                ("equivalent_kernel", [dict(template="one:rbf-unscaled", factor=.1), dict(template="two:unscaled-c1", factor=1.)])]:
                accepted, refused = admit_distinct(schema, kind, proposals)
                pd.DataFrame(accepted+refused).to_csv(output / f"{name}.csv", index=False)
                require(name+"/one_admission_one_refusal", len(accepted) == 1 and len(refused) == 1 and refused[0]["reason"] == "same-constructor")
                repeated, later_refused = admit_distinct(schema, kind, proposals[:1], [accepted[0]["constructor_sha256"]])
                require(name+"/prior_identity_used", not repeated and len(later_refused) == 1)
            for factor in (0., 21., np.nan):
                try:
                    new(schema, kind, "base:linear", factor)
                except ValueError:
                    require(f"invalid_factor/{factor}", True)
                else:
                    require(f"invalid_factor/{factor}", False)
    try:
        constructor_description(object())
    except TypeError:
        require("unsupported_identity_refused", True)
    else:
        require("unsupported_identity_refused", False)
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    require("frozen_inputs_unchanged", True)
    print(f"{len(rows)} construction/identity checks passed; zero fits")


def smoke():
    helper = executor()
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    if not pd.read_csv(WORK / "preflight/CHECKS.csv").passed.eq(True).all():
        raise ValueError("Construction checks must pass first")
    if helper.sha(Path(__file__)) != helper.sha(WORK / "source" / Path(__file__).name):
        raise ValueError("Driver changed after freeze")
    with (WORK / "SMOKE-STARTED.md").open("x") as handle:
        handle.write("# Four-attempt phase admitted\n\nNo retry or replacement. No final data.\n")
    helper.power("smoke", True)
    rows = []
    try:
        for row in pd.read_csv(WORK / "PLAN.csv").to_dict("records"):
            helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
            output = WORK / "attempts" / str(row["attempt"])
            output.mkdir(parents=True)
            result = helper.execute(row["task"], row["kind"], WORK / "candidates" / str(row["attempt"]) / "candidate.py", output, "search")
            rows.append(dict(**row, **result))
            pd.DataFrame(rows).to_csv(WORK / "LEDGER.csv", index=False)
            print(f"{row['attempt']}/4 {row['version']} task {row['task']}: {result['status']}; selection score {result.get('selection_score')}", flush=True)
    finally:
        helper.power("smoke", False)
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    (WORK / "SMOKE-COMPLETE.md").write_text("# Four attempts completed\n\nNo final scores or efficacy inference. Recheck predictions next.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "preflight", "smoke"])
    {"prepare": prepare, "preflight": preflight, "smoke": smoke}[parser.parse_args().action]()
