"""Execute the prespecified, author-guided comparison; students use the lab prompts."""
import argparse
import csv
import hashlib
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd
from sklearn.datasets import make_moons, make_regression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


RULES = {
    "v0": "Promote the child task skill only if its training score is strictly better than the parent's training score.",
    "v1": "Promote the child task skill only if its selection score is strictly better than the parent's selection score.",
}
CHOICES = {"parent": "Choose the fixed linear pipeline for this task.",
           "child": "Choose the fixed unpruned tree for this task."}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def score(task, target, predicted):
    metric = mean_absolute_error if task == "regression" else balanced_accuracy_score
    return float(metric(target, predicted))


def better(task, child, parent):
    return child < parent if task == "regression" else child > parent


def policy(path):
    text = path.read_text(encoding="utf-8")
    found = [version for version, rule in RULES.items() if rule in text]
    if len(found) != 1:
        raise ValueError("The retained policy must contain exactly one supported rule.")
    version = found[0]
    return version, "training" if version == "v0" else "selection", sha(path)


def predictions(frame, model, path, task):
    inputs = frame.filter(regex=r"^x\d+$")
    result = frame[["source_row", "partition", "target"]].copy()
    result["prediction"] = model.predict(inputs)
    result.to_csv(path, index=False)
    return score(task, result.target, result.prediction)


def checked_score(data, candidate, partition, task):
    expected = data.loc[data.partition == partition, ["source_row", "partition", "target"]]
    measured = pd.read_csv(candidate / f"{partition}-predictions.csv")
    if list(measured.source_row) != list(expected.source_row):
        raise ValueError("Prediction row identities differ from the named partition.")
    if set(measured.partition) != {partition} or not np.allclose(measured.target, expected.target, rtol=0, atol=1e-10):
        raise ValueError("Prediction targets or partition labels differ from the source.")
    if not np.isfinite(measured.prediction).all():
        raise ValueError("Nonfinite prediction.")
    return score(task, measured.target, measured.prediction)


def child_fit(root, task, arm, candidate):
    dest = root / "rounds" / task / arm / candidate
    dest.mkdir(parents=True, exist_ok=False)
    data = pd.read_csv(root / "cases" / f"{task}.csv")
    skill = root / "skills" / f"TASK-SKILL-{candidate}.md"
    instruction = skill.read_text(encoding="utf-8")
    if CHOICES[candidate] not in instruction:
        raise ValueError("Unexpected task-skill choice.")
    if candidate == "parent":
        learner = Ridge(alpha=10) if task == "regression" else LogisticRegression(class_weight="balanced", max_iter=1000, random_state=17)
        model = make_pipeline(StandardScaler(), learner)
    else:
        model = DecisionTreeRegressor(random_state=17) if task == "regression" else DecisionTreeClassifier(random_state=17)
    training = data[data.partition == "training"]
    started = time.perf_counter()
    model.fit(training.filter(regex=r"^x\d+$"), training.target)
    elapsed = time.perf_counter() - started
    with (dest / "model.pkl").open("wb") as stream:
        pickle.dump(model, stream)
    rows = []
    for partition in ["training", "selection"]:
        value = predictions(data[data.partition == partition], model, dest / f"{partition}-predictions.csv", task)
        rows.append(dict(partition=partition, score=value))
    table(dest / "scores.csv", rows)
    save(dest / "EXECUTION.md", f"# Actual fit\n\nTask: {task}; arm: {arm}; candidate: {candidate}.\n\nRead instruction: {CHOICES[candidate]}\n\nSkill SHA-256: {sha(skill)}. Data SHA-256: {sha(root / 'cases' / f'{task}.csv')}. Model SHA-256: {sha(dest / 'model.pkl')}. Fit seconds: {elapsed:.9f}.\n\nTraining-only preprocessing, one fit, no final predictions. The serialized model is generated locally by this driver; load only this recorded artifact.\n")
    table(dest / "cost.csv", [dict(fits=1, fit_seconds=elapsed, agent_cost="unavailable")])
    print(f"{task}/{arm}/{candidate}: one fit; {rows}")


def final_scores(root):
    freeze = root / "FROZEN-DECISIONS.csv"
    if sha(freeze) != (root / "FROZEN-DECISIONS.sha256").read_text().strip():
        raise ValueError("Frozen decisions changed.")
    result = []
    for decision in csv.DictReader(freeze.open(encoding="utf-8", newline="")):
        task, arm = decision["task"], decision["improver"]
        data = pd.read_csv(root / "cases" / f"{task}.csv")
        values = {}
        for candidate in dict.fromkeys(["parent", decision["retained"]]):
            dest = root / "rounds" / task / arm / candidate
            with (dest / "model.pkl").open("rb") as stream:
                model = pickle.load(stream)
            predictions(data[data.partition == "final"], model, dest / "final-predictions.csv", task)
            values[candidate] = checked_score(data, dest, "final", task)
        parent, retained = values["parent"], values[decision["retained"]]
        gain = parent-retained if task == "regression" else retained-parent
        result.append(dict(task=task, improver=arm, retained=decision["retained"], parent_final=parent,
                           retained_final=retained, final_gain=gain, fits=2))
    table(root / "FINAL-RESULTS.csv", result)
    print(result)


