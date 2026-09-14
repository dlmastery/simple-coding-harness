"""Step 02 - run npm and node from Python, on Windows too.

The step's Node side has three commands: `npm install` (once), `npm run
build` (esbuild writes static/bundle.js) and `node prompt.mjs` (the system
prompt). demo.py, server.py and test_step.py call these helpers so that a
fresh checkout works with one command.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
NODE = shutil.which("node")
NPM = shutil.which("npm")

# The lang-core package sends install telemetry unless told not to.
ENV = {**os.environ, "OPENUI_TELEMETRY_DISABLED": "1", "DO_NOT_TRACK": "1"}


def run(*args: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=HERE, env=ENV, capture_output=True, text=True, encoding="utf-8", timeout=timeout)


def ensure_node_modules() -> bool:
    """Install the pinned packages once. False when npm is not available."""
    if (HERE / "node_modules" / "@openuidev" / "react-lang").exists():
        return True
    if NPM is None:
        return False
    result = run(NPM, "install", "--no-audit", "--no-fund")
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return True


def ensure_bundle() -> Path:
    """static/bundle.js, built with esbuild when missing or older than the sources."""
    bundle = HERE / "static" / "bundle.js"
    sources = [HERE / "app.mjs", HERE / "library.mjs"]
    if not bundle.exists() or bundle.stat().st_mtime < max(s.stat().st_mtime for s in sources):
        ensure_node_modules()
        result = run(NPM, "run", "build")
        if result.returncode:
            raise RuntimeError(result.stderr[-2000:])
    return bundle


def ensure_prompt() -> str:
    """prompt.txt, regenerated from library.mjs when missing or stale."""
    prompt = HERE / "prompt.txt"
    if not prompt.exists() or prompt.stat().st_mtime < (HERE / "library.mjs").stat().st_mtime:
        ensure_node_modules()
        result = run(NODE, "prompt.mjs")
        if result.returncode:
            raise RuntimeError(result.stderr[-2000:])
        prompt.write_text(result.stdout, encoding="utf-8")
    return prompt.read_text(encoding="utf-8")
