"""Offline tests for step 02. The model is a scripted reply fed in chunks; the
SDK's parsers, the generate loop, the SSE endpoint, the action round trip and
the page's state module are tested against it. Tests that need the
a2ui-agent-sdk package skip when it is not installed."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import envelope  # noqa: E402

HERE = Path(__file__).parent
CATALOG = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

GOOD_REPLY = """<a2ui-json>{"version": "v0.9", "createSurface": {"surfaceId": "main", "catalogId": "%s"}}</a2ui-json>
<a2ui-json>{"version": "v0.9", "updateComponents": {"surfaceId": "main", "components": [
  {"id": "root", "component": "Card", "child": "col"},
  {"id": "col", "component": "Column", "children": ["email", "send", "status"]},
  {"id": "email", "component": "TextField", "label": "Email", "value": {"path": "/form/email"}},
  {"id": "send", "component": "Button", "child": "send_label", "variant": "primary",
   "action": {"event": {"name": "submit", "context": {"email": {"path": "/form/email"}}}}},
  {"id": "send_label", "component": "Text", "text": "Send"},
  {"id": "status", "component": "Text", "text": {"path": "/form/status"}, "variant": "caption"}
]}}</a2ui-json>
<a2ui-json>{"version": "v0.9", "updateDataModel": {"surfaceId": "main", "path": "/form", "value": {"email": "", "status": "",}}}</a2ui-json>
""" % CATALOG  # the trailing comma in the last block is on purpose: the SDK repairs it

CLEAN_REPLY = GOOD_REPLY.replace('"status": "",}', '"status": ""}')
BAD_REPLY = GOOD_REPLY.replace('"component": "TextField"', '"component": "TextInput"')


def chunks(text, size=25):
    return [text[i:i + size] for i in range(0, len(text), size)]


@pytest.fixture
def sdk():
    return pytest.importorskip("a2ui", reason="pip install a2ui-agent-sdk")


@pytest.fixture
def scripted(sdk, monkeypatch):
    """server with stream_model replaced by a queue of scripted replies."""
    import server

    replies = []
    monkeypatch.setattr(server, "stream_model", lambda messages: iter(chunks(replies.pop(0))))
    monkeypatch.setattr(server, "STORE", envelope.SurfaceStore())
    server.llm.last_usage = None
    return server, replies


# ------------------------------------------------------------ the SDK pieces


def test_system_prompt_comes_from_the_catalog(sdk):
    import prompt

    text = prompt.system_prompt()
    assert prompt.ROLE.splitlines()[0] in text
    assert "<a2ui-json>" in text and "---BEGIN A2UI JSON SCHEMA---" in text
    assert '"TextField"' in text and '"ChoicePicker"' in text
    assert prompt.catalog_id() == CATALOG
    assert len(text) > 30_000  # the whole schema rides along; the price of prompt-first


def test_parse_reply_repairs_and_validates(sdk):
    import prompt

    messages, prose = prompt.parse_reply("Here is the form.\n" + GOOD_REPLY + "\nDone.")
    assert [envelope.message_type(m) for m in messages] == ["createSurface", "updateComponents", "updateDataModel"]
    assert messages[2]["updateDataModel"]["value"] == {"email": "", "status": ""}  # trailing comma gone
    assert prose == ["Here is the form.", "Done."]
    assert all(envelope.validate(m) is None for m in messages)
    with pytest.raises(ValueError, match="TextInput"):
        prompt.parse_reply(BAD_REPLY)
    with pytest.raises(ValueError):
        prompt.parse_reply("no blocks here")


def test_stream_parser_yields_placeholders_before_children(sdk):
    import prompt

    parser = prompt.stream_parser()
    seen = []
    for chunk in chunks(CLEAN_REPLY):
        for part in parser.process_chunk(chunk):
            seen.extend(part.a2ui_json or [])
    kinds = [envelope.message_type(m) for m in seen]
    assert kinds[0] == "createSurface"
    first = next(m for m in seen if envelope.message_type(m) == "updateComponents")
    ids = [c["id"] for c in first["updateComponents"]["components"]]
    assert "root" in ids and any(i.startswith("loading_") for i in ids)  # a Row stands in for a child not yet seen
    last = [m for m in seen if envelope.message_type(m) == "updateComponents"][-1]
    assert not any(c["id"].startswith("loading_") for c in last["updateComponents"]["components"])


# ------------------------------------------------------------ the generate loop


def test_generate_streams_then_sends_the_validated_final_messages(scripted):
    server, replies = scripted
    replies.append(CLEAN_REPLY)
    events = list(server.generate("a form"))
    messages = [payload for event, payload in events if event is None]
    kinds = [envelope.message_type(m) for m in messages]
    assert kinds.count("createSurface") == 1
    assert kinds.count("updateComponents") > 2  # progressive ones, then the final one
    assert kinds[-2:] == ["updateComponents", "updateDataModel"]  # the final pass
    assert not any(c["id"].startswith("loading_") for c in messages[-2]["updateComponents"]["components"])
    notes = [payload for event, payload in events if event == "note"]
    assert notes[-1]["attempt"] == 1 and notes[-1]["reply_chars"] == len(CLEAN_REPLY)
    mirror = server.STORE.surfaces["main"]
    assert mirror.tree()["component"] == "Card"
    assert envelope.pointer_get(mirror.data, "/form/status") == ""


def test_stream_parser_gives_up_on_a_trailing_comma_but_the_final_pass_repairs_it(scripted):
    server, replies = scripted
    replies.append(GOOD_REPLY)  # has the trailing comma
    events = list(server.generate("a form"))
    notes = [payload for event, payload in events if event == "note"]
    assert any("streaming_stopped" in n for n in notes)
    kinds = [envelope.message_type(payload) for event, payload in events if event is None]
    assert kinds[-2:] == ["updateComponents", "updateDataModel"]
    assert envelope.pointer_get(server.STORE.surfaces["main"].data, "/form/email") == ""


def test_generate_sends_the_error_back_and_retries_once(scripted):
    server, replies = scripted
    replies.extend([BAD_REPLY, GOOD_REPLY])
    events = list(server.generate("a form"))
    notes = [payload for event, payload in events if event == "note"]
    failure = next(n for n in notes if "error" in n)
    assert failure["attempt"] == 1 and "TextInput" in failure["error"]
    kinds = [envelope.message_type(payload) for event, payload in events if event is None]
    assert "deleteSurface" in kinds  # the partial surface from attempt 1 is withdrawn
    assert kinds.index("deleteSurface") < len(kinds) - kinds[::-1].index("createSurface") - 1
    assert notes[-1]["attempt"] == 2
    assert server.STORE.surfaces["main"].tree()["component"] == "Card"


def test_generate_gives_up_after_two_bad_replies(scripted):
    server, replies = scripted
    replies.extend([BAD_REPLY, BAD_REPLY])
    events = list(server.generate("a form"))
    assert events[-1][1]["error"].startswith("gave up")
    assert server.STORE.surfaces == {}


# ------------------------------------------------------------ the endpoints


def read_sse(text):
    frames = [f for f in text.split("\n\n") if f.strip()]
    out = []
    for frame in frames:
        event = next((l[7:] for l in frame.splitlines() if l.startswith("event: ")), None)
        data = json.loads(next(l[6:] for l in frame.splitlines() if l.startswith("data: ")))
        out.append((event, data))
    return out


def test_generate_endpoint_and_action_round_trip(scripted):
    from fastapi.testclient import TestClient

    server, replies = scripted
    replies.append(GOOD_REPLY)
    client = TestClient(server.app)
    events = read_sse(client.post("/generate", json={"prompt": "a form"}).text)
    assert events[-1][0] == "done"
    assert [e for e, _ in events].count(None) >= 3
    action = {"name": "submit", "surfaceId": "main", "sourceComponentId": "send", "timestamp": "t",
              "context": {"email": "ada@example.com"}}
    answer = client.post("/action", json=action).json()
    assert len(answer) == 1 and envelope.validate(answer[0]) is None
    body = answer[0]["updateDataModel"]
    assert body["path"] == "/form/status"  # found through the server's mirror of the surface
    assert "ada@example.com" in body["value"] and "'submit'" in body["value"]
    assert envelope.pointer_get(server.STORE.surfaces["main"].data, "/form/status") == body["value"]
    assert client.get("/").status_code == 200


def test_a_second_generation_deletes_the_first_surface_first(scripted):
    """Generate twice on one page: the official renderer refuses a repeated createSurface,
    so the server withdraws the old surface before the new one, and the mirror starts clean."""
    server, replies = scripted
    replies.extend([CLEAN_REPLY, CLEAN_REPLY.replace('"id": "email"', '"id": "mail"').replace('["email",', '["mail",')])
    list(server.generate("a form"))
    assert "email" in server.STORE.surfaces["main"].components
    kinds = [envelope.message_type(payload) for event, payload in server.generate("another form") if event is None]
    assert kinds[:2] == ["deleteSurface", "createSurface"]
    components = server.STORE.surfaces["main"].components
    assert "mail" in components and "email" not in components  # no stale components merged in


def test_bad_bodies_are_422_not_500(scripted):
    from fastapi.testclient import TestClient

    server, _ = scripted
    client = TestClient(server.app)
    assert client.post("/generate", json={"prompt": 42}).status_code == 422
    assert client.post("/generate", json={}).status_code == 422
    assert client.post("/action", json={"surfaceId": "main"}).status_code == 422
    assert client.post("/action", content=b"not json", headers={"content-type": "application/json"}).status_code == 422


def test_action_for_an_unknown_surface_falls_back_to_slash_status(scripted):
    server, _ = scripted
    answer = server.answer_action({"name": "x", "surfaceId": "ghost", "context": {}})
    assert answer[0]["updateDataModel"]["path"] == "/status"


# ------------------------------------------------------------ envelope, unchanged from step 01


def test_envelope_validate_and_surface_state():
    pytest.importorskip("jsonschema")
    assert envelope.validate(envelope.create_surface("s")) is None
    problem = envelope.validate(envelope.update_components("s", [{"id": "root", "component": "TextField", "value": {"path": "/x"}}]))
    assert problem["message"] == "'label' is a required property"
    store = envelope.SurfaceStore()
    store.apply(envelope.create_surface("s"))
    surface = store.apply(envelope.update_components("s", [{"id": "root", "component": "Column", "children": ["later"]}]))
    assert surface.missing_ids() == ["later"]
    surface.apply(envelope.update_data_model("s", "/form/email", "a@b.c"))
    assert surface.resolve({"path": "/form/email"}) == "a@b.c"
    # what a model can write: a component inside itself, and a repeated createSurface
    surface.apply(envelope.update_components("s", [{"id": "later", "component": "Card", "child": "root"}]))
    assert surface.tree()["children"][0]["children"][0] == {"id": "root", "cycle": True}
    assert store.apply(envelope.create_surface("s")).components == {}


# ------------------------------------------------------------ the page's state module


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_node_surface_module():
    result = subprocess.run(["node", "--test", "surface.test.mjs"], cwd=HERE, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
