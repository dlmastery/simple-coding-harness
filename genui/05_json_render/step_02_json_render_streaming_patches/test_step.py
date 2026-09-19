"""Step 2 offline tests. json_patch.py is checked against the RFC 6902 examples
and against the library's own compiler on the same fixture stream; the server
relays a fake model's chunks and compiles them on the way. No model or
network call.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import llm
import server
from json_patch import PatchError, SpecStream, apply_patch, apply_patches
from prompt import catalog_json, system_prompt
from spec import check_spec

STEP = Path(__file__).resolve().parent
NODE = shutil.which("node")
NPM = shutil.which("npm")
FIXTURE = (STEP / "tests" / "patches.jsonl").read_text(encoding="utf-8")


def ensure_node_modules():
    if (STEP / "node_modules").exists():
        return
    if NPM is None:
        pytest.skip("node_modules is missing and npm is not installed")
    subprocess.run([NPM, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True, capture_output=True, timeout=600)


class FakeStream:
    """Stands in for llm.Stream: yields scripted chunks, then reports usage."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.usage = None

    def __iter__(self):
        yield from self.chunks
        self.usage = {"prompt_tokens": 10, "completion_tokens": 5}


# --- RFC 6902, appendix A ---------------------------------------------------

def test_rfc_examples():
    doc = {"foo": "bar"}
    apply_patch(doc, {"op": "add", "path": "/baz", "value": "qux"})
    assert doc == {"baz": "qux", "foo": "bar"}

    doc = {"foo": ["bar", "baz"]}
    apply_patch(doc, {"op": "add", "path": "/foo/1", "value": "qux"})
    assert doc == {"foo": ["bar", "qux", "baz"]}

    doc = {"baz": "qux", "foo": "bar"}
    apply_patch(doc, {"op": "remove", "path": "/baz"})
    assert doc == {"foo": "bar"}

    doc = {"baz": "qux", "foo": "bar"}
    apply_patch(doc, {"op": "replace", "path": "/baz", "value": "boo"})
    assert doc == {"baz": "boo", "foo": "bar"}

    doc = {"foo": {"bar": "baz", "waldo": "fred"}, "qux": {"corge": "grault"}}
    apply_patch(doc, {"op": "move", "from": "/foo/waldo", "path": "/qux/thud"})
    assert doc == {"foo": {"bar": "baz"}, "qux": {"corge": "grault", "thud": "fred"}}

    doc = {"foo": ["all", "grass", "cows", "eat"]}
    apply_patch(doc, {"op": "move", "from": "/foo/1", "path": "/foo/3"})
    assert doc == {"foo": ["all", "cows", "eat", "grass"]}

    doc = {"baz": "qux", "foo": ["a", 2, "c"]}
    apply_patches(doc, [{"op": "test", "path": "/baz", "value": "qux"}, {"op": "test", "path": "/foo/1", "value": 2}])
    with pytest.raises(PatchError, match="test failed"):
        apply_patch(doc, {"op": "test", "path": "/baz", "value": "bar"})

    doc = {"foo": ["bar"]}
    apply_patch(doc, {"op": "add", "path": "/foo/-", "value": ["abc", "def"]})
    assert doc == {"foo": ["bar", ["abc", "def"]]}

    doc = {"/": 9, "~1": 10}
    apply_patch(doc, {"op": "test", "path": "/~01", "value": 10})
    apply_patch(doc, {"op": "copy", "from": "/~1", "path": "/copy"})
    assert doc["copy"] == 9


def test_add_and_replace_create_paths_like_the_library_and_the_rest_stays_strict():
    doc = {}
    apply_patch(doc, {"op": "add", "path": "/elements/card-1/props/title", "value": "T"})
    apply_patch(doc, {"op": "add", "path": "/state/days/0", "value": {"id": "mon"}})
    apply_patch(doc, {"op": "replace", "path": "/state/details/title", "value": "D"})
    assert doc == {"elements": {"card-1": {"props": {"title": "T"}}}, "state": {"days": [{"id": "mon"}], "details": {"title": "D"}}}
    with pytest.raises(PatchError, match="not found"):
        apply_patch(doc, {"op": "remove", "path": "/elements/ghost"})
    with pytest.raises(PatchError, match="not found"):
        apply_patch(doc, {"op": "move", "from": "/elements/ghost", "path": "/elements/x"})
    with pytest.raises(PatchError, match="unknown op"):
        apply_patch(doc, {"op": "upsert", "path": "/x", "value": 1})
    with pytest.raises(PatchError, match="needs a value"):
        apply_patch(doc, {"op": "add", "path": "/x"})


# --- the stream compiler ---------------------------------------------------

def test_spec_stream_ignores_chunk_boundaries():
    whole = SpecStream()
    whole.push(FIXTURE)
    whole.finish()
    pieces = SpecStream()
    applied = sum(len(pieces.push(FIXTURE[i:i + 7])) for i in range(0, len(FIXTURE), 7))
    applied += len(pieces.finish())
    assert pieces.spec == whole.spec
    assert applied == len(pieces.patches) == 13
    assert pieces.skipped == []
    assert pieces.spec["elements"]["card-1"]["props"]["subtitle"] == "Week 33"
    assert "delta" not in pieces.spec["elements"]["metric-1"]["props"]
    assert pieces.spec["elements"]["table-1"]["props"]["rows"] == [["Mon", "12"], ["Tue", "30"]]
    assert check_spec(pieces.spec, catalog_json()) == []


