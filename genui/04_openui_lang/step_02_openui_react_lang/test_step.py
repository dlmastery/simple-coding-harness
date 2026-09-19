"""Step 02 tests. Offline: the model is a fake that yields scripted chunks.

The Python side (SSE route, prompt caching) is tested here. The Node side
(the Zod catalog, the generated prompt, the real parser, <Renderer>) runs
through `npm test`; when node_modules is missing and npm is available the
pinned packages are installed first.
"""

import json
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import llm  # noqa: E402
import nodetools  # noqa: E402
import server  # noqa: E402

SCRIPTED = ['root = Stack([m])\n', 'm = Metric("Cups", ', '241, "+8%")\n']


def fake_stream(messages):
    """What the model would say, in three chunks; the messages are checked."""
    assert messages[0]["role"] == "system" and "Component Signatures" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "lemonade"}
    yield from SCRIPTED


def test_messages_have_the_generated_prompt_as_system_message():
    messages = server.messages_for("hi", "SYSTEM")
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[0]["content"] == "SYSTEM"


def test_generate_route_streams_deltas_as_sse(monkeypatch):
    monkeypatch.setattr(llm, "stream_completion", fake_stream)
    srv = server.make_server(system_prompt="## Component Signatures\nMetric(label: string, value: string | number)")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{srv.server_port}/generate",
            data=json.dumps({"prompt": "lemonade"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            assert response.headers["Content-Type"] == "text/event-stream"
            body = response.read().decode()
    finally:
        srv.shutdown()
    deltas = [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ") and line != "data: {}"]
    assert deltas == SCRIPTED
    assert body.endswith("event: done\ndata: {}\n\n")
    assert server.LAST["program"] == "".join(SCRIPTED)


def fail_midway(messages, usage=None):
    """A model that streams one chunk, then dies (network, bad key, rate limit)."""
    yield SCRIPTED[0]
    raise RuntimeError("upstream closed the connection")


def test_generate_route_ends_with_an_error_event_when_the_model_dies(monkeypatch):
    monkeypatch.setattr(llm, "stream_completion", fail_midway)
    srv = server.make_server(system_prompt="x")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{srv.server_port}/generate",
            data=json.dumps({"prompt": "lemonade"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            body = response.read().decode()
        bad = urllib.request.Request(f"http://127.0.0.1:{srv.server_port}/generate", data=b"not json", headers={"Content-Type": "application/json"})
        with pytest.raises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(bad)
        assert failure.value.code == 400
    finally:
        srv.shutdown()
    assert body.startswith(f"data: {json.dumps(SCRIPTED[0])}\n\n")
    assert body.endswith('event: error\ndata: "RuntimeError: upstream closed the connection"\n\n')
    assert "event: done" not in body
    assert server.LAST["program"] == SCRIPTED[0]  # what did arrive is kept for the demo


def test_static_files_are_served():
    srv = server.make_server(system_prompt="x")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/") as response:
            assert b'<script type="module" src="/static/bundle.js">' in response.read()
    finally:
        srv.shutdown()


def test_api_key_falls_back_to_openai_key(monkeypatch):
    """The env file holds OPENAI_API_KEY; llm.py maps it to API_KEY when API_KEY is unset."""
    import importlib

    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-openai")
    monkeypatch.setattr(Path, "home", lambda: HERE / "no-such-home")  # no ~/.simple-harness/env in the way
    reloaded = importlib.reload(llm)
    assert reloaded.API_KEY == "sk-from-openai"
    monkeypatch.setenv("API_KEY", "explicit")
    assert importlib.reload(llm).API_KEY == "explicit"  # a real API_KEY wins


# ── the Node side ───────────────────────────────────────────────────────────

def need_node_modules():
    if nodetools.NODE is None or nodetools.NPM is None:
        pytest.skip("node and npm are not installed")
    if not nodetools.ensure_node_modules():
        pytest.skip("npm install did not run")


def test_prompt_is_generated_from_the_catalog():
    need_node_modules()
    text = nodetools.ensure_prompt()
    assert "## Component Signatures" in text
    assert "Metric(label: string, value: string | number, delta?: string)" in text
    assert text.startswith("You turn a request into a small dashboard or form.")


def test_node_suite_passes():
    need_node_modules()
    result = nodetools.run(nodetools.NPM, "test")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout


def test_bundle_builds_with_esbuild():
    need_node_modules()
    bundle = nodetools.ensure_bundle()
    text = bundle.read_text(encoding="utf-8")
    assert "process.env" not in text  # defined away; the browser has no process
    assert 'name: "Metric"' in text
