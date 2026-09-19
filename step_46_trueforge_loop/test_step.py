"""Step 46 - Offline tests: the real SDK against a fake TrueForge server in a thread."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

import demo
import setup_server
from client import loop

# ------------------------------------------------------------ the fake server


def sse(event):
    """One Server-Sent Event: a `data:` line with the JSON, then a blank line."""
    return f"data: {json.dumps(event)}\n\n".encode("utf-8")


def turn_script(prompt, session_id):
    """The five events of one plain turn, shaped like the server's own stream."""
    message_id = "msg-1"
    first, second = "Echo: ", prompt
    output = None
    if prompt != "no-output":
        output = {"type": "model.message", "id": message_id, "thread_id": "main",
                  "created_at": "2026-01-01T00:00:00Z", "content": first + second}
    state = {"status": "done", "output": output, "required_actions": [], "completed_at": "2026-01-01T00:00:01Z",
             "metrics": {"total_input_tokens": 1000 + len(prompt), "total_output_tokens": 7, "total_tokens": 1007 + len(prompt)}}
    if prompt == "fail":
        state = {"status": "error", "message": "model unavailable", "completed_at": "2026-01-01T00:00:01Z",
                 "metrics": {"total_input_tokens": 1004, "total_output_tokens": 7, "total_tokens": 1011}}
    if prompt == "cancel":
        state = {"status": "cancelled", "reason": "server-execution-timeout", "completed_at": "2026-01-01T00:00:01Z",
                 "metrics": {"total_input_tokens": 500, "total_tokens": 500}}
    events = [
        {"type": "turn.created", "id": "ev-1", "thread_id": None, "turn_id": f"turn-{session_id}", "previous_turn_id": None,
         "input": [{"type": "user.message", "content": prompt}], "state": {"status": "running"}, "created_at": "2026-01-01T00:00:00Z"},
        {"type": "model.message", "id": message_id, "thread_id": "main", "created_at": "2026-01-01T00:00:00Z"},
        {"type": "model.message.delta", "id": message_id, "thread_id": "main", "content": first},
        {"type": "model.message.delta", "id": message_id, "thread_id": "main", "content": second},
        {"type": "turn.done", "id": "ev-9", "thread_id": None, "created_at": "2026-01-01T00:00:01Z", "state": state},
    ]
    if prompt == "truncated":  # the connection drops after the first delta: no turn.done ever arrives
        return events[:3]
    return events


