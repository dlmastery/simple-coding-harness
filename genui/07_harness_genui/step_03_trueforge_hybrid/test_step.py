"""Step 03 offline tests: the parser's partial state, the artifact finder, the CSP, the SDK against a fake server, the page server.

Nothing here contacts localhost:8790. A fake TrueForge in a thread answers
`POST /api/v1/sessions` and streams hand-written SSE events for
`POST /api/v1/sessions/{id}/turns`, the artifact document split across
deltas mid-string; the real trueforge_sdk is pointed at it.
"""

import http.client
import json
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import artifact
import openui_parse as op
import server
from client import genui

HERE = Path(__file__).resolve().parent
SAMPLE_CATALOG = (HERE / "sample_catalog.md").read_text(encoding="utf-8")
SAMPLE_ARTIFACT = (HERE / "sample_artifact.md").read_text(encoding="utf-8")

DOCUMENT = "<!doctype html><html><head><title>Counter</title></head><body><button id='n'>0</button><script>let c=0;document.querySelector('#n').onclick=e=>{e.target.textContent=String(++c)}</script></body></html>"
PROGRAM = f"""root = Stack([intro, artifact], "column", "m")
intro = TextContent("Here is a counter:", "default")
artifact = HtmlArtifact("Interactive counter", "{DOCUMENT}")
"""

# ------------------------------------------------------- partial() and the tree


def test_partial_reads_the_open_artifact_line_as_far_as_it_goes():
    parser = op.Parser()
    parser.feed('root = Stack([intro, artifact])\nintro = TextContent("Hi")\nartifact = HtmlArtifact("Counter", "<html><body>a \\"q\\" \\n b\\')
    assert parser.partial() == ("artifact", "HtmlArtifact", ["Counter", '<html><body>a "q" \n b'])  # the lone trailing backslash is dropped
    node = parser.tree()["args"][0][1]
    assert node == {"type": "HtmlArtifact", "args": ["Counter", '<html><body>a "q" \n b'], "partial": True}
    assert parser.pending() == ["artifact"]  # still no statement for it
    parser.feed('</body></html>")\n')
    assert parser.partial() is None and parser.pending() == []
    node = parser.tree()["args"][0][1]
    assert "partial" not in node and node["args"][1].endswith("</body></html>")


def test_partial_handles_scalars_and_ignores_lines_that_are_not_a_call():
    parser = op.Parser()
    parser.feed('t = Tag("a", null, 3, -1.5')
    assert parser.partial() == ("t", "Tag", ["a", "null", 3, -1.5])
    parser = op.Parser()
    parser.feed("n = 42")
    assert parser.partial() is None
    parser.feed("\n")
    assert parser.tree("n") == 42


