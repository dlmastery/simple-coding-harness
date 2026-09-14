"""Step 47 - offline tests: the MCP tools server in-process, and the approval loop
against a fake TrueForge server that speaks hand-written SSE. Nothing here
contacts a model, port 8790, or port 8931."""

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import register
import tools_server
from client import approve
from client.connect import connect


# --- the tools server ------------------------------------------------------


@pytest.fixture
def project(tmp_path):
    (tmp_path / "hello.py").write_text('def hello():\n    print("hello")\n', encoding="utf-8")
    (tmp_path / "pkg").mkdir()
    tools_server.PROJECT = tmp_path.resolve()
    return tmp_path


def test_tools_carry_annotations(project):
    """TrueForge reads readOnlyHint and destructiveHint to decide what pauses."""
    from mcp.shared.memory import create_connected_server_and_client_session

    async def run():
        server = tools_server.build_server(project)
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            listed = await session.list_tools()
            hints = {t.name: t.annotations.model_dump(exclude_none=True) for t in listed.tools}
            result = await session.call_tool("read_file", {"path": "hello.py"})
            return hints, result.content[0].text

    hints, text = asyncio.run(run())
    assert set(hints) == {"read_file", "list_dir", "write_file", "str_replace", "bash"}
    for name in ("read_file", "list_dir"):
        assert hints[name]["readOnlyHint"] is True and hints[name]["destructiveHint"] is False
    for name in ("write_file", "str_replace", "bash"):
        assert hints[name]["readOnlyHint"] is False and hints[name]["destructiveHint"] is True
    assert text.startswith("def hello():")


def test_tools_run_inside_the_project(project):
    assert tools_server.list_dir(".") == "hello.py\npkg/"
    assert tools_server.write_file("pkg/a.txt", "one") == "Wrote pkg/a.txt"
    assert tools_server.read_file("pkg/a.txt") == "one"
    assert tools_server.str_replace("pkg/a.txt", "one", "two") == "Replaced 1 match(es) in pkg/a.txt"
    assert tools_server.read_file("pkg/a.txt") == "two"
    assert "43" in tools_server.bash('python -c "print(42 + 1)"')


def test_errors_are_results(project):
    """A bad path or a bad match comes back as text, never as an exception."""
    assert tools_server.read_file("../outside.txt").startswith("Error:")
    assert tools_server.write_file("../outside.txt", "x").startswith("Error:")
    assert tools_server.read_file("missing.py").startswith("Error:")
    assert tools_server.str_replace("hello.py", "nope", "x") == "Error: old_str was not found in hello.py"
    tools_server.write_file("twice.txt", "a a")
    assert tools_server.str_replace("twice.txt", "a", "b").startswith("Error: old_str matches 2 times")
    assert tools_server.str_replace("twice.txt", "a", "b", allow_multi_edit=True) == "Replaced 2 match(es) in twice.txt"
    assert not (project.parent / "outside.txt").exists()


# --- a fake TrueForge server -------------------------------------------------


def sse(events):
    """Encode events as one SSE body: `data: {...}` lines separated by blank lines."""
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events).encode()


def ev(type_, id_, **fields):
    return {"type": type_, "id": id_, "created_at": "2026-01-01T00:00:00Z", "thread_id": "main", **fields}


DONE = {"completed_at": "2026-01-01T00:00:01Z", "required_actions": []}
PAUSED = [
    ev("turn.created", "e0", thread_id=None, turn_id="t1", input=[], state={"status": "running"}),
    ev("model.message", "m1"),
    ev("model.message.delta", "m1", tool_calls=[{"index": 0, "id": "call-1", "function": {"name": "str_replace", "arguments": '{"path": "hel'}}]),
    ev("model.message.delta", "m1", tool_calls=[{"index": 0, "function": {"arguments": 'lo.py", "old_str": "a", "new_str": "b"}'}}]),
    ev("tool.approval_required", "a1", tool_calls=[{"id": "call-1", "source_event_id": "m1"}]),
    ev("turn.done", "e9", thread_id=None, state={"status": "done", "output": None, "metrics": {"total_input_tokens": 100, "total_output_tokens": 10, "total_tokens": 110}, **DONE}),
]
FINISHED = [
    ev("turn.created", "e0", thread_id=None, turn_id="t2", input=[], state={"status": "running"}),
    ev("tool.response", "r1", tool_call_id="call-1", content='{"result":"Replaced 1 match(es) in hello.py"}'),
    ev("model.message", "m2"),
    ev("model.message.delta", "m2", content="Done, "),
    ev("model.message.delta", "m2", content="one edit."),
    ev("turn.done", "e9", thread_id=None, state={"status": "done", "output": ev("model.message", "m2", content="Done, one edit."), "metrics": {"total_input_tokens": 200, "total_output_tokens": 20, "total_tokens": 220}, **DONE}),
]
TOOLS = [
    {"name": "read_file", "annotations": {"readOnlyHint": True, "destructiveHint": False}},
    {"name": "bash", "annotations": {"readOnlyHint": False, "destructiveHint": True}},
]


