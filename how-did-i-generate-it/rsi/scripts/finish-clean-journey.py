"""Freeze the real bike result, evaluate once, and preserve a post-final refusal."""
import argparse
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pandas as pd


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(repo, root):
    run = root / "02-05"
    out = root / "08-02"
    out.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader((run / "trials.csv").open(encoding="utf-8")))
    chosen = min((row for row in rows if row["status"] == "ok"), key=lambda row: float(row["score"]))
    ledger_hash = sha(run / "trials.csv")
    assert chosen["candidate"] == "trial-002"
    save(out / "SELECTION-DECISION.md", f"# Freeze the bike choice\n\nRetain {chosen['candidate']}: {chosen['model']} with {chosen['features']} features, seed {chosen['seed']}. It has the lowest selection MAE, {chosen['score']}, among three successful candidates in the original 02-05 workspace.\n\nLedger SHA-256: {ledger_hash}. Contract SHA-256: {sha(run / 'CONTRACT.md')}.\n\nThese selection outcomes determine the choice before this journey's final evaluation. The author has seen this public task's final result in a separate earlier walkthrough; this is a replay of a declared selection rule, not a new blind evaluation. Source remains pinned at 75e9988. Final evaluation refits the frozen recipe on the original training rows only. It has its own one-refit allowance and does not extend selection.\n")
    script = root / "02-04/controller.py"
    common = ["--repo", str(repo), "--workspace", str(run), "--limit", "3"]
    actions = [("final", ["final", *common, "--candidate", chosen["candidate"]], 0),
               ("post-final-request", ["run", *common, "--model", "forest", "--features", "calendar", "--hypothesis", "Verify refusal after final feedback."], 1)]
    for label, arguments, expected in actions:
        command = [sys.executable, str(script), *arguments]
        started = time.perf_counter()
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=60)
        elapsed = time.perf_counter()-started
        save(out / f"{label}.md", f"# {label}\n\nArguments: {command!r}\n\nExit: {result.returncode}; expected: {expected}; wall seconds: {elapsed:.6f}.\n\n```text\n{result.stdout}\n{result.stderr}\n```\n")
        assert result.returncode == expected
    assert ledger_hash == sha(run / "trials.csv")
    sys.path.insert(0, str(repo / "rsi/tools"))
    import lab
    source = lab.read_data("bike")
    expected = source.loc[lab.partitions(source, "bike")["final"]]
    actual = pd.read_csv(run / "final-predictions.csv")
    assert list(actual.source_row) == list(expected.index)
    assert np.allclose(actual.actual, expected.cnt, rtol=0, atol=0)
    mae = float(np.abs(actual.actual-actual.predicted).mean())
    save(out / "CHECK.md", f"# Final prediction check\n\nChecked all {len(actual)} final row identities and targets against the pinned source. MAE recomputed directly from saved predictions: {mae:.9f}. The original selection ledger hash is unchanged. One final refit ran; the forest request failed before fitting.\n\nFinal prediction SHA-256: {sha(run / 'final-predictions.csv')}. No further search in this workspace.\n")
    save(out / "PROGRESS.md", "# Author progress\n\nThe frozen recipe was evaluated once and the post-final refusal was retained. Files in 02-05 hold the original contract and final outputs; this folder holds the lesson's decision and audit. Learner prediction, quiz, and teach-back remain unattempted.\n")
    print(f"Final bike MAE {mae:.9f}; {len(actual)} row identities checked; post-final fit refused.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    main(args.repo.resolve(), args.workspace.resolve())
