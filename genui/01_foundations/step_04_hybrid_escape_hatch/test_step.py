"""Step 04 tests. Offline: the model is a fake stream of scripted chunks."""

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
import progress  # noqa: E402
import server  # noqa: E402
import tokens  # noqa: E402
from partial_json import PartialDict, PartialList, is_partial, parse_partial  # noqa: E402


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
        # Snapshot the transcript: the server appends to the same list after the call.
        self.requests.append({**request, "messages": list(request["messages"])})
        return iter(self.chunks)


TOOL_SCRIPT = [
    call_chunk(0, cid="c1", name="show_metric", arguments='{"title": "Cups sold", '),
    call_chunk(0, arguments='"value": "412", "delta": "+12%"}'),
    call_chunk(1, cid="c2", name="show_chart", arguments='{"kind": "bar", "labels": ["Mon", "Tue"], "values": [40, 52]}'),
    usage_chunk(),
]

TREE = {
    "type": "Card", "props": {"title": "Lemonade stand"},
    "children": [
        {"type": "Row", "props": {}, "children": [
            {"type": "Metric", "props": {"title": "Cups", "value": "412", "delta": "+12%"}},
            {"type": "Metric", "props": {"title": "Revenue", "value": "$625", "delta": "+10%"}},
        ]},
        {"type": "Row", "props": {}, "children": [
            {"type": "Table", "props": {"columns": ["Day", "Cups"], "rows": [["Mon", "40"], ["Tue", "52"]]}},
            {"type": "Chart", "props": {"kind": "bar", "labels": ["Mon", "Tue"], "values": [40, 52]}},
        ]},
    ],
}

FLAT = {
    "root": "card",
    "elements": {
        "card": {"type": "Card", "props": {"title": "Lemonade stand"}, "children": ["r1", "r2"]},
        "r1": {"type": "Row", "props": {}, "children": ["m1", "m2"]},
        "r2": {"type": "Row", "props": {}, "children": ["t", "c"]},
        "m1": {"type": "Metric", "props": {"title": "Cups", "value": "412", "delta": "+12%"}},
        "m2": {"type": "Metric", "props": {"title": "Revenue", "value": "$625", "delta": "+10%"}},
        "t": {"type": "Table", "props": {"columns": ["Day", "Cups"], "rows": [["Mon", "40"], ["Tue", "52"]]}},
        "c": {"type": "Chart", "props": {"kind": "bar", "labels": ["Mon", "Tue"], "values": [40, 52]}},
    },
}


def chunks_of(text, size=12):
    """The model's JSON as it would stream: fixed-size pieces."""
    return [text[i : i + size] for i in range(0, len(text), size)]


def json_script(spec):
    return [text_chunk(piece) for piece in chunks_of(json.dumps(spec))] + [usage_chunk()]


@pytest.fixture
def fake(monkeypatch):
    def install(chunks):
        client = FakeClient(chunks)
        monkeypatch.setattr(llm, "client", client)
        return client
    return install


# ---------------------------------------------------------- partial_json.py


def test_partial_json_agrees_with_json_on_complete_text():
    text = json.dumps(FLAT)
    assert parse_partial(text) == json.loads(text)
    assert not is_partial(parse_partial(text))


def test_every_prefix_parses_and_marks_open_containers():
    text = json.dumps(FLAT)
    for n in range(len(text) + 1):
        value = parse_partial(text[:n])
        assert value is None or isinstance(value, dict)
    cut = text.index('"m1": {') + 7  # root, r1, r2 closed; m1 just opened
    value = parse_partial(text[:cut])
    assert isinstance(value, PartialDict) and isinstance(value["elements"], PartialDict)
    assert value["elements"]["card"]["children"] == ["r1", "r2"] and not is_partial(value["elements"]["card"])
    assert isinstance(value["elements"]["m1"], PartialDict)


