"""Offline tests for step 03. A scripted reply stands in for the model; the
AG-UI wire is decoded with the ag-ui-protocol event classes; the Node side
(the AG-UI client, @a2ui/web_core's processor, and the esbuild bundle) runs
through npm. Tests that need a2ui-agent-sdk or ag-ui-protocol skip when the
package is not installed."""

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

REPLY = """<a2ui-json>{"version": "v0.9", "createSurface": {"surfaceId": "main", "catalogId": "%s"}}</a2ui-json>
<a2ui-json>{"version": "v0.9", "updateComponents": {"surfaceId": "main", "components": [
  {"id": "root", "component": "Card", "child": "col"},
  {"id": "col", "component": "Column", "children": ["email", "send", "status"]},
  {"id": "email", "component": "TextField", "label": "Email", "value": {"path": "/form/email"}},
  {"id": "send", "component": "Button", "child": "send_label", "variant": "primary",
   "action": {"event": {"name": "submit", "context": {"email": {"path": "/form/email"}}}}},
  {"id": "send_label", "component": "Text", "text": "Send"},
  {"id": "status", "component": "Text", "text": {"path": "/form/status"}, "variant": "caption"}
]}}</a2ui-json>
Here is your form.
<a2ui-json>{"version": "v0.9", "updateDataModel": {"surfaceId": "main", "path": "/form", "value": {"email": "", "status": ""}}}</a2ui-json>
""" % CATALOG
BAD_REPLY = REPLY.replace('"component": "TextField"', '"component": "TextInput"')


def chunks(text, size=25):
    return [text[i:i + size] for i in range(0, len(text), size)]


def run_input(messages=(), forwarded_props=None, run_id="r1"):
    return {"threadId": "t1", "runId": run_id, "state": {}, "messages": list(messages), "tools": [], "context": [],
            "forwardedProps": forwarded_props or {}}


def decode(text):
    """The SSE body as a list of AG-UI event dicts (camelCase, as on the wire)."""
    return [json.loads(f[6:]) for f in text.split("\n\n") if f.startswith("data: ")]


@pytest.fixture
def scripted(monkeypatch):
    pytest.importorskip("a2ui", reason="pip install a2ui-agent-sdk")
    pytest.importorskip("ag_ui", reason="pip install ag-ui-protocol")
    import server

    replies = []
    monkeypatch.setattr(server, "stream_model", lambda messages: iter(chunks(replies.pop(0))))
    monkeypatch.setattr(server, "STORE", envelope.SurfaceStore())
    server.llm.last_usage = {"prompt_tokens": 1, "completion_tokens": 2}
    return server, replies


# ------------------------------------------------------------ the AG-UI wire


