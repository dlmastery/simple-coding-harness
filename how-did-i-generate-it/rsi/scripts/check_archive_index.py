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
    # One Git process avoids thousands of Windows process launches while
    # retaining the same comparison of every staged byte and SHA256.
    process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for item in entries:
            path = (archive / item["path"]).resolve()
            path.relative_to(archive)
            relative = path.relative_to(root).as_posix()
            if "\n" in relative or "\r" in relative:
                raise ValueError("Unsupported path in Git batch protocol")
            process.stdin.write((":" + relative + "\n").encode("utf-8"))
            process.stdin.flush()
            header = process.stdout.readline().decode("utf-8").strip().split()
            if len(header) != 3 or header[1] != "blob":
                raise ValueError("Staged blob missing or invalid: " + relative)
            size = int(header[2])
            blob = process.stdout.read(size)
            if len(blob) != size or process.stdout.read(1) != b"\n":
                raise ValueError("Incomplete Git blob response")
            passed = len(blob) == int(item["bytes"]) and hashlib.sha256(blob).hexdigest() == item["sha256"] and blob == path.read_bytes()
            records.append(dict(path=relative, passed=passed))
            if not passed:
                raise ValueError("Staged archive identity differs: " + relative)
        process.stdin.close()
        if process.wait(timeout=30) != 0:
            raise ValueError("Git batch reader failed")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream and not stream.closed:
                stream.close()
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
