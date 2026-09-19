"""Step 01 tests. Offline: the model is a fake stream of scripted chunks."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import catalog  # noqa: E402
import llm  # noqa: E402
import server  # noqa: E402


# ------------------------------------------------------------ a fake stream


def text_chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text, tool_calls=None))], usage=None)


def call_chunk(index, cid=None, name=None, arguments=None):
    piece = SimpleNamespace(index=index, id=cid, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]))], usage=None)


def usage_chunk(prompt=120, completion=60):
    return SimpleNamespace(choices=[], usage=SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion))


class FakeClient:
    """Stands in for llm.client: records the request, yields the scripted chunks."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        return iter(self.chunks)


SCRIPT = [
    call_chunk(0, cid="c1", name="show_metric", arguments='{"title": "Cups sold", '),
    call_chunk(0, arguments='"value": "412", "delta": "+12%"}'),
    call_chunk(1, cid="c2", name="show_chart", arguments='{"kind": "bar", "labels": ["Mon", "Tue"], '),
    call_chunk(1, arguments='"values": [40, 52]}'),
    usage_chunk(),
]


@pytest.fixture
def fake(monkeypatch):
    def install(chunks):
        client = FakeClient(chunks)
        monkeypatch.setattr(llm, "client", client)
        return client
    return install


# ------------------------------------------------------------------- llm.py


def test_stream_chat_assembles_tool_calls_in_order(fake):
    client = fake(SCRIPT)
    events = list(llm.stream_chat([{"role": "user", "content": "hi"}], tools=catalog.TOOL_SCHEMAS))
    assert [e["type"] for e in events] == ["tool_call", "tool_call", "usage"]
    assert events[0]["name"] == "show_metric"
    assert json.loads(events[0]["arguments"]) == {"title": "Cups sold", "value": "412", "delta": "+12%"}
    assert events[1]["id"] == "c2"
    assert events[-1]["completion_tokens"] == 60
    assert client.requests[0]["stream"] is True
    assert [t["function"]["name"] for t in client.requests[0]["tools"]] == ["show_metric", "show_table", "show_chart"]


def test_interleaved_pieces_and_missing_indexes_still_assemble(fake):
    # two calls streamed in alternation (some providers do this), then a piece with no index
    fake([
        call_chunk(0, cid="c1", name="show_metric", arguments='{"title": "a", '),
        call_chunk(1, cid="c2", name="show_chart", arguments='{"kind": "bar", '),
        call_chunk(0, arguments='"value": "1", "delta": "+1"}'),
        call_chunk(None, cid="c2", arguments='"labels": [], "values": []}'),
        usage_chunk(),
    ])
    events = list(llm.stream_chat([], tools=catalog.TOOL_SCHEMAS))
    calls = [e for e in events if e["type"] == "tool_call"]
    assert [c["name"] for c in calls] == ["show_metric", "show_chart"]
    assert json.loads(calls[0]["arguments"]) == {"title": "a", "value": "1", "delta": "+1"}
    assert json.loads(calls[1]["arguments"]) == {"kind": "bar", "labels": [], "values": []}


def test_text_deltas_come_through(fake):
    fake([text_chunk("hel"), text_chunk("lo"), usage_chunk()])
    events = list(llm.stream_chat([]))
    assert [e.get("text") for e in events[:2]] == ["hel", "lo"]
    assert events[-1]["type"] == "usage"


def test_env_file_fills_the_environment_and_openai_api_key_is_an_alias(monkeypatch, tmp_path):
    import importlib

    (tmp_path / ".simple-harness").mkdir()
    lines = ["# comment", "OPENAI_API_KEY=from-file", "MODEL=m-file"]
    (tmp_path / ".simple-harness" / "env").write_text("\n".join(lines), encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for key in ("API_KEY", "OPENAI_API_KEY", "MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MODEL", "m-env")  # the environment wins over the file
    fresh = importlib.reload(llm)
    try:
        assert fresh.API_KEY == "from-file" and fresh.MODEL == "m-env"
        assert fresh.BASE_URL.startswith("http")
    finally:
        importlib.reload(llm)


# --------------------------------------------------------------- catalog.py


def test_every_tool_schema_is_strict_and_closed():
    for schema in catalog.TOOL_SCHEMAS:
        function = schema["function"]
        assert function["strict"] is True
        assert function["parameters"]["additionalProperties"] is False
        assert set(function["parameters"]["required"]) == set(function["parameters"]["properties"])


def test_message_from_call_maps_names_and_rejects_bad_input():
    assert catalog.message_from_call("show_metric", '{"title": "a", "value": "1", "delta": "+1"}') == {
        "component": "Metric", "props": {"title": "a", "value": "1", "delta": "+1"},
    }
    assert catalog.message_from_call("show_table", '{"columns": ["x"], "rows": [["1"]]}')["component"] == "Table"
    assert catalog.message_from_call("show_gauge", "{}") is None
    assert catalog.message_from_call("show_metric", "{not json") is None
    assert catalog.message_from_call("show_metric", "[1, 2]") is None


# ---------------------------------------------------------------- server.py


def frames(text):
    """The JSON messages of an SSE body."""
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def test_run_streams_one_message_per_component_then_done(fake):
    fake(SCRIPT)
    client = TestClient(server.app)
    response = client.post("/api/run", json={"prompt": "lemonade"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    messages = frames(response.text)
    assert [m.get("component") for m in messages] == ["Metric", "Chart", None]
    assert messages[0]["props"]["title"] == "Cups sold"
    assert messages[-1] == {"done": True, "usage": {"prompt_tokens": 120, "completion_tokens": 60}}


def test_prose_becomes_a_note_not_a_component(fake):
    fake([text_chunk("Sure, "), text_chunk("here."), usage_chunk()])
    client = TestClient(server.app)
    messages = frames(client.post("/api/run", json={"prompt": "x"}).text)
    assert messages[:2] == [{"note": "Sure, "}, {"note": "here."}]
    assert messages[-1]["done"] is True


def test_a_model_failure_ends_the_stream_with_an_error_frame(monkeypatch):
    def boom(**request):
        raise RuntimeError("model down")

    monkeypatch.setattr(llm, "client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom))))
    response = TestClient(server.app).post("/api/run", json={"prompt": "x"})
    assert response.status_code == 200  # the headers were already out; the error is the last frame
    messages = frames(response.text)
    assert messages[-1] == {"done": True, "error": "RuntimeError: model down"}


def test_no_api_key_is_an_error_frame_not_a_cut_stream(monkeypatch):
    monkeypatch.setattr(llm, "client", None)
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x"}).text)[-1]
    assert done["done"] is True and "no API key" in done["error"]


def test_system_prompt_forbids_prose(fake):
    client = fake(SCRIPT)
    TestClient(server.app).post("/api/run", json={"prompt": "x"})
    system = client.requests[0]["messages"][0]
    assert system["role"] == "system" and "show_" in system["content"]


def test_page_is_served():
    client = TestClient(server.app)
    assert "<script type=\"module\" src=\"app.js\">" in client.get("/").text
    assert "export function render" in client.get("/render.mjs").text


# ------------------------------------------------------------- node tests


def test_node_suite_passes():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    result = subprocess.run(
        [node, "--test", "tests/render.test.mjs"], cwd=HERE, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
