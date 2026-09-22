"""Step 38 - check 1: app.py imports, the app starts in a TestClient, and GET /health answers."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import client, fail, load_app, ok  # noqa: E402

try:
    app = load_app()
except Exception as error:  # noqa: BLE001 - whatever broke the import is the finding
    fail(f"app.py did not import: {type(error).__name__}: {error}")

try:
    with client(app) as http:
        response = http.get("/health")
except Exception as error:  # noqa: BLE001
    fail(f"the app did not start: {type(error).__name__}: {error}")

if response.status_code != 200:
    fail(f"GET /health returned {response.status_code}")
if response.json() != {"status": "ok"}:
    fail(f"GET /health returned {response.text}")
ok("app.py starts and GET /health answers ok")
