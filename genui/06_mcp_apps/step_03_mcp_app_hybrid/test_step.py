"""Step 03 - offline tests: the server in process, the wire in process, two fake models.

No network. The server's own model call (the generated region) is a fake
whose reply is a scripted HTML document with a scripted usage. The host's
model call is a fake too, as in step 01. The streamable HTTP round trip
runs through httpx's ASGI transport. The node tests cover the bridge, the
browser client, the view's catalog and the inner boundary.
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
import report  # noqa: E402
import server  # noqa: E402

UI_EXTENSION = "io.modelcontextprotocol/ui"

REGION = """<!doctype html>
<html><head><style>body{font:12px system-ui}</style></head>
<body><input type="range" id="price" min="0.5" max="3" step="0.1" value="1.5"><span id="out"></span>
<script>price.oninput = () => parent.postMessage({type: "event", name: "price_changed", payload: {price: Number(price.value)}}, "*");</script>
</body></html>"""


def run(coro):
    return asyncio.run(coro)


# --- two fake models -------------------------------------------------------------


class FakeCompletions:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []

    def create(self, **request):
        self.requests.append(request)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def fake_client(*replies):
    completions = FakeCompletions(replies)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def text_reply(content, prompt_tokens=370, completion_tokens=480):
    """What the server's model call returns: a plain message with usage."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=None))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


def tool_call_reply(name, arguments):
    """What the host's model call returns: a tool call."""
    call = SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[call]))], usage=None)


@pytest.fixture
def region_model(monkeypatch):
    client, completions = fake_client(text_reply("```html\n" + REGION + "\n```"))
    monkeypatch.setattr(llm, "client", client)
    return completions


# --- the server, in process ----------------------------------------------------------


def test_tool_points_at_a_ui_resource():
    tools = run(server.server.list_tools())
    tool = next(t for t in tools if t.name == "lemonade_report")
    assert tool.meta == {"ui": {"resourceUri": server.VIEW_URI}}
    assert server.VIEW_URI.startswith("ui://")
    assert tool.inputSchema["properties"]["days"]["type"] == "integer"
    assert tool.inputSchema["properties"]["focus"]["type"] == "string"


