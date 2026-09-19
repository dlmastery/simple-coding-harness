"""Step 27 offline tests. Every hook here is a Python function in this file or
a `python -c` one-liner, so nothing depends on the shell or on PATH. The
shipped hooks in .agents are tested from a copy in a temp directory. The
step 26 tests are kept and run with no hooks configured.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, context, hooks, llm, mcp_client, permissions, session, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

STEP = Path(__file__).parent

PY = f'"{sys.executable}"'  # a command hook that runs under this interpreter, on any OS


@pytest.fixture(autouse=True)
def no_shipped_hooks(tmp_path, monkeypatch):
    """Each test starts with an empty hook config; configure() fills it."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(hooks, "SESSION_CONTEXT", [])
    monkeypatch.setattr(context, "SESSION_CONTEXT", hooks.SESSION_CONTEXT)


def configure(tmp_path, config):
    """Write a hooks.json the autouse fixture points at."""
    (tmp_path / "hooks.json").write_text(json.dumps(config), encoding="utf-8")


def one_liner(code):
    """A command hook: this interpreter running one line, with the event on stdin."""
    return f'{PY} -c "{code}"'


# hook functions used through "test_step:<name>" python entries


def refuse_env(event):
    if str(event["tool_input"].get("path", "")).endswith(".env"):
        return {"block": "no .env edits"}


def upper_result(event):
    return {"result": str(event["tool_result"]).upper()}


def add_context(event):
    return {"context": f"the user said: {event['prompt']}"}


def explode(event):
    raise RuntimeError("hook bug")


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


def test_a_broken_mcp_config_file_is_noted_and_skipped(tmp_path, monkeypatch):
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


# ------------------------------------------------------------------- hooks


def test_python_hook_blocks_a_call(tmp_path):
    configure(tmp_path, {"PreToolUse": [{"matcher": "write_file|str_replace", "python": "test_step:refuse_env"}]})
    blocked = call("w1", "write_file", json.dumps({"path": str(tmp_path / ".env"), "content": "SECRET=1"}))
    args, action, reason = tools.decide(blocked)
    assert (action, reason) == ("blocked", "no .env edits")
    assert tools.execute(blocked) == (args, "Blocked by hook: no .env edits")
    assert not (tmp_path / ".env").exists()  # the tool never ran
    allowed = call("w2", "write_file", json.dumps({"path": str(tmp_path / "notes.txt"), "content": "ok"}))
    assert tools.decide(allowed)[1] != "blocked"  # the hook let it through to the rules


def test_command_hook_replaces_a_result(tmp_path):
    (tmp_path / "hello.txt").write_text("hello")
    code = "import json,sys; e=json.load(sys.stdin); print(json.dumps({'result': e['tool_name'] + ' said: ' + e['tool_result'].upper()}))"
    configure(tmp_path, {"PostToolUse": [{"matcher": "read_file", "command": one_liner(code)}]})
    read = call("r1", "read_file", json.dumps({"path": str(tmp_path / "hello.txt")}))
    assert tools.run(read, {"path": str(tmp_path / "hello.txt")}) == "read_file said: HELLO"
    assert tools.run(call("b1", "bash", "{}"), {"command": "echo untouched"}).strip() == "untouched"  # no matcher hit


def test_command_hook_blocks_with_exit_2_and_stderr(tmp_path):
    code = "import sys; sys.stderr.write('not on my watch'); sys.exit(2)"
    configure(tmp_path, {"PreToolUse": [{"matcher": "bash", "command": one_liner(code)}]})
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": "bash", "tool_input": {"command": "ls"}})
    assert outcome == hooks.HookOutcome(blocked=True, reason="not on my watch")


def reject_errors(event):
    assert event["ok"] == (not str(event["tool_result"]).startswith("Error"))
    if not event["ok"]:
        return {"block": "the tool failed, do not go on"}


def note_size(event):
    return {"context": f"the result is {len(str(event['tool_result']))} chars"}


def test_post_hook_can_reject_a_result_and_sees_whether_the_tool_succeeded(tmp_path):
    configure(tmp_path, {"PostToolUse": [{"matcher": "read_file", "python": "test_step:reject_errors"}, {"python": "test_step:note_size"}]})
    (tmp_path / "ok.txt").write_text("fine")
    good = tools.run(call("r1", "read_file", "{}"), {"path": str(tmp_path / "ok.txt")})
    assert good == "fine\n<hook>\nthe result is 4 chars\n</hook>"  # ok: True; the context rides on the result
    bad = tools.run(call("r2", "read_file", "{}"), {"path": str(tmp_path / "missing.txt")})
    assert bad == "Blocked by hook: the tool failed, do not go on"  # the tool ran and raised; the hook rejected the outcome