def test_a_run_is_run_started_steps_custom_a2ui_events_text_and_run_finished(scripted):
    from fastapi.testclient import TestClient

    server, replies = scripted
    replies.append(REPLY)
    client = TestClient(server.app)
    response = client.post("/agent", json=run_input([{"id": "m1", "role": "user", "content": "a form"}]))
    assert response.headers["content-type"].startswith("text/event-stream")
    events = decode(response.text)
    types = [e["type"] for e in events]
    assert types[0] == "RUN_STARTED" and events[0]["threadId"] == "t1" and events[0]["runId"] == "r1"
    assert types[1] == "STEP_STARTED" and events[1]["stepName"] == "attempt 1"
    assert types[-1] == "RUN_FINISHED" and events[-1]["result"]["usage"] == {"prompt_tokens": 1, "completion_tokens": 2}
    a2ui = [e["value"] for e in events if e["type"] == "CUSTOM" and e["name"] == "a2ui"]
    kinds = [envelope.message_type(m) for m in a2ui]
    assert kinds[0] == "createSurface" and a2ui[0]["createSurface"]["sendDataModel"] is True
    assert kinds[-2:] == ["updateComponents", "updateDataModel"]
    assert all(envelope.validate(m) is None for m in a2ui)
    assert "TEXT_MESSAGE_START" in types and "TEXT_MESSAGE_END" in types
    assert next(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT") == "Here is your form."
    assert types.index("STEP_FINISHED") < types.index("RUN_FINISHED")


def test_the_correction_attempt_is_a_second_step(scripted):
    from fastapi.testclient import TestClient

    server, replies = scripted
    replies.extend([BAD_REPLY, REPLY])
    events = decode(TestClient(server.app).post("/agent", json=run_input([{"id": "m1", "role": "user", "content": "a form"}])).text)
    steps = [e["stepName"] for e in events if e["type"] in ("STEP_STARTED", "STEP_FINISHED")]
    assert steps == ["attempt 1", "attempt 1", "attempt 2", "attempt 2"]
    notes = [e["value"] for e in events if e["type"] == "CUSTOM" and e["name"] == "a2ui.note"]
    assert any("TextInput" in n.get("error", "") for n in notes)
    kinds = [envelope.message_type(e["value"]) for e in events if e["type"] == "CUSTOM" and e["name"] == "a2ui"]
    assert "deleteSurface" in kinds and kinds.count("createSurface") == 2
    assert events[-1]["type"] == "RUN_FINISHED" and events[-1]["result"]["attempt"] == 2


def test_two_bad_replies_end_in_run_error(scripted):
    from fastapi.testclient import TestClient

    server, replies = scripted
    replies.extend([BAD_REPLY, BAD_REPLY])
    events = decode(TestClient(server.app).post("/agent", json=run_input([{"id": "m1", "role": "user", "content": "x"}])).text)
    assert events[-1]["type"] == "RUN_ERROR" and events[-1]["message"].startswith("gave up")
    assert server.STORE.surfaces == {}


# ------------------------------------------------------------ the action run


def test_an_action_run_answers_with_one_custom_a2ui_event(scripted):
    from fastapi.testclient import TestClient

    server, replies = scripted
    replies.append(REPLY)
    client = TestClient(server.app)
    client.post("/agent", json=run_input([{"id": "m1", "role": "user", "content": "a form"}]))
    action = {"name": "submit", "surfaceId": "main", "sourceComponentId": "send", "timestamp": "t", "context": {"email": "ada@example.com"}}
    data_model = {"version": "v0.9.1", "surfaces": {"main": {"form": {"email": "ada@example.com", "status": ""}}}}
    events = decode(client.post("/agent", json=run_input(
        [{"id": "m1", "role": "user", "content": "a form"}],
        {"a2ui": {"action": action, "a2uiClientDataModel": data_model}}, run_id="r2")).text)
    assert [e["type"] for e in events] == ["RUN_STARTED", "CUSTOM", "RUN_FINISHED"]
    assert events[1]["name"] == "a2ui"
    body = events[1]["value"]["updateDataModel"]
    assert body["path"] == "/form/status"
    assert "email='ada@example.com'" in body["value"]  # the Button's context
    assert 'the client data model says {"form": {"email": "ada@example.com", "status": ""}}' in body["value"]  # sendDataModel
    assert events[-1]["result"] == {"answered": "submit"}
    assert envelope.pointer_get(server.STORE.surfaces["main"].data, "/form/status") == body["value"]
    assert not replies  # no model call for an action


def test_a_second_generation_deletes_the_first_surface_first(scripted):
    """Generate twice on one page: the official renderer throws on a repeated createSurface,
    so the run withdraws the old surface first, and the mirror does not keep stale components."""
    from fastapi.testclient import TestClient

    server, replies = scripted
    replies.extend([REPLY, REPLY.replace('"id": "email"', '"id": "mail"').replace('["email",', '["mail",')])
    client = TestClient(server.app)
    client.post("/agent", json=run_input([{"id": "m1", "role": "user", "content": "a form"}]))
    assert "email" in server.STORE.surfaces["main"].components
    events = decode(client.post("/agent", json=run_input([{"id": "m2", "role": "user", "content": "another"}], run_id="r2")).text)
    kinds = [envelope.message_type(e["value"]) for e in events if e["type"] == "CUSTOM" and e["name"] == "a2ui"]
    assert kinds[:2] == ["deleteSurface", "createSurface"]
    components = server.STORE.surfaces["main"].components
    assert "mail" in components and "email" not in components


def test_a_bad_body_is_422_and_a_failing_model_is_run_error(scripted):
    from fastapi.testclient import TestClient

    server, replies = scripted
    client = TestClient(server.app)
    assert client.post("/agent", json={"threadId": "t1"}).status_code == 422  # RunAgentInput validates
    assert client.post("/agent", content=b"not json", headers={"content-type": "application/json"}).status_code == 422

    def boom(messages):
        raise RuntimeError("no key")

    server.stream_model = boom
    events = decode(client.post("/agent", json=run_input([{"id": "m1", "role": "user", "content": "x"}])).text)
    assert [e["type"] for e in events] == ["RUN_STARTED", "STEP_STARTED", "RUN_ERROR"]
    assert events[-1]["message"] == "RuntimeError: no key"  # the page logs it and a2uiDone still flips


def test_events_are_built_with_the_ag_ui_classes():
    ag_ui = pytest.importorskip("ag_ui", reason="pip install ag-ui-protocol")
    from ag_ui.core import CustomEvent, RunAgentInput
    from ag_ui.encoder import EventEncoder

    frame = EventEncoder().encode(CustomEvent(name="a2ui", value=envelope.delete_surface("s")))
    assert frame == 'data: {"type":"CUSTOM","name":"a2ui","value":{"version":"v0.9.1","deleteSurface":{"surfaceId":"s"}}}\n\n'
    parsed = RunAgentInput.model_validate(run_input([{"id": "m", "role": "user", "content": "hi"}], {"a2ui": {"action": {"name": "x"}}}))
    assert parsed.thread_id == "t1" and parsed.forwarded_props["a2ui"]["action"]["name"] == "x"
    assert ag_ui.core.EventType.CUSTOM == "CUSTOM"


# ------------------------------------------------------------ the Node side


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_node_client_processor_and_bundle():
    npm = shutil.which("npm")
    if not (HERE / "node_modules").exists():
        if npm is None:
            pytest.skip("node_modules is missing and npm is not on PATH")
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=HERE, check=True, capture_output=True)
    result = subprocess.run(["node", "--test", "--test-reporter=tap", "agui.test.mjs"], cwd=HERE, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
    bundle = HERE / "static" / "bundle.js"
    stale = not bundle.exists() or any(f.stat().st_mtime > bundle.stat().st_mtime for f in (HERE / "src").glob("*.mjs"))
    if npm is not None and stale:  # build once (as demo.py does), not on every test run
        build = subprocess.run([npm, "run", "build"], cwd=HERE, capture_output=True, text=True)
        assert build.returncode == 0, build.stdout + build.stderr
    if bundle.exists():
        assert bundle.stat().st_size > 100_000  # the whole renderer rides in one file
