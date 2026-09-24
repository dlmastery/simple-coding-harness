"""Offline tests for step 01: builders, schema validation, JSON Pointer, surface
state, the SSE replay endpoint, and the node tests for the page's state module.
No model, no network."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import a2ui  # noqa: E402

HERE = Path(__file__).parent
STREAM = a2ui.read_stream(HERE / "contact_form.jsonl")


# ------------------------------------------------------------ builders and schema


def test_builders_produce_valid_envelopes():
    pytest.importorskip("jsonschema")
    messages = [
        a2ui.create_surface("s", theme={"primaryColor": "#00bfff"}, send_data_model=True),
        a2ui.update_components("s", [{"id": "root", "component": "Text", "text": {"path": "/greeting"}}]),
        a2ui.update_data_model("s", "/greeting", "hello"),
        a2ui.update_data_model("s", "/greeting", remove=True),
        a2ui.delete_surface("s"),
    ]
    assert [a2ui.validate(m) for m in messages] == [None] * 5
    assert "value" not in messages[3]["updateDataModel"]


def test_validate_reports_the_spec_error_shape():
    pytest.importorskip("jsonschema")
    problem = a2ui.validate({"version": "v0.9.1", "createSurface": {"surfaceId": "s"}})
    assert problem == {"code": "VALIDATION_FAILED", "surfaceId": "s", "path": "/createSurface", "message": "'catalogId' is a required property"}
    unknown = a2ui.validate(a2ui.update_components("s", [{"id": "root", "component": "Texto", "text": "x"}]))
    assert unknown["message"] == "'Texto' is not a component of the Basic Catalog"
    extra = a2ui.validate(a2ui.update_components("s", [{"id": "root", "component": "Text", "text": "x", "colour": "red"}]))
    assert "colour" in extra["message"]
    missing = a2ui.validate(a2ui.update_components("s", [{"id": "root", "component": "TextField", "value": {"path": "/x"}}]))
    assert missing["message"] == "'label' is a required property"
    two_keys = {"version": "v0.9.1", "createSurface": {"surfaceId": "s", "catalogId": "x"}, "deleteSurface": {"surfaceId": "s"}}
    assert a2ui.validate(two_keys)["path"] == "/"


def test_spec_example_stream_needs_the_checks_repair():
    """The protocol document's own contact form writes checks as {call, args, message};
    the schema's CheckRule wants {condition, message}."""
    pytest.importorskip("jsonschema")
    messages = json.loads(json.dumps(STREAM))
    assert [a2ui.message_type(m) for m in messages] == ["createSurface", "updateComponents", "updateDataModel", "deleteSurface"]
    problem = a2ui.validate(messages[1])
    assert problem["path"] == "/updateComponents/components/14/checks/0"
    assert problem["message"] == "'condition' is a required property"
    assert a2ui.repair_checks(messages[1]) == 3
    assert a2ui.validate(messages[1]) is None
    assert a2ui.repair_checks(messages[1]) == 0  # idempotent
    assert [a2ui.validate(m) for m in (messages[0], messages[2], messages[3])] == [None, None, None]


# ------------------------------------------------------------ JSON Pointer


def test_pointer_get_set_delete():
    doc = {}
    a2ui.pointer_set(doc, "/contact/email", "a@b.c")
    assert a2ui.pointer_get(doc, "/contact/email") == "a@b.c"
    assert a2ui.pointer_get(doc, "/contact/phone") is None
    assert a2ui.pointer_get(doc, "/") == doc
    a2ui.pointer_set(doc, "/tags", ["x", "y"])
    assert a2ui.pointer_get(doc, "/tags/1") == "y"
    a2ui.pointer_delete(doc, "/tags/0")
    assert doc["tags"] == [None, "y"]  # arrays keep their length
    a2ui.pointer_set(doc, "/a~1b/c~0d", 1)
    assert doc["a/b"]["c~d"] == 1
    a2ui.pointer_delete(doc, "/nothing/here")
    a2ui.pointer_set(doc, "/", {"fresh": True})
    assert doc == {"fresh": True}
    with pytest.raises(ValueError):
        a2ui.pointer_tokens("relative/path")


def test_pointer_list_indexes_must_be_digits_on_every_operation():
    doc = {"tags": ["x"]}
    assert a2ui.pointer_get(doc, "/tags/x") is None
    assert a2ui.pointer_delete(doc, "/tags/x") == {"tags": ["x"]}  # nothing to delete, no crash
    assert a2ui.pointer_delete(doc, "/tags/x/y") == {"tags": ["x"]}
    for path in ("/tags/x", "/tags/x/y"):
        with pytest.raises(ValueError, match="not a list index"):
            a2ui.pointer_set(doc, path, 1)
    assert doc == {"tags": ["x"]}


# ------------------------------------------------------------ surface state


