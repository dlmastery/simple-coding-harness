"""The trace log: append-only JSON lines, fixed fields, one per event.

Every fit of every arm lands here, and so do the boot checksums, the test
score and each card written. The verifier reads pairs out of it, Dream-RSI
replays it as a simulator, the meta harness checksums what a generation
booted. There is no method that rewrites or deletes a line.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("t", "event", "problem", "arm", "seed", "recipe", "val_score", "error", "seconds", "info")


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

    def rows(self, event=None, **match):
        """The rows in the order they were written, filtered by event and any other field."""
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        return [r for r in rows if (event is None or r["event"] == event) and all(r.get(k) == v for k, v in match.items())]
