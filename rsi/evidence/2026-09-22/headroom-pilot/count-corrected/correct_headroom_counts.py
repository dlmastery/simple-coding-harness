"""Preserve raw pilot and derive nonnegative bike scores without new fits.

The original pilot omitted the course's count-output clipping. This repair is
declared after development results were observed, not a preregistered outcome.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import shutil

import numpy as np
import pandas as pd


def correct(source, destination):
    if destination.exists():
        raise ValueError("Correction needs a fresh workspace")
    if not (source / "CHECKS.csv").exists():
        raise ValueError("Audit the complete raw run before correction")
    shutil.copytree(source, destination)
    changes = []
    data = np.load(source / "bike.npz", allow_pickle=False)
    denominator = np.abs(data["y_selection"] - np.median(data["y_train"])).mean()
    for path in sorted((destination / "attempts/bike").glob("*/predictions.csv")):
        original_path = source / path.relative_to(destination)
        frame = pd.read_csv(path)
        raw = frame.predicted.to_numpy().copy()
        frame["predicted"] = np.maximum(raw, 0)
        frame.to_csv(path, index=False)
        result_path = path.parent / "result.csv"
        result = pd.read_csv(result_path, keep_default_na=False)
        score = float(np.abs(frame.actual - frame.predicted).mean())
        old_score = float(result.at[0, "score"])
        result.loc[0, "score"] = score
        result.loc[0, "normalized_loss"] = score / denominator
        result.loc[0, "note"] = "Derived count clipping; original fit cost retained; no refit"
        result.to_csv(result_path, index=False)
        changes.append(dict(recipe=path.parent.name, negative_count=int((raw < 0).sum()),
                            raw_score=old_score, corrected_score=score,
                            raw_prediction_sha256=hashlib.sha256(original_path.read_bytes()).hexdigest(),
                            corrected_prediction_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    pd.DataFrame(changes).to_csv(destination / "COUNT-CORRECTION.csv", index=False)
    (destination / "CORRECTION.md").write_text(
        "# Derived scoring correction; zero additional fits\n\n"
        f"Original workspace: {source.name}\n\n"
        "The pilot adapter did not enforce the existing course's nonnegative-count rule. "
        "This mismatch was found after development results were observed. "
        "Every bike prediction is clipped at zero, irrespective of its model or score. "
        "Other tasks retain their raw predictions. Original evidence is preserved separately. "
        "Fit and process times in this copy describe the original executions, not new training. "
        "The raw source snapshot describes training; correct_headroom_counts.py describes this transformation. "
        "Both raw and corrected analyses are retained. No final evaluation or positive RSI result is implied.\n",
        encoding="utf-8")
    shutil.copyfile(__file__, destination / "correct_headroom_counts.py")
    # Regenerate all aggregates from the corrected per-candidate records.
    spec = importlib.util.spec_from_file_location("pilot_analysis", source / "pilot-source.py")
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    pilot.summarize(destination)
    print(f"Corrected {sum(row['negative_count'] for row in changes)} values; zero new fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    correct(args.source.resolve(), args.destination.resolve())