def test_cut_scalars_are_dropped_and_cut_strings_kept():
    assert parse_partial('{"a": tr') == {}
    assert parse_partial('{"a": -') == {}
    assert parse_partial('{"a": 1.') == {}
    assert parse_partial('{"a": 1.5, "b": nul') == {"a": 1.5}
    assert parse_partial('{"title": "Lemon') == {"title": "Lemon"}
    assert parse_partial('{"title": "Lemon\\') == {"title": "Lemon"}
    assert parse_partial('{"ti') == {}
    assert parse_partial('["a", "b') == ["a", "b"] and isinstance(parse_partial('["a", "b'), PartialList)
    assert parse_partial("  ") is None


def test_escapes_are_decoded():
    assert parse_partial(r'{"t": "a\"b\né"}') == {"t": 'a"b\né'}


# --------------------------------------------------------------- catalog.py


def test_schemas_accept_the_examples_and_reject_strangers():
    assert catalog.validate(TREE, "tree") == []
    assert catalog.validate(FLAT, "flat") == []
    assert catalog.validate(catalog.TREE_EXAMPLE, "tree") == []
    assert catalog.validate(catalog.FLAT_EXAMPLE, "flat") == []
    bad = {"type": "Gauge", "props": {"value": 3}}
    assert catalog.validate(bad, "tree")
    leaf = {"type": "Metric", "props": {"title": "a", "value": "1", "delta": "+1"}, "children": []}
    assert catalog.validate(leaf, "tree") == []  # an empty list on a leaf is tolerated
    leaf["children"] = [catalog.TREE_EXAMPLE]
    assert catalog.validate(leaf, "tree")
    missing_prop = {"type": "Card", "props": {}, "children": []}
    assert any("title" in p for p in catalog.validate(missing_prop, "tree"))


def test_flat_validation_checks_that_ids_resolve():
    dangling = {"root": "a", "elements": {"a": {"type": "Row", "props": {}, "children": ["zz"]}}}
    assert catalog.validate(dangling, "flat") == ["a: child 'zz' is not an element"]
    no_root = {"root": "nope", "elements": {"a": {"type": "Row", "props": {}, "children": []}}}
    assert catalog.validate(no_root, "flat") == ["root 'nope' is not an element"]


def test_system_prompt_lists_the_catalog_and_the_shape():
    tree, flat = catalog.system_prompt("tree"), catalog.system_prompt("flat")
    for name in catalog.CATALOG:
        assert f"- {name}(" in tree and f"- {name}(" in flat
    assert "takes children" in tree and "list of nodes" in tree
    assert '"root" first' in flat and "top-down" in flat
    assert json.dumps(catalog.FLAT_EXAMPLE) in flat


def test_static_tools_are_still_there():
    assert [t["function"]["name"] for t in catalog.TOOL_SCHEMAS] == ["show_metric", "show_table", "show_chart"]
    assert catalog.message_from_call("show_metric", '{"title": "a", "value": "1", "delta": "+1"}')["component"] == "Metric"


# -------------------------------------------------------------- progress.py


def test_flat_layout_is_known_early_and_tree_layout_only_at_the_end():
    tree = progress.replay(chunks_of(json.dumps(TREE)), "tree")
    flat = progress.replay(chunks_of(json.dumps(FLAT)), "flat")
    assert tree["skeleton_chunk"] == tree["chunks"]  # the root closes with the last chunk
    assert flat["skeleton_chunk"] < flat["chunks"] // 4  # the root element is the first thing written
    assert tree["first_paint_chunk"] and flat["first_paint_chunk"]
    assert flat["first_paint_chunk"] <= tree["first_paint_chunk"] + 3


def test_measure_counts_closed_components_reachable_from_root():
    assert progress.measure(TREE, "tree") == {"complete": 7, "skeleton": True}
    assert progress.measure(FLAT, "flat") == {"complete": 7, "skeleton": True}
    text = json.dumps(FLAT)
    cut = text.index('"m2": {') + 7  # card, r1, r2, m1 closed
    assert progress.measure(parse_partial(text[:cut]), "flat") == {"complete": 4, "skeleton": True}
    assert progress.measure(None, "flat") == {"complete": 0, "skeleton": False}
    assert progress.measure(None, "tree") == {"complete": 0, "skeleton": False}


# ---------------------------------------------------------------- server.py


