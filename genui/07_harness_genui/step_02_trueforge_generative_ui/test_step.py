"""Step 02 offline tests: the parser (Python and JS), the extractor, the SDK against a fake server, the page server.

Nothing here contacts localhost:8790. A fake TrueForge in a thread answers
`POST /api/v1/sessions` and streams hand-written SSE events for
`POST /api/v1/sessions/{id}/turns`; the real trueforge_sdk is pointed at it.
"""

import http.client
import json
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import openui_parse as op
import server
from client import genui

HERE = Path(__file__).resolve().parent
SAMPLE = (HERE / "sample_reply.md").read_text(encoding="utf-8")

PROGRAM = """root = Stack([header, kpis, note], "column", "l")
header = TextContent("Lemonade stand", "large-heavy")
kpis = Stack([Card([TextContent("Cups", "small"), TextContent("" + cups, "large-heavy")])], "row")
cups = 370
note = TextContent("Done \\"today\\".", "default")
"""

# ------------------------------------------------------------ the parser


def test_tokenizer_covers_every_literal():
    tokens = op.tokenize('x = Card(["a\\"b", -1.5, 3, true, null], y)')
    assert [t[0] for t in tokens] == ["id", "punct", "id", "punct", "punct", "str", "punct", "num", "punct", "num", "punct", "id", "punct", "id", "punct", "punct", "id", "punct"]
    assert tokens[5] == ("str", 'a"b') and tokens[7] == ("num", -1.5) and tokens[9] == ("num", 3)


def test_forward_references_resolve_into_one_tree():
    parsed = op.parse(PROGRAM)
    assert parsed.errors == [] and parsed.pending() == []
    tree = parsed.tree()
    assert tree["type"] == "Stack" and tree["args"][1:] == ["column", "l"]
    header, kpis, note = tree["args"][0]
    assert header == {"type": "TextContent", "args": ["Lemonade stand", "large-heavy"]}
    assert kpis["args"][0][0]["args"][0][1]["args"] == ["370", "large-heavy"]  # "" + cups concatenates
    assert note["args"][0] == 'Done "today".'


def test_streaming_feed_holds_back_unfinished_lines_and_marks_pending():
    parser = op.Parser()
    parser.feed('root = Stack([header, kpis], "col')
    assert parser.statements == {} and parser.tree() == {"type": "Pending", "ref": "root"}
    parser.feed('umn")\nheader = TextContent("Hi")\n')
    assert parser.pending() == ["kpis"]
    assert parser.tree()["args"][0] == [{"type": "TextContent", "args": ["Hi"]}, {"type": "Pending", "ref": "kpis"}]
    parser.feed('kpis = Stack([\n  header,\n  header\n], "row")\n')  # a statement across four lines
    assert parser.pending() == [] and len(parser.tree()["args"][0][1]["args"][0]) == 2


def test_parse_errors_are_collected_not_raised():
    parsed = op.parse('a = Card(1))\nb = 1\nc = ?\nd = a\n')
    assert len(parsed.errors) == 2 and "trailing tokens" in parsed.errors[0] and "unexpected text" in parsed.errors[1]
    assert parsed.tree("d")["type"] == "Pending"
    assert op.parse("a = b\nb = a\n").tree("a") == {"type": "Cycle", "ref": "a"}


def test_one_unbalanced_line_does_not_hold_back_the_rest():
    """A stray bracket closes at the next statement; it is an error, and the lines after it still parse."""
    parsed = op.parse('a = Stack([x)\nb = TextContent("hi")\nroot = Stack([a, b])\n')
    assert list(parsed.statements) == ["b", "root"] and len(parsed.errors) == 1
    assert parsed.tree()["args"][0][1] == {"type": "TextContent", "args": ["hi"]}
    assert parsed.tree()["args"][0][0] == {"type": "Pending", "ref": "a"}


def test_plus_on_anything_but_numbers_is_text():
    parsed = op.parse('root = Stack([x, y])\nx = null + 1\ny = 2 + 3\n')
    assert parsed.tree()["args"][0] == ["null1", 5]  # the same text the page's JS parser produces


def test_a_failed_request_is_one_line_naming_the_server():
    from trueforge_sdk.core.api_error import ApiError
    assert genui.describe_error(ApiError(status_code=404, headers={}, body={"error": "no such session"})).startswith(f"{genui.BASE_URL} answered 404")
    assert genui.describe_error(ConnectionError("refused")) == f"{genui.BASE_URL} is not answering (ConnectionError: refused)"


def test_a_turn_that_does_not_end_done_is_an_error(fake_trueforge, monkeypatch):
    """A turn that ends `error` (or a stream with no turn.done) raises: a truncated program is never returned as complete."""
    monkeypatch.setattr(FakeTrueForge, "status", "error")
    with pytest.raises(RuntimeError, match=r"the turn ended 'error' \(the model provider returned 500\)"):
        genui.ask("show a report", on_delta=None)


