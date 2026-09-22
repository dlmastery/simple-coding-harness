"""Add disclosed infrastructure costs without changing the frozen comparison."""
import argparse
from pathlib import Path
import shutil

import numpy as np
import pandas as pd


def annotate(work):
    if not pd.read_csv(work / "EVALUATION-CHECKS.csv").passed.all():
        raise ValueError("Complete the independent evaluation checks first")
    if (work / "REPORT-generated.md").exists():
        raise ValueError("Preserve existing report annotation")
    result = pd.read_csv(work / "RESULTS.csv")
    exclusion = pd.read_csv(work / "standby-recovery/EXCLUSION.csv").iloc[0]
    tree = pd.read_csv(work / "rollouts/8105/broad-stop/TREE.csv")
    if len(result) != 80 or len(tree) != exclusion.interrupted_attempts:
        raise ValueError("Unexpected planned or excluded work")
    expected = set(zip(result.seed, result.arm)) | {(8105, "broad-stop")}
    actual = {(int(path.parent.parent.name), path.parent.name) for path in (work / "rollouts").glob("*/*/TREE.csv")}
    if actual != expected:
        raise ValueError("Unaccounted rollout")
    if not np.isclose(tree.seconds.sum(), exclusion.recorded_worker_seconds):
        raise ValueError("Excluded cost changed")
    costs = pd.DataFrame([
        dict(category="completed paired search", attempts=int(result.attempts.sum()),
             failures=int(result.failures.sum()), measured_process_seconds=result.worker_seconds.sum(),
             recorded_fit_seconds=result.fit_seconds.sum()),
        dict(category="separate final scoring refits", attempts=len(result), failures=0,
             measured_process_seconds=result.scoring_process_seconds.sum(),
             recorded_fit_seconds=result.scoring_fit_seconds.sum()),
        dict(category="excluded host-interrupted task", attempts=len(tree),
             failures=int(tree.status.ne("ok").sum()), measured_process_seconds=tree.seconds.sum(),
             recorded_fit_seconds=pd.to_numeric(tree.fit_seconds, errors="coerce").sum()),
    ])
    costs.to_csv(work / "INCURRED-COSTS.csv", index=False)
    shutil.copyfile(work / "REPORT.md", work / "REPORT-generated.md")
    note = (
        "\n## Disclosed infrastructure deviation\n\n"
        "Windows Modern Standby interrupted task 8105. Before final scoring, task 8123 replaced it, "
        "with the same kind and signal family. The original task, failed history, power events, "
        "task plan and data hashes remain in standby-recovery and rollouts/8105. "
        "All method code and comparison rules stayed fixed.\n\n"
        f"The paired table covers {int(result.attempts.sum())} search attempts and {len(result)} scoring refits. "
        f"An additional {len(tree)} admitted attempts belong to the excluded infrastructure case, "
        f"with {tree.seconds.sum():.3f} recorded worker-process seconds. "
        "That elapsed interval includes the host interruption and must not be interpreted as active model compute.\n\n"
        f"Total admitted model attempts across this phase, including scoring and the interruption: {int(costs.attempts.sum())}. "
        "INCURRED-COSTS.csv preserves the separate categories. The failed worker wrote partial fit telemetry, "
        "but its fit time is absent from the accepted tree and is not invented in this ledger. "
        "Its original worker-result.csv remains available as unaccepted output.\n\n"
        "The paired efficiency comparison excludes the host-interrupted task. It is not a claim about "
        "net total research cost, which also includes development, orchestration and unmetered agent inference. "
        "REPORT-generated.md preserves the analyzer's original output. This annotation changes no result or contrast.\n"
    )
    with (work / "REPORT.md").open("a", encoding="utf-8") as stream:
        stream.write(note)
    print(note)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    annotate(parser.parse_args().workspace.resolve())
