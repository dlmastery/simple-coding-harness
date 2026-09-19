"""Step 49 - Offline tests: the real SDK against a fake TrueForge server in a thread.

The fake serves `POST /api/v1/sessions` and `POST /api/v1/sessions/{id}/turns`.
The first turn streams a question (`ask_user_question` split across deltas,
then `tool.response_required`); the resume turn streams a text reply. Every
request body is recorded so the tests can check what the client sent.
Nothing here contacts `localhost:8790`.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import demo
from client import context, questions

SESSION = "01fakesession"
MSG_Q = "msg-question"
MSG_A = "msg-answer"
CALL = "call-q-01"
USAGE = {
    "input_tokens": 1091, "output_tokens": 33, "cache_read_tokens": 0, "cache_write_tokens": 0,
    "input_tokens_breakdown": {"harness": 1288, "skills": 0, "instructions": 67,
                               "tool_definitions": 0, "messages": 0},
}


def question_turn():
    """The events of a turn that ends paused on one question, as the live server sends them."""
    return [
        {"type": "turn.created", "id": "e1", "turn_id": "turn-1", "previous_turn_id": None,
         "input": [{"type": "user.message", "content": "set up a project for me"}],
         "state": {"status": "running"}, "created_at": "2026-01-01T00:00:00Z"},
        {"type": "model.message", "id": MSG_Q, "thread_id": "main", "created_at": "2026-01-01T00:00:00Z"},
        {"type": "model.message.delta", "id": MSG_Q, "thread_id": "main", "tool_calls": [
            {"index": 0, "id": CALL, "type": "function",
             "function": {"name": "ask_user_question", "arguments": ""},
             "tool_info": {"type": "truefoundry-system", "name": "ask_user_question"}}]},
        {"type": "model.message.delta", "id": MSG_Q, "thread_id": "main", "tool_calls": [
            {"index": 0, "function": {"arguments": '{"question":"Which kind of project?",'}}]},
        {"type": "model.message.delta", "id": MSG_Q, "thread_id": "main", "tool_calls": [
            {"index": 0, "function": {"arguments": '"options":["python","node"]}'}}]},
        {"type": "model.message.delta", "id": MSG_Q, "thread_id": "main",
         "finish_reason": "tool_calls", "usage": USAGE},
        {"type": "tool.response_required", "id": "e7", "thread_id": "main",
         "tool_calls": [{"id": CALL, "source_event_id": MSG_Q}], "created_at": "2026-01-01T00:00:00Z"},
        {"type": "turn.done", "id": "e8", "thread_id": None, "created_at": "2026-01-01T00:00:00Z",
         "state": {"status": "done", "output": None, "completed_at": "2026-01-01T00:00:00Z",
                   "metrics": {"total_input_tokens": 1091, "total_output_tokens": 33, "total_tokens": 1124},
                   "required_actions": [{"type": "tool.response_required", "id": "e7", "thread_id": "main",
                                         "tool_calls": [{"id": CALL, "source_event_id": MSG_Q}],
                                         "created_at": "2026-01-01T00:00:00Z"}]}},
    ]


def errored_question_turn():
    """The question was asked, then the turn died: the pending call must not be answered."""
    events = question_turn()
    events[-1] = {"type": "turn.done", "id": "e8", "thread_id": None, "created_at": "2026-01-01T00:00:00Z",
                  "state": {"status": "error", "message": "You have reached iteration limit of 8, please request again",
                            "completed_at": "2026-01-01T00:00:00Z",
                            "metrics": {"total_input_tokens": 1091, "total_output_tokens": 33, "total_tokens": 1124}}}
    return events


def other_tool_turn():
    """A pending client-side tool that is not a question."""
    events = question_turn()
    events[2] = {"type": "model.message.delta", "id": MSG_Q, "thread_id": "main", "tool_calls": [
        {"index": 0, "id": CALL, "type": "function", "function": {"name": "open_browser", "arguments": ""}}]}
    return events


def answer_turn():
    """The events of the resume turn: a plain text reply."""
    usage = dict(USAGE, input_tokens=1131, output_tokens=54)
    return [
        {"type": "turn.created", "id": "e9", "turn_id": "turn-2", "previous_turn_id": "turn-1",
         "input": [], "state": {"status": "running"}, "created_at": "2026-01-01T00:00:01Z"},
        {"type": "model.message", "id": MSG_A, "thread_id": "main", "created_at": "2026-01-01T00:00:01Z"},
        {"type": "model.message.delta", "id": MSG_A, "thread_id": "main", "content": "For a Python project: "},
        {"type": "model.message.delta", "id": MSG_A, "thread_id": "main", "content": "main.py, README.md"},
        {"type": "model.message.delta", "id": MSG_A, "thread_id": "main", "finish_reason": "stop", "usage": usage},
        {"type": "turn.done", "id": "e14", "thread_id": None, "created_at": "2026-01-01T00:00:02Z",
         "state": {"status": "done", "completed_at": "2026-01-01T00:00:02Z", "required_actions": [],
                   "metrics": {"total_input_tokens": 1131, "total_output_tokens": 54, "total_tokens": 1185},
                   "output": {"type": "model.message", "id": MSG_A, "thread_id": "main",
                              "content": "For a Python project: main.py, README.md",
                              "created_at": "2026-01-01T00:00:01Z", "finish_reason": "stop", "usage": usage}}},
    ]


class FakeTrueForge(BaseHTTPRequestHandler):
    """Two routes, hand-written SSE, every body recorded on the server object."""

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("content-length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        self.server.requests.append((self.path, body))
        if self.path == "/api/v1/sessions":
            self._json({"data": {"id": SESSION, "agent": {"type": "inline", "spec": body["agent"]["spec"]},
                                 "title": None, "created_by": "fake", "created_at": "2026-01-01T00:00:00Z",
                                 "updated_at": "2026-01-01T00:00:00Z"}})
        elif self.path == f"/api/v1/sessions/{SESSION}/turns":
            items = body.get("input") or []
            kinds = {item.get("type") for item in items}
            prompt = items[0].get("content", "") if items else ""
            if "user.tool_response" in kinds:
                events = question_turn() if self.server.keep_asking else answer_turn()
            elif prompt == "fail":
                events = errored_question_turn()
            elif prompt == "cut":
                events = question_turn()[:4]  # the connection drops mid-message: no turn.done
            elif prompt == "other-tool":
                events = other_tool_turn()
            else:
                events = question_turn()
            self._sse(events)
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, payload):
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _sse(self, events):
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.end_headers()
        for number, event in enumerate(events, 1):
            self.wfile.write(f"data: {json.dumps(event)}\nid: {number}\n\n".encode())
        self.wfile.flush()


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("127.0.0.1", 0), FakeTrueForge)
    httpd.requests = []
    httpd.keep_asking = False  # when True every resume is answered with the same question again
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


@pytest.fixture(scope="module")
def client(server):
    return context.connect(f"http://127.0.0.1:{server.server_port}")  # one client: each costs ~1s


@pytest.fixture(autouse=True)
def fresh_requests(server):
    server.requests.clear()
    server.keep_asking = False


# --- the spec ---------------------------------------------------------------

def test_spec_sets_every_limit():
    spec = context.build_spec("be brief", compact_at=12_345, iteration_limit=7)
    body = spec.model_dump(exclude_none=True)
    compaction = body["config"]["context_management"]["compaction"]
    assert compaction == {"enabled": True, "trigger": {"type": "input_tokens", "value": 12_345}}
    assert body["config"]["context_management"]["large_tool_response"] == {"enabled": True}
    assert body["config"]["iteration_limit"] == 7
    assert body["config"]["ask_user_questions"] == {"enabled": True}
    assert body["config"]["dynamic_sub_agents"] == {"enabled": False}  # one thread only in this step
    assert body["model"] == {"name": context.MODEL}
    assert body["instructions"] == "be brief"


def test_describe_spec_names_each_limit():
    text = context.describe_spec(context.build_spec("x"))
    assert "20,000 input tokens" in text
    assert "8 model calls" in text
    assert "ask_user_question enabled: True" in text


def test_session_is_created_with_the_inline_spec(client, server):
    session_id = context.open_session(client, context.build_spec("hello"))
    assert session_id == SESSION
    path, body = server.requests[0]
    assert path == "/api/v1/sessions"
    assert body["agent"]["spec"]["instructions"] == "hello"
    assert body["agent"]["spec"]["config"]["iteration_limit"] == context.ITERATION_LIMIT


# --- merging deltas ---------------------------------------------------------

def test_merge_assembles_tool_call_and_usage():
    events = question_turn()
    base = events[1]
    for delta in events[2:6]:
        context.merge(base, delta)
    call = base["tool_calls"][0]
    assert call["id"] == CALL
    assert call["function"]["name"] == "ask_user_question"
    assert context.arguments_of(call) == {"question": "Which kind of project?", "options": ["python", "node"]}
    assert base["finish_reason"] == "tool_calls"
    assert base["usage"]["input_tokens_breakdown"]["harness"] == 1288


def test_merge_appends_text():
    base = {"type": "model.message", "id": "m"}
    context.merge(base, {"content": "ab"})
    context.merge(base, {"content": "cd"})
    assert base["content"] == "abcd"


# --- the stream and the question loop ---------------------------------------

def test_stream_turn_collects_the_pending_question(client):
    turn = context.stream_turn(client, SESSION, [{"type": "user.message", "content": "go"}])
    assert turn.turn_id == "turn-1"
    assert len(turn.messages) == 1 and len(turn.pending) == 1
    assert turn.metrics["total_tokens"] == 1124
    found = questions.questions(turn)
    assert found == [{"thread_id": "main", "tool_call_id": CALL,
                      "question": "Which kind of project?", "options": ["python", "node"]}]


def test_ask_maps_a_number_to_its_option(capsys):
    def closed(_):
        raise EOFError

    assert questions.ask("Which?", ["python", "node"], read=lambda _: "2") == "node"
    assert questions.ask("Which?", ["python", "node"], read=lambda _: "rust") == "rust"
    assert questions.ask("Which?", [], read=lambda _: "") == "(no answer given)"
    assert questions.ask("Which?", ["python"], read=closed) == "(no answer given)"  # ctrl-d is an answer too
    out = capsys.readouterr().out
    assert "? Which?" in out and "  1. python" in out and "  2. node" in out


def test_run_resumes_with_one_tool_response(client, server):
    deltas = []
    turns = questions.run(client, SESSION, "set up a project for me", read=lambda _: "1",
                          on_delta=deltas.append)
    assert len(turns) == 2
    assert turns[-1].text == "For a Python project: main.py, README.md"
    assert "".join(deltas) == turns[-1].text
    first, resume = [body for path, body in server.requests if path.endswith("/turns")]
    assert first["input"] == [{"type": "user.message", "content": "set up a project for me"}]
    assert resume["input"] == [{"type": "user.tool_response", "thread_id": "main",
                                "tool_call_id": CALL, "content": "python"}]
    assert first["stream"] is True


def test_a_question_in_an_errored_turn_is_not_answered(client, server):
    asked = []
    turns = questions.run(client, SESSION, "fail", read=lambda p: asked.append(p) or "1")
    assert len(turns) == 1 and turns[0].status == "error"
    assert asked == []
    assert len([1 for path, _ in server.requests if path.endswith("/turns")]) == 1
    assert context.status_line(turns[0].state).startswith("status: error - You have reached iteration limit")


def test_a_cut_stream_is_incomplete(client):
    turns = questions.run(client, SESSION, "cut", read=lambda _: "1")
    assert len(turns) == 1 and turns[0].status == "incomplete"
    assert context.status_line(turns[0].state) == "status: incomplete - the stream ended before turn.done"


def test_a_pending_tool_that_is_not_a_question_is_declined(client, server):
    turns = questions.run(client, SESSION, "other-tool", read=lambda _: "1")
    assert len(turns) == 2
    resume = [body for path, body in server.requests if path.endswith("/turns")][1]
    assert resume["input"] == [{"type": "user.tool_response", "thread_id": "main", "tool_call_id": CALL,
                                "content": "Error: this client cannot run open_browser"}]


def test_the_question_loop_is_capped(client, server, monkeypatch):
    monkeypatch.setattr(questions, "MAX_ROUNDS", 3)
    server.keep_asking = True
    turns = questions.run(client, SESSION, "set up a project for me", read=lambda _: "1")
    assert len(turns) == 4  # the first turn and three resumes
    assert turns[-1].status == "error" and "still asking after 3" in turns[-1].state["message"]


def test_sum_metrics_adds_every_turn():
    a = context.Turn(state={"status": "done", "metrics": {"total_input_tokens": 1, "total_tokens": 2}})
    b = context.Turn(state={"status": "done", "metrics": {"total_input_tokens": 10, "total_output_tokens": 5}})
    assert context.sum_metrics([a, b]) == {"total_input_tokens": 11, "total_tokens": 2, "total_output_tokens": 5}
    assert context.sum_metrics([context.Turn()]) == {}


# --- the usage table --------------------------------------------------------

def test_usage_table_has_one_row_per_call_and_a_total():
    messages = [{"type": "model.message", "usage": USAGE},
                {"type": "model.message", "usage": dict(USAGE, input_tokens=1131, output_tokens=54)},
                {"type": "model.message"}]  # a message without usage is skipped
    table = context.usage_table(messages)
    lines = table.splitlines()
    assert lines[0].split() == ["call", *context.CATEGORIES, "input", "output"]
    assert lines[2].split() == ["1", "1,288", "0", "67", "0", "0", "1,091", "33"]
    assert lines[4].split() == ["all", "2,576", "0", "134", "0", "0", "2,222", "87"]
    assert lines[6].startswith("harness") and lines[6].endswith("#" * context.BAR)
    assert lines[8].split() == ["instructions", "134", "##"]
    assert context.usage_table([{"type": "model.message"}]) == "no usage reported"


def test_status_line_reports_the_iteration_limit():
    assert context.status_line({"status": "done"}) == "status: done"
    tripped = {"status": "error", "message": "You have reached iteration limit of 2, please request again"}
    assert context.status_line(tripped) == "status: error - You have reached iteration limit of 2, please request again"
    assert context.status_line({"status": "cancelled", "reason": "client-cancelled"}) == "status: cancelled - client-cancelled"
    assert context.metrics_line({}) == "metrics: none"


# --- the demo end to end -----------------------------------------------------

def test_demo_asks_answers_and_prints_the_table(server, capsys):
    base_url = f"http://127.0.0.1:{server.server_port}"
    assert demo.main(["--answer", "python", "--base-url", base_url]) == 0
    out = capsys.readouterr().out
    assert "? Which kind of project?" in out
    assert "answer> python" in out
    assert "For a Python project: main.py, README.md" in out
    assert "2 turn(s), 2 model call(s)" in out
    assert "all              2,576" in out
    assert "metrics: 2,222 in, 87 out, 2,309 total" in out  # both turns added up
    assert out.rstrip().endswith("status: done")


def test_demo_exits_1_on_an_errored_turn(server, capsys):
    assert demo.main(["fail", "--answer", "python", "--base-url", f"http://127.0.0.1:{server.server_port}"]) == 1
    out = capsys.readouterr().out
    assert "status: error - You have reached iteration limit" in out
    assert "answer>" not in out  # the question in the dead turn was not asked


def test_demo_reports_a_dead_server_in_one_line(capsys, monkeypatch):
    from trueforge_sdk import TrueForge

    monkeypatch.setattr(context, "connect", lambda url: TrueForge(base_url=url, max_retries=0))
    assert demo.main(["--base-url", "http://127.0.0.1:1"]) == 1
    assert capsys.readouterr().err.startswith("request failed: http://127.0.0.1:1 is not answering")
