"""Preserve checked memory/replay artifacts without calling them a model run."""
import hashlib
from pathlib import Path
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
source = ROOT.parent / "rsi-work-2026-09-22-tabular-memory"
destination = ROOT / "rsi/evidence/2026-09-22/tabular-memory"
if destination.exists() or not pd.read_csv(source / "MEMORY-CHECKS.csv").passed.all():
    raise ValueError("Fresh archive and passing memory checks required")
shutil.copyfile(Path(__file__), source / "source" / Path(__file__).name)
rows = []
for path in sorted(source.rglob("*")):
    if not path.is_file() or "__pycache__" in path.parts:
        continue
    relative = path.relative_to(source)
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    raw = path.read_bytes()
    assert raw == target.read_bytes()
    rows.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
pd.DataFrame(rows).to_csv(destination / "ARCHIVE-MANIFEST.csv", index=False)
print(f"{len(rows)} files archived with matching bytes")
