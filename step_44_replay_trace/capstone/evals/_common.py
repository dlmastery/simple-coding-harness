"""Step 38 - shared helpers for the capstone checks.

Every check runs with the workspace as cwd. `load_app` imports `app.py`
from there with a fresh temporary database, and `client` opens a
TestClient on it, so the startup code runs without binding a port.
"""

import importlib
import os
import sys
import tempfile
from pathlib import Path


def load_app():
    """Import `app` from the workspace's app.py. Raises when it is missing or broken."""
    workspace = Path.cwd()
    if not (workspace / "app.py").exists():
        raise FileNotFoundError("app.py is missing")
    os.environ["TODO_DB"] = str(Path(tempfile.mkdtemp(prefix="capstone-db-")) / "check.db")
    sys.path.insert(0, str(workspace))
    module = importlib.import_module("app")
    if not hasattr(module, "app"):
        raise AttributeError("app.py has no module-level variable named app")
    return module.app


def client(app):
    """A TestClient whose `with` block runs the app's startup and shutdown."""
    from fastapi.testclient import TestClient

    return TestClient(app)


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message):
    print(f"PASS: {message}")
    sys.exit(0)