def frames(text):
    """The JSON messages of an SSE body."""
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def test_static_mode_is_step_01_plus_the_raw_text(fake):
    fake(TOOL_SCRIPT)
    messages = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "static"}).text)
    assert [m.get("component") for m in messages] == ["Metric", "Chart", None]
    assert messages[-1]["mode"] == "static" and messages[-1]["done"] is True
    assert messages[-1]["raw"].splitlines()[0] == 'show_metric {"title": "Cups sold", "value": "412", "delta": "+12%"}'


HTML = (
    "<!doctype html><html><head><style>body{font:14px sans-serif}</style></head><body><h1>Lemonade</h1>"
    "<button onclick=\"parent.postMessage({type:'event',name:'refresh',payload:{}}, '*')\">Refresh</button></body></html>"
)


def test_html_mode_streams_the_document_then_hands_it_over(fake):
    client = fake([text_chunk(piece) for piece in chunks_of(HTML, 20)] + [usage_chunk()])
    messages = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "html"}).text)
    assert "".join(m["delta"] for m in messages if "delta" in m) == HTML
    done = messages[-1]
    assert done["done"] and done["mode"] == "html" and done["html"] == HTML and done["raw"] == HTML
    assert done["usage"]["completion_tokens"] == 60
    request = client.requests[0]
    assert "tools" not in request and "response_format" not in request
    assert "postMessage" in request["messages"][0]["content"] and "no external" in request["messages"][0]["content"]


def test_html_mode_strips_a_code_fence_but_keeps_raw(fake):
    fake([text_chunk("```html\n" + HTML + "\n```"), usage_chunk()])
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "html"}).text)[-1]
    assert done["html"] == HTML and done["raw"].startswith("```html")


def test_declarative_done_carries_raw_too(fake):
    fake(json_script(FLAT))
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "flat"}).text)[-1]
    assert done["raw"] == json.dumps(FLAT)


# ---------------------------------------------------------------- tokens.py


class FakeEncoding:
    def encode(self, text):
        return text.split()  # one token per word: enough to check the arithmetic


def test_token_table_uses_flat_as_the_base(monkeypatch):
    monkeypatch.setattr(tokens, "encoding", lambda: FakeEncoding())
    lines = tokens.table([
        ("static", "tool calls", "a b c d", 5),
        ("flat", "JSON", "a b c d e", 6),
        ("html", "HTML", " ".join(["x"] * 40), 44),
    ])
    assert lines[0].split() == ["mode", "what", "the", "model", "wrote", "tiktoken", "api", "vs", "flat"]
    assert lines[1].split() == ["static", "tool", "calls", "4", "5", "0.8x"]
    assert lines[2].split() == ["flat", "JSON", "5", "6", "1.0x"]
    assert lines[3].split() == ["html", "HTML", "40", "44", "8.0x"]


def test_token_table_falls_back_to_api_counts(monkeypatch):
    monkeypatch.setattr(tokens, "encoding", lambda: None)
    assert tokens.count("anything") is None
    lines = tokens.table([("flat", "JSON", "x", 10), ("html", "HTML", "y", 65)])
    assert lines[1].split() == ["flat", "JSON", "-", "10", "1.0x"]
    assert lines[2].split() == ["html", "HTML", "-", "65", "6.5x"]


def test_encoding_never_raises(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def no_tiktoken(name, *args, **kwargs):
        if name == "tiktoken":
            raise ImportError("no tiktoken here")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_tiktoken)
    monkeypatch.setattr(tokens, "_encoding", None)
    assert tokens.encoding() is None
    monkeypatch.setattr(tokens, "_encoding", None)


@pytest.mark.parametrize("shape,spec", [("tree", TREE), ("flat", FLAT)])
def test_declarative_modes_stream_deltas_then_the_checked_spec(fake, shape, spec):
    client = fake(json_script(spec))
    messages = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": shape}).text)
    deltas = [m["delta"] for m in messages if "delta" in m]
    assert "".join(deltas) == json.dumps(spec)
    done = messages[-1]
    assert done["done"] and done["valid"] and done["errors"] == [] and done["spec"] == spec and done["mode"] == shape
    assert done["usage"] == {"prompt_tokens": 120, "completion_tokens": 60}
    request = client.requests[0]
    assert "tools" not in request and request["response_format"] == {"type": "json_object"}
    assert request["messages"][0]["content"] == catalog.system_prompt(shape)