def test_child_before_parent_and_missing_refs():
    store = a2ui.SurfaceStore()
    store.apply(a2ui.create_surface("s"))
    surface = store.apply(a2ui.update_components("s", [
        {"id": "title", "component": "Text", "text": "Hi"},  # arrives before root
    ]))
    assert surface.tree() == {"id": "root", "missing": True}
    surface.apply(a2ui.update_components("s", [{"id": "root", "component": "Column", "children": ["title", "later"]}]))
    assert surface.missing_ids() == ["later"]
    assert surface.tree()["children"][1] == {"id": "later", "missing": True}
    surface.apply(a2ui.update_components("s", [{"id": "later", "component": "Text", "text": "Now"}]))
    assert surface.missing_ids() == []
    assert [c["component"] for c in surface.tree()["children"]] == ["Text", "Text"]


def test_binding_two_way_and_action_context():
    surface = a2ui.Surface("s", a2ui.BASIC_CATALOG_ID)
    surface.apply(a2ui.update_components("s", [
        {"id": "root", "component": "Column", "children": ["field", "send"]},
        {"id": "field", "component": "TextField", "label": "Email", "value": {"path": "/contact/email"}},
        {"id": "send", "component": "Button", "child": "label",
         "action": {"event": {"name": "submit", "context": {"email": {"path": "/contact/email"}, "formId": "f1",
                                                              "when": {"call": "formatDate", "args": {}}}}}},
        {"id": "label", "component": "Text", "text": "Send"},
    ]))
    assert surface.resolve({"path": "/contact/email"}) is None
    surface.apply(a2ui.update_data_model("s", "/contact", {"email": "a@b.c"}))
    assert surface.resolve({"path": "/contact/email"}) == "a@b.c"
    surface.set("/contact/email", "new@b.c")
    assert surface.action("send", "t0") == {
        "name": "submit", "surfaceId": "s", "sourceComponentId": "send", "timestamp": "t0",
        "context": {"email": "new@b.c", "formId": "f1", "when": None},
    }


def test_store_lifecycle():
    store = a2ui.SurfaceStore()
    with pytest.raises(ValueError, match="never created"):
        store.apply(a2ui.update_data_model("s", "/", {}))
    store.apply(a2ui.create_surface("s"))
    store.apply(a2ui.update_data_model("s", "/stale", True))
    assert store.apply(a2ui.create_surface("s")).data == {}  # a repeated createSurface is a reset
    store.apply(a2ui.update_data_model("s", "/user", {"name": "Ada", "temp": 1}))
    surface = store.apply(a2ui.update_data_model("s", "/user/temp", remove=True))
    assert surface.data == {"user": {"name": "Ada"}}
    store.apply(a2ui.delete_surface("s"))
    assert store.surfaces == {}


def test_a_component_inside_itself_is_a_cycle_not_a_crash():
    surface = a2ui.Surface("s", a2ui.BASIC_CATALOG_ID)
    surface.apply(a2ui.update_components("s", [
        {"id": "root", "component": "Column", "children": ["root", "card"]},
        {"id": "card", "component": "Card", "child": "root"},
    ]))
    tree = surface.tree()
    assert tree["children"][0] == {"id": "root", "cycle": True}
    assert tree["children"][1]["children"][0] == {"id": "root", "cycle": True}
    assert surface.missing_ids() == []


def test_spec_stream_through_the_store():
    store = a2ui.SurfaceStore()
    messages = json.loads(json.dumps(STREAM))
    for message in messages[:3]:
        surface = store.apply(message)
    assert surface.tree()["component"] == "Card"
    assert len(surface.components) == 25
    assert surface.missing_ids() == []
    assert a2ui.pointer_get(surface.data, "/contact/firstName") == "John"
    store.apply(messages[3])
    assert store.surfaces == {}


# ------------------------------------------------------------ the SSE endpoint


def test_stream_endpoint_replays_repaired_messages(monkeypatch):
    pytest.importorskip("jsonschema")
    from fastapi.testclient import TestClient

    import server

    monkeypatch.setattr(server, "GAP", 0)
    client = TestClient(server.app)
    text = client.get("/stream?all=1").text
    frames = [f for f in text.split("\n\n") if f.strip()]
    data = [json.loads(f.split("data: ", 1)[1]) for f in frames if not f.startswith("event: done")]
    assert [a2ui.message_type(m) for m in data] == ["createSurface", "updateComponents", "updateDataModel", "deleteSurface"]
    assert all(a2ui.validate(m) is None for m in data)
    assert frames[-1].startswith("event: done")
    without_delete = client.get("/stream").text
    assert "deleteSurface" not in without_delete
    assert client.get("/").status_code == 200


# ------------------------------------------------------------ the page's state module


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_node_surface_module():
    result = subprocess.run(["node", "--test", "--test-reporter=tap", "surface.test.mjs"], cwd=HERE, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
