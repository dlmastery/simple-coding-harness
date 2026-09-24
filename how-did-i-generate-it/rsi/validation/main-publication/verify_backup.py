"""Verify every archived pre-replacement file against its original Git blob."""
import hashlib
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[4]
SOURCE = "c8c5153d87947cf2e872bfe6894e808a97be83d4"
ARCHIVE = ROOT / "backups/rsi-before-masterclass-2026-09-24/rsi-original.zip"

entries = subprocess.check_output(
    ["git", "ls-tree", "-rz", SOURCE, "rsi"], cwd=ROOT
).split(b"\0")
expected = {}
for entry in entries:
    if not entry:
        continue
    metadata, path = entry.split(b"\t", 1)
    mode, kind, blob = metadata.split()
    assert kind == b"blob", (kind, path)
    expected["original/" + path.decode()] = blob.decode()

with zipfile.ZipFile(ARCHIVE) as archive:
    actual = {info.filename for info in archive.infolist() if not info.is_dir()}
    assert actual == set(expected), "Archive membership differs from original RSI tree"
    for path, blob in expected.items():
        content = archive.read(path)
        header = f"blob {len(content)}\0".encode()
        assert hashlib.sha1(header + content).hexdigest() == blob, path

digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
assert digest == "bf378e0b1f54cc1da4b43663f81f2822219e951c957209db9172cb46684860a6"
print(f"PASS: {len(expected)} original files match Git blobs; archive SHA-256 {digest}")
