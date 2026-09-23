"""Prepare, search and globally freeze, then score the six-procedure comparison."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "rsi/experiments/real-tabular/comparison"
WORK = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"
TASKS = [6, 23, 31, 361235, 361237, 361247]
BUILDER_FILES = ["study_engine.py", "parent_engine.py", "revision_one_engine.py", "revision_two_engine.py"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root, destination, paths=None):
    paths = paths if paths is not None else sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    pd.DataFrame([dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in paths]).to_csv(destination, index=False)


def verify_manifest(root, path):
    for item in pd.read_csv(path).itertuples():
        file = root / item.path
        if file.stat().st_size != item.bytes or sha(file) != item.sha256:
            raise ValueError(f"Frozen identity changed: {file}")


def prepare():
    if WORK.exists():
        raise ValueError("Fresh study workspace required")
    WORK.mkdir()
    source = WORK / "source"
    shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(Path(__file__), source / Path(__file__).name)
    protocol = ROOT / "how-did-i-generate-it/rsi/validation/TABULAR-COMPARISON-PROTOCOL.md"
    shutil.copyfile(protocol, source / protocol.name)
    archive = ROOT / "rsi/evidence/2026-09-22"
    ancestors = {"parent_engine.py": "real-tabular-baseline/source/engine.py",
                 "revision_one_engine.py": "real-tabular-revision-1/source/engine.py",
                 "revision_two_engine.py": "real-tabular-revision-2/source/engine.py"}
    for target, original in ancestors.items():
        shutil.copyfile(archive / original, source / target)
    memory = WORK / "memory"
    memory.mkdir()
    for name in ("EXPERIENCE.csv", "MEMORY.md", "SELECTED-POLICY.md", "MEMORY-CHECKS.csv"):
        shutil.copyfile(archive / "tabular-memory" / name, memory / name)
    if not pd.read_csv(memory / "MEMORY-CHECKS.csv").passed.all():
        raise ValueError("Memory checks must pass")
    data = archive / "real-tabular-data-v2"
    panel = pd.read_csv(data / "DATASET-PANEL.csv")
    panel = panel[panel.task.isin(TASKS)].sort_values("task")
    if panel.task.tolist() != TASKS or not (panel.role == "procedure-comparison").all():
        raise ValueError("Reserved task identities differ")
    panel.to_csv(WORK / "PANEL.csv", index=False)
    for task in TASKS:
        public = WORK / "public" / str(task)
        public.mkdir(parents=True)
        for name in ("SCHEMA.csv", "train.csv", "selection.csv"):
            original = data / "tasks" / str(task) / ("" if name == "SCHEMA.csv" else "public") / name
            shutil.copyfile(original, public / name)
        private = WORK / "evaluator" / str(task)
        private.mkdir(parents=True)
        shutil.copyfile(data / "tasks" / str(task) / "evaluator/final.csv", private / "final.csv")
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl")}
    (WORK / "ENVIRONMENT.md").write_text("# Study environment\n\nPython: " + sys.version + "\n\n" + "\n".join(f"{key}: {value}" for key,value in versions.items()) + "\n")
    manifest(WORK, WORK / "STUDY-FREEZE.csv")
    (WORK / "PREPARED.md").write_text(f"# Study prepared\n\nUTC: {datetime.now(timezone.utc).isoformat()}\nZero fits so far.\n")
    print(f"Prepared {WORK}; zero fits")


def load_policy():
    sys.path.insert(0, str(WORK / "source"))
    import study_policy
    return study_policy


def check_start(action):
    verify_manifest(WORK, WORK / "STUDY-FREEZE.csv")
    if sha(Path(__file__)) != sha(WORK / "source" / Path(__file__).name):
        raise ValueError("Run driver differs from frozen source")
    if (WORK / f"STARTED-{action}.md").exists():
        raise ValueError("This phase was already admitted; reconcile interruption rather than retry")
    if list(WORK.rglob(".running")):
        raise ValueError("Unreconciled worker record")
    if action == "score":
        if not (WORK / "SEARCH-COMPLETE.md").exists() or not pd.read_csv(WORK / "SEARCH-CHECKS.csv").passed.all():
            raise ValueError("All search choices must be complete and independently checked")
        verify_manifest(WORK, WORK / "CHOICE-FREEZE.csv")
    (WORK / f"STARTED-{action}.md").write_text(f"# Phase admitted\n\n{action}\nUTC: {datetime.now(timezone.utc).isoformat()}\n")


def power(action, enter):
    if os.name != "nt":
        return
    result = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 if enter else 0x80000000)
    if enter and result == 0:
        raise OSError("Temporary idle-sleep prevention failed before model fitting")
    with (WORK / f"POWER-{action}.md").open("a") as file:
        file.write(f"{'Started' if enter else 'Released'} UTC: {datetime.now(timezone.utc).isoformat()}; PID {os.getpid()}; return {result}; no persistent setting change\n")


def verify_predictions(task, kind, output, splits):
    schema = pd.read_csv(WORK / "public" / str(task) / "SCHEMA.csv")
    target, = schema[schema.role == "target"].column.tolist()
    dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
    train = pd.read_csv(WORK / "public" / str(task) / "train.csv", dtype=dtype)
    scale = float(np.mean(np.abs(train[target]-np.median(train[target])))) if kind == "regression" else 1.
    metrics = pd.read_csv(output / "METRICS.csv").set_index("split")
    if set(metrics.index) != set(splits):
        raise ValueError("Unexpected output partitions")
    for split in splits:
        path = WORK / ("evaluator" if split == "final" else "public") / str(task) / f"{split}.csv"
        original = pd.read_csv(path, dtype=dtype)
        prediction = pd.read_csv(output / f"{split}-predictions.csv", dtype={"truth": str, "prediction": str} if kind == "classification" else None)
        if original.row_id.tolist() != prediction.row_id.tolist() or not np.array_equal(original[target], prediction.truth):
            raise ValueError("Row or truth identity mismatch")
        if kind == "classification":
            if not set(prediction.prediction) <= set(train[target]):
                raise ValueError("Unknown predicted label")
            score = np.mean([np.mean(prediction.loc[prediction.truth == label, "prediction"] == label) for label in sorted(prediction.truth.unique())])
            loss = 1-score
        else:
            if not np.isfinite(prediction.prediction).all():
                raise ValueError("Nonfinite prediction")
            score = np.mean(np.abs(prediction.truth-prediction.prediction))
            loss = score/scale
        if not np.allclose([score, loss, scale], metrics.loc[split, ["score", "loss", "training_scale"]].to_numpy(float), rtol=1e-12, atol=1e-12):
            raise ValueError("Metric mismatch")
    return metrics


def execute(task, kind, builder, output, phase):
    command = [sys.executable, str(WORK / "source/study_worker.py"), "--phase", phase,
               "--task", str(WORK / "public" / str(task)), "--builder", str(builder), "--kind", kind, "--output", str(output)]
    if phase == "score":
        command.extend(["--final-file", str(WORK / "evaluator" / str(task) / "final.csv")])
    env = os.environ.copy()
    env.update({name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    env["PYTHONHASHSEED"] = "41"
    (output / "ADMITTED.md").write_text(f"# Admitted {phase} attempt\n\nUTC: {datetime.now(timezone.utc).isoformat()}\n30 worker-process seconds; one fit; seed 41; one thread.\n")
    started = time.perf_counter()
    with (output / "stdout.txt").open("w") as stdout, (output / "stderr.txt").open("w") as stderr:
        process = subprocess.Popen(command, cwd=output, env=env, stdout=stdout, stderr=stderr)
        (output / ".running").write_text(str(process.pid))
        try:
            process.wait(timeout=30)
            status = "success" if process.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            status = "timeout"
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            (output / ".running").unlink()
    result = dict(status=status, exit_code=process.returncode, worker_seconds=time.perf_counter()-started)
    if status == "success":
        try:
            metrics = verify_predictions(task, kind, output, ["train", "selection"] + (["final"] if phase == "score" else []))
            result.update(train_loss=float(metrics.loc["train", "loss"]), selection_loss=float(metrics.loc["selection", "loss"]), selection_score=float(metrics.loc["selection", "score"]))
            if phase == "score":
                result.update(final_loss=float(metrics.loc["final", "loss"]), final_score=float(metrics.loc["final", "score"]))
        except Exception as error:
            result["status"] = "invalid-output"
            (output / "VERIFICATION-FAILURE.md").write_text(f"{type(error).__name__}: {error}\n")
    return result


def write_skill(run, number, plans, roles, diagnosis, history, policy):
    directory = run / "skills" / str(number)
    directory.mkdir(parents=True)
    pd.DataFrame(plans).to_csv(directory / "PROPOSALS.csv", index=False)
    pd.DataFrame(roles, columns=["role", "policy", "sha256"]).to_csv(directory / "ROLE-READS.csv", index=False)
    previous = run / "skills" / str(number-1) / "RESEARCH-SKILL.md"
    text = f"# Research skill {number}\n\nWritten before its fits.\n\nDiagnosis: {diagnosis}\n\n"
    text += f"Prior skill SHA256: {sha(previous) if previous.exists() else 'none'}\n"
    text += f"Updater implementation SHA256: {sha(WORK / 'source/study_policy.py')}\n"
    text += f"Observed steps: {','.join(str(r['step']) for r in history) or 'none'}\n"
    if history:
        best = policy.winner(history)
        text += f"Retained incumbent before this round: step {best['step']}; selection loss {best['selection_loss']}\n"
    text += "\nExecute only the proposals in PROPOSALS.csv, in order. Check each result. Keep an earlier candidate unless a checked selection loss improves. Do not inspect final rows.\n"
    text += "\n" + "\n".join(f"{i+1}. {p['template']}, capacity factor {p['factor']}; parent step {p['parent_step']}. {p['reason']}" for i,p in enumerate(plans)) + "\n"
    (directory / "RESEARCH-SKILL.md").write_text(text, encoding="utf-8")
    manifest(directory, directory / "SKILL-FREEZE.csv")
    return directory


def build_node(run, step, plan):
    node = run / "attempts" / f"{step:02d}"
    builder = node / "builder"
    builder.mkdir(parents=True)
    parent = run / "attempts" / f"{int(plan['parent_step']):02d}" / "builder"
    inherited = []
    for name in BUILDER_FILES:
        source = parent / name if parent.exists() else WORK / "source" / name
        shutil.copyfile(source, builder / name)
        inherited.append(dict(path=name, source_sha256=sha(source), child_sha256=sha(builder / name)))
    if parent.exists():
        shutil.copyfile(parent / "candidate.py", node / "PARENT-CANDIDATE.py")
    pd.DataFrame(inherited).to_csv(node / "INHERITANCE.csv", index=False)
    code = "from study_engine import build_recipe\n\n\ndef build(schema, kind, seed=41):\n"
    code += f"    return build_recipe(schema, kind, {plan['template']!r}, {plan['factor']!r}, seed)\n"
    (builder / "candidate.py").write_text(code, encoding="utf-8")
    manifest(builder, node / "BUILDER-FREEZE.csv")
    return node


def search():
    check_start("search")
    policy = load_policy()
    experience = pd.read_csv(WORK / "memory/EXPERIENCE.csv")
    ledger, choices = [], []
    power("search", True)
    try:
        for task_index, task in enumerate(pd.read_csv(WORK / "PANEL.csv").itertuples()):
            order = policy.ARMS[task_index:] + policy.ARMS[:task_index]
            for arm in order:
                run = WORK / "runs" / str(task.task) / arm
                run.mkdir(parents=True)
                history, round_number = [], 0
                while len(history) < 8:
                    verify_manifest(WORK, WORK / "STUDY-FREEZE.csv")
                    plans, roles, diagnosis = policy.make_plan(arm, task.task, task.kind, history, experience, WORK / "source/roles")
                    if len(history) + len(plans) > 8:
                        raise ValueError("Plan exceeds task/arm allowance")
                    skill = write_skill(run, round_number, plans, roles, diagnosis, history, policy)
                    for plan in plans:
                        verify_manifest(skill, skill / "SKILL-FREEZE.csv")
                        step = len(history)+1
                        node = build_node(run, step, plan)
                        verify_manifest(node / "builder", node / "BUILDER-FREEZE.csv")
                        record = dict(task=int(task.task), kind=task.kind, arm=arm, step=step, round=round_number,
                                      **plan, skill_sha256=sha(skill / "RESEARCH-SKILL.md"), candidate_sha256=sha(node / "builder/candidate.py"))
                        record.update(execute(task.task, task.kind, node / "builder/candidate.py", node, "search"))
                        history.append(record)
                        ledger.append(record)
                        pd.DataFrame(history).to_csv(run / "LEDGER.csv", index=False)
                        pd.DataFrame(ledger).to_csv(WORK / "SEARCH-LEDGER.csv", index=False)
                        print(f"{len(ledger):03d}/288 task {task.task} {arm} step {step}: {record['status']}; loss {record.get('selection_loss', 'NA')}", flush=True)
                    incumbent = policy.winner(history)
                    (skill / "RETENTION.md").write_text(f"# Post-round retention\n\nRetained step {incumbent['step']} with checked selection loss {incumbent['selection_loss']}.\nThis verdict is written before any later skill generation.\n")
                    round_number += 1
                choice = policy.winner(history).copy()
                choices.append(choice)
                pd.DataFrame(choices).to_csv(WORK / "CHOICES.csv", index=False)
        selected = [WORK / "CHOICES.csv", WORK / "SEARCH-LEDGER.csv"]
        for row in choices:
            node = WORK / "runs" / str(row["task"]) / row["arm"] / "attempts" / f"{row['step']:02d}"
            selected.extend(node / "builder" / name for name in BUILDER_FILES + ["candidate.py"])
        manifest(WORK, WORK / "CHOICE-FREEZE.csv", selected)
        (WORK / "SEARCH-COMPLETE.md").write_text("# Search complete\n\n288 admitted attempts; all 36 choices frozen before any final scoring. Independent search checks required next.\n")
    finally:
        power("search", False)


def score():
    check_start("score")
    scored = []
    power("score", True)
    try:
        for row in pd.read_csv(WORK / "CHOICES.csv").itertuples():
            verify_manifest(WORK, WORK / "CHOICE-FREEZE.csv")
            node = WORK / "runs" / str(row.task) / row.arm / "attempts" / f"{row.step:02d}"
            output = WORK / "scoring" / str(row.task) / row.arm
            output.mkdir(parents=True)
            result = dict(task=row.task, kind=row.kind, arm=row.arm, selected_step=row.step,
                          template=row.template, factor=row.factor, candidate_sha256=row.candidate_sha256)
            result.update(execute(row.task, row.kind, node / "builder/candidate.py", output, "score"))
            if result["status"] == "success" and not np.isclose(result["selection_loss"], row.selection_loss, rtol=1e-12, atol=1e-12):
                result["status"] = "refit-mismatch"
            scored.append(result)
            pd.DataFrame(scored).to_csv(WORK / "SCORES.csv", index=False)
            print(f"Score {len(scored):02d}/36 task {row.task} {row.arm}: {result['status']}; final loss {result.get('final_loss', 'NA')}", flush=True)
        (WORK / "SCORING-COMPLETE.md").write_text("# Scoring complete\n\n36 charged refits. Independently check every result before reporting comparisons.\n")
    finally:
        power("score", False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "search", "score"])
    {"prepare": prepare, "search": search, "score": score}[parser.parse_args().action]()
