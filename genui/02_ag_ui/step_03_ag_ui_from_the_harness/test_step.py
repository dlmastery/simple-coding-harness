"""Step 03 offline tests. The harness's model client is the same fake the
harness codelab uses: scripted chunks with text and tool call fragments.
The tests check that the bridge turns one harness turn into the right AG-UI
events, that real harness tools run (in a temp work directory) with the
permission layer reporting through CUSTOM events, and that the endpoint
streams. The @ag-ui/client side has a node --test suite against a fake
server; test_step.py runs npm install, npm run build and node --test when
node is on the PATH.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")
STEP = Path(__file__).resolve().parent
sys.path.insert(0, str(STEP))
# The harness takes the current directory as its project when it is imported,
# so the server (which imports the bridge) is pointed at a temp directory first.
WORKDIR = Path(tempfile.mkdtemp(prefix="agui-step03-"))
os.environ["HARNESS_WORKDIR"] = str(WORKDIR)

import server  # noqa: E402  (chdir + harness import happen here)
import bridge  # noqa: E402
from ag_ui.core import RunAgentInput, UserMessage  # noqa: E402
from ag_ui.encoder import EventEncoder  # noqa: E402
from harness import llm as harness_llm  # noqa: E402
from harness import todos  # noqa: E402
from sse import parse_sse  # noqa: E402


def text_chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text, tool_calls=None))], usage=None)


def call_chunk(index, cid=None, name=None, arguments=None):
    piece = SimpleNamespace(index=index, id=cid, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]))], usage=None)


def usage_chunk(prompt=40, completion=9):
    usage = SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion,
                            completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
                            prompt_tokens_details=SimpleNamespace(cached_tokens=0))
    return SimpleNamespace(choices=[], usage=usage)


class FakeClient:
    """Stands in for harness.llm.client: each request pops the next scripted reply."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(json.loads(json.dumps(request)))
        return iter(self.replies.pop(0))


WRITE_THEN_RUN = [
    text_chunk("Writing "), text_chunk("the file."),
    call_chunk(0, cid="c1", name="write_file", arguments='{"path": "hello.py", '),
    call_chunk(0, arguments='"content": "print(\\"hi\\")"}'),
    call_chunk(1, cid="c2", name="bash", arguments='{"command": "python hello.py"}'),
    usage_chunk(),
]
PLAN = [
    call_chunk(0, cid="c3", name="write_todos", arguments=json.dumps({"todos": [
        {"content": "write hello.py", "activeForm": "Writing hello.py", "status": "in_progress"},
        {"content": "run it", "activeForm": "Running it", "status": "pending"},
    ]})),
    usage_chunk(),
]
DONE = [text_chunk("All done."), usage_chunk(prompt=80, completion=3)]


def run_input(text="write hello.py and run it"):
    return RunAgentInput(thread_id="t1", run_id="r1", messages=[UserMessage(id="u1", content=text)],
                         tools=[], context=[], forwarded_props={}, state={})


def types(events):
    return [e.type.value for e in events]


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(bridge.todos, "TODOS", todos.TODOS)

    def install(replies):
        client = FakeClient(replies)
        monkeypatch.setattr(harness_llm, "client", client)
        return client

    return install


def test_one_turn_becomes_events(fake):
    client = fake([WRITE_THEN_RUN, DONE])
    events = list(bridge.run(run_input()))
    assert types(events) == [
        "RUN_STARTED", "STATE_SNAPSHOT",
        "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
        "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "TOOL_CALL_RESULT",
        "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "CUSTOM", "TOOL_CALL_RESULT",
        "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
        "RUN_FINISHED",
    ]
    # the harness's real tools ran in the work directory
    assert (WORKDIR / "hello.py").read_text() == 'print("hi")'
    results = [e for e in events if e.type.value == "TOOL_CALL_RESULT"]
    assert results[0].content == "Wrote hello.py"
    assert results[1].content.strip() == "hi"
    # bash needed permission: the rules said ask, the bridge said allow and told the page
    custom = next(e for e in events if e.type.value == "CUSTOM")
    assert custom.name == "permission" and custom.value == {"reason": "run: python hello.py", "decision": "allow"}
    # usage from the harness's streamed call rides on RUN_FINISHED
    assert events[-1].usage[0].input_tokens == 80 and events[-1].usage[0].output_tokens == 3
    # the second request carried the tool results and the harness's late injection
    second = client.requests[1]["messages"]
    assert [m["role"] for m in second[-3:]] == ["tool", "tool", "user"]
    assert "<env>" in second[-1]["content"]


def test_write_todos_becomes_state_delta(fake):
    fake([PLAN, DONE])
    events = list(bridge.run(run_input()))
    assert events[1].snapshot == {"todos": []}
    delta = next(e for e in events if e.type.value == "STATE_DELTA")
    assert delta.delta[0]["op"] == "replace" and delta.delta[0]["path"] == "/todos"
    assert [t["status"] for t in delta.delta[0]["value"]] == ["in_progress", "pending"]
    assert types(events).index("STATE_DELTA") > types(events).index("TOOL_CALL_RESULT")


def test_system_prompt_is_the_harness_prompt(fake):
    client = fake([DONE])
    list(bridge.run(run_input("hi")))
    first = client.requests[0]["messages"][0]
    assert first["role"] == "system" and "coding agent" in first["content"]
    assert client.requests[0]["stream"] is True


def test_model_failure_becomes_run_error(monkeypatch):
    def boom(**request):
        raise RuntimeError("model down")

    monkeypatch.setattr(harness_llm, "client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom))))
    events = list(bridge.run(run_input()))
    assert types(events)[-1] == "RUN_ERROR" and events[-1].message == "model down"


def test_endpoint_streams_the_harness(fake):
    from fastapi.testclient import TestClient

    fake([WRITE_THEN_RUN, DONE])
    with TestClient(server.app) as client:
        body = json.loads(run_input().model_dump_json(by_alias=True))
        with client.stream("POST", "/agent", json=body, headers={"accept": "text/event-stream"}) as response:
            assert response.status_code == 200
            text = "".join(response.iter_text())
        assert client.get("/").status_code == 200
    events = parse_sse(text)
    start = next(e for e in events if e["type"] == "TOOL_CALL_START")
    assert start["toolCallName"] == "write_file"
    assert events[-1]["type"] == "RUN_FINISHED" and events[-1]["usage"][0]["inputTokens"] == 80


def test_wire_omits_empty_optional_fields(fake):
    fake([DONE])
    lines = [EventEncoder().encode(e) for e in bridge.run(run_input())]
    finished = json.loads(lines[-1][6:])
    assert "outcome" not in finished and "result" not in finished


def test_node_suite_and_bundle():
    node, npm = shutil.which("node"), shutil.which("npm")
    if node is None:
        pytest.skip("node is not installed")
    if not (STEP / "node_modules").exists():
        if npm is None:
            pytest.skip("npm is not installed")
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True, capture_output=True, shell=os.name == "nt")
    result = subprocess.run([node, "--test"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    if not (STEP / "vendor" / "ag-ui-client.js").exists() and npm is not None:
        subprocess.run([npm, "run", "build"], cwd=STEP, check=True, capture_output=True, shell=os.name == "nt")
    assert (STEP / "vendor" / "ag-ui-client.js").exists(), "the page needs the bundled @ag-ui/client"
