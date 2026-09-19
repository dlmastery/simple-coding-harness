"""Step 02 offline tests. The model is a fake client that yields scripted
chunks, including tool call fragments; the tests check the tool call and
state events, the JSON Patch code, the client tool hand-off and the
endpoint. The JavaScript side (SSE reader, JSON Patch) has its own
node --test suite, run here through npm when node is on the PATH.
"""

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")
STEP = Path(__file__).resolve().parent
sys.path.insert(0, str(STEP))

import agent  # noqa: E402
import llm  # noqa: E402
from ag_ui.core import AssistantMessage, FunctionCall, RunAgentInput, Tool, ToolCall, ToolMessage, UserMessage  # noqa: E402
from ag_ui.encoder import EventEncoder  # noqa: E402
from json_patch import apply_patch, split_pointer  # noqa: E402
from sse import parse_sse  # noqa: E402
import tools  # noqa: E402
from tools import execute, initial_state  # noqa: E402


def text_chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text, tool_calls=None))])


def call_chunk(index, cid=None, name=None, arguments=None):
    piece = SimpleNamespace(index=index, id=cid, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]))])


class FakeClient:
    """Stands in for llm.client: each request pops the next scripted reply."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(copy.deepcopy(request))  # the agent keeps appending to its list
        return iter(self.replies.pop(0))


METRIC = [
    call_chunk(0, cid="c1", name="show_metric", arguments='{"title": "Cups sold"'),
    call_chunk(0, arguments=', "value": "120", "delta": "+8%"}'),
    call_chunk(1, cid="c2", name="show_chart", arguments='{"kind": "bar", "labels": ["Mon", "Tue"], "values": [40, 80]}'),
]
DONE = [text_chunk("Here is "), text_chunk("your dashboard.")]
CONFIRM = [call_chunk(0, cid="c3", name="confirm_purchase", arguments='{"item": "cooler", "cost": 40}')]
RECORD = [call_chunk(0, cid="c4", name="record_purchase", arguments='{"item": "cooler", "cost": 40}')]

CONFIRM_TOOL = Tool(name="confirm_purchase", description="ask the user", parameters={"type": "object", "properties": {}})


def run_input(messages, state=None, tools=(CONFIRM_TOOL,)):
    return RunAgentInput(
        thread_id="t1", run_id="r1", messages=messages, tools=list(tools), context=[], forwarded_props={}, state=state,
    )


def types(events):
    return [e.type.value for e in events]


def test_tool_calls_become_events_and_state_deltas(monkeypatch):
    fake = FakeClient([METRIC, DONE])
    monkeypatch.setattr(llm, "client", fake)
    events = list(agent.run(run_input([UserMessage(id="u1", content="dashboard please")])))
    assert types(events) == [
        "RUN_STARTED", "STATE_SNAPSHOT",
        "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_ARGS", "TOOL_CALL_END",
        "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END",
        "STATE_DELTA", "TOOL_CALL_RESULT", "STATE_DELTA", "TOOL_CALL_RESULT",
        "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
        "RUN_FINISHED",
    ]
    deltas = [e for e in events if e.type.value == "STATE_DELTA"]
    assert deltas[0].delta == [{"op": "add", "path": "/dashboard/metrics/-", "value": {"title": "Cups sold", "value": "120", "delta": "+8%"}}]
    assert deltas[1].delta[0]["path"] == "/dashboard/chart"
    # the second model request carries the assistant tool calls and both tool results
    second = fake.requests[1]["messages"]
    assert second[-3]["tool_calls"][0]["function"]["name"] == "show_metric"
    assert [m["role"] for m in second[-2:]] == ["tool", "tool"]
    # the state the tools built is the one the snapshot would show next run
    state = initial_state()
    for d in deltas:
        apply_patch(state, d.delta)
    assert state["dashboard"]["chart"]["values"] == [40, 80]


def test_snapshot_comes_from_the_input_state(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient([DONE]))
    state = {"dashboard": {"metrics": [{"title": "x", "value": "1", "delta": ""}], "table": None, "chart": None, "purchases": []}}
    events = list(agent.run(run_input([UserMessage(id="u1", content="hi")], state=state)))
    assert events[1].snapshot == state
    assert events[1].snapshot is not state, "the run works on a copy"


def test_client_tool_ends_the_run_without_a_result(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient([CONFIRM]))
    events = list(agent.run(run_input([UserMessage(id="u1", content="buy a cooler")])))
    assert types(events) == ["RUN_STARTED", "STATE_SNAPSHOT", "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "RUN_FINISHED"]
    assert events[2].tool_call_name == "confirm_purchase"


def test_next_run_continues_from_the_client_tool_result(monkeypatch):
    fake = FakeClient([RECORD, DONE])
    monkeypatch.setattr(llm, "client", fake)
    history = [
        UserMessage(id="u1", content="buy a cooler"),
        AssistantMessage(id="a1", content=None, tool_calls=[
            ToolCall(id="c3", function=FunctionCall(name="confirm_purchase", arguments='{"item": "cooler", "cost": 40}')),
        ]),
        ToolMessage(id="t1", tool_call_id="c3", content="confirmed"),
    ]
    events = list(agent.run(run_input(history)))
    sent = fake.requests[0]["messages"]
    assert sent[-1] == {"role": "tool", "tool_call_id": "c3", "content": "confirmed"}
    assert sent[-2]["tool_calls"][0]["id"] == "c3"
    delta = next(e for e in events if e.type.value == "STATE_DELTA")
    assert delta.delta == [{"op": "add", "path": "/dashboard/purchases/-", "value": {"item": "cooler", "cost": 40}}]
    assert types(events)[-1] == "RUN_FINISHED"


def test_client_tool_schema_reaches_the_model(monkeypatch):
    fake = FakeClient([DONE])
    monkeypatch.setattr(llm, "client", fake)
    list(agent.run(run_input([UserMessage(id="u1", content="hi")])))
    names = [t["function"]["name"] for t in fake.requests[0]["tools"]]
    assert names == ["show_metric", "show_table", "show_chart", "record_purchase", "confirm_purchase"]


def test_execute_never_raises_every_failure_is_a_result(monkeypatch):
    assert execute("nope", "{}") == ("Error: no tool named 'nope'.", [])
    assert execute("show_metric", '{"title": ')[0].startswith("Error: the arguments of show_metric are not a JSON object")
    assert execute("show_metric", "[1, 2]")[0] == "Error: the arguments of show_metric are not a JSON object: got list"
    result, ops = execute("show_metric", '{"title": "t", "value": "1", "bogus": 1}')
    assert result == "Error: got an unexpected keyword argument 'bogus'" and ops == []
    assert execute("show_metric", '{"value": "1"}')[0] == "Error: missing a required argument: 'title'"

    def boom(**args):
        raise ValueError("no chart today")

    monkeypatch.setitem(tools.TOOLS, "show_chart", boom)
    assert execute("show_chart", '{"kind": "bar"}') == ("Error: ValueError: no chart today", [])


def test_tool_failures_are_results_and_the_run_goes_on(monkeypatch):
    """One TOOL_CALL_RESULT per call, error text included; the model gets to try again."""
    broken = [
        call_chunk(0, cid="c1", name="show_metric", arguments='{"title": "Cups"'),  # cut JSON
        call_chunk(1, cid="c2", name="show_gauge", arguments="{}"),                 # no such tool
        call_chunk(2, cid="c3", name="show_metric", arguments='{"value": "1"}'),    # missing title
    ]
    fake = FakeClient([broken, DONE])
    monkeypatch.setattr(llm, "client", fake)
    events = list(agent.run(run_input([UserMessage(id="u1", content="go")])))
    results = [e for e in events if e.type.value == "TOOL_CALL_RESULT"]
    assert [r.tool_call_id for r in results] == ["c1", "c2", "c3"]
    assert all(r.content.startswith("Error") for r in results)
    assert "STATE_DELTA" not in types(events) and types(events)[-1] == "RUN_FINISHED"
    assert [m["role"] for m in fake.requests[1]["messages"][-3:]] == ["tool", "tool", "tool"]


def test_a_model_that_never_stops_calling_tools_hits_the_cap(monkeypatch):
    forever = [[call_chunk(0, cid=f"c{i}", name="show_metric", arguments='{"title": "t", "value": "1"}')] for i in range(50)]
    fake = FakeClient(forever)
    monkeypatch.setattr(llm, "client", fake)
    events = list(agent.run(run_input([UserMessage(id="u1", content="go")])))
    assert len(fake.requests) == agent.MAX_TURNS
    assert events[-1].type.value == "RUN_ERROR" and f"stopped after {agent.MAX_TURNS} tool rounds" in events[-1].message
    assert types(events).count("TOOL_CALL_RESULT") == agent.MAX_TURNS  # every call that was made got its result


def test_text_message_ends_before_the_first_tool_call(monkeypatch):
    """A text message never stays open across tool events: older clients refuse that order."""
    fake = FakeClient([[text_chunk("Sure, ")] + CONFIRM])
    monkeypatch.setattr(llm, "client", fake)
    events = types(agent.run(run_input([UserMessage(id="u1", content="buy a cooler")])))
    assert events.index("TEXT_MESSAGE_END") < events.index("TOOL_CALL_START")
    assert events.count("TEXT_MESSAGE_END") == 1


def test_a_call_without_id_or_name_still_gets_an_id(monkeypatch):
    piece = SimpleNamespace(index=0, id=None, function=SimpleNamespace(name=None, arguments='{"title": "t", "value": "1"}'))
    chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]))])
    monkeypatch.setattr(llm, "client", FakeClient([[chunk]]))
    pieces = list(llm.stream_chat([], []))
    assert pieces[0] == ("tool_start", "call_0", "") and pieces[-1] == ("tool_end", "call_0")


def test_json_patch_python():
    assert split_pointer("/a/b~1c/~0") == ["a", "b/c", "~"]
    doc = {"list": [1, 3], "obj": {}}
    apply_patch(doc, [
        {"op": "add", "path": "/list/1", "value": 2},
        {"op": "add", "path": "/list/-", "value": 4},
        {"op": "replace", "path": "/obj", "value": {"k": "v"}},
        {"op": "remove", "path": "/obj/k"},
    ])
    assert doc == {"list": [1, 2, 3, 4], "obj": {}}
    for bad in (
        {"op": "move", "path": "/list/0", "from": "/list/1"},   # not one of the three
        {"op": "add", "path": "/list/x", "value": 1},           # not a list index
        {"op": "add", "path": "/nowhere/k", "value": 1},        # no such parent
        {"op": "replace", "path": "", "value": {}},             # the root
    ):
        with pytest.raises(ValueError):
            apply_patch(doc, [bad])
    assert doc == {"list": [1, 2, 3, 4], "obj": {}}  # nothing half-applied


def test_wire_format_of_state_events(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient([METRIC, DONE]))
    encoder = EventEncoder()
    lines = [encoder.encode(e) for e in agent.run(run_input([UserMessage(id="u1", content="go")]))]
    events = parse_sse("".join(lines))
    start = next(e for e in events if e["type"] == "TOOL_CALL_START")
    assert set(start) == {"type", "toolCallId", "toolCallName", "parentMessageId"}
    delta = next(e for e in events if e["type"] == "STATE_DELTA")
    assert delta["delta"][0]["op"] == "add"


def test_endpoint_streams_tool_events(monkeypatch):
    from fastapi.testclient import TestClient

    import server

    monkeypatch.setattr(llm, "client", FakeClient([METRIC, DONE]))
    with TestClient(server.app) as client:
        body = json.loads(run_input([UserMessage(id="u1", content="go")]).model_dump_json(by_alias=True))
        with client.stream("POST", "/agent", json=body, headers={"accept": "text/event-stream"}) as response:
            assert response.status_code == 200
            text = "".join(response.iter_text())
        assert client.get("/render.mjs").status_code == 200
    kinds = [e["type"] for e in parse_sse(text)]
    assert "STATE_DELTA" in kinds and kinds[-1] == "RUN_FINISHED"


def test_disconnect_closes_the_generator(monkeypatch):
    """The endpoint pulls one event per step; when the page has gone it closes the run."""
    import asyncio

    import server

    closed = []

    class Run:
        def __init__(self):
            self.it = iter(agent.run(run_input([UserMessage(id="u1", content="go")])))

        def __next__(self):
            return next(self.it)

        def close(self):
            closed.append(True)

    class Request:
        headers = {}

        async def is_disconnected(self):
            return True

    monkeypatch.setattr(llm, "client", FakeClient([DONE]))
    monkeypatch.setattr(server, "run", lambda input: Run())
    body = server.agent_endpoint(run_input([UserMessage(id="u1", content="go")]), Request()).body_iterator

    async def drain():
        return [frame async for frame in body]

    assert asyncio.run(drain()) == [] and closed == [True]


def test_node_suite_passes():
    node, npm = shutil.which("node"), shutil.which("npm")
    if node is None:
        pytest.skip("node is not installed")
    package = json.loads((STEP / "package.json").read_text(encoding="utf-8"))
    needs_install = package.get("dependencies") or package.get("devDependencies")
    if needs_install and not (STEP / "node_modules").exists():
        if npm is None:
            pytest.skip("npm is not installed")
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True, capture_output=True)
    result = subprocess.run([node, "--test"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