def test_pre_hook_context_reaches_the_result_and_post_hooks_skip_calls_that_never_ran(tmp_path, monkeypatch):
    ran = []
    monkeypatch.setattr(hooks, "run_python", lambda target, event: ran.append((target, event["event"])) or ({"context": "checked"} if "pre" in target else None))
    configure(tmp_path, {"PreToolUse": [{"python": "x:pre"}], "PostToolUse": [{"python": "x:post"}]})
    args, result = tools.execute(call("b1", "bash", json.dumps({"command": "echo hi"})))
    assert result.startswith("hi") and result.endswith("<hook>\nchecked\n</hook>")
    assert [e for _, e in ran] == ["PreToolUse", "PostToolUse"]
    ran.clear()
    assert tools.execute(call("b2", "bash", json.dumps({"command": "rm -rf x"})))[1].startswith("Blocked by policy")
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    assert tools.execute(call("b3", "bash", json.dumps({"command": "python x.py"})))[1] == tools.DENIED
    assert tools.execute(call("b4", "bash", "{bad json"))[1].startswith("Error: the arguments")
    assert ran == [("x:pre", "PreToolUse")]  # a denied call saw no hook; a declined one only the pre hook; a broken one none


def test_prompt_submit_adds_context_to_the_late_block(tmp_path, quiet, monkeypatch):
    configure(tmp_path, {"UserPromptSubmit": [{"python": "test_step:add_context"}]})
    seen = []

    def fake(messages, tools=None, on_delta=None):
        seen.append(messages[-1]["content"])
        return FakeMessage(content="ok", tool_calls=None), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)
    agent.turn([{"role": "system", "content": "s"}], "fix the tests")
    assert "<hooks>\nthe user said: fix the tests\n</hooks>" in seen[0]
    assert "<hooks>" not in context.reminder()["content"]  # the context was for that turn only


def test_session_start_context_stays_for_the_whole_session(tmp_path):
    code = "import json; print(json.dumps({'context': 'branch policy: no force pushes'}))"
    configure(tmp_path, {"SessionStart": [{"command": one_liner(code)}]})
    hooks.session_start()
    assert hooks.SESSION_CONTEXT == ["branch policy: no force pushes"]
    assert "<hooks>\nbranch policy: no force pushes\n</hooks>" in context.reminder()["content"]
    assert "no force pushes\nbe brief" in context.reminder(hook_context="be brief")["content"]


def test_matchers_are_globs_joined_by_bars():
    hook = {"matcher": "bash|write_*"}
    assert hooks.matches(hook, "bash") and hooks.matches(hook, "write_file") and hooks.matches(hook, "write_todos")
    assert not hooks.matches(hook, "read_file") and not hooks.matches(hook, "str_replace")
    assert hooks.matches({"matcher": "*"}, "anything") and hooks.matches({}, "anything")
    assert hooks.matches({"matcher": "mcp__fs__*"}, "mcp__fs__read") and not hooks.matches({"matcher": "mcp__fs__*"}, "mcp__git__log")
    assert hooks.matches({"matcher": "bash"}, None)  # an event without a tool runs every hook
    assert not hooks.matches({"matcher": "Bash"}, "bash")  # case matters, on Windows too


