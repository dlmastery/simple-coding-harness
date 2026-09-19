"""Step 00 - the trace log: append-only JSON lines, one per fit, fixed fields.

Every fit of every arm lands here. Step 02's verifier reads pairs out of it,
step 04 replays it as a simulator, step 05 checksums what a generation booted.
There is no method that rewrites or deletes a line.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("t", "recipe", "val_auc", "error", "seconds", "seed", "arm")


class TraceLog:
    def __init__(self, path):
        self.path = Path(path)

    def append(self, **row):
        unknown = set(row) - set(FIELDS)
        if unknown:
            raise ValueError(f"a trace row has exactly the fields {FIELDS}; not {sorted(unknown)}")
        row = {k: row.get(k) for k in FIELDS}
        row["t"] = row["t"] or datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:   # "a": append is the only mode
            f.write(json.dumps(row) + "\n")

    def rows(self):
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def replay(self, arm=None):
        """The rows in the order they were written, optionally one arm's: the world a later step sees."""
        for row in self.rows():
            if arm is None or row["arm"] == arm:
                yield row
