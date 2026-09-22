"""Apply the declared single-task replacement without editing any rollout."""
import argparse
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd

import evaluate_discovery as evaluation


def recover(work):
    evaluation.check_freeze(work)
    if (work / "SELECTED.csv").exists() or (work / "scoring").exists():
        raise ValueError("Recovery must precede phase selection and final scoring")
    record = work / "standby-recovery"
    if record.exists():
        raise ValueError("Preserve existing recovery; this operation runs once")
    old, new = 8105, 8123
    table = pd.read_csv(work / "ORDER.csv")
    old_rows = table[table.seed == old]
    if len(old_rows) != 5 or new in table.seed.values:
        raise ValueError("Unexpected original task plan")
    if set(old_rows.kind) != {"classification"} or set(old_rows.family) != {(new - 1101) % 3}:
        raise ValueError("Replacement must match kind and signal family")
    affected = work / "rollouts" / str(old)
    if sorted(path.name for path in affected.iterdir()) != ["broad-stop"]:
        raise ValueError("Unexpected work on the interrupted task")
    tree = pd.read_csv(affected / "broad-stop/TREE.csv")
    if len(tree) != 2 or list(tree.status) != ["ok", "timeout"] or tree.seconds.sum() <= 120:
        raise ValueError("Unexpected interruption record")
    record.mkdir()
    for name in ("ORDER.csv", "DATA-FREEZE.csv", "SOURCE-FREEZE.csv"):
        shutil.copyfile(work / name, record / f"original-{name}")
    proposal = evaluation.ROOT / "how-did-i-generate-it/rsi/validation/DISCOVERY-STANDBY-DEVIATION.md"
    shutil.copyfile(proposal, record / "DEVIATION.md")
    shutil.copyfile(__file__, record / "recovery-source.py")
    (record / "DECISION.md").write_text(
        f"# Replacement fixed before its data generation\n\nUnix time: {time.time()}\n"
        f"Original task: {old}\nReplacement: {new}\n"
        "Same kind, family, arm order and procedures. No final rows scored.\n"
        f"Preserved interrupted attempts: {len(tree)}\n"
        f"Recorded interrupted-task worker seconds: {tree.seconds.sum()}\n", encoding="utf-8")
    public, final = evaluation.public_and_final(new)
    frozen_data = pd.read_csv(work / "DATA-FREEZE.csv").to_dict("records")
    for role, content in (("public", public), ("evaluator", final)):
        target = work / role / f"task-{new}.npz"
        if target.exists():
            raise ValueError("Do not overwrite replacement data")
        np.savez_compressed(target, **content)
        frozen_data.append(dict(path=target.relative_to(work).as_posix(), sha256=evaluation.digest(target)))
    table.loc[table.seed == old, "seed"] = new
    table.to_csv(work / "ORDER.csv", index=False)
    pd.DataFrame(frozen_data).to_csv(work / "DATA-FREEZE.csv", index=False)
    pd.DataFrame([dict(original_seed=old, replacement_seed=new, reason="Windows Modern Standby",
        interrupted_attempts=len(tree), recorded_worker_seconds=tree.seconds.sum(),
        original_tree_sha256=evaluation.digest(affected / "broad-stop/TREE.csv"))]).to_csv(record / "EXCLUSION.csv", index=False)
    pd.DataFrame([dict(path=name, sha256=evaluation.digest(work / name))
                  for name in ("ORDER.csv", "DATA-FREEZE.csv", "SOURCE-FREEZE.csv")]).to_csv(record / "EFFECTIVE-FREEZE.csv", index=False)
    evaluation.check_freeze(work)
    print("Recorded replacement 8105 -> 8123; original rollout, sources and data preserved; zero fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    recover(parser.parse_args().workspace.resolve())
