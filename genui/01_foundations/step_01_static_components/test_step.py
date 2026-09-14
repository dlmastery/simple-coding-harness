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


def test_first_call_is_emitted_as_soon_as_the_second_starts(fake):
    fake(SCRIPT)
    stream = llm.stream_chat([], tools=catalog.TOOL_SCHEMAS)
    first = next(stream)  # arrives before the chart's arguments are read
    assert first["type"] == "tool_call" and first["name"] == "show_metric"


def test_text_deltas_come_through(fake):
    fake([text_chunk("hel"), text_chunk("lo"), usage_chunk()])
    events = list(llm.stream_chat([]))
    assert [e.get("text") for e in events[:2]] == ["hel", "lo"]
    assert events[-1]["type"] == "usage"


def test_env_file_is_never_printed_and_key_is_mapped():
    assert "API_KEY" in llm.__doc__ and "never printed" in llm.__doc__
    assert llm.BASE_URL.startswith("http")


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
