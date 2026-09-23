"""Publish a completed, independently checked nested-study phase byte for byte."""
import argparse
import hashlib
from pathlib import Path
import shutil

import pandas as pd

from run_nested_research import ARCHIVE, ARMS, workspace


def archive(phase):
    work = workspace(phase)
    destination = ARCHIVE / ("nested-research-" + phase)
    if destination.exists() or list(work.rglob(".running")):
        raise ValueError("Fresh destination and closed workers required")
    checks = pd.read_csv(work / "FINAL-CHECKS.csv")
    if checks.empty or not checks.passed.all() or not (work / "SCORING-COMPLETE.md").exists():
        raise ValueError("Complete verified phase required")
    if phase == "development" and not (work / "GENERATION-TWO-FREEZE.csv").exists():
        raise ValueError("Preserve the later inherited rewrite before closing development")
    if not (work / "REPORT.md").exists():
        raise ValueError("Checked report required")
    shutil.copyfile(Path(__file__), work / "analysis-source" / Path(__file__).name)
    records = []
    for source in sorted(work.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts:
            continue
        relative = source.relative_to(work)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        target.write_bytes(raw)
        if target.read_bytes() != raw:
            raise ValueError("Copy identity failed")
        records.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    pd.DataFrame(records).to_csv(destination / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"Archived {len(records)} original files; byte identities verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=list(ARMS))
    archive(parser.parse_args().phase)
