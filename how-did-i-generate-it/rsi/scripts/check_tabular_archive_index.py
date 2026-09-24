"""Verify every manifest byte against Git's staged blob, including ignored run folders."""
import csv
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "rsi/evidence/2026-09-22/tabular-comparison/"


def main():
    with (ROOT / PREFIX / "ARCHIVE-MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    tracked = set(subprocess.check_output(["git", "ls-files", "-z", "--", PREFIX], cwd=ROOT).decode().split("\0")) - {""}
    expected = {PREFIX + row["path"] for row in rows} | {PREFIX + "ARCHIVE-MANIFEST.csv"}
    if tracked != expected:
        raise ValueError(f"Git coverage differs: missing {len(expected-tracked)}, extra {len(tracked-expected)}")
    process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output = ROOT / "how-did-i-generate-it/rsi/validation/TABULAR-ARCHIVE-INDEX-CHECK.csv"
    try:
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "passed"])
            writer.writeheader()
            for row in rows:
                process.stdin.write((":"+PREFIX+row["path"]+"\n").encode())
                process.stdin.flush()
                header = process.stdout.readline().decode().split()
                if len(header) != 3 or header[1] != "blob":
                    raise ValueError(f"Missing staged blob {row['path']}: {header}")
                raw = process.stdout.read(int(header[2]))
                if process.stdout.read(1) != b"\n":
                    raise ValueError("Invalid batch boundary")
                digest = hashlib.sha256(raw).hexdigest()
                passed = len(raw) == int(row["bytes"]) and digest == row["sha256"]
                writer.writerow(dict(path=row["path"], bytes=len(raw), sha256=digest, passed=passed))
                if not passed:
                    raise ValueError(f"Staged bytes differ: {row['path']}")
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    print(f"All {len(rows)} original files match staged Git bytes; manifest also tracked")


if __name__ == "__main__":
    main()
