"""Audit researcher traces, constructor lineage and independently recomputed metrics."""
import argparse
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from run_nested_research import ARMS, BUILDER_FILES, TASKS, load, sha, support, workspace


def check(phase, final=False):
    work = workspace(phase)
    support(work)  # Make only the frozen ancestor-builder imports available.
    engine = load("audit_refinement", work / "source/refinement_engine.py")
    checks = []
    completed = False
    destination = work / ("FINAL-CHECKS.csv" if final else "SEARCH-CHECKS.csv")

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    def manifest(base, path):
        records = pd.read_csv(path)
        require(str(path.relative_to(work)) + "/unique", not records.path.duplicated().any())
        for row in records.itertuples():
            file = base / row.path
            require(str(file.relative_to(work)) + "/identity", file.stat().st_size == row.bytes and sha(file) == row.sha256)

    frames = {}

    def predictions(task, kind, directory, expected, splits):
        if task not in frames:
            public = work / "public" / str(task)
            schema = pd.read_csv(public / "SCHEMA.csv")
            target, = schema[schema.role == "target"].column.tolist()
            dtype = {row.column: str if row.kind == "categorical" else float for row in schema.itertuples()}
            data = {split: pd.read_csv(public / (split + ".csv"), dtype=dtype) for split in ("train", "selection")}
            scale = np.abs(data["train"][target]-np.median(data["train"][target])).mean() if kind == "regression" else 1.
            frames[task] = (target, dtype, data, scale)
        target, dtype, data, scale = frames[task]
        if "final" in splits and "final" not in data:
            data["final"] = pd.read_csv(work / "evaluator" / str(task) / "final.csv", dtype=dtype)
        metrics = pd.read_csv(directory / "METRICS.csv").set_index("split")
        require(str(directory.relative_to(work)) + "/splits", set(metrics.index) == set(splits))
        for split in splits:
            label = str(directory.relative_to(work)) + "/" + split
            rows = pd.read_csv(directory / (split + "-predictions.csv"), dtype={"truth": str, "prediction": str} if kind == "classification" else None)
            require(label + "/rows", rows.row_id.tolist() == data[split].row_id.tolist() and not rows.row_id.duplicated().any())
            require(label + "/truth", np.array_equal(rows.truth, data[split][target]))
            if kind == "classification":
                require(label + "/labels", set(rows.prediction) <= set(data["train"][target]))
                score = np.mean([np.mean(rows.loc[rows.truth == label, "prediction"] == label) for label in sorted(rows.truth.unique())])
                loss = 1-score
            else:
                require(label + "/finite", np.isfinite(rows.prediction).all())
                score = np.abs(rows.truth-rows.prediction).mean()
                loss = score/scale
            require(label + "/metric", np.allclose([score, loss, scale], metrics.loc[split, ["score", "loss", "training_scale"]].to_numpy(float), atol=1e-12, rtol=1e-12))
            require(label + "/ledger", np.isclose(loss, expected[split + "_loss"], atol=1e-12, rtol=1e-12))

    try:
        require("search_complete", (work / "SEARCH-COMPLETE.md").exists())
        require("preflight_complete", (work / "PREFLIGHT-COMPLETE.md").exists() and pd.read_csv(work / "PREFLIGHT-CHECKS.csv").passed.all())
        require("no_live_workers", not list(work.rglob(".running")))
        manifest(work, work / "STUDY-FREEZE.csv")
        manifest(work, work / "CHOICE-FREEZE.csv")
        ledger = pd.read_csv(work / "SEARCH-LEDGER.csv")
        choices = pd.read_csv(work / "CHOICES.csv")
        require("allocation", len(ledger) == len(TASKS[phase])*len(ARMS[phase])*12 and ledger.groupby(["task", "arm"]).size().eq(12).all())
        require("declared_tasks_and_arms", set(ledger.task) == set(TASKS[phase]) and set(ledger.arm) == set(ARMS[phase]))
        require("choices", len(choices) == len(TASKS[phase])*len(ARMS[phase]) and not choices.duplicated(["task", "arm"]).any())
        require("worker_limits", ledger.worker_seconds.gt(0).all() and ledger.worker_seconds.le(32).all())
        require("no_search_final_predictions", not list((work / "runs").rglob("final-predictions.csv")))
        for (task, arm), rows in ledger.groupby(["task", "arm"]):
            label = f"{task}/{arm}"
            kind = rows.kind.iloc[0]
            run = work / "runs" / str(task) / arm
            source = work / "researchers" / arm / "researcher.py"
            require(label + "/executed_source", sha(source) == sha(run / "researcher.py") and rows.researcher_sha256.eq(sha(source)).all())
            require(label + "/ordered_steps", rows.step.tolist() == list(range(1, 13)))
            require(label + "/distinct_constructors", not rows.constructor_sha256.duplicated().any())
            require(label + "/serial_bounds", rows.serial.is_monotonic_increasing and rows.serial.between(1, 128).all())
            expected = rows[rows.status == "success"].sort_values(["selection_loss", "step"])
            require(label + "/incumbent_exists", not expected.empty)
            choice = choices[(choices.task == task) & (choices.arm == arm)].iloc[0]
            require(label + "/selection", choice.step == expected.iloc[0].step and choice.candidate_sha256 == expected.iloc[0].candidate_sha256)
            schema = pd.read_csv(work / "public" / str(task) / "SCHEMA.csv")
            for row in rows.itertuples():
                node = run / "attempts" / f"{row.step:02d}"
                builder = node / "builder"
                manifest(builder, node / "BUILDER-FREEZE.csv")
                require(label + f"/{row.step}/candidate", sha(builder / "candidate.py") == row.candidate_sha256)
                require(label + f"/{row.step}/admission", (node / "ADMITTED.md").exists() and (node / "stdout.txt").exists() and (node / "stderr.txt").exists())
                require(label + f"/{row.step}/parent", 0 <= row.parent_step < row.step)
                for name in BUILDER_FILES:
                    ancestor = run / "attempts" / f"{row.parent_step:02d}" / "builder" / name if row.parent_step else work / "source" / name
                    require(label + f"/{row.step}/inherited/{name}", sha(ancestor) == sha(builder / name))
                if row.parent_step:
                    require(label + f"/{row.step}/parent_candidate", sha(node / "PARENT-CANDIDATE.py") == sha(run / "attempts" / f"{row.parent_step:02d}" / "builder/candidate.py"))
                if row.status == "success":
                    predictions(task, kind, node, row._asdict(), ("train", "selection"))
            # Re-execute the complete loop using only each already-observed outcome.
            # This is a deterministic trace replay, not another model evaluation.
            module = load("audit_researcher", source)
            seen, replay_rejected = set(), []
            row_list = rows.to_dict("records")
            target, = schema[schema.role == "target"].column.tolist()
            nonnegative = kind != "regression" or pd.read_csv(work / "public" / str(task) / "train.csv")[target].min() >= 0

            def replay(plan, serial, step):
                signature = engine.constructor_signature(engine.build_recipe(schema, kind, plan["template"], plan["factor"]))
                if signature in seen:
                    return dict(status="duplicate-constructor", constructor_sha256=signature)
                seen.add(signature)
                row = row_list[step-1]
                require(label + f"/{step}/replayed_choice", serial == row["serial"] and plan["template"] == row["template"] and plan["parent_step"] == row["parent_step"] and np.isclose(plan["factor"], row["factor"], atol=1e-15, rtol=1e-15) and plan["reason"] == row["reason"] and signature == row["constructor_sha256"])
                return row

            _, selected = module.research(task, kind, nonnegative, replay,
                                           lambda plan, serial, result: replay_rejected.append(dict(serial=serial, **plan, **result)))
            require(label + "/replayed_selection", selected["step"] == int(choice.step))
            refused_path = work / "REJECTED-PROPOSALS.csv"
            refused = pd.read_csv(refused_path) if refused_path.exists() else pd.DataFrame(columns=["task", "arm"])
            refused = refused[(refused.task == task) & (refused.arm == arm)]
            require(label + "/rejected_count", len(refused) == len(replay_rejected))
            for number, (_, actual) in enumerate(refused.iterrows()):
                replayed = replay_rejected[number]
                require(label + f"/rejection/{number}", actual.serial == replayed["serial"] and actual.template == replayed["template"] and actual.constructor_sha256 == replayed["constructor_sha256"])
        if final:
            require("scoring_complete", (work / "SCORING-COMPLETE.md").exists())
            scores = pd.read_csv(work / "SCORES.csv")
            require("scoring_allocation", len(scores) == len(choices) and not scores.duplicated(["task", "arm"]).any())
            require("scoring_success", scores.status.eq("success").all())
            require("scoring_budget", scores.worker_seconds.gt(0).all() and scores.worker_seconds.le(32).all())
            for row in scores.itertuples():
                choice = choices[(choices.task == row.task) & (choices.arm == row.arm)].iloc[0]
                require(f"{row.task}/{row.arm}/frozen_selection", row.selected_step == choice.step and row.candidate_sha256 == choice.candidate_sha256 and np.isclose(row.selection_loss, choice.selection_loss, atol=1e-12, rtol=1e-12))
                predictions(row.task, row.kind, work / "scoring" / str(row.task) / row.arm, row._asdict(), ("train", "selection", "final"))
        source = work / "analysis-source"
        source.mkdir(exist_ok=True)
        shutil.copyfile(Path(__file__), source / Path(__file__).name)
        completed = True
    finally:
        checks.append(dict(check="audit_completed", passed=completed))
        pd.DataFrame(checks).to_csv(destination, index=False)
    print(f"{len(checks)} {'final' if final else 'search'} checks passed; no new fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=list(ARMS))
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    check(args.phase, args.final)
