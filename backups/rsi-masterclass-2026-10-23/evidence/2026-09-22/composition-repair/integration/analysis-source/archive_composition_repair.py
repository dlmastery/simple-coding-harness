"""Archive the failed preflight, executed integration check and no-fit capacity review."""
import hashlib
from pathlib import Path
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / "rsi/evidence/2026-09-22/composition-repair"
SOURCES = {
    "failed-preflight": ROOT.parent / "rsi-work-2026-09-22-composition-repair",
    "integration": ROOT.parent / "rsi-work-2026-09-22-composition-repair-2",
    "capacity-review": ROOT.parent / "rsi-work-2026-09-22-composition-capacity-review",
}


def main():
    if DESTINATION.exists() or any(list(path.rglob(".running")) for path in SOURCES.values()):
        raise ValueError("Fresh archive and terminal workers required")
    for path in (SOURCES["integration"] / "REPAIR-CHECKS.csv", SOURCES["capacity-review"] / "CAPACITY-CHECKS.csv", SOURCES["capacity-review"] / "preflight/CHECKS.csv"):
        frame = pd.read_csv(path)
        if frame.empty or not frame.passed.eq(True).all():
            raise ValueError(f"Unpassed repair checks: {path}")
    if not (SOURCES["integration"] / "SMOKE-COMPLETE.md").is_file():
        raise ValueError("Integration run has not completed")
    post = SOURCES["integration"] / "analysis-source"
    post.mkdir(exist_ok=True)
    for name in ("check_composition_repair.py", Path(__file__).name):
        shutil.copyfile(Path(__file__).with_name(name), post / name)
    records = []
    for label, root in SOURCES.items():
        for source in sorted(root.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            relative = Path(label) / source.relative_to(root)
            target = DESTINATION / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            raw = source.read_bytes()
            if target.read_bytes() != raw:
                raise ValueError(f"Archive mismatch: {relative}")
            records.append(dict(path=relative.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    pd.DataFrame(records).to_csv(DESTINATION / "ARCHIVE-MANIFEST.csv", index=False)
    print(f"Archived and byte-verified {len(records)} original files across all three versions")


if __name__ == "__main__":
    main()
