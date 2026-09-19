"""Step 01 offline tests. The model is a fake client that yields scripted
chunks; the tests check the event sequence, the wire format, the FastAPI
endpoint and the Python SSE reader. The JavaScript SSE reader has its own
node --test suite, run here through npm when node is on the PATH.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")
STEP = Path(__file__).resolve().parent
sys.path.insert(0, str(STEP))

import agent  # noqa: E402
import llm  # noqa: E402
from ag_ui.core import RunAgentInput, UserMessage  # noqa: E402
from ag_ui.encoder import EventEncoder  # noqa: E402
from sse import parse_sse  # noqa: E402


def chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


class FakeClient:
    """Stands in for llm.client: records the request, yields scripted chunks."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        return iter(self.chunks)


SCRIPT = [chunk("Fresh "), chunk("lemons, "), SimpleNamespace(choices=[]), chunk("cold water.")]


def run_input(text="what makes good lemonade?"):
    return RunAgentInput(
        thread_id="t1", run_id="r1", messages=[UserMessage(id="u1", content=text)],
        tools=[], context=[], forwarded_props={}, state={},
    )


@pytest.fixture
def fake(monkeypatch):
    client = FakeClient(SCRIPT)
    monkeypatch.setattr(llm, "client", client)
    return client


def test_run_yields_the_protocol_sequence(fake):
    events = list(agent.run(run_input()))
    assert [e.type.value for e in events] == [
        "RUN_STARTED", "TEXT_MESSAGE_START",
        "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_CONTENT",
        "TEXT_MESSAGE_END", "RUN_FINISHED",
    ]
    deltas = [e.delta for e in events if e.type.value == "TEXT_MESSAGE_CONTENT"]
    assert "".join(deltas) == "Fresh lemons, cold water."
    ids = {e.message_id for e in events if hasattr(e, "message_id")}
    assert len(ids) == 1, "start, content and end share one message id"


def test_model_gets_openai_messages(fake):
    list(agent.run(run_input("hi")))
    sent = fake.requests[0]["messages"]
    assert sent[0]["role"] == "system"
    assert sent[1] == {"role": "user", "content": "hi"}
    assert fake.requests[0]["stream"] is True


def test_wire_format_is_camel_case_json_per_line(fake):
    encoder = EventEncoder()
    lines = [encoder.encode(e) for e in agent.run(run_input())]
    assert all(line.startswith("data: ") and line.endswith("\n\n") for line in lines)
    first = json.loads(lines[0][6:])
    assert first == {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"}
    assert "messageId" in json.loads(lines[1][6:])
    assert encoder.get_content_type() == "text/event-stream"


def test_model_failure_becomes_run_error(monkeypatch):
    def boom(**request):
        raise RuntimeError("model down")

    monkeypatch.setattr(llm, "client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom))))
    types = [e.type.value for e in agent.run(run_input())]
    assert types[-1] == "RUN_ERROR"
    assert "RUN_FINISHED" not in types


def test_endpoint_streams_events(fake):
    from fastapi.testclient import TestClient

    import server

    with TestClient(server.app) as client:
        body = json.loads(run_input().model_dump_json(by_alias=True))
        with client.stream("POST", "/agent", json=body, headers={"accept": "text/event-stream"}) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            text = "".join(response.iter_text())
    events = parse_sse(text)
    assert [e["type"] for e in events][:2] == ["RUN_STARTED", "TEXT_MESSAGE_START"]
    assert events[-1]["type"] == "RUN_FINISHED"


def test_page_files_are_served():
    from fastapi.testclient import TestClient

    import server

    with TestClient(server.app) as client:
        assert "AG-UI" in client.get("/").text
        assert client.get("/app.js").status_code == 200
        assert client.get("/server.py").status_code == 404


def test_parse_sse_handles_split_and_comments():
    text = 'data: {"a": 1}\n\n: keepalive\n\ndata: {"b": 2}\n\n'
    assert parse_sse(text) == [{"a": 1}, {"b": 2}]
    assert parse_sse(text.replace("\n", "\r\n")) == [{"a": 1}, {"b": 2}]  # the spec allows CRLF


def test_stream_text_skips_chunks_without_a_delta(monkeypatch):
    chunks = [SimpleNamespace(choices=[SimpleNamespace(delta=None)]), chunk("ok"), SimpleNamespace(choices=[])]
    monkeypatch.setattr(llm, "client", FakeClient(chunks))
    assert list(llm.stream_text([])) == ["ok"]


def test_disconnect_closes_the_generator(fake):
    """The endpoint pulls one event per step; when the page has gone it closes the run."""
    import asyncio

    import server

    closed = []

    class Run:
        def __init__(self):
            self.it = iter(agent.run(run_input()))

        def __next__(self):
            return next(self.it)

        def close(self):
            closed.append(True)

    class Request:
        headers = {}

        async def is_disconnected(self):
            return True

    monkeypatch_events = Run()
    original = server.run
    server.run = lambda input: monkeypatch_events
    try:
        response = server.agent_endpoint(run_input(), Request())
        body = response.body_iterator

        async def drain():
            return [frame async for frame in body]

        frames = asyncio.run(drain())
    finally:
        server.run = original
    assert frames == [] and closed == [True]


def test_node_suite_passes():
    node, npm = shutil.which("node"), shutil.which("npm")
    if node is None:
        pytest.skip("node is not installed")
    package = json.loads((STEP / "package.json").read_text(encoding="utf-8"))
    needs_install = package.get("dependencies") or package.get("devDependencies")
    if needs_install and not (STEP / "node_modules").exists():
        if npm is None:
            pytest.skip("npm is not installed")
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True, capture_output=True)
    result = subprocess.run([node, "--test"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
