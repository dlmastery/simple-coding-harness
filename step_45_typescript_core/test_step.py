"""Step 45 offline tests. The TypeScript port has its own suite under
harness-ts/tests, run by node's test runner against a fake client. This
file runs that suite when node 22.6 or newer is on the PATH, and checks
that a session log crosses the language line in both directions: written
by Python, loaded by TypeScript, and the reverse. The Python harness copied
from step 44 gets an import smoke test only. No model, browser or network
is launched.
"""

import inspect
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent
NODE = shutil.which("node")
BRIDGE = "harness-ts/tests/session_bridge.ts"


def node_version():
    out = subprocess.run([NODE, "--version"], capture_output=True, text=True).stdout.strip()  # v22.12.0
    match = re.match(r"v(\d+)\.(\d+)", out)
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def need_node():
    """Skip, the way pytest.importorskip does, when node cannot run .ts files."""
    if NODE is None:
        pytest.skip("node is not installed")
    version = node_version()
    if version < (22, 6):
        pytest.skip(f"node {version[0]}.{version[1]} has no --experimental-strip-types (22.6+)")


def run_node(*args, timeout=120):
    return subprocess.run(
        [NODE, "--experimental-strip-types", *args],
        cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=timeout,
    )


@pytest.fixture
def store(tmp_path, monkeypatch):
    """The Python session module pointed at a temp directory."""
    from harness import session

    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    return session


def test_node_suite_passes():
    need_node()
    result = run_node("--test", "harness-ts/tests/*.test.ts", timeout=300)
    tail = "\n".join(result.stdout.splitlines()[-12:])
    assert result.returncode == 0, tail + result.stderr[-2000:]
    assert "# fail 0" in result.stdout, tail


def test_typescript_session_loads_in_python(tmp_path, store):
    need_node()
    result = run_node(BRIDGE, "write", str(tmp_path), "from-ts")
    assert result.returncode == 0, result.stderr
    lines = (tmp_path / "from-ts.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[5]) == {"rewind_to": 2}
    assert store.load("from-ts") == [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": "list the files"},
        {"role": "assistant", "content": "héllo from TypeScript"},
    ]
    assert store.title(store.load("from-ts")) == "list the files"


def test_python_session_loads_in_typescript(tmp_path, store, monkeypatch):
    need_node()
    monkeypatch.setattr(store, "CURRENT", "from-py")
    messages = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": "list the files"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "bash", "arguments": "{\"command\": \"ls\"}"}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "README.md\nharness\n"},
        {"role": "assistant", "content": "Two entries: README.md and harness/."},
    ]
    if "usage" in inspect.signature(store.save).parameters:  # step 44 writes a usage entry after a model call
        store.save(messages, usage={"prompt_tokens": 12, "completion_tokens": 3})
    else:
        store.save(messages)
    store.rewind_to(2)
    store.save(messages[:2] + [{"role": "assistant", "content": "héllo from Python"}])
    store.compacted([{"role": "system", "content": "You are a coding agent.\n\n<summary>\nGreeted.\n</summary>"}, {"role": "assistant", "content": "héllo from Python"}])
    store.save(store.load("from-py") + [{"role": "user", "content": "thanks"}])

    result = run_node(BRIDGE, "load", str(tmp_path), "from-py")
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stdout)
    assert loaded == store.load("from-py")
    assert [m["role"] for m in loaded] == ["system", "assistant", "user"]
    assert loaded[-1]["content"] == "thanks"


def test_python_harness_still_imports():
    from harness import agent, llm, session, tools  # noqa: F401

    assert callable(agent.main) and "bash" in tools.TOOLS and hasattr(session, "load")