class FakeTrueForge(BaseHTTPRequestHandler):
    """Answers the four requests the step makes. Every request body is kept for the assertions."""

    requests: list = []
    turns: list = []  # SSE event lists, one per POST .../turns, consumed in order

    def log_message(self, *args):
        pass

    def body(self):
        length = int(self.headers.get("content-length") or 0)
        return json.loads(self.rfile.read(length) or b"null")

    def reply(self, status, payload, content_type="application/json"):
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_PUT(self):
        manifest = self.body()["manifest"]
        self.requests.append(("PUT", self.path, manifest))
        saved = {"data": {"name": manifest["name"], "manifest": manifest, "auth_status": {"status": "not_required"}}}
        self.reply(200, json.dumps(saved).encode())

    def do_GET(self):
        self.requests.append(("GET", self.path, None))
        self.reply(200, json.dumps({"data": TOOLS}).encode())

    def do_POST(self):
        payload = self.body()
        self.requests.append(("POST", self.path, payload))
        if self.path.endswith("/turns"):
            self.reply(200, sse(self.turns.pop(0)), "text/event-stream")
        else:
            self.reply(201, json.dumps({"data": {"id": "sess-1", "agent": {"type": "inline", "spec": payload["agent"]["spec"]}}}).encode())


@pytest.fixture
def fake():
    FakeTrueForge.requests = []
    FakeTrueForge.turns = []
    httpd = HTTPServer(("127.0.0.1", 0), FakeTrueForge)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield connect(f"http://127.0.0.1:{httpd.server_port}")
    httpd.shutdown()


def test_register_sends_a_remote_manifest_without_auth(fake):
    saved = register.register(fake, "http://localhost:8931/mcp")
    method, path, manifest = FakeTrueForge.requests[0]
    assert (method, path) == ("PUT", "/api/v1/settings/mcp-servers")
    assert manifest == {"type": "remote", "name": "s47-tools", "url": "http://localhost:8931/mcp", "description": register.DESCRIPTION}
    assert saved["name"] == "s47-tools"
    tools = register.list_tools(fake)
    assert FakeTrueForge.requests[1][1] == "/api/v1/mcp-servers/s47-tools/tools"
    assert [register.gate(t) for t in tools] == ["runs", "asks (@destructive)"]


def test_agent_spec_attaches_the_server_deferred():
    spec = approve.agent_spec().spec
    assert spec.model.name == "openai/gpt-4-1-mini"
    server = spec.mcp_servers[0]
    assert server.name == "s47-tools"
    assert server.preload is False
    assert server.preload_tools == ["read_file", "str_replace"]
    assert server.require_approval_for_tools is None  # the default: @write and @destructive
    assert spec.config.iteration_limit == 12


def test_merge_delta_assembles_text_and_tool_calls():
    from trueforge_sdk import ModelMessageDeltaEvent

    message = {"content": "", "tool_calls": []}
    for raw in PAUSED[2:4]:
        approve.merge_delta(message, ModelMessageDeltaEvent(**raw))
    approve.merge_delta(message, ModelMessageDeltaEvent(id="m1", thread_id="main", content="hi"))
    assert message["content"] == "hi"
    assert message["tool_calls"] == [{"id": "call-1", "name": "str_replace", "arguments": '{"path": "hello.py", "old_str": "a", "new_str": "b"}'}]
    assert approve.describe_call(message["tool_calls"][0]) == 'str_replace {"path": "hello.py", "old_str": "a", "new_str": "b"}'


def test_describe_call_unwraps_the_meta_tool():
    call = {"id": "c", "name": "call_tool", "arguments": '{"mcp_server": "s47-tools", "tool_name": "bash", "input": {"command": "ls"}}'}
    assert approve.describe_call(call) == 'bash {"command": "ls"}'


def scripted(answers):
    answers = list(answers)
    return lambda prompt: answers.pop(0)


def quiet(*args, **kwargs):
    pass


def test_approval_loop_allows_and_resumes(fake):
    FakeTrueForge.turns = [PAUSED, FINISHED]
    printed = []
    approver = approve.Approver(scripted(["y"]))
    result = approve.chat(fake, "sess-1", "edit it", approver, out=lambda *a, **k: printed.append("".join(map(str, a))))
    first, second = [r[2] for r in FakeTrueForge.requests if r[0] == "POST"]
    assert first["input"] == [{"type": "user.message", "content": "edit it"}]
    assert second["input"] == [{"type": "user.tool_approval", "thread_id": "main", "tool_call_id": "call-1", "approval": {"status": "allow"}}]
    assert result.text == "Done, one edit."
    assert result.metrics["total_tokens"] == 330  # summed over both turns
    assert any("Replaced 1 match" in line for line in printed)


def test_approval_loop_denies_with_a_reason(fake):
    FakeTrueForge.turns = [PAUSED, FINISHED]
    approve.chat(fake, "sess-1", "edit it", approve.Approver(scripted(["maybe", "n"])), out=quiet)
    second = [r[2] for r in FakeTrueForge.requests if r[0] == "POST"][1]
    assert second["input"][0]["approval"] == {"status": "deny", "reason": "The user denied this tool call."}


def test_always_answers_the_next_pause_itself(fake):
    FakeTrueForge.turns = [PAUSED, PAUSED, FINISHED]
    approver = approve.Approver(scripted(["a"]))  # one answer for two pauses
    approve.chat(fake, "sess-1", "edit it", approver, out=quiet)
    posts = [r[2] for r in FakeTrueForge.requests if r[0] == "POST"]
    assert len(posts) == 3
    assert posts[1]["input"][0]["approval"] == {"status": "allow"}
    assert posts[2]["input"][0]["approval"] == {"status": "allow"}
    assert approver.always == {"str_replace"}