def test_a_crashing_hook_is_noted_and_ignored(tmp_path, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    monkeypatch.setattr(hooks, "TIMEOUT", 2)
    configure(tmp_path, {"PreToolUse": [
        {"python": "test_step:explode"},
        {"python": "no_such_module:fn"},
        {"command": one_liner("import sys; sys.exit(1)")},
        {"command": one_liner("print('not json')")},
        {"command": one_liner("import time; time.sleep(60)")},
        {"matcher": "bash"},
    ]})
    started = time.time()
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": "bash", "tool_input": {"command": "ls"}})
    assert time.time() - started < 10  # the sleeping hook was killed at the timeout, script and shell both
    assert outcome == hooks.HookOutcome()  # every failure was skipped; the call may run
    assert len(notes) == 6
    assert notes[0].startswith("hook `test_step:explode` failed and was ignored: RuntimeError: hook bug")
    assert "ModuleNotFoundError" in notes[1]
    assert "exited 1 and was ignored" in notes[2]
    assert "JSONDecodeError" in notes[3]
    assert "took more than 2s and was ignored" in notes[4]
    assert notes[5].startswith("hook without command or python skipped")


def test_a_broken_config_file_is_noted_and_skipped(tmp_path, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    (tmp_path / "hooks.json").write_text("{not json", encoding="utf-8")
    assert hooks.load_config() == {event: [] for event in hooks.EVENTS}
    assert notes and notes[0].startswith("hook config") and "skipped" in notes[0]
    hooks.load_config()
    assert len(notes) == 1  # the file did not change, so it was not read (or complained about) again


def test_config_files_merge_in_order(tmp_path):
    home, project = tmp_path / "home.json", tmp_path / "project.json"
    home.write_text(json.dumps({"PreToolUse": [{"matcher": "bash", "command": "a"}], "Unknown": [{"command": "x"}]}))
    project.write_text(json.dumps({"PreToolUse": [{"command": "b"}], "SessionEnd": [{"python": "m:f"}]}))
    config = hooks.load_config([tmp_path / "missing.json", home, project])
    assert [h["command"] for h in config["PreToolUse"]] == ["a", "b"]
    assert config["SessionEnd"] == [{"python": "m:f"}] and "Unknown" not in config


def refuse_compaction(event):
    assert event["event"] == "PreCompact" and event["prompt"] == "2 messages"
    return {"block": "keep it"}


def test_precompact_hook_can_keep_the_transcript(tmp_path, monkeypatch):
    configure(tmp_path, {"PreCompact": [{"python": "test_step:refuse_compaction"}]})
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}]
    assert commands.compact(messages) is messages
    assert notes == ["compaction blocked by hook: keep it"]


def test_hooks_command_lists_the_config(tmp_path, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/hooks", messages) is messages
    assert notes == ["no hooks configured (see .agents/hooks.json)"]
    configure(tmp_path, {"PreToolUse": [{"matcher": "bash", "command": "python check.py"}], "SessionEnd": [{"python": "m:f"}]})
    commands.handle("/hooks", messages)
    lines = notes[-1].splitlines()
    assert lines[0].split() == ["PreToolUse", "bash", "python", "check.py"]
    assert lines[1].split() == ["SessionEnd", "*", "m:f"]
    assert "/hooks" in commands.COMMANDS


def test_shipped_hooks_block_env_writes_and_log_tool_names(tmp_path, quiet, monkeypatch):
    """The two example hooks, run from a copy of .agents in a temp project."""
    shutil.copytree(STEP / ".agents", tmp_path / ".agents", ignore=shutil.ignore_patterns("skills", "tool_log.txt"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / ".agents" / "hooks.json"])

    env = call("w1", "write_file", json.dumps({"path": str(tmp_path / ".env"), "content": "KEY=1"}))
    args, result = tools.execute(env)
    assert result == "Blocked by hook: .env holds secrets; edit it by hand, not through the agent"
    assert not (tmp_path / ".env").exists()

    args, result = tools.execute(call("r1", "read_file", json.dumps({"path": str(tmp_path / ".agents" / "hooks.json")})))
    assert '"PreToolUse"' in result  # the read itself was not touched
    args, result = tools.execute(call("w2", "write_file", json.dumps({"path": str(tmp_path / "env.txt"), "content": "fine"})))
    assert result.startswith("Wrote")
    logged = (tmp_path / ".agents" / "tool_log.txt").read_text().splitlines()
    assert [line.split()[-1] for line in logged] == ["read_file", "write_file"]


def test_turn_feeds_a_blocked_result_back_to_the_model(tmp_path, quiet, monkeypatch):
    configure(tmp_path, {"PreToolUse": [{"matcher": "write_*", "python": "test_step:refuse_env"}]})
    replies = [
        FakeMessage(content=None, tool_calls=[call("w1", "write_file", json.dumps({"path": str(tmp_path / ".env"), "content": "x"}))]),
        FakeMessage(content="A hook stopped me from editing .env.", tool_calls=None),
    ]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))
    messages = agent.turn([{"role": "system", "content": llm.SYSTEM_PROMPT}], "put a key in .env")
    assert messages[3] == {"role": "tool", "tool_call_id": "w1", "content": "Blocked by hook: no .env edits"}
    assert messages[-1]["content"] == "A hook stopped me from editing .env."
    assert not (tmp_path / ".env").exists()


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
