"""Step 01 - offline tests: the server in process, the wire in process, a fake model.

No network. The streamable HTTP round trip runs through httpx's ASGI
transport, so the real `mcp` client talks to the real server without a
socket. The model is a fake whose reply is scripted. The node tests for
the bridge and the browser client run through `node --test` when node is
on PATH.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")
STEP = Path(__file__).parent
sys.path.insert(0, str(STEP))

import data  # noqa: E402
import host  # noqa: E402
import llm  # noqa: E402
import server  # noqa: E402

UI_EXTENSION = "io.modelcontextprotocol/ui"


def run(coro):
    return asyncio.run(coro)


# --- the server, in process --------------------------------------------------


def test_tool_points_at_a_ui_resource():
    tools = run(server.server.list_tools())
    tool = next(t for t in tools if t.name == "lemonade_dashboard")
    assert tool.meta == {"ui": {"resourceUri": server.VIEW_URI}}
    assert server.VIEW_URI.startswith("ui://")
    assert tool.inputSchema["properties"]["days"]["type"] == "integer"


def test_resource_is_an_mcp_app_document():
    contents = run(server.server.read_resource(server.VIEW_URI))
    assert len(contents) == 1
    assert contents[0].mime_type == "text/html;profile=mcp-app"
    html = contents[0].content
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "ui/initialize" in html and "ui/notifications/initialized" in html
    assert "ui/notifications/tool-result" in html
    listing = run(server.server.list_resources())
    entry = next(r for r in listing if str(r.uri) == server.VIEW_URI)
    assert entry.meta["ui"]["prefersBorder"] is True
    assert entry.meta["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}


def test_tool_result_carries_text_for_the_model_and_data_for_the_view():
    result = run(server.server.call_tool("lemonade_dashboard", {"days": 3}))
    assert result.content[0].text.startswith("Lemonade stand, last 3 days: 97 cups, $145.50 revenue, best day Tue.")
    assert result.structuredContent["days"] == 3
    assert [row["day"] for row in result.structuredContent["rows"]] == ["Mon", "Tue", "Wed"]
    assert result.structuredContent["summary"] == {"total_cups": 97, "total_revenue": 145.5, "best_day": "Tue"}
    assert result.isError is False


def test_days_are_clamped():
    result = run(server.server.call_tool("lemonade_dashboard", {"days": 400}))
    assert result.structuredContent["days"] == 28
    result = run(server.server.call_tool("lemonade_dashboard", {"days": 0}))
    assert result.structuredContent["days"] == 1


def test_data_is_deterministic():
    assert data.sales(7) == data.sales(7)
    assert data.summary(data.sales(7)) == {"total_cups": 172, "total_revenue": 258.0, "best_day": "Tue"}
    assert data.as_text(1, data.sales(1)).splitlines() == [
        "Lemonade stand, last 1 days: 37 cups, $55.50 revenue, best day Mon.",
        "Mon: 37 cups at 28 C ($55.50)",
    ]


# --- the wire, in process: a host that declares the extension ------------------


class HostSession:
    """What the browser client does, with the real Python client: initialize with the ui extension."""

    def __init__(self):
        self.captured = {}

    async def __call__(self):
        import httpx
        from mcp import ClientSession, types
        from mcp.client.streamable_http import streamable_http_client  # mcp >= 1.26

        app = server.http_app()

        class UiSession(ClientSession):
            async def initialize(self):
                caps = types.ClientCapabilities(extensions={UI_EXTENSION: {"mimeTypes": [server.MIME_TYPE]}})
                params = types.InitializeRequestParams(protocolVersion=types.LATEST_PROTOCOL_VERSION, capabilities=caps, clientInfo=self._client_info)
                result = await self.send_request(types.ClientRequest(types.InitializeRequest(params=params)), types.InitializeResult)
                await self.send_notification(types.ClientNotification(types.InitializedNotification()))
                return result

        # no socket: httpx calls the ASGI app directly; the Host header must still be a local one
        http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765")

        async with server.server.session_manager.run():
            async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=http) as (read, write, session_id):
                async with UiSession(read, write) as session:
                    init = await session.initialize()
                    self.captured["server"] = init.serverInfo.name
                    self.captured["session_id"] = session_id()
                    self.captured["tools"] = (await session.list_tools()).tools
                    self.captured["result"] = await session.call_tool("lemonade_dashboard", {"days": 2})
                    self.captured["resource"] = await session.read_resource(server.VIEW_URI)


@pytest.fixture(scope="module")
def wire():
    session = HostSession()
    run(session())
    return session.captured


def test_wire_handshake_and_tool_metadata(wire):
    assert wire["server"] == "lemonade"
    assert wire["session_id"]  # the mcp-session-id header the browser client keeps
    tool = wire["tools"][0]
    assert tool.name == "lemonade_dashboard"
    assert tool.model_dump(by_alias=True)["_meta"] == {"ui": {"resourceUri": server.VIEW_URI}}


def test_wire_tool_result_and_resource(wire):
    result = wire["result"]
    assert result.structuredContent["days"] == 2
    assert result.content[0].text.startswith("Lemonade stand, last 2 days")
    content = wire["resource"].contents[0]
    assert content.mimeType == server.MIME_TYPE
    assert content.text.lstrip().lower().startswith("<!doctype html>")
    assert content.model_dump(by_alias=True)["_meta"]["ui"]["prefersBorder"] is True


# --- the host's model turn, with a fake model ------------------------------------


class FakeCompletions:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []

    def create(self, **request):
        self.requests.append(request)
        reply = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=reply)])


def fake_client(*replies):
    completions = FakeCompletions(replies)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def tool_call_reply(name, arguments):
    call = SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))
    return SimpleNamespace(content=None, tool_calls=[call])


def test_chat_turn_returns_the_models_tool_call(monkeypatch):
    client, completions = fake_client(tool_call_reply("lemonade_dashboard", {"days": 5}))
    monkeypatch.setattr(llm, "client", client)
    tools = [{"type": "function", "function": {"name": "lemonade_dashboard", "description": "d", "parameters": {"type": "object"}}}]
    reply = host.chat_turn([{"role": "user", "content": "show the dashboard"}], tools)
    assert reply == {"content": None, "tool_calls": [{"id": "call_1", "name": "lemonade_dashboard", "arguments": '{"days": 5}'}]}
    request = completions.requests[0]
    assert request["messages"][0]["role"] == "system"
    assert request["messages"][-1]["content"] == "show the dashboard"
    assert request["tools"] == tools


def test_chat_turn_returns_text_after_the_tool_result(monkeypatch):
    client, completions = fake_client(SimpleNamespace(content="Tuesday was the best day.", tool_calls=None))
    monkeypatch.setattr(llm, "client", client)
    messages = [
        {"role": "user", "content": "show the dashboard"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "lemonade_dashboard", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "Lemonade stand, last 7 days: 172 cups"},
    ]
    reply = host.chat_turn(messages, [])
    assert reply == {"content": "Tuesday was the best day.", "tool_calls": []}
    assert "tools" not in completions.requests[0]  # an empty list means no tools


def test_chat_endpoint(monkeypatch):
    from fastapi.testclient import TestClient

    client, _ = fake_client(SimpleNamespace(content="hi", tool_calls=None))
    monkeypatch.setattr(llm, "client", client)
    response = TestClient(host.app).post("/chat", json={"messages": [{"role": "user", "content": "hello"}], "tools": []})
    assert response.status_code == 200
    assert response.json() == {"content": "hi", "tool_calls": []}
    page = TestClient(host.app).get("/")
    assert page.status_code == 200 and "Minimal MCP Apps host" in page.text
    module = TestClient(host.app).get("/bridge.mjs")
    assert module.status_code == 200 and "export class HostBridge" in module.text


def test_no_key_is_a_clear_error(monkeypatch):
    monkeypatch.setattr(llm, "client", None)
    with pytest.raises(RuntimeError, match="no API key"):
        llm.complete([{"role": "user", "content": "x"}])


# --- the browser side, through node ---------------------------------------------


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_node_bridge_and_client():
    result = subprocess.run(["node", "--test", "--test-reporter=tap", "bridge.test.mjs"], cwd=STEP, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
