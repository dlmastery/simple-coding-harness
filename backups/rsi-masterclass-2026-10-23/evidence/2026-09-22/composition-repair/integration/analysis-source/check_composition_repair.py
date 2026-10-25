"""Recompute repair outputs and preserve both preflight versions and the four fits."""
import hashlib
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

from run_composition_repair import ROOT, WORK, executor


def main():
    helper = executor()
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        pd.DataFrame(checks).to_csv(WORK / "REPAIR-CHECKS.csv", index=False)
        if not condition:
            raise AssertionError(name)

    require("terminal", (WORK / "SMOKE-COMPLETE.md").exists() and not list(WORK.rglob(".running")))
    require("no_final_data_or_predictions", not list(WORK.rglob("final.csv")) and not list(WORK.rglob("final-predictions.csv")))
    require("construction_checks", pd.read_csv(WORK / "preflight/CHECKS.csv").passed.eq(True).all())
    plan = pd.read_csv(WORK / "PLAN.csv")
    ledger = pd.read_csv(WORK / "LEDGER.csv")
    require("exact_four_allocations", len(ledger) == 4 and ledger.attempt.tolist() == [1, 2, 3, 4] and ledger[plan.columns].equals(plan))
    require("process_limits", ledger.worker_seconds.between(0, 32, inclusive="right").all())
    sys.path.insert(0, str(WORK / "source"))
    from study_engine import build_recipe as old
    from refinement_engine import build_recipe as new, constructor_signature
    observations = []
    for row in ledger.itertuples():
        path = WORK / "attempts" / str(row.attempt)
        require(f"{row.attempt}/charged_record", all((path / name).is_file() for name in ["ADMITTED.md", "stdout.txt", "stderr.txt"]))
        schema = pd.read_csv(WORK / "public" / str(row.task) / "SCHEMA.csv")
        model = (old if row.version == "original" else new)(schema, row.kind, row.template, row.factor)
        pipeline = model if row.kind == "classification" else model.regressor
        if row.status == "success":
            require(f"{row.attempt}/exit", row.exit_code == 0)
            metrics = helper.verify_predictions(row.task, row.kind, path, ["train", "selection"])
            require(f"{row.attempt}/recorded_score", np.isclose(row.selection_score, metrics.loc["selection", "score"], atol=1e-12, rtol=1e-12))
            require(f"{row.attempt}/recorded_loss", np.isclose(row.selection_loss, metrics.loc["selection", "loss"], atol=1e-12, rtol=1e-12))
        else:
            require(f"{row.attempt}/failure_kept", row.status in {"failed", "timeout", "invalid-output"})
        observations.append(dict(attempt=row.attempt, task=row.task, version=row.version,
                                 max_depth=pipeline.named_steps["model"].max_depth,
                                 min_samples_leaf=pipeline.named_steps["model"].min_samples_leaf,
                                 constructor_sha256=constructor_signature(model), status=row.status,
                                 selection_score=getattr(row, "selection_score", np.nan)))
    pd.DataFrame(observations).to_csv(WORK / "CONSTRUCTION-AND-RESULT.csv", index=False)
    pairs = []
    for first, second in [(1, 2), (3, 4)]:
        before = pd.read_csv(WORK / "attempts" / str(first) / "selection-predictions.csv")
        after = pd.read_csv(WORK / "attempts" / str(second) / "selection-predictions.csv")
        require(f"pair/{first}-{second}/same_rows", before.row_id.tolist() == after.row_id.tolist())
        pairs.append(dict(original_attempt=first, revised_attempt=second, rows=len(before),
                          changed_predictions=int((before.prediction != after.prediction).sum())))
    pd.DataFrame(pairs).to_csv(WORK / "PREDICTION-CHANGES.csv", index=False)
    failed = ROOT.parent / "rsi-work-2026-09-22-composition-repair"
    prior = pd.read_csv(failed / "preflight/CHECKS.csv")
    require("earlier_failure_retained", len(prior[prior.passed == False]) == 1 and not (failed / "SMOKE-STARTED.md").exists())
    helper.verify_manifest(WORK, WORK / "REPAIR-FREEZE.csv")
    require("source_and_inputs_unchanged", True)
    print(f"{len(checks)} repair checks passed; four charged attempts; zero extra fits")
    print(pd.DataFrame(observations).drop(columns="constructor_sha256").to_string(index=False))
    print(pd.DataFrame(pairs).to_string(index=False))


if __name__ == "__main__":
    main()
