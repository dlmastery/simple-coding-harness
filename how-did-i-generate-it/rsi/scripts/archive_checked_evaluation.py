"""Copy a completed evaluation into the evidence tree and verify every byte."""
import argparse
import hashlib
from pathlib import Path
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(source, destination):
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError("Use a new archive outside the source workspace")
    if not destination.is_relative_to(ROOT / "rsi/evidence"):
        raise ValueError("Destination must be inside the course evidence tree")
    if not (source / "REPORT.md").exists() or not pd.read_csv(source / "EVALUATION-CHECKS.csv").passed.all():
        raise ValueError("Archive only a completed, checked evaluation")
    if list(source.rglob(".running")):
        raise ValueError("Resolve live or stale workers before archiving")
    records = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        before, after = sha(path), sha(target)
        if before != after:
            raise ValueError(f"Archive identity mismatch: {relative}")
        records.append(dict(path=relative.as_posix(), bytes=target.stat().st_size, sha256=after))
    pd.DataFrame(records).to_csv(destination / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"Archived {len(records)} byte-verified files; excluded only regenerable Python caches")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    archive(args.source.resolve(), args.destination.resolve())