def test_invalid_spec_is_reported_not_hidden(fake):
    fake([text_chunk('{"type": "Gauge", "props": {}}'), usage_chunk()])
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "tree"}).text)[-1]
    assert done["valid"] is False and done["errors"]


def test_fenced_or_broken_json_is_handled(fake):
    fake([text_chunk("```json\n" + json.dumps(catalog.TREE_EXAMPLE) + "\n```"), usage_chunk()])
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "tree"}).text)[-1]
    assert done["valid"] is True
    fake([text_chunk('{"type": '), usage_chunk()])
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "tree"}).text)[-1]
    assert done["spec"] is None and done["errors"] == ["the reply is not JSON"]


def test_schema_endpoint_and_page():
    client = TestClient(server.app)
    assert client.get("/api/schema/flat").json() == catalog.flat_schema()
    assert client.get("/api/schema/tree").json()["$defs"]["node"]["allOf"]
    assert "partial-json.mjs" in client.get("/app.js").text and "sandbox.mjs" in client.get("/app.js").text
    page = client.get("/").text
    assert 'sandbox="allow-scripts"' in page and 'value="html"' in page
    assert "GeneratedView" in client.get("/render.mjs").text and "/api/action" in client.get("/app.js").text


# ------------------------------------------------------------- the loop

HYBRID = {
    "root": "card",
    "elements": {
        "card": {"type": "Card", "props": {"title": "Stand"}, "children": ["stock", "gauge", "restock"]},
        "stock": {"type": "Metric", "props": {"title": "Lemons", "value": "20", "delta": "-5"}},
        "gauge": {"type": "GeneratedView", "props": {"html": "<svg viewBox='0 0 10 10'><circle r='4' cx='5' cy='5'/></svg>"}},
        "restock": {"type": "Button", "props": {"label": "Restock", "action": "restock_lemons"}},
    },
}


def test_generated_view_and_button_are_in_the_catalog_and_the_prompt():
    assert catalog.validate(HYBRID, "flat") == []
    prompt = catalog.system_prompt("flat")
    assert "- GeneratedView(html: string)" in prompt and "escape hatch" in prompt
    assert "Button.action is an event name" in prompt
    bad = {"root": "g", "elements": {"g": {"type": "GeneratedView", "props": {"html": "<b>x</b>"}, "children": ["a"]}}}
    assert catalog.validate(bad, "flat")


def test_action_runs_the_next_turn_on_the_same_transcript(fake, monkeypatch):
    monkeypatch.setattr(server, "SESSIONS", {})
    client = fake(json_script(HYBRID))
    api = TestClient(server.app)
    first = frames(api.post("/api/run", json={"prompt": "lemonade", "mode": "flat"}).text)[-1]
    assert first["turn"] == 1 and first["session"] in server.SESSIONS

    after = json.loads(json.dumps(HYBRID))
    after["elements"]["stock"]["props"] = {"title": "Lemons", "value": "100", "delta": "+80"}
    client.chunks = json_script(after)
    messages = frames(api.post("/api/action", json={"session": first["session"], "action": "restock_lemons", "payload": {"label": "Restock"}}).text)
    second = messages[-1]
    assert [m for m in messages if "delta" in m]  # the reply streams like a first turn
    assert second["turn"] == 2 and second["session"] == first["session"] and second["valid"]
    assert second["spec"]["elements"]["stock"]["props"]["value"] == "100"

    transcript = client.requests[1]["messages"]
    assert [m["role"] for m in transcript] == ["system", "user", "assistant", "user"]
    assert transcript[2]["content"] == json.dumps(HYBRID)  # the layout the user was looking at
    assert "'restock_lemons'" in transcript[3]["content"] and '{"label": "Restock"}' in transcript[3]["content"]
    assert server.SESSIONS[first["session"]]["messages"][-1]["role"] == "assistant"


