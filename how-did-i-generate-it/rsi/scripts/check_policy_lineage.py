"""Re-execute archived policy decisions and verify promotion and later use."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rsi/tools"))
from discovery import World, replay


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(work, output):
    checks = []

    def require(name, value):
        checks.append(dict(check=name, passed=bool(value)))
        if not value:
            raise ValueError(name)

    def local(recorded):
        suffix = str(recorded).replace("\\", "/").split("rsi-work-2026-09-22-discovery/", 1)[1]
        path = (work / suffix).resolve()
        if not path.is_relative_to(work):
            raise ValueError("Recorded path leaves archive")
        return path

    for generation in (0, 1):
        for folder in sorted((work / f"replay-{generation}").iterdir()):
            table = pd.read_csv(folder / "REPLAY.csv")
            require(str(folder.relative_to(work)) + "/pool_size", len(table) == 2 * (generation + 1))
            for index, row in enumerate(table.itertuples()):
                prefix = f"{folder.relative_to(work).as_posix()}/{index}"
                world_path = local(row.world)
                require(prefix + "/world_identity", sha(world_path) == row.world_sha256)
                spec = importlib.util.spec_from_file_location(f"policy_{generation}_{index}", folder / "policy.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                result = replay(World.read(world_path), module.choose, 8)
                stored = pd.read_csv(folder / f"world-{index:02d}-decisions.csv", keep_default_na=False)
                require(prefix + "/decision_trace", list(result.decisions) == list(stored.itertuples(index=False, name=None)))
                require(prefix + "/terminal", result.terminal == row.terminal)
                require(prefix + "/unknown", result.unknown_requests == row.unknown_requests)
                require(prefix + "/quality", np.isclose(result.best_loss, row.best_loss))
                require(prefix + "/cost", np.isclose(result.represented_seconds, row.represented_seconds))
                require(prefix + "/revealed_count", len(result.observations) == row.revealed_attempts)
        promotion = work / f"promotion-{generation}"
        candidates = pd.read_csv(promotion / "CANDIDATES.csv")
        eligible = candidates[candidates.eligible].sort_values(["mean_utility", "order"], kind="stable")
        selected = eligible.iloc[0]
        require(f"promotion-{generation}/ranking", sha(promotion / "policy.py") == selected.policy_sha256)
        require(f"promotion-{generation}/incumbent", sha(promotion / "parent-policy.py") == candidates.iloc[0].policy_sha256)
        for row in candidates.itertuples():
            require(f"promotion-{generation}/source-{row.order}", sha(local(row.source) / "policy.py") == row.policy_sha256)
        for kind in ("classification", "regression"):
            rollout = work / f"generation-{generation + 1}" / kind
            require(f"deployment-{generation + 1}/{kind}", sha(rollout / "policy.py") == selected.policy_sha256)
            contract = dict(pd.read_csv(rollout / "contract.csv").itertuples(index=False, name=None))
            require(f"deployment-{generation + 1}/{kind}/contract", contract["policy_sha256"] == selected.policy_sha256)
    require("one_changed_promotion", sha(work / "promotion-0/policy.py") != sha(work / "promotion-0/parent-policy.py"))
    require("later_incumbent_retained", sha(work / "promotion-1/policy.py") == sha(work / "promotion-1/parent-policy.py"))
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(checks).to_csv(output, index=False)
    print(f"{len(checks)} policy-lineage checks passed; all recorded decisions replayed; zero ML fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    check(args.workspace.resolve(), args.output.resolve())
