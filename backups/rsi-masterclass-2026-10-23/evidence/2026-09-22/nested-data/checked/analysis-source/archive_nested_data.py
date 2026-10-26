"""Preserve both data-preparation versions and their original byte identities."""
import hashlib
from pathlib import Path
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / "rsi/evidence/2026-09-22/nested-data"
SOURCES = {"parser-failure": ROOT.parent / "rsi-work-2026-09-22-nested-data",
           "checked": ROOT.parent / "rsi-work-2026-09-22-nested-data-2"}


def main():
    if DESTINATION.exists():
        raise ValueError("Archive already exists; preserve it")
    checked = SOURCES["checked"]
    checks = pd.read_csv(checked / "DATA-CHECKS.csv")
    if checks.empty or not checks.passed.eq(True).all():
        raise ValueError("Data checks must pass")
    if (SOURCES["parser-failure"] / "PREPARATION-MANIFEST.csv").exists():
        raise ValueError("Unexpected successful preparation in failed version")
    analysis = checked / "analysis-source"
    analysis.mkdir(exist_ok=False)
    for name in (Path(__file__).name, "check_nested_data.py"):
        shutil.copyfile(Path(__file__).with_name(name), analysis / name)
    records = []
    for label, workspace in SOURCES.items():
        for source in sorted(workspace.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            relative = Path(label) / source.relative_to(workspace)
            target = DESTINATION / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            raw = source.read_bytes()
            if target.read_bytes() != raw:
                raise ValueError("Copy identity failed")
            records.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    pd.DataFrame(records).to_csv(DESTINATION / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"Archived {len(records)} original files, byte-verified; both versions retained")


if __name__ == "__main__":
    main()