def test_step_02_behaviour_is_unchanged():
    parsed = op.parse(PROGRAM)
    assert parsed.errors == [] and parsed.pending() == []
    intro, art = parsed.tree()["args"][0]
    assert intro == {"type": "TextContent", "args": ["Here is a counter:", "default"]}
    assert art["args"] == ["Interactive counter", DOCUMENT]
    assert op.parse("a = b\nb = a\n").tree("a") == {"type": "Cycle", "ref": "a"}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_js_parser_and_sandbox_agree_with_python():
    result = subprocess.run(["node", "--test"], cwd=HERE, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


# ------------------------------------------------------------ artifact.py


def test_find_artifacts_walks_statements_and_the_partial_line():
    found = artifact.find_artifacts(PROGRAM)
    assert [(a.name, a.title, a.partial) for a in found] == [("artifact", "Interactive counter", False)]
    assert found[0].document == DOCUMENT
    inline = 'root = Stack([HtmlArtifact("A", "<p>a</p>"), Card([HtmlArtifact("B", "<p>b</p>")])])\n'
    assert [a.title for a in artifact.find_artifacts(inline)] == ["A", "B"]
    parser = op.Parser()
    parser.feed('root = Stack([art])\nart = HtmlArtifact("Half", "<p>so far')
    (half,) = artifact.find_artifacts(parser)
    assert (half.name, half.title, half.document, half.partial) == ("art", "Half", "<p>so far", True)
    assert artifact.find_artifacts('root = TextContent("no artifact")\n') == []


def test_csp_is_injected_first_in_head_and_replaces_the_models_own():
    doc = '<html><head><meta charset="utf-8"><title>x</title></head><body>hi</body></html>'
    out = artifact.sandboxed(doc)
    assert out.startswith("<html><head>" + artifact.META + '<meta charset="utf-8">')
    loosened = '<html><head><meta http-equiv="Content-Security-Policy" content="default-src *"></head><body></body></html>'
    out = artifact.sandboxed(loosened)
    assert out.count("Content-Security-Policy") == 1 and "default-src *" not in out
    assert artifact.sandboxed("<p>fragment</p>") == artifact.META + "<p>fragment</p>"
    assert "default-src 'none'" in artifact.CSP and "script-src 'unsafe-inline'" in artifact.CSP


def test_check_document_lists_what_the_csp_will_block():
    assert artifact.check_document(DOCUMENT) == []
    bad = '<script src="https://cdn.example/x.js"></script><script>fetch("/x")</script><meta http-equiv="refresh" content="0">'
    assert artifact.check_document(bad) == ["external resource: https://cdn.example/x.js", "network call in script", "meta refresh"]
    assert artifact.check_document("x" * (artifact.MAX_DOCUMENT_CHARS + 1))[0].startswith("document is 200001 characters")


def test_recorded_replies_parse_and_match_their_prompts():
    catalog = op.parse(genui.extract_program(SAMPLE_CATALOG))
    assert catalog.errors == [] and catalog.pending() == [] and artifact.find_artifacts(catalog) == []
    hybrid = op.parse(genui.extract_program(SAMPLE_ARTIFACT))
    assert hybrid.errors == [] and hybrid.pending() == []
    (found,) = artifact.find_artifacts(hybrid)
    assert found.name == "artifact" and "<script>" in found.document and artifact.check_document(found.document) == []
    assert hybrid.tree()["args"][0][0]["type"] == "TextContent"  # the intro comes first


# ------------------------------------------------------ the fake TrueForge

REPLY = "Here you go.\n```openui\n" + PROGRAM + "```"
# the document string is cut mid-way across deltas, as the live stream does
CUT = REPLY.index("<button")
DELTAS = [REPLY[:CUT], REPLY[CUT:CUT + 40], REPLY[CUT + 40:]]
GUIDE = "<openui>\nAll openui code must be fenced.\n</openui>"


def usage(input_tokens, output_tokens, messages):
    """A model call's usage as TrueForge reports it, with the input breakdown by source."""
    breakdown = {"harness": 1288, "instructions": 200, "messages": messages, "skills": 0, "tool_definitions": 0}
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "cache_read_tokens": 0, "cache_write_tokens": 0, "input_tokens_breakdown": breakdown}


def event(**fields):
    fields.setdefault("id", "01evt")
    fields.setdefault("created_at", "2026-09-14T10:00:00.000Z")
    return f"data: {json.dumps(fields)}\n\n".encode()


class FakeTrueForge(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append((self.path, body))
        if self.path == "/api/v1/sessions":
            return self.json({"data": {"id": "sess-1", "agent": {"type": "inline", "spec": body["agent"]["spec"]}, "created_at": "2026-09-14T10:00:00.000Z"}})
        assert self.path == "/api/v1/sessions/sess-1/turns"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(event(type="turn.created", turn_id="turn-1"))
        # first model call: the agent loads the catalog guide through the system tool
        self.wfile.write(event(type="model.message", id="msg-1", thread_id="main"))
        self.wfile.write(event(type="model.message.delta", id="msg-1", thread_id="main",
                               tool_calls=[{"id": "call-1", "index": 0, "type": "function", "function": {"name": "get_openui_instructions", "arguments": ""}}]))
        self.wfile.write(event(type="model.message.delta", id="msg-1", thread_id="main", finish_reason="tool_calls",
                               usage=usage(1500, 14, messages=0)))
        self.wfile.write(event(type="tool.response", id="resp-1", thread_id="main", tool_call_id="call-1", content=GUIDE))
        # second model call: the reply, the artifact document split across deltas
        self.wfile.write(event(type="model.message", id="msg-2", thread_id="main"))
        for piece in DELTAS:
            self.wfile.write(event(type="model.message.delta", id="msg-2", thread_id="main", content=piece))
        self.wfile.write(event(type="model.message.delta", id="sub-1", thread_id="sub", content="ignored: not the main thread"))
        self.wfile.write(event(type="model.message.delta", id="msg-2", thread_id="main", finish_reason="stop",
                               usage=usage(6000, 300, messages=4500)))
        output = {"type": "model.message", "id": "msg-2", "thread_id": "main", "content": REPLY, "finish_reason": "stop", "created_at": "2026-09-14T10:00:01.000Z"}
        metrics = {"total_input_tokens": 7500, "total_output_tokens": 314, "total_tokens": 7814}
        self.wfile.write(event(type="turn.done", state={"status": "done", "completed_at": "2026-09-14T10:00:02.000Z", "output": output, "metrics": metrics, "required_actions": []}))
        self.wfile.flush()

    def json(self, payload):
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def fake_trueforge(monkeypatch):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeTrueForge)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    FakeTrueForge.requests.clear()
    monkeypatch.setattr(genui, "BASE_URL", f"http://127.0.0.1:{httpd.server_address[1]}")
    monkeypatch.setattr(genui, "_client", None)
    yield httpd
    httpd.shutdown()


