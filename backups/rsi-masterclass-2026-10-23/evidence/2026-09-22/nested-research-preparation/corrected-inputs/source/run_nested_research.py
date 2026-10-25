"""Freeze and execute complete researchers; reuse the checked single-fit evaluator."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "rsi/experiments/real-tabular/nested"
ARCHIVE = ROOT / "rsi/evidence/2026-09-22"
BUILDER_FILES = ["study_engine.py", "parent_engine.py", "revision_one_engine.py", "revision_two_engine.py", "refinement_engine.py"]
TASKS = {"development": [6, 23, 31, 361235, 361237, 361247],
         "evaluation": [43, 45, 2074, 361241, 361251, 361260]}
ARMS = {"development": ["parent", "i0", "i1"], "evaluation": ["fixed", "random", "parent", "i0", "i1"]}


def workspace(phase):
    return ROOT.parent / ("rsi-work-2026-09-22-nested-" + phase + "-2")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def support(work):
    sys.path.insert(0, str(work / "source"))
    module = load("nested_execution_support", work / "source/execution_support.py")
    module.WORK = work
    return module


def generate(work, version, generation, parent, evidence, rejected):
    module = load("generator_" + version, work / "source" / (version + ".py"))
    destination = work / "generations" / str(generation) / version
    researcher = module.generate(parent, evidence, generation, rejected, destination)
    with (destination / "GENERATION.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\nInvoked version entry SHA256: {sha(work / 'source' / (version + '.py'))}\n")
    return researcher


def prepare(phase):
    work = workspace(phase)
    if work.exists():
        raise ValueError("Preserve the existing study workspace")
    if phase == "evaluation":
        development = workspace("development")
        checks = pd.read_csv(development / "FINAL-CHECKS.csv")
        if checks.empty or not checks.passed.all() or not (development / "GENERATION-TWO-FREEZE.csv").exists():
            raise ValueError("Checked development and frozen later generation required")
        support(development).verify_manifest(development, development / "GENERATION-TWO-FREEZE.csv")
    work.mkdir()
    shutil.copytree(PACKAGE, work / "source", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(Path(__file__), work / "source" / Path(__file__).name)
    files = {
        "execution_support.py": ROOT / "how-did-i-generate-it/rsi/scripts/run_tabular_comparison.py",
        "study_worker.py": ROOT / "rsi/experiments/real-tabular/comparison/study_worker.py",
        "study_engine.py": ROOT / "rsi/experiments/real-tabular/comparison/study_engine.py",
        "refinement_engine.py": ROOT / "rsi/experiments/real-tabular/refinement-v2/refinement_engine.py",
        "parent_engine.py": ARCHIVE / "real-tabular-baseline/source/engine.py",
        "revision_one_engine.py": ARCHIVE / "real-tabular-revision-1/source/engine.py",
        "revision_two_engine.py": ARCHIVE / "real-tabular-revision-2/source/engine.py",
        "NESTED-RESEARCH-PROTOCOL.md": ROOT / "how-did-i-generate-it/rsi/validation/NESTED-RESEARCH-PROTOCOL.md",
    }
    for name, path in files.items():
        shutil.copyfile(path, work / "source" / name)
    helper = support(work)
    if phase == "development":
        prior = work / "prior-comparison"
        prior.mkdir()
        for name in ("SEARCH-LEDGER.csv", "SEARCH-CHECKS.csv", "FINAL-CHECKS.csv", "SCORES.csv"):
            shutil.copyfile(ARCHIVE / "tabular-comparison" / name, prior / name)
        if not pd.read_csv(prior / "FINAL-CHECKS.csv").passed.all():
            raise ValueError("Earlier evidence not checked")
        generated = {version: generate(work, version, 1, work / "source/researcher.py", prior / "SEARCH-LEDGER.csv", False) for version in ("i0", "i1")}
    else:
        generated = {version: workspace("development") / "generations/2" / version / "researcher.py" for version in ("i0", "i1")}
    for arm in ARMS[phase]:
        target = work / "researchers" / arm
        target.mkdir(parents=True)
        original = generated[arm] if arm in generated else work / "source/researcher.py"
        raw = original.read_text(encoding="utf-8")
        if arm in {"fixed", "random"}:
            raw = raw.replace('MODE = "parent"', f'MODE = "{arm}"')
        (target / "researcher.py").write_text(raw, encoding="utf-8")
        (target / "ORIGIN.md").write_text(f"# Researcher origin\n\nSource SHA256: {sha(original)}\nProcedure: {arm}\n")
    data = ARCHIVE / ("real-tabular-data-v2" if phase == "development" else "nested-data/checked")
    panel = pd.read_csv(data / ("DATASET-PANEL.csv" if phase == "development" else "PANEL.csv"))
    panel = panel[panel.task.isin(TASKS[phase])].sort_values("task")
    if panel.task.tolist() != TASKS[phase]:
        raise ValueError("Task identities differ")
    panel.to_csv(work / "PANEL.csv", index=False)
    for item in panel.itertuples():
        source = data / "tasks" / str(item.task)
        public = work / "public" / str(item.task)
        public.mkdir(parents=True)
        shutil.copyfile(source / "SCHEMA.csv", public / "SCHEMA.csv")
        for split in ("train", "selection"):
            shutil.copyfile(source / "public" / (split + ".csv"), public / (split + ".csv"))
        evaluator = work / "evaluator" / str(item.task)
        evaluator.mkdir(parents=True)
        shutil.copyfile(source / "evaluator/final.csv", evaluator / "final.csv")
    helper.manifest(work, work / "STUDY-FREEZE.csv")
    print(f"Prepared {phase}; sources and data frozen; zero fits")


def start(work, action):
    helper = support(work)
    helper.verify_manifest(work, work / "STUDY-FREEZE.csv")
    if sha(Path(__file__)) != sha(work / "source" / Path(__file__).name):
        raise ValueError("Driver changed after freeze")
    marker = work / ("STARTED-" + action + ".md")
    if marker.exists() or list(work.rglob(".running")):
        raise ValueError("Existing admission must be reconciled; no restart")
    if action == "search":
        if not (work / "PREFLIGHT-COMPLETE.md").exists():
            raise ValueError("Successful preflight completion required")
        checks = pd.read_csv(work / "PREFLIGHT-CHECKS.csv")
    else:
        checks = pd.read_csv(work / "SEARCH-CHECKS.csv")
        helper.verify_manifest(work, work / "CHOICE-FREEZE.csv")
    if checks.empty or not checks.passed.all():
        raise ValueError("Required checks failed")
    marker.write_text(f"# Admitted {action}\n\nOne execution; no retry.\n")
    return helper


def search(phase):
    work = workspace(phase)
    helper = start(work, "search")
    engine = load("nested_refinement", work / "source/refinement_engine.py")
    ledger, choices, rejected = [], [], []
    helper.power("search", True)
    try:
        for index, task in enumerate(pd.read_csv(work / "PANEL.csv").itertuples()):
            arms = ARMS[phase]
            order = arms[index % len(arms):] + arms[:index % len(arms)]
            schema = pd.read_csv(work / "public" / str(task.task) / "SCHEMA.csv")
            target, = schema[schema.role == "target"].column.tolist()
            nonnegative = task.kind != "regression" or pd.read_csv(work / "public" / str(task.task) / "train.csv")[target].min() >= 0
            for arm in order:
                helper.verify_manifest(work, work / "STUDY-FREEZE.csv")
                run = work / "runs" / str(task.task) / arm
                run.mkdir(parents=True)
                source = work / "researchers" / arm / "researcher.py"
                shutil.copyfile(source, run / "researcher.py")
                researcher = load(f"researcher_{task.task}_{arm}", run / "researcher.py")
                seen = set()

                def reject(plan, serial, result):
                    rejected.append(dict(task=task.task, arm=arm, serial=serial, **plan, **result))
                    pd.DataFrame(rejected).to_csv(work / "REJECTED-PROPOSALS.csv", index=False)

                def execute(plan, serial, step):
                    if step > 12 or serial > 128:
                        raise ValueError("Researcher exceeds host budget")
                    model = engine.build_recipe(schema, task.kind, plan["template"], plan["factor"])
                    signature = engine.constructor_signature(model)
                    if signature in seen:
                        return dict(status="duplicate-constructor", constructor_sha256=signature)
                    seen.add(signature)
                    node = run / "attempts" / f"{step:02d}"
                    builder = node / "builder"
                    builder.mkdir(parents=True, exist_ok=False)
                    parent = run / "attempts" / f"{plan['parent_step']:02d}" / "builder"
                    inheritance = []
                    for name in BUILDER_FILES:
                        origin = parent / name if plan["parent_step"] else work / "source" / name
                        shutil.copyfile(origin, builder / name)
                        inheritance.append(dict(path=name, parent_sha256=sha(origin), child_sha256=sha(builder / name)))
                    if plan["parent_step"]:
                        shutil.copyfile(parent / "candidate.py", node / "PARENT-CANDIDATE.py")
                    pd.DataFrame(inheritance).to_csv(node / "INHERITANCE.csv", index=False)
                    code = f"from refinement_engine import build_recipe\n\ndef build(schema, kind, seed=41):\n    return build_recipe(schema, kind, {plan['template']!r}, {plan['factor']!r}, seed)\n"
                    (builder / "candidate.py").write_text(code, encoding="utf-8")
                    helper.manifest(builder, node / "BUILDER-FREEZE.csv")
                    pd.DataFrame([dict(serial=serial, step=step, **plan)]).to_csv(node / "PROPOSAL.csv", index=False)
                    record = dict(task=task.task, kind=task.kind, arm=arm, serial=serial, step=step, **plan,
                                  researcher_sha256=sha(source), constructor_sha256=signature, candidate_sha256=sha(builder / "candidate.py"))
                    record.update(helper.execute(task.task, task.kind, builder / "candidate.py", node, "search"))
                    ledger.append(record)
                    pd.DataFrame(ledger).to_csv(work / "SEARCH-LEDGER.csv", index=False)
                    print(f"{phase} {len(ledger)}/{len(TASKS[phase])*len(ARMS[phase])*12}: {task.task} {arm} {step} {record['status']}; loss {record.get('selection_loss', 'NA')}", flush=True)
                    return record

                history, choice = researcher.research(task.task, task.kind, nonnegative, execute, reject)
                if len(history) != 12:
                    raise ValueError("Researcher did not complete its declared attempts")
                pd.DataFrame(history).to_csv(run / "LEDGER.csv", index=False)
                choices.append(choice)
                pd.DataFrame(choices).to_csv(work / "CHOICES.csv", index=False)
        selected = [work / "CHOICES.csv", work / "SEARCH-LEDGER.csv"]
        for row in choices:
            bundle = work / "runs" / str(row["task"]) / row["arm"] / "attempts" / f"{row['step']:02d}" / "builder"
            selected.extend(bundle / name for name in BUILDER_FILES + ["candidate.py"])
        helper.manifest(work, work / "CHOICE-FREEZE.csv", selected)
        (work / "SEARCH-COMPLETE.md").write_text(f"# Search complete\n\n{len(ledger)} attempts; {len(choices)} choices frozen. Independent checks required.\n")
    finally:
        helper.power("search", False)


def score(phase):
    work = workspace(phase)
    helper = start(work, "score")
    results = []
    helper.power("score", True)
    try:
        choices = pd.read_csv(work / "CHOICES.csv")
        for row in choices.itertuples():
            helper.verify_manifest(work, work / "CHOICE-FREEZE.csv")
            node = work / "runs" / str(row.task) / row.arm / "attempts" / f"{row.step:02d}"
            output = work / "scoring" / str(row.task) / row.arm
            output.mkdir(parents=True, exist_ok=False)
            result = dict(task=row.task, kind=row.kind, arm=row.arm, selected_step=row.step,
                          template=row.template, factor=row.factor, candidate_sha256=row.candidate_sha256)
            result.update(helper.execute(row.task, row.kind, node / "builder/candidate.py", output, "score"))
            if result["status"] == "success" and not np.isclose(result["selection_loss"], row.selection_loss, rtol=1e-12, atol=1e-12):
                result["status"] = "refit-mismatch"
            results.append(result)
            pd.DataFrame(results).to_csv(work / "SCORES.csv", index=False)
            print(f"{phase} score {len(results)}/{len(choices)}: {row.task} {row.arm} {result['status']}; loss {result.get('final_loss', 'NA')}", flush=True)
        (work / "SCORING-COMPLETE.md").write_text(f"# Scoring complete\n\n{len(results)} charged refits. Independent final checks required.\n")
    finally:
        helper.power("score", False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "search", "score"])
    parser.add_argument("phase", choices=list(TASKS))
    args = parser.parse_args()
    {"prepare": prepare, "search": search, "score": score}[args.action](args.phase)
