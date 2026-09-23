"""Check every archived original against the staged Git blob before committing."""
import argparse
import csv
import hashlib
from pathlib import Path
import subprocess


def check(archive, report):
    root = Path(__file__).resolve().parents[3]
    archive = archive.resolve()
    records = []
    with (archive / "ARCHIVE-MANIFEST.csv").open(newline="") as stream:
        entries = list(csv.DictReader(stream))
    if not entries or len({r["path"] for r in entries}) != len(entries):
        raise ValueError("Empty or repeated archive entries")
    for item in entries:
        path = (archive / item["path"]).resolve()
        path.relative_to(archive)
        relative = path.relative_to(root).as_posix()
        blob = subprocess.run(["git", "show", ":" + relative], cwd=root, capture_output=True, check=True).stdout
        passed = len(blob) == int(item["bytes"]) and hashlib.sha256(blob).hexdigest() == item["sha256"] and blob == path.read_bytes()
        records.append(dict(path=relative, passed=passed))
        if not passed:
            raise ValueError("Staged archive identity differs: " + relative)
    with report.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "passed"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Verified {len(records)} original archived files against staged Git blobs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    check(args.archive, args.report)