def test_sdk_streams_the_hybrid_reply_and_the_artifact_shows_up_part_way(fake_trueforge):
    parser, states = op.Parser(), []

    def on_delta(piece):
        # feed the deltas as the page would, and note the artifact's state after each
        parser.feed(piece.split("```openui\n", 1)[-1] if "```openui" in piece else piece)
        found = artifact.find_artifacts(parser)
        states.append((found[0].partial, len(found[0].document)) if found else None)

    session_id, reply, metrics = genui.ask("build me a counter", on_delta=on_delta)
    assert session_id == "sess-1" and reply == REPLY
    opened = CUT - REPLY.index("<!doctype")  # document characters that arrived in the first delta
    assert states == [(True, opened), (True, opened + 40), (False, len(DOCUMENT))]
    assert metrics["total_output_tokens"] == 314 and metrics["tools"] == ["get_openui_instructions"]
    assert [c["input_tokens"] for c in metrics["calls"]] == [1500, 6000]
    assert metrics["calls"][1]["input_tokens_breakdown"]["messages"] == 4500

    path, body = FakeTrueForge.requests[0]
    assert path == "/api/v1/sessions"
    spec = body["agent"]["spec"]
    assert spec["model"]["name"] == genui.MODEL and spec["config"]["generative_ui"]["enabled"] is True
    assert "HtmlArtifact(" in spec["instructions"] and "get_openui_instructions" in spec["instructions"]
    path, body = FakeTrueForge.requests[1]
    assert path == "/api/v1/sessions/sess-1/turns" and body["input"][0] == {"type": "user.message", "content": "build me a counter"}


def test_extract_program_finds_the_fence_or_says_none():
    assert genui.extract_program(REPLY) == PROGRAM.rstrip("\n")
    assert genui.extract_program("plain prose only") is None
    assert genui.extract_program("```openui\nroot = Stack([a])\na = HtmlArtifact(\"T\", \"<p>cut") == 'root = Stack([a])\na = HtmlArtifact("T", "<p>cut'


# ---------------------------------------------------------- the page server


def test_page_server_streams_chunks_then_null_and_serves_the_sandbox_module():
    httpd, url = server.serve(PROGRAM, "raw reply text", port=0, chunk_delay=0, chunk_size=50)
    host, port = httpd.server_address
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/")
        page = conn.getresponse().read()
        assert b'id="surface"' in page and b".artifact-frame" in page
        for name in ("/app.js", "/openui-parse.mjs", "/render.mjs", "/sandbox.mjs"):
            conn.request("GET", name)
            assert conn.getresponse().status == 200, name
        conn.request("GET", "/reply")
        assert conn.getresponse().read() == b"raw reply text"
        conn.request("GET", "/events")
        stream = conn.getresponse()
        pieces = [json.loads(l[6:]) for l in stream.read().decode().split("\n\n") if l.startswith("data: ")]
        assert pieces[-1] is None and "".join(pieces[:-1]) == PROGRAM
        assert all(len(p) <= 50 for p in pieces[:-1]) and len(pieces) - 1 == -(-len(PROGRAM) // 50)
        conn.close()
    finally:
        httpd.shutdown()
