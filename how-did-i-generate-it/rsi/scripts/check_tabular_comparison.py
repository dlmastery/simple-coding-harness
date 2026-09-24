"""Audit the frozen search, actual skill/source inheritance and final predictions."""
import argparse
import hashlib
import os
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"
ARMS = ["fixed", "random", "memory", "parent", "harness", "updater"]
TASKS = {6, 23, 31, 361235, 361237, 361247}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(phase):
    checks = []
    output = WORK / ("SEARCH-CHECKS.csv" if phase == "search" else "FINAL-CHECKS.csv")

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            pd.DataFrame(checks).to_csv(output, index=False)
            raise AssertionError(name)

    def identities(root, manifest):
        for row in pd.read_csv(manifest).itertuples():
            file = root / row.path
            require(f"identity/{file.relative_to(WORK)}", file.stat().st_size == row.bytes and sha(file) == row.sha256)

    require("search_complete", (WORK / "SEARCH-COMPLETE.md").exists())
    require("no_live_workers", not list(WORK.rglob(".running")))
    require("preflight", pd.read_csv(WORK / "preflight/CHECKS.csv").passed.all())
    identities(WORK, WORK / "STUDY-FREEZE.csv")
    identities(WORK, WORK / "CHOICE-FREEZE.csv")
    ledger = pd.read_csv(WORK / "SEARCH-LEDGER.csv")
    choices = pd.read_csv(WORK / "CHOICES.csv")
    require("search_allocation", len(ledger) == 288 and (ledger.groupby(["task", "arm"]).size() == 8).all())
    require("task_and_procedure_sets", set(ledger.task) == TASKS and set(ledger.arm) == set(ARMS))
    require("choices", len(choices) == 36 and not choices.duplicated(["task", "arm"]).any())
    require("process_limits", (ledger.worker_seconds > 0).all() and (ledger.worker_seconds <= 32).all())
    require("no_final_search_predictions", not list((WORK / "runs").rglob("final-predictions.csv")))
    require("search_power_released", os.name != "nt" or "Released UTC:" in (WORK / "POWER-search.md").read_text())
    panel = pd.read_csv(WORK / "PANEL.csv").set_index("task")
    experience = pd.read_csv(WORK / "memory/EXPERIENCE.csv")
    data_cache = {}

    def predictions(task, kind, directory, splits, expected):
        if task not in data_cache:
            public = WORK / "public" / str(task)
            schema = pd.read_csv(public / "SCHEMA.csv")
            target, = schema[schema.role == "target"].column.tolist()
            dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
            frames = {split: pd.read_csv(public / f"{split}.csv", dtype=dtype) for split in ("train", "selection")}
            scale = float(np.mean(np.abs(frames["train"][target]-np.median(frames["train"][target])))) if kind == "regression" else 1.
            data_cache[task] = (target, dtype, frames, scale)
        target, dtype, frames, scale = data_cache[task]
        if "final" in splits and "final" not in frames:
            frames["final"] = pd.read_csv(WORK / "evaluator" / str(task) / "final.csv", dtype=dtype)
        metrics = pd.read_csv(directory / "METRICS.csv").set_index("split")
        require(f"{directory.relative_to(WORK)}/partitions", set(metrics.index) == set(splits))
        for split in splits:
            records = pd.read_csv(directory / f"{split}-predictions.csv", dtype={"truth": str, "prediction": str} if kind == "classification" else None)
            truth = frames[split]
            label = f"{directory.relative_to(WORK)}/{split}"
            require(label+"/row_identity", records.row_id.tolist() == truth.row_id.tolist() and not records.row_id.duplicated().any())
            require(label+"/truth", np.array_equal(records.truth, truth[target]))
            if kind == "classification":
                require(label+"/labels", set(records.prediction) <= set(frames["train"][target]))
                recalls = [np.mean(records.loc[records.truth == value, "prediction"] == value) for value in sorted(records.truth.unique())]
                score = float(np.mean(recalls))
                loss = 1-score
            else:
                require(label+"/finite", np.isfinite(records.prediction).all())
                score = float(np.mean(np.abs(records.truth-records.prediction)))
                loss = score/scale
            require(label+"/score", np.isclose(score, metrics.loc[split, "score"], atol=1e-12, rtol=1e-12))
            require(label+"/loss", np.isclose(loss, metrics.loc[split, "loss"], atol=1e-12, rtol=1e-12))
            require(label+"/scale", np.isclose(scale, metrics.loc[split, "training_scale"], atol=1e-12, rtol=1e-12))
            if split in expected:
                require(label+"/ledger", np.isclose(loss, expected[split], atol=1e-12, rtol=1e-12))

    for (task, arm), run_rows in ledger.groupby(["task", "arm"]):
        run = WORK / "runs" / str(task) / arm
        kind = str(panel.loc[task, "kind"])
        require(f"{task}/{arm}/ordered_steps", run_rows.step.tolist() == list(range(1, 9)))
        require(f"{task}/{arm}/public_boundary", kind in {"classification", "regression"} and (run_rows.kind == kind).all())
        prefix = (["base:linear", "base:extra-trees", "base:rbf-1", "base:hist-boost"] if kind == "classification"
                  else ["one:median-reference", "base:linear", "base:random-forest", "base:rbf-1"])
        require(f"{task}/{arm}/common_start", run_rows.iloc[:4].template.tolist() == prefix and (run_rows.iloc[:4].factor == 1).all())
        require(f"{task}/{arm}/parameter_domain", run_rows.factor.between(.05, 20).all())
        if arm in {"parent", "harness", "updater", "random"}:
            require(f"{task}/{arm}/new_parameterized_candidates", (run_rows.iloc[4:].factor != 1).any())
        if arm == "memory":
            peers = experience[experience.kind == kind].copy()
            peers["rank"] = peers.groupby("task").selection_loss.rank(method="average")
            ranked = peers.groupby("candidate", as_index=False)["rank"].mean().sort_values(["rank", "candidate"]).candidate.tolist()
            require(f"{task}/memory/frozen_retrieval", run_rows.iloc[4:].template.tolist() == [t for t in ranked if t not in prefix][:4])
        good = run_rows[run_rows.status == "success"].sort_values(["selection_loss", "step"])
        require(f"{task}/{arm}/has_incumbent", len(good) > 0)
        chosen = choices[(choices.task == task) & (choices.arm == arm)].iloc[0]
        require(f"{task}/{arm}/selection", int(chosen.step) == int(good.iloc[0].step))
        for round_number, round_rows in run_rows.groupby("round"):
            skill = run / "skills" / str(round_number)
            identities(skill, skill / "SKILL-FREEZE.csv")
            require(f"{task}/{arm}/{round_number}/skill_use", set(round_rows.skill_sha256) == {sha(skill / "RESEARCH-SKILL.md")})
            plans = pd.read_csv(skill / "PROPOSALS.csv")
            require(f"{task}/{arm}/{round_number}/plan_execution", len(plans) == len(round_rows) and plans.template.tolist() == round_rows.template.tolist()
                    and np.allclose(plans.factor, round_rows.factor, rtol=0, atol=1e-12) and plans.parent_step.tolist() == round_rows.parent_step.tolist())
            if arm in {"parent", "harness", "updater"} and round_number > 0:
                require(f"{task}/{arm}/{round_number}/two_later_actions", len(round_rows) == 2)
                roles = pd.read_csv(skill / "ROLE-READS.csv")
                version = "v1" if arm == "updater" else "v0"
                require(f"{task}/{arm}/{round_number}/five_roles", set(roles.role) == {"Analyzer", "Retriever", "Allocator", "Proposer", "Evolver"} and len(roles) == 5)
                for role in roles.itertuples():
                    require(f"{task}/{arm}/{round_number}/{role.role}", role.sha256 == sha(WORK / "source/roles" / version / f"{role.role}.md"))
                previous = run / "skills" / str(round_number-1) / "RESEARCH-SKILL.md"
                require(f"{task}/{arm}/{round_number}/prior_skill", f"Prior skill SHA256: {sha(previous)}" in (skill / "RESEARCH-SKILL.md").read_text())
                prior = run_rows[(run_rows.step < round_rows.step.min()) & (run_rows.status == "success")].sort_values(["selection_loss", "step"]).iloc[0]
                require(f"{task}/{arm}/{round_number}/incumbent_inheritance", (round_rows.parent_step == prior.step).all())
            through = run_rows[(run_rows.step <= round_rows.step.max()) & (run_rows.status == "success")].sort_values(["selection_loss", "step"]).iloc[0]
            require(f"{task}/{arm}/{round_number}/retention", f"Retained step {through.step} " in (skill / "RETENTION.md").read_text())
        for row in run_rows.itertuples():
            node = run / "attempts" / f"{row.step:02d}"
            require(f"{task}/{arm}/{row.step}/admitted", (node / "ADMITTED.md").exists() and (node / "stdout.txt").exists() and (node / "stderr.txt").exists())
            identities(node / "builder", node / "BUILDER-FREEZE.csv")
            require(f"{task}/{arm}/{row.step}/candidate", sha(node / "builder/candidate.py") == row.candidate_sha256)
            inheritance = pd.read_csv(node / "INHERITANCE.csv")
            require(f"{task}/{arm}/{row.step}/acyclic", 0 <= row.parent_step < row.step)
            parent = run / "attempts" / f"{row.parent_step:02d}" / "builder" if row.parent_step else WORK / "source"
            for item in inheritance.itertuples():
                require(f"{task}/{arm}/{row.step}/inherits/{item.path}", sha(parent / item.path) == item.source_sha256 == item.child_sha256 == sha(node / "builder" / item.path))
            if row.parent_step:
                require(f"{task}/{arm}/{row.step}/parent_candidate", (node / "PARENT-CANDIDATE.py").read_bytes() == (parent / "candidate.py").read_bytes())
            if row.status == "success":
                require(f"{task}/{arm}/{row.step}/exit", row.exit_code == 0)
                predictions(task, kind, node, ["train", "selection"], {"train": row.train_loss, "selection": row.selection_loss})
            else:
                require(f"{task}/{arm}/{row.step}/failure_charged", row.status in {"failed", "timeout", "invalid-output"})
    if phase == "final":
        require("scoring_complete", (WORK / "SCORING-COMPLETE.md").exists())
        scores = pd.read_csv(WORK / "SCORES.csv")
        require("scoring_allocation", len(scores) == 36 and not scores.duplicated(["task", "arm"]).any())
        require("score_limits", (scores.worker_seconds > 0).all() and (scores.worker_seconds <= 32).all())
        require("scoring_power_released", os.name != "nt" or "Released UTC:" in (WORK / "POWER-score.md").read_text())
        for row in scores.itertuples():
            chosen = choices[(choices.task == row.task) & (choices.arm == row.arm)].iloc[0]
            directory = WORK / "scoring" / str(row.task) / row.arm
            require(f"{row.task}/{row.arm}/frozen_scored_choice", row.selected_step == chosen.step and row.candidate_sha256 == chosen.candidate_sha256)
            if row.status == "success":
                require(f"{row.task}/{row.arm}/reproduced_selection", np.isclose(row.selection_loss, chosen.selection_loss, rtol=1e-12, atol=1e-12))
                predictions(row.task, row.kind, directory, ["train", "selection", "final"], {"train": row.train_loss, "selection": row.selection_loss, "final": row.final_loss})
            else:
                require(f"{row.task}/{row.arm}/scoring_failure", row.status in {"failed", "timeout", "invalid-output", "refit-mismatch"})
    pd.DataFrame(checks).to_csv(output, index=False)
    print(f"{len(checks)} {phase} checks passed; final scoring {'included' if phase == 'final' else 'not inspected'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["search", "final"])
    audit(parser.parse_args().phase)
