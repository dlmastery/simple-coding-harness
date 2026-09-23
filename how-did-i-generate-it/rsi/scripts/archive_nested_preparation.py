"""Archive failed preflight and immutable corrected inputs while search runs."""
import hashlib
from pathlib import Path
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
FAILED = ROOT.parent / "rsi-work-2026-09-22-nested-development"
CORRECTED = ROOT.parent / "rsi-work-2026-09-22-nested-development-2"
DESTINATION = ROOT / "rsi/evidence/2026-09-22/nested-research-preparation"


def main():
    if DESTINATION.exists():
        raise ValueError("Preserve existing archive")
    sources = [("failed-preflight", FAILED, p) for p in FAILED.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    # Never read or snapshot a live attempt's output. Only frozen study inputs
    # and already-closed preflight artifacts enter this preparation archive.
    paths = [CORRECTED / row.path for row in pd.read_csv(CORRECTED / "STUDY-FREEZE.csv").itertuples()]
    paths += [CORRECTED / name for name in ("STUDY-FREEZE.csv", "PREFLIGHT-CHECKS.csv", "PREFLIGHT-COMPLETE.md", "PREFLIGHT-FIXTURE-TRACE.csv")]
    for name in ("preflight-generations", "preflight-source", "preflight-review-1"):
        paths.extend(p for p in (CORRECTED / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    sources.extend(("corrected-inputs", CORRECTED, p) for p in sorted(set(paths)))
    records = []
    for label, root, source in sources:
        relative = Path(label) / source.relative_to(root)
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        target.write_bytes(raw)
        if target.read_bytes() != raw:
            raise ValueError("Copied bytes differ")
        records.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    pd.DataFrame(records).to_csv(DESTINATION / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"Archived {len(records)} immutable preparation files; no live outputs copied")


if __name__ == "__main__":
    main()
