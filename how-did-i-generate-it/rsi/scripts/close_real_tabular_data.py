"""Resolve chess schema against its original source, then preserve both preparations."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
import shutil
import urllib.request
import zipfile

import pandas as pd
from scipy.io import arff

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent = ROOT.parent
    v2 = parent / "rsi-work-2026-09-22-real-tabular-data-v2"
    source = v2 / "original-chess"
    source.mkdir(exist_ok=False)
    url = "https://archive.ics.uci.edu/static/public/22/chess%2Bking%2Brook%2Bvs%2Bking%2Bpawn.zip"
    with urllib.request.urlopen(url, timeout=60) as response:
        raw = response.read()
    (source / "chess.zip").write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        for name in ("kr-vs-kp.data", "kr-vs-kp.names"):
            match, = [p for p in names if p.split("/")[-1] == name]
            (source / name).write_bytes(archive.read(match))
    original = pd.read_csv(source / "kr-vs-kp.data", header=None, dtype=str)
    parsed, _ = arff.loadarff(v2 / "tasks/3/original.arff")
    converted = pd.DataFrame(parsed).map(lambda x: x.decode() if isinstance(x, bytes) else str(x))
    same = Counter(map(tuple, original.to_numpy())) == Counter(map(tuple, converted.to_numpy()))
    if original.shape != (3196, 37) or not same:
        raise ValueError("Original chess and OpenML rows differ; preserve acquisition for review")
    (source / "REVIEW.md").write_text(
        "# Chess source comparison\n\n"
        f"Retrieved UTC: {datetime.now(timezone.utc).isoformat()}\n\nURL: {url}\n\n"
        f"ZIP SHA256: {sha(source / 'chess.zip')}\n\n"
        "The original file has 3,196 rows and 37 columns: 36 inputs plus the target. "
        "Its complete row multiset matches OpenML exactly, including labels and duplicate counts. "
        "The modern UCI page's 35-feature summary conflicts with these files; retain the 36 actual inputs. "
        "No column is dropped to match that summary. Alen Shapiro, Chess (King-Rook vs. King-Pawn), "
        "UCI DOI 10.24432/C5DK5C, CC BY 4.0. No model fit was performed.\n", encoding="utf-8")
    shutil.copyfile(Path(__file__), v2 / "source" / Path(__file__).name)
    checker = ROOT / "how-did-i-generate-it/rsi/scripts/check_real_tabular_data.py"
    shutil.copyfile(checker, v2 / "source" / checker.name)
    for version in (1, 2):
        work = parent / f"rsi-work-2026-09-22-real-tabular-data-v{version}"
        if version == 1 and not (work / "FAILURE.md").exists():
            raise ValueError("Missing original failure record")
        if version == 2 and not pd.read_csv(work / "DATA-CHECKS.csv").passed.all():
            raise ValueError("Data checks did not pass")
        destination = ROOT / f"rsi/evidence/2026-09-22/real-tabular-data-v{version}"
        if destination.exists():
            raise ValueError("Never overwrite an archive")
        rows = []
        for path in sorted(work.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(work)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            assert sha(path) == sha(target)
            rows.append(dict(path=relative.as_posix(), bytes=target.stat().st_size, sha256=sha(target)))
        pd.DataFrame(rows).to_csv(destination / "ARCHIVE-MANIFEST.csv", index=False)
        print(f"v{version}: {len(rows)} original files archived with matching bytes", flush=True)


if __name__ == "__main__":
    main()