def test_spec_stream_has_root_only_once_the_root_element_exists():
    stream = SpecStream()
    stream.push('{"op":"add","path":"/root","value":"card-1"}\n')
    assert not stream.has_root()
    stream.push('{"op":"add","path":"/elements/card-1","value":{"type":"Card","props":{"title":"x"},"children":[]}}\n')
    assert stream.has_root()


def test_spec_stream_skips_bad_lines_and_keeps_going():
    stream = SpecStream()
    stream.push('not json\n{"op":"remove","path":"/nothing"}\n{"op":"add","path":"/root","value":"a"}\n')
    assert stream.spec == {"root": "a"}
    assert [reason for _, reason in stream.skipped] == ["Expecting value: line 1 column 1 (char 0)", "/nothing: not found"]


def test_spec_stream_skips_lines_that_are_not_patch_objects():
    """The model wraps its patches in an array, writes a bare string, or aims below a scalar: skipped, never a crash."""
    stream = SpecStream()
    stream.push("\n".join([
        '[{"op":"add","path":"/root","value":"a"}]',
        '"just a string"',
        '{"op":"add","path":"/root","value":"card"}',
        '{"op":"add","path":"/root/x/y","value":1}',
        '{"op":"add","path":"","value":5}',
        '{"op":"add","path":"/elements","value":[]}',
        '{"op":"add","path":"/elements/card-1","value":{}}',
    ]) + "\n")
    assert stream.spec == {"root": "card", "elements": []}
    assert [reason for _, reason in stream.skipped] == [
        "a patch must be an object, got list",
        "a patch must be an object, got str",
        "/root/x/y: parent is not a container",
        "the whole document must be an object",
        "/elements/card-1: 'card-1' is not an array index",
    ]
    assert stream.has_root() is False  # elements is a list, root is a string: nothing to paint, no TypeError
    stream = SpecStream()
    stream.push('{"op":"add","path":"/root","value":{"type":"Card"}}\n')
    assert stream.has_root() is False  # the element itself at /root: not a root id


def test_server_ends_a_failed_stream_with_an_error_line(monkeypatch):
    class DyingStream(FakeStream):
        def __iter__(self):
            yield from self.chunks
            raise RuntimeError("upstream closed the connection")

    first = FIXTURE.split("\n")[0] + "\n"
    monkeypatch.setattr(llm, "stream_text", lambda system, user: DyingStream([first]))
    server.LAST.clear()
    client = TestClient(server.app)
    with client.stream("POST", "/stream", json={"prompt": "lemonade"}) as response:
        body = "".join(response.iter_text())
    assert body == first + "\n" + json.dumps({"error": "RuntimeError: upstream closed the connection"}) + "\n"
    last = client.get("/last").json()
    assert last["error"] == "RuntimeError: upstream closed the connection"
    assert last["spec"] == {"root": "card-1"} and last["skipped"] == []  # the error line is not a patch, and it is not counted as one


def test_python_and_library_compile_the_fixture_to_the_same_spec():
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    out = subprocess.run([NODE, "tests/compile.mjs", "tests/patches.jsonl"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    stream = SpecStream()
    stream.push(FIXTURE)
    stream.finish()
    assert json.loads(out) == stream.spec


# --- the server ------------------------------------------------------------

def test_server_relays_chunks_and_compiles_a_copy(monkeypatch):
    chunks = [FIXTURE[i:i + 50] for i in range(0, len(FIXTURE), 50)]
    monkeypatch.setattr(llm, "stream_text", lambda system, user: FakeStream(chunks))
    server.LAST.clear()
    client = TestClient(server.app)
    assert client.get("/last").status_code == 404
    with client.stream("POST", "/stream", json={"prompt": "lemonade"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        body = "".join(response.iter_text())
    assert body == FIXTURE, "the page gets the model's text unchanged"
    last = client.get("/last").json()
    assert len(last["patches"]) == 13
    assert last["spec"]["root"] == "card-1"
    assert last["problems"] == []
    assert last["usage"] == {"prompt_tokens": 10, "completion_tokens": 5}
    assert last["timings"]["first_paint"] is not None
    assert last["timings"]["first_paint"] <= last["timings"]["complete"]
    assert client.get("/spec").json() == last["spec"]


def test_prompt_cache_matches_node_and_asks_for_patches():
    assert "OUTPUT FORMAT (JSONL, RFC 6902 JSON Patch)" in system_prompt()
    assert "Reply with ONE JSON object" not in system_prompt()
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    for script, cache in [("prompt.mjs", "prompt.txt"), ("catalog_json.mjs", "catalog.json")]:
        out = subprocess.run([NODE, script], cwd=STEP, capture_output=True, text=True, encoding="utf-8", check=True).stdout
        assert out == (STEP / cache).read_text(encoding="utf-8"), f"{cache} is stale: delete it and rerun"


def test_node_suite_passes():
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    result = subprocess.run([NODE, "--test", "tests/stream.test.mjs"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