class FakeTrueForge(BaseHTTPRequestHandler):
    """Enough of the TrueForge HTTP API for one session, one turn and one settings PUT."""

    requests = []
    sessions = 0
    providers = []
    disable_nagle_algorithm = True  # each SSE event leaves as its own packet, without a delayed-ACK stall

    def log_message(self, *args):
        pass

    def body(self):
        length = int(self.headers.get("content-length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def reply(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/v1/settings/model-providers":
            return self.reply(200, {"data": FakeTrueForge.providers})
        self.reply(404, {"error": "not found"})

    def do_PUT(self):
        if self.path == "/api/v1/settings/model-providers":
            manifest = self.body()["manifest"]
            manifest["auth"] = {"api_key": "sk-***REDACTED***"}
            FakeTrueForge.providers = [{"name": manifest["type"], "manifest": manifest}]
            return self.reply(200, {"data": FakeTrueForge.providers[0]})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        body = self.body()
        FakeTrueForge.requests.append((self.path, body))
        if self.path == "/api/v1/sessions":
            FakeTrueForge.sessions += 1
            session_id = f"s46-fake-{FakeTrueForge.sessions}"
            session = {"id": session_id, "agent": {"type": "inline", "spec": body["agent"]["spec"]}, "title": None,
                       "created_by": "trueforge-default", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}
            return self.reply(201, {"data": session})
        if self.path.startswith("/api/v1/sessions/") and self.path.endswith("/turns"):
            session_id = self.path.split("/")[4]
            prompt = body["input"][0]["content"]
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("cache-control", "no-cache")
            self.end_headers()
            for event in turn_script(prompt, session_id):
                self.wfile.write(sse(event))
                self.wfile.flush()
            return
        self.reply(404, {"error": "not found"})


@pytest.fixture(scope="module")
def server():
    """Start the fake server once and point both modules at it; the SDK client is built on first use."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeTrueForge)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{httpd.server_port}"
    saved = loop.BASE_URL, loop._client, setup_server.BASE_URL
    loop.BASE_URL, loop._client, setup_server.BASE_URL = base_url, None, base_url
    yield base_url
    loop.BASE_URL, loop._client, setup_server.BASE_URL = saved
    httpd.shutdown()


@pytest.fixture
def fake(server):
    """The fake server with a clean request log."""
    FakeTrueForge.requests = []
    FakeTrueForge.sessions = 0
    return FakeTrueForge


# ------------------------------------------------------------ chat


def test_chat_streams_deltas_and_returns_text_and_metrics(fake):
    seen = []
    session_id, text, metrics, status = loop.chat("hello", on_delta=seen.append)
    assert session_id == "s46-fake-1"
    assert seen == ["Echo: ", "hello"]
    assert text == "Echo: hello"
    assert metrics == {"total_input_tokens": 1005, "total_output_tokens": 7, "total_tokens": 1012}
    assert status == "done"


def test_chat_opens_a_session_with_an_inline_spec(fake):
    loop.chat("hello", on_delta=None)
    path, body = fake.requests[0]
    assert path == "/api/v1/sessions"
    assert body["agent"]["spec"]["model"]["name"] == loop.MODEL
    assert body["agent"]["spec"]["instructions"] == loop.INSTRUCTIONS
    path, body = fake.requests[1]
    assert path == "/api/v1/sessions/s46-fake-1/turns"
    assert body["input"] == [{"type": "user.message", "content": "hello"}]
    assert body["stream"] is True


def test_second_chat_reuses_the_session(fake):
    session_id, _, _, _ = loop.chat("first", on_delta=None)
    again, text, _, _ = loop.chat("second", session_id=session_id, on_delta=None)
    assert again == session_id
    assert text == "Echo: second"
    assert fake.sessions == 1
    paths = [path for path, _ in fake.requests]
    assert paths == ["/api/v1/sessions", f"/api/v1/sessions/{session_id}/turns", f"/api/v1/sessions/{session_id}/turns"]


def test_chat_falls_back_to_the_joined_deltas_when_output_is_missing(fake):
    _, text, metrics, status = loop.chat("no-output", on_delta=None)
    assert text == "Echo: no-output"
    assert metrics["total_output_tokens"] == 7
    assert status == "done"


def test_chat_reports_an_error_state_with_its_metrics(fake):
    _, text, metrics, status = loop.chat("fail", on_delta=None)
    assert text == "[turn error: model unavailable]"
    assert status == "error"
    assert metrics["total_tokens"] == 1011  # the tokens spent before the error are kept


def test_chat_reports_a_cancelled_state(fake):
    _, text, metrics, status = loop.chat("cancel", on_delta=None)
    assert (text, status) == ("[turn cancelled: server-execution-timeout]", "cancelled")
    assert metrics == {"total_input_tokens": 500, "total_tokens": 500}


def test_a_stream_without_turn_done_is_incomplete_not_done(fake):
    """A dropped connection must not look like a finished turn."""
    _, text, metrics, status = loop.chat("truncated", on_delta=None)
    assert status == "incomplete"
    assert text == "Echo: "  # what arrived before the drop
    assert metrics == {}


def test_describe_error_names_the_server(fake):
    from trueforge_sdk.core.api_error import ApiError

    assert loop.describe_error(ApiError(status_code=404, headers={}, body={"error": "no such session"})).startswith(f"{loop.BASE_URL} answered 404")
    assert loop.describe_error(httpx.ConnectError("refused")).startswith(f"{loop.BASE_URL} is not answering")


def test_usage_line():
    assert loop.usage_line({"total_input_tokens": 1034, "total_output_tokens": 7, "total_tokens": 1041}) == "1,034 input, 7 output, 1,041 total"
    assert loop.usage_line({"total_tokens": 5, "total_cost_in_usd": 0.00123}) == "5 total, $0.0012"
    assert loop.usage_line({}) == ""


# ------------------------------------------------------------ demo.py


def test_headless_prints_the_reply_and_exits(fake, capsys):
    assert demo.main(["-p", "ping"]) == 0
    out, err = capsys.readouterr()
    assert out == "Echo: ping\n"
    assert "1,004 input, 7 output, 1,011 total" in err
    assert "session s46-fake-1" in err


def test_headless_resume_continues_the_session(fake, capsys):
    assert demo.main(["--resume", "s46-earlier", "-p", "again"]) == 0
    out, err = capsys.readouterr()
    assert out == "Echo: again\n"
    assert fake.sessions == 0
    assert fake.requests[0][0] == "/api/v1/sessions/s46-earlier/turns"


def test_repl_runs_turns_until_exit(fake, capsys, monkeypatch):
    prompts = iter(["one", "", "two", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))
    assert demo.main([]) == 0
    out, _ = capsys.readouterr()
    assert "Echo: one" in out and "Echo: two" in out
    assert out.count("[1,00") == 2
    assert "python demo.py --resume s46-fake-1" in out
    assert fake.sessions == 1


def test_repl_ends_on_eof_and_shows_a_failed_turn(fake, capsys, monkeypatch):
    prompts = iter(["fail"])
    monkeypatch.setattr("builtins.input", lambda _: next(prompts, None) or (_ for _ in ()).throw(EOFError()))
    assert demo.main([]) == 0
    out, _ = capsys.readouterr()
    assert "[turn error: model unavailable]" in out
    assert "python demo.py --resume s46-fake-1" in out


# ------------------------------------------------------------ setup_server.py


def test_setup_reads_the_key_file_and_never_prints_it(fake, tmp_path, monkeypatch, capsys):
    env_file = tmp_path / "env"
    env_file.write_text("# keys\nOPENAI_API_KEY=sk-test-secret-value\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(setup_server, "ENV_FILE", env_file)
    assert setup_server.read_key(env_file) == "sk-test-secret-value"
    assert setup_server.main() == 0
    out, _ = capsys.readouterr()
    assert "openai/gpt-4-1-mini  ->  gpt-4.1-mini  (context 1,047,576)" in out
    assert "sk-test-secret-value" not in out
    stored = fake.providers[0]["manifest"]
    assert stored["type"] == "openai"
    assert stored["models"][0] == {"model_id": "gpt-4.1-mini", "name": "gpt-4-1-mini",
                                   "properties": {"context_length": 1047576, "max_output_tokens": 32768}}
