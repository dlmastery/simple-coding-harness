import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, llm, mcp_client, permissions, session, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

STEP = Path(__file__).parent


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def part(text=None, kind="text"):
    """One content part of a tool result: text, or something else like an image."""
    return SimpleNamespace(type=kind, text=text) if text is not None else SimpleNamespace(type=kind)


def tool(name, description, properties, required=()):
    """What ClientSession.list_tools() hands back per tool: name, description, inputSchema."""
    return SimpleNamespace(name=name, description=description, inputSchema={"type": "object", "properties": properties, "required": list(required)})


class FakeSession:
    """Stands in for mcp.ClientSession: an async call_tool that logs and answers."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        reply = self.answers[name]
        if isinstance(reply, Exception):
            raise reply
        return reply


ECHO_TOOLS = [
    tool("echo", "Return the text unchanged.", {"text": {"type": "string"}}, ["text"]),
    tool("shout", None, {"text": {"type": "string"}}),
]


@pytest.fixture
def registry(monkeypatch):
    """A fresh client and registry: MCP tools added by a test vanish after it."""
    monkeypatch.setattr(mcp_client, "_client", None)
    monkeypatch.setattr(mcp_client, "SERVERS", {})
    monkeypatch.setattr(tools, "TOOLS", dict(tools.TOOLS))
    monkeypatch.setattr(tools, "TOOL_SCHEMAS", list(tools.TOOL_SCHEMAS))
    yield tools
    mcp_client.close_all()


@pytest.fixture
def fake_server(registry):
    """A server named fake, connected through a FakeSession, with two tools."""
    fake = FakeSession({
        "echo": SimpleNamespace(content=[part("hello"), part(kind="image"), part("world")], isError=False),
        "shout": SimpleNamespace(content=[part("too loud")], isError=True),
    })
    mcp_client.client().sessions["fake"] = fake
    mcp_client.register("fake", ECHO_TOOLS)
    return fake


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)


# ------------------------------------------------------------ registration


def test_register_mangles_names_and_passes_the_schema_through(fake_server, registry):
    assert "mcp__fake__echo" in registry.TOOLS and "mcp__fake__shout" in registry.TOOLS
    schemas = {s["function"]["name"]: s["function"] for s in registry.TOOL_SCHEMAS}
    assert schemas["mcp__fake__echo"]["description"] == "Return the text unchanged."
    assert schemas["mcp__fake__echo"]["parameters"] == ECHO_TOOLS[0].inputSchema  # the server's schema, untouched
    assert schemas["mcp__fake__shout"]["description"] == "shout from the fake MCP server"  # a missing description gets one


def test_wrapper_joins_text_parts_and_names_the_rest(fake_server, registry):
    assert registry.TOOLS["mcp__fake__echo"](text="hi") == "hello\n[image part]\nworld"
    assert fake_server.calls == [("echo", {"text": "hi"})]  # keyword args become the MCP arguments dict


def test_error_results_and_failed_calls_come_back_as_error_strings(fake_server, registry):
    assert registry.TOOLS["mcp__fake__shout"](text="hi") == "Error: too loud"
    fake_server.answers["echo"] = RuntimeError("server went away\nmore detail")
    assert registry.TOOLS["mcp__fake__echo"](text="hi") == "Error: RuntimeError: server went away"
    assert mcp_client.call_tool("nowhere", "echo", {}) == "Error: RuntimeError: MCP server nowhere is not connected"


def test_long_results_are_capped_like_any_tool_output(fake_server, registry, monkeypatch):
    fake_server.answers["echo"] = SimpleNamespace(content=[part("word " * 5000)], isError=False)
    monkeypatch.setattr(mcp_client.history, "spill", lambda text: "SPILLED")
    out = registry.TOOLS["mcp__fake__echo"](text="hi")
    assert len(out) < 12_000 and mcp_client.history.CAPPED in out  # the whole text is on disk for this turn


def test_connect_all_notes_and_skips_a_server_that_fails(registry, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))

    def connect(self, name, spec):
        if name == "broken":
            raise FileNotFoundError("[WinError 2] The system cannot find the file specified")
        return ECHO_TOOLS[:1]

    monkeypatch.setattr(mcp_client.Client, "connect", connect)
    servers = mcp_client.connect_all({"broken": {"command": "nope", "args": []}, "good": {"command": "x", "args": []}})
    assert servers["good"] == {"status": "connected", "tools": ["mcp__good__echo"]}
    assert servers["broken"]["status"].startswith("failed: FileNotFoundError")
    assert notes == ["mcp server 'broken' failed to start (FileNotFoundError: [WinError 2] The system cannot find the file specified); skipped"]
    assert "mcp__good__echo" in registry.TOOLS and "mcp__broken__echo" not in registry.TOOLS


# -------------------------------------------------------------- permissions


def test_mcp_tools_ask_unless_allow_listed(monkeypatch):
    monkeypatch.setattr(permissions, "MCP_ALLOW", [])
    action, reason = permissions.check("mcp__echo__echo", {"text": "hi"})
    assert action == "ask" and reason == 'call MCP tool mcp__echo__echo with {"text": "hi"}'
    monkeypatch.setattr(permissions, "MCP_ALLOW", ["mcp__fs__*", "mcp__echo__add"])
    assert permissions.check("mcp__fs__read_file", {"path": "x"}) == ("allow", None)
    assert permissions.check("mcp__echo__add", {"a": 1, "b": 2}) == ("allow", None)
    assert permissions.check("mcp__echo__echo", {"text": "hi"})[0] == "ask"
    assert permissions.check("read_file", {"path": "x"}) == ("allow", None)  # built-ins are untouched


# ------------------------------------------------------------------ config


def test_config_merges_files_and_resolves_python_and_paths(tmp_path, monkeypatch):
    home = tmp_path / "home" / "mcp.json"
    project = tmp_path / "project" / ".agents" / "mcp.json"
    home.parent.mkdir(parents=True)
    project.parent.mkdir(parents=True)
    (project.parent / "server.py").write_text("")
    home.write_text(json.dumps({"servers": {"fs": {"command": "npx", "args": ["-y", "server-fs"]}, "echo": {"command": "old"}}}))
    project.write_text(json.dumps({"mcpServers": {"echo": {"command": "python", "args": [".agents/server.py"], "env": {"LEVEL": "1", "TOKEN": "${HARNESS_TEST_TOKEN}"}}}}))
    monkeypatch.chdir(project.parent.parent)
    monkeypatch.setenv("HARNESS_TEST_TOKEN", "t0k3n")

    servers = mcp_client.load_config([home, project])
    assert set(servers) == {"fs", "echo"}
    assert servers["fs"] == {"command": "npx", "args": ["-y", "server-fs"], "env": {}}
    assert servers["echo"]["command"] == sys.executable  # not whatever `python` means on this PATH
    assert servers["echo"]["args"] == [str((project.parent / "server.py").resolve())]
    assert servers["echo"]["env"] == {"LEVEL": "1", "TOKEN": "t0k3n"}  # only what the file names, ${VAR} filled in
    assert "API_KEY" not in servers["echo"]["env"]  # the harness's own key never reaches a server
    assert mcp_client.load_config([tmp_path / "missing.json"]) == {}


def test_a_broken_config_file_is_noted_and_skipped(tmp_path, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    (tmp_path / "mcp.json").write_text("{not json", encoding="utf-8")
    assert mcp_client.load_config([tmp_path / "mcp.json"]) == {}
    assert len(notes) == 1 and notes[0].startswith("mcp config") and "skipped" in notes[0]


def test_tool_names_are_made_safe_for_the_api(registry):
    assert mcp_client.tool_name("my server", "fs.read") == "mcp__my_server__fs_read"
    assert len(mcp_client.tool_name("x" * 40, "y" * 40)) == 64
    long_tools = [tool("a.b", "", {}), tool("a_b", "", {})]  # both sanitise to the same name
    names = mcp_client.register("s", long_tools)
    assert names == ["mcp__s__a_b", "mcp__s__a_b_2"]


def test_shipped_config_points_at_the_echo_server():
    config = json.loads((STEP / ".agents" / "mcp.json").read_text())
    assert config["servers"]["echo"]["args"] == [".agents/mcp_echo_server.py"]
    assert (STEP / ".agents" / "mcp_echo_server.py").exists()


# ---------------------------------------------------------------- commands


def test_mcp_command_lists_servers_status_and_tools(registry, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/mcp", messages) is messages
    assert notes == ["no MCP servers configured (see .agents/mcp.json)"]
    mcp_client.SERVERS.update({
        "echo": {"status": "connected", "tools": ["mcp__echo__echo", "mcp__echo__add"]},
        "broken": {"status": "failed: FileNotFoundError: nope", "tools": []},
    })
    commands.handle("/mcp", messages)
    lines = notes[-1].splitlines()
    assert lines[0].startswith("echo") and "connected" in lines[0] and "mcp__echo__echo, mcp__echo__add" in lines[0]
    assert lines[1].startswith("broken") and "failed: FileNotFoundError: nope" in lines[1] and lines[1].endswith("-")
    assert "/mcp" in commands.COMMANDS


# --------------------------------------------------------------- the loop


def test_turn_runs_an_mcp_tool_and_feeds_the_result_back(fake_server, registry, quiet, monkeypatch):
    replies = [
        FakeMessage(content=None, tool_calls=[call("m1", "mcp__fake__echo", '{"text": "ping"}')]),
        FakeMessage(content="The server said hello world.", tool_calls=None),
    ]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))
    monkeypatch.setattr(permissions, "MCP_ALLOW", ["mcp__fake__*"])
    messages = agent.turn([{"role": "system", "content": llm.SYSTEM_PROMPT}], "ping the fake server")
    assert fake_server.calls == [("echo", {"text": "ping"})]
    assert messages[3] == {"role": "tool", "tool_call_id": "m1", "content": "hello\n[image part]\nworld"}
    assert messages[-1]["content"] == "The server said hello world."


# ------------------------------------------------------------------ live


def test_live_echo_server_over_stdio(registry):
    pytest.importorskip("mcp")
    server = STEP / ".agents" / "mcp_echo_server.py"
    servers = mcp_client.connect_all({"echo": {"command": sys.executable, "args": [str(server)], "env": None}})
    assert servers["echo"] == {"status": "connected", "tools": ["mcp__echo__echo", "mcp__echo__add"]}
    schema = next(s["function"] for s in registry.TOOL_SCHEMAS if s["function"]["name"] == "mcp__echo__echo")
    assert schema["parameters"]["required"] == ["text"] and schema["description"] == "Return the text unchanged."
    assert registry.TOOLS["mcp__echo__echo"](text="round trip") == "round trip"
    assert registry.TOOLS["mcp__echo__add"](a=2, b=3) == "5.0"
    assert registry.TOOLS["mcp__echo__add"](a="x", b=3).startswith("Error: Error executing tool add")
    client = mcp_client._client
    mcp_client.close_all()
    assert mcp_client._client is None and not client.thread.is_alive()  # the loop thread is gone too


# ----------------------------------------------- the error paths of the loop


def raw_call(cid, name, arguments):
    """A tool call whose arguments are exactly this string, valid JSON or not."""
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def fake_model(monkeypatch, *replies):
    """A call_llm that plays the replies in order, for the main loop."""
    queue = list(replies)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (queue.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))


def test_bad_arguments_unknown_tool_and_a_raising_tool_each_get_one_tool_message(quiet, monkeypatch, tmp_path):
    fake_model(
        monkeypatch,
        FakeMessage(content=None, tool_calls=[
            raw_call("c1", "read_file", '{"path": '),                                   # cut off mid-stream
            raw_call("c2", "no_such_tool", "{}"),                                       # a name the registry lacks
            raw_call("c3", "read_file", json.dumps({"path": str(tmp_path / "no.txt")})),  # the tool raises
            raw_call("c4", "bash", "[1, 2]"),                                           # JSON, but not an object
            raw_call("c5", "bash", "{}"),                                               # a required argument missing
        ]),
        FakeMessage(content="None of that worked.", tool_calls=None),
    )
    messages = agent.turn([{"role": "system", "content": "s"}], "try a few things")
    results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
    assert list(results) == ["c1", "c2", "c3", "c4", "c5"]  # one tool message per call, in reply order
    assert results["c1"].startswith("Error: the arguments of read_file are not a JSON object:")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: FileNotFoundError:")
    assert results["c4"] == "Error: the arguments of bash are not a JSON object: got list"
    assert results["c5"] == "Blocked by policy: bash: missing argument 'command'"
    assert messages[-1]["content"] == "None of that worked."  # the loop went on to the next reply


def test_a_failed_model_call_is_a_note_and_the_transcript_stays_valid(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))

    def down(messages, tools=None, on_delta=None):
        raise openai.APIConnectionError(request=httpx.Request("POST", "https://example.invalid/v1"))

    monkeypatch.setattr(agent, "call_llm", down)
    messages = agent.turn([{"role": "system", "content": "s"}], "hello?")
    assert [m["role"] for m in messages] == ["system", "user"]  # the prompt stays, nothing dangles
    assert notes[-1].startswith("model call failed:")


def test_ctrl_c_mid_turn_answers_the_pending_tool_calls(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    fake_model(monkeypatch, FakeMessage(content=None, tool_calls=[raw_call("c1", "bash", json.dumps({"command": "echo hi"}))]))

    def interrupted(tool_calls, allowed=None):
        raise KeyboardInterrupt

    monkeypatch.setattr(agent, "execute_all", interrupted)
    messages = agent.turn([{"role": "system", "content": "s"}], "run it")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": agent.INTERRUPTED}
    assert notes[-1] == "interrupted"


def test_the_turn_stops_after_max_calls(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    monkeypatch.setattr(agent, "MAX_CALLS", 3)
    forever = lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=[raw_call("c", "bash", '{"command": "echo again"}')]), {"prompt_tokens": 1, "completion_tokens": 1})
    monkeypatch.setattr(agent, "call_llm", forever)
    messages = agent.turn([{"role": "system", "content": "s"}], "loop")
    assert sum(1 for m in messages if m["role"] == "assistant") == 3
    assert messages[-1]["role"] == "tool"  # every call answered before the stop
    assert notes[-1] == "stopped after 3 model calls in one turn; say 'continue' to go on"


def test_session_load_repairs_a_dangling_tool_call(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    pending = {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]}
    (tmp_path / "old.jsonl").write_text("".join(json.dumps(m) + "\n" for m in [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}, pending]), encoding="utf-8")
    messages = session.load("old")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": session.UNANSWERED}
    assert session.repair([{"role": "user", "content": "hi"}]) == [{"role": "user", "content": "hi"}]  # nothing to repair


def test_rewind_offers_only_user_messages_and_leaves_no_orphan(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "x"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "ok"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    kept = commands.handle("/rewind", list(messages))
    assert len(offered) == 2 and "first" in offered[0] and "second" in offered[1]  # never the tool call
    assert kept == messages[:5]
    monkeypatch.setattr(ui, "pick", lambda title, rows: 0)
    assert commands.handle("/rewind", list(messages)) == messages[:1]
    assert (tmp_path / f"{session.CURRENT}.jsonl").exists()  # a fresh chat got its file before the marker


def test_write_todos_rejects_a_bad_status_and_leaves_the_list_alone(monkeypatch):
    monkeypatch.setattr(todos, "TODOS", [{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b"}]) == "Error: item 0 needs a non-empty string 'activeForm'"
    assert todos.write_todos("b").startswith("Error:")
    assert todos.write_todos([{"content": "b", "activeForm": "b", "status": "in_progress"}, {"content": "c", "activeForm": "c", "status": "in_progress"}]).startswith("Error: 2 tasks are in_progress")
    assert todos.TODOS == before


def test_utf8_survives_write_file_read_file_and_bash(tmp_path):
    path = tmp_path / "näme.txt"
    text = "héllo wörld — ünïcode ✓\r\nline two\n"
    assert tools.write_file(str(path), text).startswith("Wrote")
    assert tools.read_file(str(path)) == text  # bytes and line endings as written
    assert tools.str_replace(str(path), "", "x") == "Error: old_str is empty; give the exact text to replace"
    assert tools.bash(f'"{sys.executable}" -X utf8 -c "print(\'ünïcode ✓\')"').strip() == "ünïcode ✓"
    assert tools.write_file(str(tmp_path / "deep" / "er" / "file.txt"), "x") == f"Wrote {tmp_path / 'deep' / 'er' / 'file.txt'}"  # parents are created