def test_outline_is_the_terminal_view():
    lines = op.outline(op.parse(PROGRAM).tree())
    assert lines[0] == "Stack('column', 'l')" and lines[1] == "  TextContent('Lemonade stand', 'large-heavy')"
    assert "      TextContent('370', 'large-heavy')" in lines


def test_recorded_reply_parses_cleanly():
    program = genui.extract_program(SAMPLE)
    parsed = op.parse(program)
    assert parsed.errors == [] and parsed.pending() == [] and parsed.tree()["type"] == "Stack"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_js_parser_agrees_with_python():
    result = subprocess.run(["node", "--test"], cwd=HERE, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


# --------------------------------------------------------- the extractor


def test_extract_program_finds_the_fence_or_says_none():
    assert genui.extract_program("Here:\n```openui\nroot = Text(\"a\")\n```\nDone.") == 'root = Text("a")'
    assert genui.extract_program("plain prose only") is None
    assert genui.extract_program("```openui\nroot = Stack([a])\na = Text(\"x\")") == 'root = Stack([a])\na = Text("x")'  # cut mid-stream
    assert genui.extract_program(SAMPLE).startswith("root = Stack(")


# ------------------------------------------------------ the fake TrueForge

REPLY = "Here is the report.\n```openui\nroot = TextContent(\"Hi\", \"large-heavy\")\n```"
DELTAS = ["Here is the report.\n", "```openui\nroot = TextContent(", "\"Hi\", \"large-heavy\")\n```"]


def event(**fields):
    fields.setdefault("id", "01evt")
    fields.setdefault("created_at", "2026-09-14T10:00:00.000Z")
    return f"data: {json.dumps(fields)}\n\n".encode()


class FakeTrueForge(BaseHTTPRequestHandler):
    requests = []
    status = "done"  # a test sets "error" to end the turn without a reply

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
        self.wfile.write(event(type="model.message", id="msg-1", thread_id="main"))
        for piece in DELTAS:
            self.wfile.write(event(type="model.message.delta", id="msg-1", thread_id="main", content=piece))
        self.wfile.write(event(type="model.message.delta", id="sub-1", thread_id="sub", content="ignored: not the main thread"))
        output = {"type": "model.message", "id": "msg-1", "thread_id": "main", "content": REPLY, "finish_reason": "stop", "created_at": "2026-09-14T10:00:01.000Z"}
        metrics = {"total_input_tokens": 120, "total_output_tokens": 30, "total_tokens": 150}
        state = {"status": "done", "completed_at": "2026-09-14T10:00:02.000Z", "output": output, "metrics": metrics, "required_actions": []}
        if self.status == "error":  # the SDK's error state: a message, no output
            state = {"status": "error", "completed_at": state["completed_at"], "message": "the model provider returned 500", "metrics": metrics}
        self.wfile.write(event(type="turn.done", state=state))
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


def test_sdk_streams_the_reply_from_the_fake_server(fake_trueforge):
    seen = []
    session_id, reply, metrics = genui.ask("show a report", on_delta=seen.append)
    assert session_id == "sess-1" and reply == REPLY and seen == DELTAS
    assert metrics["total_output_tokens"] == 30
    assert genui.extract_program(reply) == 'root = TextContent("Hi", "large-heavy")'

    path, body = FakeTrueForge.requests[0]
    assert path == "/api/v1/sessions"
    spec = body["agent"]["spec"]
    assert spec["model"]["name"] == genui.MODEL and spec["config"]["generative_ui"]["enabled"] is True
    path, body = FakeTrueForge.requests[1]
    assert path == "/api/v1/sessions/sess-1/turns" and body["stream"] is True
    assert body["input"][0] == {"type": "user.message", "content": "show a report"}


# ---------------------------------------------------------- the page server


def test_page_server_streams_one_line_per_event_then_null():
    httpd, url = server.serve(PROGRAM, "raw reply text", port=0, line_delay=0)
    host, port = httpd.server_address
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/")
        assert b'id="surface"' in conn.getresponse().read()
        for name in ("/app.js", "/openui-parse.mjs", "/render.mjs"):
            conn.request("GET", name)
            assert conn.getresponse().status == 200
        conn.request("GET", "/../server.py")
        assert conn.getresponse().status == 404  # nothing outside web/ is served
        conn.request("GET", "/reply")
        assert conn.getresponse().read() == b"raw reply text"
        conn.request("GET", "/events")
        stream = conn.getresponse()
        lines = [json.loads(l[6:]) for l in stream.read().decode().split("\n\n") if l.startswith("data: ")]
        assert lines == PROGRAM.splitlines() + [None]
        conn.close()
    finally:
        httpd.shutdown()