def test_resource_is_one_self_contained_document():
    contents = run(server.server.read_resource(server.VIEW_URI))
    assert len(contents) == 1
    assert contents[0].mime_type == "text/html;profile=mcp-app"
    html = contents[0].content
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "ui/initialize" in html and "ui/notifications/tool-result" in html
    # the modules are inlined: no import, no export, no module script, no src
    assert 'type="module"' not in html and "import {" not in html and "export " not in html and "<script src" not in html
    assert html.count("<script>") == 1
    assert "function renderComponents" in html and "function isEvent" in html and "function sandboxed" in html
    listing = run(server.server.list_resources())
    entry = next(r for r in listing if str(r.uri) == server.VIEW_URI)
    assert entry.meta["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}  # unchanged from step 01


def test_bundle_inlines_each_module_once(tmp_path):
    (tmp_path / "a.mjs").write_text('import { b } from "./b.mjs";\nexport const a = b + 1;\n', encoding="utf-8")
    (tmp_path / "b.mjs").write_text("export const b = 1;\n", encoding="utf-8")
    html = '<html><head></head><body><script type="module">\n  import { a } from "./a.mjs";\n  import { b } from "./b.mjs";\n  console.log(a, b);\n</script></body></html>'
    out = server.bundle(html, tmp_path)
    assert out.count("const b = 1;") == 1
    assert out.count("const a = b + 1;") == 1
    assert "import" not in out and "export" not in out
    assert out.startswith("<html><head></head><body><script>")


def test_tool_result_has_a_static_spec_and_a_generated_region(region_model):
    result = run(server.server.call_tool("lemonade_report", {"days": 3, "focus": "a what-if price slider"}))
    assert result.isError is False
    text = result.content[0].text
    assert text.startswith("Lemonade stand, last 3 days: 97 cups, $145.50 revenue, best day Tue.")
    assert text.endswith("The interface also shows a what-if price slider (model).")
    spec = result.structuredContent
    assert spec["days"] == 3 and spec["focus"] == "a what-if price slider"
    assert [c["component"] for c in spec["components"]] == ["Metric", "Metric", "Metric", "BarChart", "Table", "Text"]
    generated = spec["generated"]
    assert generated["source"] == "model"
    assert generated["html"] == REGION  # the fence came off
    assert generated["bytes"] == len(REGION.encode("utf-8"))
    assert generated["usage"] == {"prompt_tokens": 370, "completion_tokens": 480}
    assert generated["note"] == ""


def test_the_server_prompt_carries_the_contract_and_the_data(region_model):
    run(server.server.call_tool("lemonade_report", {"days": 2, "focus": "a temperature gauge"}))
    request = region_model.requests[0]
    assert "tools" not in request  # a plain generation, no tools
    system, user = request["messages"]
    assert system["role"] == "system" and "a temperature gauge" in system["content"]
    assert '<input type="range">' in system["content"] and "parent.postMessage" in system["content"]
    assert user["role"] == "user"
    assert "Mon, 28, 37, 55.50" in user["content"] and "Tue, 30, 51, 76.50" in user["content"]
    assert "$1.50 per cup" in user["content"]


def test_no_key_on_the_server_gives_the_fallback_region(monkeypatch):
    monkeypatch.setattr(llm, "client", None)
    result = run(server.server.call_tool("lemonade_report", {"days": 5}))
    generated = result.structuredContent["generated"]
    assert generated["source"] == "fallback" and generated["usage"] is None
    assert generated["note"] == "no API key on the server"
    assert 'input type="range"' in generated["html"] and "parent.postMessage" in generated["html"]
    assert "const baseCups = 132, basePrice = 1.5;" in generated["html"]
    assert result.content[0].text.endswith("(fallback).")


def test_a_failed_model_call_falls_back_with_a_note(monkeypatch):
    client, _ = fake_client(RuntimeError("rate limited"))
    monkeypatch.setattr(llm, "client", client)
    generated = run(server.server.call_tool("lemonade_report", {"days": 1})).structuredContent["generated"]
    assert generated["source"] == "fallback"
    assert generated["note"] == "model call failed: rate limited"


def test_components_are_exact_for_the_same_rows():
    rows = data.sales(3)
    components = report.components_for(3, rows)
    assert components[0] == {"component": "Metric", "props": {"title": "cups sold", "value": "97", "delta": "32.3 per day"}}
    assert components[1]["props"] == {"title": "revenue", "value": "$145.50", "delta": "$1.50 per cup"}
    assert components[2]["props"] == {"title": "best day", "value": "Tue", "delta": "51 cups at 30 C"}
    assert components[3] == {"component": "BarChart", "props": {"labels": ["Mon", "Tue", "Wed"], "values": [37, 51, 9]}}
    assert components[4]["props"]["columns"] == ["day", "temp", "cups", "revenue"]
    assert components[4]["props"]["rows"][0] == ["Mon", "28 C", "37", "$55.50"]
    assert components[5]["component"] == "Text"
    assert len(json.dumps(components)) < 900  # the declarative half is small


def test_days_are_clamped(monkeypatch):
    monkeypatch.setattr(llm, "client", None)
    assert run(server.server.call_tool("lemonade_report", {"days": 400})).structuredContent["days"] == 28
    assert run(server.server.call_tool("lemonade_report", {"days": 0})).structuredContent["days"] == 1


# --- the wire, in process: a host that declares the extension ------------------------


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
        http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8767")

        async with server.server.session_manager.run():
            async with streamable_http_client("http://127.0.0.1:8767/mcp", http_client=http) as (read, write, session_id):
                async with UiSession(read, write) as session:
                    init = await session.initialize()
                    self.captured["server"] = init.serverInfo.name
                    self.captured["session_id"] = session_id()
                    self.captured["tools"] = (await session.list_tools()).tools
                    self.captured["result"] = await session.call_tool("lemonade_report", {"days": 2})
                    self.captured["resource"] = await session.read_resource(server.VIEW_URI)


@pytest.fixture(scope="module")
def wire():
    session = HostSession()
    with pytest.MonkeyPatch.context() as patch:
        client, _ = fake_client(text_reply(REGION, 300, 200))
        patch.setattr(llm, "client", client)
        run(session())
    return session.captured


def test_wire_handshake_and_tool_metadata(wire):
    assert wire["server"] == "lemonade"
    assert wire["session_id"]  # the mcp-session-id header the browser client keeps
    tool = wire["tools"][0]
    assert tool.name == "lemonade_report"
    assert tool.model_dump(by_alias=True)["_meta"] == {"ui": {"resourceUri": server.VIEW_URI}}


def test_wire_tool_result_and_resource(wire):
    result = wire["result"]
    assert result.structuredContent["days"] == 2
    assert result.structuredContent["generated"] == {"html": REGION, "source": "model", "usage": {"prompt_tokens": 300, "completion_tokens": 200}, "bytes": len(REGION.encode()), "note": ""}
    assert result.content[0].text.startswith("Lemonade stand, last 2 days")
    content = wire["resource"].contents[0]
    assert content.mimeType == server.MIME_TYPE
    assert content.text.lstrip().lower().startswith("<!doctype html>")
    assert "function renderComponents" in content.text  # the bundled resource crossed the wire
    assert content.model_dump(by_alias=True)["_meta"]["ui"]["prefersBorder"] is True


# --- the host's model turn, with a fake model ----------------------------------------


def test_chat_turn_returns_the_models_tool_call(monkeypatch):
    client, completions = fake_client(tool_call_reply("lemonade_report", {"days": 5, "focus": "a what-if price slider"}))
    monkeypatch.setattr(llm, "client", client)
    tools = [{"type": "function", "function": {"name": "lemonade_report", "description": "d", "parameters": {"type": "object"}}}]
    reply = host.chat_turn([{"role": "user", "content": "show the report"}], tools)
    assert reply == {"content": None, "tool_calls": [{"id": "call_1", "name": "lemonade_report", "arguments": '{"days": 5, "focus": "a what-if price slider"}'}]}
    request = completions.requests[0]
    assert [m["role"] for m in request["messages"]] == ["system", "user"]  # no context: one system message
    assert request["tools"] == tools


def test_chat_turn_puts_the_apps_context_in_front(monkeypatch):
    client, completions = fake_client(text_reply("At $2.40 you would sell 96 cups."))
    monkeypatch.setattr(llm, "client", client)
    messages = [{"role": "user", "content": "what did I just set?"}]
    reply = host.chat_turn(messages, [], context="In the report's interactive region the user set priceChange: {\"price\": 2.4}.")
    assert reply == {"content": "At $2.40 you would sell 96 cups.", "tool_calls": []}
    system = completions.requests[0]["messages"][:2]
    assert [m["role"] for m in system] == ["system", "system"]
    assert system[1]["content"].startswith("Context from the interface: In the report's interactive region")
    assert "tools" not in completions.requests[0]


def test_chat_endpoint(monkeypatch):
    from fastapi.testclient import TestClient

    client, completions = fake_client(text_reply("hi"))
    monkeypatch.setattr(llm, "client", client)
    response = TestClient(host.app).post("/chat", json={"messages": [{"role": "user", "content": "hello"}], "tools": [], "context": "the slider is at 2.4"})
    assert response.status_code == 200
    assert response.json() == {"content": "hi", "tool_calls": []}
    assert completions.requests[0]["messages"][1] == {"role": "system", "content": "Context from the interface: the slider is at 2.4"}
    page = TestClient(host.app).get("/")
    assert page.status_code == 200 and "Minimal MCP Apps host" in page.text and "context: state.modelContext" in page.text
    module = TestClient(host.app).get("/bridge.mjs")
    assert module.status_code == 200 and "export class HostBridge" in module.text


def test_no_key_is_a_clear_error(monkeypatch):
    monkeypatch.setattr(llm, "client", None)
    with pytest.raises(RuntimeError, match="no API key"):
        llm.complete([{"role": "user", "content": "x"}])
    with pytest.raises(RuntimeError, match="no API key"):
        llm.generate([{"role": "user", "content": "x"}])


# --- the view: two listeners, one accepted shape ----------------------------------------


def test_the_view_accepts_only_one_shape_from_the_inner_frame():
    view = server.VIEW_FILE.read_text(encoding="utf-8")
    assert "event.source === window.parent" in view
    assert "event.source === generated.contentWindow && isEvent(event.data)" in view
    assert 'sandbox="allow-scripts"' not in view  # the inner sandbox attribute is set by mount(), in sandbox.mjs
    assert "ui/update-model-context" in view


# --- the browser side, through node ------------------------------------------------------


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_node_bridge_client_catalog_and_sandbox():
    result = subprocess.run(["node", "--test", "bridge.test.mjs", "catalog.test.mjs"], cwd=STEP, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
