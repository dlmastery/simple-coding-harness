"""Select from recorded replay evaluations under the frozen utility rule."""
import argparse
import hashlib
from pathlib import Path
import shutil

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select(incumbent, candidates, out):
    if out.exists():
        raise ValueError("Preserve previous selection")
    expected_worlds = None
    records = []
    for order, folder in enumerate([incumbent, *candidates]):
        table = pd.read_csv(folder / "REPLAY.csv")
        worlds = table[["world", "world_sha256"]].values.tolist()
        if expected_worlds is None:
            expected_worlds = worlds
        if worlds != expected_worlds or table.world.duplicated().any():
            raise ValueError("Policy evaluations used different or duplicate worlds")
        for row in table.itertuples():
            if sha(Path(row.world)) != row.world_sha256:
                raise ValueError("World changed after replay")
        eligible = (table.unknown_requests.eq(0).all() and table.best_loss.notna().all()
                    and table.utility.notna().all())
        expected = table.best_loss + .001 * table.represented_seconds
        if eligible and not np.allclose(table.utility, expected, rtol=1e-12, atol=1e-12):
            raise ValueError("Replay utility mismatch")
        policy_hash = sha(folder / "policy.py")
        if f"Policy SHA256: {policy_hash}" not in (folder / "RESULT.md").read_text(encoding="utf-8"):
            raise ValueError("Policy changed after replay")
        records.append(dict(order=order, source=str(folder), policy_sha256=policy_hash,
                            eligible=eligible, mean_utility=float(table.utility.mean()) if eligible else np.inf,
                            mean_loss=float(table.best_loss.mean()),
                            mean_represented_seconds=float(table.represented_seconds.mean()),
                            mean_attempts=float(table.revealed_attempts.mean())))
    permitted = [row for row in records if row["eligible"]]
    if not permitted:
        raise ValueError("No supported candidate, including incumbent")
    best = min(permitted, key=lambda row: (row["mean_utility"], row["order"]))
    out.mkdir(parents=True)
    shutil.copyfile(incumbent / "policy.py", out / "parent-policy.py")
    shutil.copyfile(Path(best["source"]) / "policy.py", out / "policy.py")
    pd.DataFrame(records).to_csv(out / "CANDIDATES.csv", index=False)
    pd.DataFrame(expected_worlds, columns=["world", "world_sha256"]).to_csv(out / "WORLDS.csv", index=False)
    (out / "PROMOTION.md").write_text(
        "# Replay selection\n\n"
        f"Selected source: {best['source']}\nSelected policy SHA256: {best['policy_sha256']}\n"
        f"Parent policy SHA256: {sha(out / 'parent-policy.py')}\n"
        f"Policy changed: {sha(out / 'policy.py') != sha(out / 'parent-policy.py')}\n"
        f"Mean replay utility: {best['mean_utility']}\n"
        "The incumbent participates, and exact ties keep the earliest candidate. "
        "This is a replay promotion, not proof of better online or final-task performance.\n",
        encoding="utf-8")
    print(f"Selected {best['source']}; mean replay utility={best['mean_utility']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    select(args.incumbent, args.candidate, args.output)