def test_action_on_an_unknown_session_is_404(fake):
    fake([])
    response = TestClient(server.app).post("/api/action", json={"session": "nope", "action": "x", "payload": None})
    assert response.status_code == 404


def test_static_and_html_modes_open_no_session(fake, monkeypatch):
    monkeypatch.setattr(server, "SESSIONS", {})
    fake(TOOL_SCRIPT)
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "static"}).text)[-1]
    assert "session" not in done
    fake([text_chunk(HTML), usage_chunk()])
    done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": "html"}).text)[-1]
    assert "session" not in done and server.SESSIONS == {}




def test_text_that_is_not_json_raises_and_cut_documents_never_do():
    import pytest as _pytest

    for bad in ("```json\n{", '{"a": 1., "b": 2}', '{"a": @}', "[" * 100):
        with _pytest.raises(ValueError):
            parse_partial(bad)
    bs = chr(92)
    with _pytest.raises(ValueError):
        parse_partial('{"a": "' + bs + 'uZZZZ"}')
    assert parse_partial('{"a": "' + bs + 'u00e9"}') == {"a": "\u00e9"}
    assert parse_partial('{"a": 1.5e3, "b": -2}') == {"a": 1500.0, "b": -2}


def test_progress_survives_a_shape_mix_up_and_non_json_chunks():
    mixed = {"root": "r", "elements": {"r": {"type": "Row", "props": {}, "children": [{"type": "Text", "props": {"text": "x"}}]}}}
    assert progress.measure(mixed, "flat") == {"complete": 1, "skeleton": True}
    replay = progress.replay(["```json", "\n", json.dumps(FLAT)], "flat")
    assert replay["chunks"] == 3 and replay["first_paint_chunk"] is None  # the fence never parses


def test_a_model_failure_ends_every_mode_with_an_error_frame(monkeypatch):
    def boom(**request):
        raise RuntimeError("model down")

    monkeypatch.setattr(llm, "client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom))))
    for mode in ("static", "tree", "flat", "html"):
        done = frames(TestClient(server.app).post("/api/run", json={"prompt": "x", "mode": mode}).text)[-1]
        assert done == {"done": True, "error": "RuntimeError: model down"}


def test_a_failed_turn_leaves_no_dangling_user_message(fake, monkeypatch):
    monkeypatch.setattr(server, "SESSIONS", {})
    client = fake(json_script(HYBRID))
    api = TestClient(server.app)
    first = frames(api.post("/api/run", json={"prompt": "lemonade", "mode": "flat"}).text)[-1]
    session = server.SESSIONS[first["session"]]
    before = list(session["messages"])

    def boom(**request):
        raise RuntimeError("model down")

    client.create = boom
    client.chat.completions.create = boom
    done = frames(api.post("/api/action", json={"session": first["session"], "action": "restock_lemons", "payload": None}).text)[-1]
    assert done["error"] == "RuntimeError: model down"
    assert session["messages"] == before  # the event was rolled back; the next action starts clean
    assert not session["lock"].locked()


def test_interleaved_pieces_and_missing_indexes_still_assemble(fake):
    fake([
        call_chunk(0, cid="c1", name="show_metric", arguments='{"title": "a", '),
        call_chunk(1, cid="c2", name="show_chart", arguments='{"kind": "bar", '),
        call_chunk(0, arguments='"value": "1", "delta": "+1"}'),
        call_chunk(None, cid="c2", arguments='"labels": [], "values": []}'),
        usage_chunk(),
    ])
    calls = [e for e in llm.stream_chat([], tools=catalog.TOOL_SCHEMAS) if e["type"] == "tool_call"]
    assert [c["name"] for c in calls] == ["show_metric", "show_chart"]
    assert json.loads(calls[0]["arguments"]) == {"title": "a", "value": "1", "delta": "+1"}
    assert json.loads(calls[1]["arguments"]) == {"kind": "bar", "labels": [], "values": []}


# ------------------------------------------------------------- node tests


def test_node_suite_passes():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    result = subprocess.run(
        [node, "--test", "--test-reporter=tap", "tests/render.test.mjs", "tests/partial-json.test.mjs", "tests/sandbox.test.mjs"],
        cwd=HERE, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