def orchestrate(root, protocol):
    root.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    shutil.copyfile(protocol, root / "PROTOCOL.md")
    save(root / "SOURCE.md", f"# Source identity\n\nDriver SHA-256: {sha(Path(__file__))}. Protocol SHA-256: {sha(protocol)}. Python: {sys.version}.\n\nSee the surrounding clean-journey package-versions.csv for resolved dependencies. This driver was authored after the base clone; it does not import or change its pinned shared runner.\n")
    for version, rule in RULES.items():
        save(root / "skills" / f"IMPROVER-{version}.md", f"# Improver {version}\n\nRead the parent task skill. Propose one child that replaces its fixed linear choice with an unpruned decision tree. Preserve the task, inputs, metric, and partitions. Run both task skills once on the same case. Recompute training and selection scores from saved predictions.\n\n{rule}\n\nRetain the parent on a tie. Keep the rejected skill and both fits. Record the inherited version and decision before final evaluation. Stop after these two fits.\n")
    for candidate, choice in CHOICES.items():
        save(root / "skills" / f"TASK-SKILL-{candidate}.md", f"# Task research skill: {candidate}\n\nRead the task contract and available inputs. {choice}\n\nTrain only on training rows. Fit scaling there when the pipeline requires it. Save predictions with source row identities, then report the task's declared metric on training and selection rows. Never train on or choose using final rows. Keep all failures and measured fit costs. The protocol fixes the precise model settings.\n")
    save(root / "CHANGE-PROPOSAL.md", "# Revise the promotion procedure\n\nThe synthetic diagnostic below has perfect training fit but worse selection MAE. The old acceptance rule would promote it. Change only the promotion partition from training to selection. Expected effect: reject an overfit child while allowing a child that improves selection. Risk: a noisy small selection set can reject useful edits or favor another overfit choice. A later final regression would challenge the usefulness of this gate. Both procedures and the external evaluator remain frozen during the comparison.\n\nThis revision is author-guided and selected using declared numerical fixtures, not discovered autonomously. Fresh synthetic ML cases are generated only after the fixture checks.\n")
    fixtures = []
    for name, training_child, selection_child in [("overfit", 0, 24), ("useful", 8, 10)]:
        for version in RULES:
            _, partition, version_hash = policy(root / "skills" / f"IMPROVER-{version}.md")
            parent, child = (12, training_child) if partition == "training" else (15, selection_child)
            fixtures.append(dict(fixture=name, improver=version, partition=partition, parent_score=parent,
                                 child_score=child, promoted=better("regression", child, parent), improver_sha256=version_hash))
    table(root / "DIAGNOSTIC-FIXTURES.csv", fixtures)
    assert [row["promoted"] for row in fixtures] == [True, False, True, True]
    summary = []
    for task in ["regression", "classification"]:
        x, y = (make_regression(n_samples=1000, n_features=12, n_informative=8, noise=30, random_state=99173)
                if task == "regression" else make_moons(n_samples=1000, noise=.25, random_state=99179))
        all_ids = np.arange(len(y))
        train, rest = train_test_split(all_ids, test_size=.4, random_state=421,
                                      stratify=y if task == "classification" else None)
        selection, final = train_test_split(rest, test_size=.5, random_state=422,
                                            stratify=y[rest] if task == "classification" else None)
        data = pd.DataFrame(x, columns=[f"x{i}" for i in range(x.shape[1])])
        data.insert(0, "target", y)
        data.insert(0, "partition", "training")
        data.insert(0, "source_row", all_ids)
        data.loc[selection, "partition"] = "selection"
        data.loc[final, "partition"] = "final"
        dest = root / "cases" / f"{task}.csv"
        dest.parent.mkdir(exist_ok=True)
        data.to_csv(dest, index=False)
        for part in ["training", "selection", "final"]:
            summary.append(dict(task=task, partition=part, rows=int((data.partition == part).sum()), data_sha256=sha(dest)))
    table(root / "DATA-IDENTITIES.csv", summary)
    calls, decisions, costs = [], [], []
    def execute(label, arguments):
        command = [sys.executable, str(Path(__file__).resolve()), "--workspace", str(root), *arguments]
        begin = time.perf_counter()
        try:
            output = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=60)
            code, stdout, stderr = output.returncode, output.stdout, output.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = 124, str(error.stdout), str(error.stderr)
        elapsed = time.perf_counter()-begin
        save(root / "commands" / f"{len(calls)+1:02}-{label}.md", f"# {label}\n\nArguments: {command!r}\n\nExit: {code}; wall seconds: {elapsed:.9f}.\n\n```text\n{stdout}\n{stderr}\n```\n")
        calls.append(dict(action=label, exit_status=code, wall_seconds=elapsed))
        table(root / "COMMANDS.csv", calls)
        if code:
            raise RuntimeError(f"Preserved failed child command: {label}")
    for task in ["regression", "classification"]:
        data = pd.read_csv(root / "cases" / f"{task}.csv")
        for arm in (["v0", "v1"] if task == "regression" else ["v1", "v0"]):
            version, partition, version_hash = policy(root / "skills" / f"IMPROVER-{arm}.md")
            assert version == arm
            round_dir = root / "rounds" / task / arm
            save(round_dir / "BEFORE.md", f"# Before fitting\n\nInherited improver: {arm}; SHA-256: {version_hash}.\n\nApplied instruction: {RULES[arm]}\n\nParent skill SHA-256: {sha(root / 'skills/TASK-SKILL-parent.md')}. Child skill SHA-256: {sha(root / 'skills/TASK-SKILL-child.md')}. Data SHA-256: {sha(root / 'cases' / f'{task}.csv')}. Exactly two fits; no proposal search.\n")
            for candidate in ["parent", "child"]:
                execute(f"{task}-{arm}-{candidate}", ["--phase", "fit", "--task", task, "--arm", arm, "--candidate", candidate])
                cost = next(csv.DictReader((round_dir / candidate / "cost.csv").open(encoding="utf-8")))
                costs.append(dict(task=task, improver=arm, candidate=candidate, **cost))
            values = {candidate: {part: checked_score(data, round_dir / candidate, part, task)
                                  for part in ["training", "selection"]} for candidate in ["parent", "child"]}
            promoted = better(task, values["child"][partition], values["parent"][partition])
            retained = "child" if promoted else "parent"
            decisions.append(dict(task=task, improver=arm, decision_partition=partition, retained=retained,
                                  parent_training=values["parent"]["training"], child_training=values["child"]["training"],
                                  parent_selection=values["parent"]["selection"], child_selection=values["child"]["selection"],
                                  improver_sha256=version_hash))
            save(round_dir / "DECISION.md", f"# Executed promotion decision\n\nRead {arm}, SHA-256 {version_hash}. Applied: {RULES[arm]}\n\nRecomputed {partition} score: parent {values['parent'][partition]:.9f}; child {values['child'][partition]:.9f}. Strictly better: {promoted}. Retained task skill: {retained}. The other proposal and its measured outcome remain on disk. Final results have not been generated.\n")
    for task in ["regression", "classification"]:
        for candidate in ["parent", "child"]:
            for part in ["training", "selection"]:
                assert sha(root / "rounds" / task / "v0" / candidate / f"{part}-predictions.csv") == sha(root / "rounds" / task / "v1" / candidate / f"{part}-predictions.csv")
    table(root / "FROZEN-DECISIONS.csv", decisions)
    save(root / "FROZEN-DECISIONS.sha256", sha(root / "FROZEN-DECISIONS.csv")+"\n")
    table(root / "FIT-COSTS.csv", costs)
    save(root / "FINAL-AUTHORIZATION.md", "# Selection closed\n\nAll four promotion decisions are saved and hashed. Both arms produced identical training and selection prediction bytes for each matched candidate. The next command scores the already fitted parent and retained descendant on final rows. No further fitting or promotion is allowed.\n")
    execute("final-scoring", ["--phase", "final"])
    save(root / "COST.md", f"# Measured costs\n\nEight fits. Total fit seconds: {sum(float(row['fit_seconds']) for row in costs):.9f}. Nine child commands; summed child wall seconds: {sum(row['wall_seconds'] for row in calls):.9f}. Driver elapsed seconds: {time.perf_counter()-started:.9f}. No final refit. Fit time is inside child wall time, not additive.\n\nThe procedure proposals and their implementation were authored once in the same agent context. Authoring time, inference tokens, and service cost are unavailable. This is equal fit allowance and matched implementations, not equal measured total research cost.\n")
    print("Completed eight fits, four frozen decisions, and final scoring without refitting.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--phase", choices=["prepare", "fit", "final"], default="prepare")
    parser.add_argument("--task", choices=["regression", "classification"])
    parser.add_argument("--arm", choices=["v0", "v1"])
    parser.add_argument("--candidate", choices=["parent", "child"])
    args = parser.parse_args()
    if args.phase == "prepare":
        if args.protocol is None:
            parser.error("Name the protocol recorded before execution.")
        orchestrate(args.workspace.resolve(), args.protocol.resolve())
    elif args.phase == "fit":
        child_fit(args.workspace.resolve(), args.task, args.arm, args.candidate)
    else:
        final_scores(args.workspace.resolve())
