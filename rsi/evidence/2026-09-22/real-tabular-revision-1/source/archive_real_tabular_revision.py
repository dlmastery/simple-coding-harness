"""Archive a terminal, checked revision stage with all original execution artifacts."""
import argparse
import hashlib
from pathlib import Path
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]


def archive(stage):
    source = ROOT.parent / f"rsi-work-2026-09-22-real-tabular-revision-{stage}"
    destination = ROOT / f"rsi/evidence/2026-09-22/real-tabular-revision-{stage}"
    if destination.exists() or list(source.rglob(".running")):
        raise ValueError("Fresh archive and terminal workers required")
    if not (source / "COMPLETE.md").exists() or not pd.read_csv(source / "REVISION-CHECKS.csv").passed.all():
        raise ValueError("Complete and checked revision required")
    for name in ("check_real_tabular_revision.py", Path(__file__).name):
        shutil.copyfile(Path(__file__).with_name(name), source / "source" / name)
    rows = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        raw = path.read_bytes()
        if raw != target.read_bytes():
            raise ValueError(f"Byte mismatch {relative}")
        rows.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    pd.DataFrame(rows).to_csv(destination / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"{len(rows)} original files archived with identical bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=int, choices=[1, 2])
    archive(parser.parse_args().stage)
