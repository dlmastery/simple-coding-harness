"""Preserve a terminal, independently checked comparison without changing frozen inputs."""
import hashlib
from pathlib import Path
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"
DESTINATION = ROOT / "rsi/evidence/2026-09-22/tabular-comparison"


def main():
    if DESTINATION.exists():
        raise ValueError("Refusing to replace an existing archive")
    if list(WORK.rglob(".running")):
        raise ValueError("A recorded worker is still running")
    for name in ("SEARCH-COMPLETE.md", "SCORING-COMPLETE.md", "REPORT.md"):
        if not (WORK / name).is_file():
            raise ValueError(f"Missing completed output: {name}")
    for name in ("SEARCH-CHECKS.csv", "FINAL-CHECKS.csv"):
        checks = pd.read_csv(WORK / name)
        if checks.empty or not checks.passed.eq(True).all():
            raise ValueError(f"Unpassed checks: {name}")
    # Add post-run tooling separately; the original source freeze stays intact.
    analysis = WORK / "analysis-source"
    analysis.mkdir(exist_ok=True)
    for name in ("check_tabular_comparison.py", "report_tabular_comparison.py", Path(__file__).name):
        shutil.copyfile(Path(__file__).with_name(name), analysis / name)
    records = []
    for source in sorted(WORK.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts:
            continue
        relative = source.relative_to(WORK)
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        raw = source.read_bytes()
        if target.read_bytes() != raw:
            raise ValueError(f"Archive byte mismatch: {relative}")
        records.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    pd.DataFrame(records).to_csv(DESTINATION / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"Archived {len(records)} original files; every copied byte verified")


if __name__ == "__main__":
    main()
