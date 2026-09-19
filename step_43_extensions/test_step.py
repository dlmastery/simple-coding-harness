"""Step 43 offline tests. The extension tests write extension files into
a temp directory and load them with extensions.load, then check the
registry, the hooks, the prompt and the commands; the shipped examples
are loaded from this step's .agents/extensions at import. The streaming
tests of step 42 stay. A scripted fake plays the model. No model,
browser or network is launched.
"""

import io
import json
import os
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.console import Console

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, agents, checkpoint, commands, context, durability, extensions, handoff, history, hooks, instructions, jobs, llm, mcp_client, memory, modes, permissions, plan, sandbox, session, stop, streaming, subagent, todos, tools  # noqa: E402
from harness import ui as ui_module  # noqa: E402
from harness.ui import ui  # noqa: E402

USAGE = {"prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": None, "cached_tokens": 3}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def say(text):
    return FakeMessage(content=text, tool_calls=None)


def use(*calls):
    return FakeMessage(content=None, tool_calls=list(calls))


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """A temp workspace as cwd, temp stores, no hooks, no jobs, nothing spent, the default agent."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(permissions, "PROJECT", workspace.resolve())
    monkeypatch.setattr(sandbox, "PROJECT", workspace.resolve())
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(modes, "CURRENT", "default")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(llm, "MODEL", "gpt-4.1")
    monkeypatch.setattr(stop, "MAX_TURN_CALLS", 40)
    monkeypatch.setattr(stop, "MAX_SESSION_COST", 5.0)
    monkeypatch.setattr(stop, "MAX_TURN_SECONDS", 900.0)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda *a, **k: None)
    handoff.reset()
    stop.reset()
    jobs.kill_all()
    yield workspace
    jobs.kill_all()
    stop.reset()
    handoff.reset()


class Scripted:
    """A thread-safe fake call_llm: one reply per call, the last one repeated, and a log of every request."""

    def __init__(self, replies, usage=None):
        self.replies = list(replies)
        self.usage = dict(USAGE if usage is None else usage)
        self.requests = []  # (tools offered, user messages) per call
        self.lock = threading.Lock()

    def __call__(self, messages, tools=None, on_delta=None):
        with self.lock:
            self.requests.append(([s["function"]["name"] for s in tools or []], [m["content"] for m in messages if m["role"] == "user"]))
            reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return reply, dict(self.usage)

    def install(self, monkeypatch):
        monkeypatch.setattr(agent, "call_llm", self)
        monkeypatch.setattr(llm, "call_llm", self)
        return self


def start():
    """The message list chat() starts with."""
    return [{"role": "system", "content": llm.build_system_prompt()}]


# --------------------------------------------------------------- helpers


def one_liner(count, delay=0.2):
    """A shell command that prints `count` numbered lines, one every `delay` seconds."""
    body = f"import sys,time; [ (print('line', i, flush=True), time.sleep({delay})) for i in range({count}) ]"
    return f'{sys.executable} -c "{body}"'


def lines_seen(monkeypatch):
    """Record every ui.tool_line call as (name, line, time)."""
    seen = []
    original = ui.tool_line

    def tool_line(name, line, stream=None):
        seen.append((name, line, time.monotonic()))
        original(name, line, stream)

    monkeypatch.setattr(ui, "tool_line", tool_line)
    return seen


def test_bash_streams_each_line_before_the_result(monkeypatch):
    seen = lines_seen(monkeypatch)
    result = tools.bash(one_liner(3, 0.25))
    finished = time.monotonic()
    assert [line for _, line, _ in seen] == ["line 0", "line 1", "line 2"]
    assert all(name == "bash" for name, _, _ in seen)
    assert finished - seen[0][2] > 0.4       # the first line arrived long before the command ended
    assert seen[2][2] - seen[0][2] > 0.4     # and the lines came one at a time, not in one batch
    assert result == "line 0\nline 1\nline 2\n"  # the model still gets the whole output, untouched


def test_the_result_is_still_capped(monkeypatch):
    seen = lines_seen(monkeypatch)
    count = history.CAP // 8 + 100  # more than CAP characters of output
    result = tools.bash(one_liner(count, 0))
    assert len(seen) == count                # every line reached the screen
    assert history.CAPPED in result          # the model got the capped version; the whole text is on disk
    assert result.startswith("line 0\n")
    assert len(result) < history.CAP + 400


def test_a_timeout_still_becomes_a_result(monkeypatch):
    monkeypatch.setattr(streaming, "TIMEOUT", 1)
    seen = lines_seen(monkeypatch)
    started = time.monotonic()
    result = tools.bash(one_liner(30, 0.3))
    assert result.startswith("Timed out after 1s and was killed.")
    assert time.monotonic() - started < 8    # the process tree was killed, not waited for
    assert seen and seen[0][1] == "line 0"   # the lines before the kill were shown
    assert ui._streams == [] and ui._live is None  # and the panel came down


def test_a_stream_panel_keeps_the_last_lines_and_comes_down():
    stream = ui.streaming("bash", {"command": "pytest -q"})
    with stream as show:
        assert ui._streams == [stream]
        for i in range(ui_module.STREAM_LINES + 3):
            show(f"line {i}")
        assert stream.count == ui_module.STREAM_LINES + 3
        assert list(stream.lines) == [f"line {i}" for i in range(3, ui_module.STREAM_LINES + 3)]
        console = Console(file=io.StringIO(), force_terminal=False, width=80)
        console.print(stream.render())
        drawn = console.file.getvalue()
        assert "bash pytest -q" in drawn and "… 3 earlier lines" in drawn and "line 10" in drawn and "line 2" not in drawn
        assert f"running · {ui_module.STREAM_LINES + 3} lines" in drawn
    assert ui._streams == [] and ui._live is None


def test_tool_line_without_a_stream_opens_one_by_name():
    ui.tool_line("bash", "hello")
    assert len(ui._streams) == 1 and ui._streams[0].name == "bash" and list(ui._streams[0].lines) == ["hello"]
    ui.tool_line("bash", "again")
    assert len(ui._streams) == 1 and ui._streams[0].count == 2  # the same panel, not a second one
    ui.stream_close(ui._streams[0])
    assert ui._streams == []


def test_the_spinner_steps_aside_while_a_panel_is_open():
    with ui.streaming("bash", {"command": "sleep 5"}):
        spinner = ui.working("thinking")
        with spinner:
            spinner.stop()  # what agent.turn does at the first delta
        assert isinstance(spinner, ui_module.Spinner)
    with ui.working("thinking") as spinner:  # and works as before once the panel is down
        spinner.stop()


def test_a_job_fills_its_log_through_the_reader_and_shows_live_while_waited_on(monkeypatch):
    seen = lines_seen(monkeypatch)
    started = jobs.bash_background(one_liner(3, 0.2))
    assert started.startswith("Started job-1")
    assert seen == []  # nobody is watching yet: the lines go to the log only
    waited = jobs.job_wait("job-1", timeout=30)
    assert "exited with code 0" in waited
    assert [line for _, line, _ in seen] == ["line 0", "line 1", "line 2"]
    assert all(name == "job-1" for name, _, _ in seen)
    assert jobs.JOBS["job-1"].log.read_text(encoding="utf-8") == "line 0\nline 1\nline 2\n"
    assert jobs.JOBS["job-1"].on_line is None  # the wait is over: nothing forwards any more


def test_a_subagent_run_streams_its_nested_calls(monkeypatch):
    seen = lines_seen(monkeypatch)
    monkeypatch.setattr(ui, "approve", lambda reason: "y")  # python -c is rated ask
    Scripted([use(call("s1", "bash", {"command": one_liner(2, 0)})), say("two lines")]).install(monkeypatch)
    report = subagent.task("count the lines")
    assert report == "two lines"
    names = [name for name, _, _ in seen]
    assert names == ["bash", "bash", "subagent exploring"]  # the bash lines, then the run's own progress line
    assert seen[2][1] == f"bash {subagent.title(one_liner(2, 0))} · 2 lines"
    assert ui._streams == []


def test_loop_smoke_streams_then_records_the_full_result(monkeypatch):
    seen = lines_seen(monkeypatch)
    monkeypatch.setattr(ui, "approve", lambda reason: "y")  # python -c is rated ask
    command = one_liner(3, 0.1)
    Scripted([use(call("t1", "bash", {"command": command})), say("done")]).install(monkeypatch)
    messages = agent.turn(start(), "run it")
    assert [line for _, line, _ in seen] == ["line 0", "line 1", "line 2"]
    tool_message = next(m for m in messages if m["role"] == "tool")
    assert tool_message["content"] == "line 0\nline 1\nline 2\n"
    assert messages[-1] == {"role": "assistant", "content": "done"}
    assert ui._streams == [] and ui._live is None


# ------------------------------------------------------------- extensions


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def names(schemas):
    return [s["function"]["name"] for s in schemas]


def extension_dir(tmp_path, **files):
    """A directory of extension files: name -> source."""
    folder = tmp_path / "extensions"
    folder.mkdir(exist_ok=True)
    for name, source in files.items():
        (folder / f"{name}.py").write_text(source, encoding="utf-8")
    return folder


@pytest.fixture
def unloaded():
    """Take back every extension a test loaded from a temp dir."""
    before = set(extensions.EXTENSIONS)
    yield
    for name in list(extensions.EXTENSIONS):
        if name not in before:
            extensions.unload(name)


FULL = '''
def shout(text: str, times: int = 1) -> str:
    """Repeat the text in capitals."""
    return (text.upper() + " ") * times

def hello(messages, arg=""):
    from harness.ui import ui
    ui.note("hello " + (arg or "there"))
    return messages

def no_rm(event):
    if "rm " in (event.get("tool_input") or {}).get("command", ""):
        return {"block": "no rm from the extension"}

def apply(ctx):
    ctx.tool(shout)
    ctx.command("/hello", "say hello", hello)
    ctx.hook("PreToolUse", no_rm, matcher="bash")
    ctx.prompt_section("Always sign off with a haiku.")
    ctx.agent({"name": "greeter", "description": "Greets people.", "tools": ["bash"], "prompt": "You are the greeter."})
'''

EXIT_2 = f'{sys.executable} -c "import sys; sys.exit(2)"'


def test_the_builtin_loaders_are_extensions():
    assert [name for name, _ in extensions.BUILTIN] == ["skills", "hooks", "agents", "mcp"]
    loaded = extensions.EXTENSIONS
    assert all(loaded[name].status == "loaded" and loaded[name].path is None for name in ("skills", "hooks", "agents", "mcp"))
    assert loaded["skills"].summary() == "tool read_skill; section skills_section"
    assert loaded["hooks"].summary() == "command /hooks"  # the checkpoint capture runs in tools.run, not as a hook
    assert loaded["agents"].summary().startswith("tool agent_coder, agent_planner") and "agent coder, planner, reviewer, router, worker" in loaded["agents"].summary()
    assert loaded["mcp"].summary() == "command /mcp"
    assert tools.TOOLS["read_skill"]("explain-code").startswith("---") and "read_skill" in names(tools.TOOL_SCHEMAS)
    assert set(extensions.COMMANDS) >= {"/hooks", "/mcp", "/status"}
    assert extensions.hooks_for("PreToolUse") == []  # nothing built in: the checkpoint capture is tools.run's
    assert extensions.PERMISSIONS["read_skill"] == "allow" and extensions.PERMISSIONS["git_diff_summary"] == "allow"
    # the shipped examples, loaded from this step's .agents/extensions at import
    assert loaded["git_tools"].summary() == "tool git_diff_summary; command /status"
    assert loaded["git_tools"].path == STEP / ".agents" / "extensions" / "git_tools.py"
    assert loaded["word_count"].summary().startswith("section This project has")


def test_the_registry_still_serves_the_old_callers(monkeypatch):
    assert names(handoff.toolset())[:2] == ["bash", "read_file"] and "read_skill" in names(handoff.toolset())
    monkeypatch.setattr(handoff, "ACTIVE", agents.AGENTS["reviewer"])
    assert names(handoff.toolset()) == ["bash", "read_file", "read_skill", "handoff_to"]
    assert agents.register() == ["agent_coder", "agent_planner", "agent_reviewer", "agent_router", "agent_worker"]
    assert "agent_coder" in tools.TOOLS and names(tools.TOOL_SCHEMAS).count("agent_coder") == 1
    fake = [SimpleNamespace(name="echo", description="Echo it back", inputSchema={"type": "object", "properties": {"text": {"type": "string"}}})]
    assert mcp_client.register("fake", fake) == ["mcp__fake__echo"]
    assert "mcp__fake__echo" in tools.TOOLS and "tool mcp__fake__echo" in extensions.EXTENSIONS["mcp"].summary()
    extensions.EXTENSIONS["mcp"].registrations = [r for r in extensions.EXTENSIONS["mcp"].registrations if r.name != "mcp__fake__echo"]
    tools.TOOLS.pop("mcp__fake__echo")
    tools.TOOL_SCHEMAS[:] = [s for s in tools.TOOL_SCHEMAS if s["function"]["name"] != "mcp__fake__echo"]
    (Path.cwd() / "hooks.json").write_text(json.dumps({"PreToolUse": [{"matcher": "bash", "command": EXIT_2}]}), encoding="utf-8")
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [Path.cwd() / "hooks.json"])
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": "bash", "tool_input": {"command": "ls"}})
    assert outcome.blocked and outcome.reason == "blocked by hook"  # a config hook still runs, after the registered ones
    prompt = llm.build_system_prompt()
    assert "You have skills available" in prompt and "- explain-code:" in prompt and "This project has" in prompt


def test_an_extension_registers_all_five_kinds(tmp_path, monkeypatch, unloaded):
    seen = notes(monkeypatch)
    folder = extension_dir(tmp_path, full=FULL)
    [loaded] = extensions.load([folder])
    assert loaded.status == "loaded" and loaded.name == "full" and loaded.path == folder / "full.py"
    assert loaded.summary() == "tool shout, agent_greeter; command /hello; hook PreToolUse:bash; section Always sign off...; agent greeter"

    assert tools.TOOLS["shout"]("hi", 2) == "HI HI "
    schema = next(s for s in tools.TOOL_SCHEMAS if s["function"]["name"] == "shout")["function"]
    assert schema["description"] == "Repeat the text in capitals."
    assert schema["parameters"] == {"type": "object", "properties": {"text": {"type": "string"}, "times": {"type": "integer"}}, "required": ["text"]}
    assert "shout" in names(handoff.toolset()) and "shout" in names(subagent.toolset())
    assert permissions.check("shout", {"text": "x"}) == ("ask", 'call shout with {"text": "x"}')  # an extension tool asks unless it says permission="allow"

    assert extensions.COMMANDS["/hello"][0] == "say hello"
    assert commands.handle("/hello world", ["m"]) == ["m"] and seen[-1] == "hello world"
    commands.handle("/hello", ["m"])
    assert seen[-1] == "hello there"

    outcome = hooks.run_hooks("PreToolUse", {"tool_name": "bash", "tool_input": {"command": "rm -rf x"}})
    assert outcome.blocked and outcome.reason == "no rm from the extension"
    assert not hooks.run_hooks("PreToolUse", {"tool_name": "bash", "tool_input": {"command": "ls"}}).blocked
    assert not hooks.run_hooks("PreToolUse", {"tool_name": "read_file", "tool_input": {"path": "rm "}}).blocked  # the matcher holds

    assert "Always sign off with a haiku." in llm.build_system_prompt()
    assert agents.AGENTS["greeter"]["prompt"] == "You are the greeter." and agents.AGENTS["greeter"]["max_turns"] == agents.DEFAULT_MAX_TURNS
    assert "agent_greeter" in tools.TOOLS and "agent_greeter:" in llm.build_system_prompt()

    extensions.unload("full")
    assert "full" not in extensions.EXTENSIONS and "shout" not in tools.TOOLS and "/hello" not in extensions.COMMANDS
    assert "greeter" not in agents.AGENTS and "agent_greeter" not in names(tools.TOOL_SCHEMAS)
    assert all(h["source"] != "full" for h in extensions.hooks_for("PreToolUse")) and "haiku" not in llm.build_system_prompt()


def test_a_broken_extension_is_skipped_and_the_rest_load(tmp_path, monkeypatch, unloaded):
    seen = notes(monkeypatch)
    folder = extension_dir(
        tmp_path,
        a_syntax="def apply(ctx):\n    return (\n",
        b_no_apply="X = 1\n",
        c_raises="def t(x: str) -> str:\n    'a tool'\n    return x\n\ndef apply(ctx):\n    ctx.tool(t)\n    raise ValueError('half way')\n",
        d_fine="def apply(ctx):\n    ctx.prompt_section('fine')\n",
    )
    loaded = extensions.load([folder])
    assert [e.name for e in loaded] == ["a_syntax", "b_no_apply", "c_raises", "d_fine"]
    assert loaded[0].status.startswith("failed: SyntaxError")
    assert loaded[1].status == "failed: no apply(ctx) function"
    assert loaded[2].status == "failed: ValueError: half way" and loaded[2].registrations == []
    assert "t" not in tools.TOOLS  # what it registered before it raised is gone
    assert loaded[3].status == "loaded" and "fine" in extensions.prompt_sections()
    assert [note.split(":")[0] for note in seen] == ["extension 'a_syntax' skipped", "extension 'b_no_apply' skipped", "extension 'c_raises' skipped"]
    assert any(row.startswith("c_raises     failed: ValueError: half way") for row in extensions.summary())


def test_the_extensions_command_lists_them(tmp_path, monkeypatch, unloaded):
    seen = notes(monkeypatch)
    extensions.load([extension_dir(tmp_path, full=FULL, broken="import nothing_here\n")])
    commands.handle("/extensions", [])
    rows = seen[-1].splitlines()
    assert rows[0].startswith("skills       loaded   built-in") and rows[0].endswith("tool read_skill; section skills_section")
    assert any(row.startswith("full         loaded") and "tool shout, agent_greeter; command /hello" in row for row in rows)
    assert any(row.startswith("broken       failed: ModuleNotFoundError") for row in rows)
    assert "/extensions" in commands.COMMANDS
    commands.handle("/hooks", [])  # the built-in loaders' commands run through the same path
    rows = seen[-1].splitlines()
    assert rows[0] == f"{'PreToolUse':<18} {'bash':<24} no_rm  (full)"
    commands.handle("/mcp", [])
    assert seen[-1] == "no MCP servers configured (see .agents/mcp.json)"
    commands.handle("/nothing", [])  # the help lists the registered commands with the built-in ones
    assert "/hello  -  say hello" in seen[-1] and "/status  -  show the git branch" in seen[-1] and "/extensions  -  " in seen[-1]


def test_a_reload_replaces_and_an_override_is_undone(tmp_path, unloaded):
    folder = extension_dir(tmp_path, over="def read_file(path: str) -> str:\n    'Read a file, in capitals.'\n    return open(path).read().upper()\n\ndef apply(ctx):\n    ctx.tool(read_file)\n")
    original = tools.TOOLS["read_file"]
    position = names(tools.TOOL_SCHEMAS).index("read_file")
    Path("x.txt").write_text("abc")
    extensions.load([folder])
    assert tools.TOOLS["read_file"]("x.txt") == "ABC" and names(tools.TOOL_SCHEMAS).index("read_file") == position
    extensions.load([folder])  # a second load replaces the first, and the record stays single
    assert [r.name for r in extensions.EXTENSIONS["over"].registrations] == ["read_file"]
    extensions.unload("over")
    assert tools.TOOLS["read_file"] is original and names(tools.TOOL_SCHEMAS).index("read_file") == position
    assert tools.TOOLS["read_file"]("x.txt") == "abc"


def test_the_example_tool_and_command_work(monkeypatch):
    seen = notes(monkeypatch)
    for command in ("git init -q", "git config user.email t@example.com", "git config user.name t", "git checkout -q -b work"):
        assert os.system(command) == 0
    Path("a.txt").write_text("one\n")
    assert os.system("git add a.txt") == 0 and os.system("git commit -q -m one") == 0
    assert tools.TOOLS["git_diff_summary"]() == "no changes"
    Path("a.txt").write_text("one\ntwo\n")
    summary = tools.TOOLS["git_diff_summary"]()
    assert "a.txt" in summary and "1 +" in summary
    assert tools.TOOLS["git_diff_summary"](staged=True) == "no changes"
    schema = next(s for s in tools.TOOL_SCHEMAS if s["function"]["name"] == "git_diff_summary")["function"]
    assert schema["parameters"] == {"type": "object", "properties": {"staged": {"type": "boolean"}}, "required": []}
    assert schema["description"].startswith("Summarise the uncommitted changes")
    commands.handle("/status", [])
    assert seen[-1] == "branch: work\n M a.txt"


def test_loop_smoke_the_model_calls_an_extension_tool(tmp_path, monkeypatch, unloaded):
    extensions.load([extension_dir(tmp_path, full=FULL)])
    asked = []
    monkeypatch.setattr(ui, "approve", lambda reason: asked.append(reason) or "y")  # shout did not say permission="allow", so it asks
    fake = Scripted([use(call("s1", "shout", {"text": "ok", "times": 2})), say("done")]).install(monkeypatch)
    messages = agent.turn(start(), "shout it")
    assert "shout" in fake.requests[0][0] and "git_diff_summary" in fake.requests[0][0]
    assert messages[3] == {"role": "tool", "tool_call_id": "s1", "content": "OK OK "}
    assert asked == ['call shout with {"text": "ok", "times": 2}']
    assert messages[-1] == {"role": "assistant", "content": "done"}
    assert "Always sign off with a haiku." in messages[0]["content"]


# ------------------------------------------------- what a bad extension cannot break


def test_a_file_named_like_a_builtin_is_refused_and_the_builtin_stays(tmp_path, monkeypatch, unloaded):
    seen = notes(monkeypatch)
    folder = extension_dir(tmp_path, skills="import nothing_here\n")
    [refused] = extensions.load([folder])
    assert refused.status.startswith("failed: name reserved")
    assert extensions.EXTENSIONS["skills"].status == "loaded" and "read_skill" in tools.TOOLS  # the real loader is untouched
    assert "You have skills available" in llm.build_system_prompt()
    assert seen[-1].startswith("extension 'skills.py' skipped: name reserved")
    extensions.unload("skills.py")


def test_an_extension_imports_a_helper_next_to_it(tmp_path, unloaded):
    folder = extension_dir(tmp_path, _helpers="GREETING = 'hi'\n", uses_helper="from _helpers import GREETING\n\ndef apply(ctx):\n    ctx.prompt_section('helper says ' + GREETING)\n")
    [loaded] = extensions.load([folder])  # _helpers.py is not an extension; uses_helper.py imports it
    assert loaded.status == "loaded" and "helper says hi" in extensions.prompt_sections()
    assert "harness_extension_uses_helper" in sys.modules


def test_a_tool_that_returns_a_dict_and_a_command_that_raises_are_results_not_crashes(tmp_path, monkeypatch, unloaded):
    seen = notes(monkeypatch)
    folder = extension_dir(tmp_path, odd="def dicty(x: str) -> str:\n    'returns a dict'\n    return {'a': x}\n\ndef boom(messages, arg=''):\n    raise RuntimeError('no git here')\n\ndef apply(ctx):\n    ctx.tool(dicty, permission='allow')\n    ctx.command('/boom', 'raise', boom)\n")
    extensions.load([folder])
    Scripted([use(call("d1", "dicty", {"x": "1"})), say("done")]).install(monkeypatch)
    messages = agent.turn(start(), "go")
    assert messages[3] == {"role": "tool", "tool_call_id": "d1", "content": '{"a": "1"}'}  # turned into JSON, never a TypeError
    assert commands.handle("/boom", ["m"]) == ["m"] and seen[-1] == "command /boom failed: RuntimeError: no git here"


# ------------------------------------------------- every tool call gets its tool message


def test_bad_arguments_an_unknown_tool_and_a_raising_tool_each_get_one_tool_message(monkeypatch):
    broken = SimpleNamespace(id="b1", function=SimpleNamespace(name="bash", arguments="{not json"))
    Scripted([
        use(broken, call("b2", "no_such_tool", {"x": 1}), call("b3", "read_file", {"path": "missing.txt"}), call("b4", "bash", {})),
        say("done"),
    ]).install(monkeypatch)
    messages = agent.turn(start(), "go")
    results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
    assert results["b1"].startswith("Error: the arguments of bash are not a JSON object:")
    assert results["b2"] == "Error: no tool named 'no_such_tool'."
    assert results["b3"].startswith("Error: FileNotFoundError:")
    assert results["b4"] == "Blocked by policy: bash: missing argument 'command'"
    assert messages[-1] == {"role": "assistant", "content": "done"}  # the loop went on


def test_utf8_round_trip_through_the_file_tools_and_bash(monkeypatch):
    text = "héllo — ünïcode ✓\r\nsecond line\n"
    assert tools.write_file("u.txt", text) == "Wrote u.txt"
    assert Path("u.txt").read_bytes() == text.encode("utf-8")  # utf-8 whatever the locale, line endings untouched
    assert tools.read_file("u.txt") == text
    assert tools.str_replace("u.txt", "ünïcode", "unicode") == "Replaced 1 match(es) in u.txt"
    assert tools.read_file("u.txt") == text.replace("ünïcode", "unicode")
    assert tools.str_replace("u.txt", "", "x").startswith("Error: old_str is empty")
    assert tools.write_file("deep/er/new.txt", "x") == "Wrote deep/er/new.txt" and Path("deep/er/new.txt").read_text() == "x"
    assert tools.bash(f'{sys.executable} -c "print(chr(0x2713))"').strip() == "✓"


def test_write_todos_with_a_bad_status_is_an_error_and_leaves_the_list_alone(monkeypatch):
    todos.write_todos([{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    result = todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}])
    assert result == "Error: item 0 has status 'done'; use one of pending, in_progress, completed."
    assert [t["content"] for t in todos.TODOS] == ["a"]  # unchanged
    assert todos.write_todos("nope") == "Error: todos must be a list."
    Scripted([use(call("t1", "write_todos", {"todos": [{"content": "b", "activeForm": "b", "status": "done"}]})), say("ok")]).install(monkeypatch)
    messages = agent.turn(start(), "plan")  # the loop survives it, and the next reminder still renders
    assert messages[3]["content"].startswith("Error: item 0 has status")
    assert "[~] a" in context.reminder()["content"]


def test_a_subagent_cannot_run_a_tool_it_was_not_offered(monkeypatch):
    Scripted([use(call("w1", "write_file", {"path": "x.txt", "content": "no"}), call("w2", "finish", {"summary": "s"})), say("report")]).install(monkeypatch)
    assert subagent.task("try to write") == "report"
    assert not Path("x.txt").exists() and stop.finished() is None  # denied by name, and finish did not end the lead's turn


def test_rewind_offers_user_messages_only_and_sessions_keeps_the_active_agent(monkeypatch):
    Scripted([use(call("r1", "bash", {"command": "echo hi"})), say("done")]).install(monkeypatch)
    messages = agent.turn(start(), "first")
    messages = agent.turn(messages, "second")
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    monkeypatch.setattr(ui, "resumed", lambda *a, **k: None)
    monkeypatch.setattr(ui, "replay", lambda m: None)
    kept = commands.handle("/rewind", messages)
    assert [row.split()[0] for row in offered] == ["1", "5"]  # the two user messages, by index
    assert [m["role"] for m in kept] == ["system", "user", "assistant", "tool", "assistant"]  # cut before "second": no orphan
    assert durability.unanswered(kept) == []
    # a session listing loads every log to title it; the handoff markers in them must not change the live agent
    session.path_for("older").write_text(json.dumps({"role": "user", "content": "hi"}) + "\n" + json.dumps({"handoff": "reviewer"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(ui, "pick", lambda title, rows: None)
    commands.handle("/sessions", kept)
    assert handoff.active_name() == "main"


def test_a_failed_summariser_keeps_the_transcript(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(llm, "call_llm", lambda *a, **k: (llm.StreamedMessage(content=None, failed="boom"), llm.usage_from(None)))
    messages = start() + [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}, {"role": "user", "content": "x" * 400_000}, {"role": "assistant", "content": "w"}]
    assert commands.compact(messages) is messages
    assert seen[-1] == "compaction failed (RuntimeError); transcript kept as is"


# ------------------------------------------------- the loop survives what used to kill it


def test_a_resumed_transcript_with_a_dangling_tool_call_is_repaired(monkeypatch):
    seen = notes(monkeypatch)
    session.SESSION_DIR.mkdir(parents=True, exist_ok=True)
    dangling = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "p1", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "missing.txt"})}},
            {"id": "p2", "type": "function", "function": {"name": "bash", "arguments": "{broken"}},
        ]},
    ]
    session.path_for("crashed").write_text("".join(json.dumps(m) + "\n" for m in dangling), encoding="utf-8")
    messages = agent.reopen(session.open_session("crashed"))
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "tool"]  # both calls answered
    assert messages[3]["content"].startswith("Error: FileNotFoundError:")
    assert messages[4]["content"].startswith("Error: the arguments of bash are not a JSON object:")
    assert durability.unanswered(messages) == [] and seen[-1] == "recovered 2 tool calls left unanswered by the last run"
    assert len(session.load("crashed")) == 5  # and saved, so the next --resume does not run them again


def test_ctrl_c_during_the_tool_calls_leaves_every_call_answered(monkeypatch):
    def interrupted(command):
        raise KeyboardInterrupt

    monkeypatch.setattr(tools, "bash", interrupted)
    monkeypatch.setitem(tools.TOOLS, "bash", interrupted)
    monkeypatch.setattr(agent, "steer", lambda where: None)  # ctrl-c again at the steer prompt: leave
    Scripted([use(call("i1", "bash", {"command": "echo one"}), call("i2", "bash", {"command": "echo two"})), say("never")]).install(monkeypatch)
    messages = start()
    with pytest.raises(KeyboardInterrupt):
        agent.turn(messages, "run both")
    results = [m for m in messages if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in results] == ["i1", "i2"]  # one result per call, in order
    assert all(m["content"] == tools.INTERRUPTED for m in results)
    assert durability.unanswered(messages) == [] and len(session.load(session.CURRENT)) == len(messages)  # valid, and on disk


def test_a_model_call_that_fails_for_good_ends_the_turn_with_a_valid_transcript(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(agent, "call_llm", lambda *a, **k: (llm.StreamedMessage(content=None, failed="model call failed and will not be retried (401 Unauthorized): bad key"), llm.usage_from(None)))
    messages = agent.turn(start(), "hello")
    assert [m["role"] for m in messages] == ["system", "user"]  # the question stays; nothing half-written follows it
    assert seen[-1].startswith("model call failed and will not be retried")


def test_a_turn_stops_after_the_model_call_cap(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(stop, "MAX_TURN_CALLS", 3)
    Scripted([use(call("c", "bash", {"command": "echo again"}))]).install(monkeypatch)  # the same call forever
    messages = agent.turn(start(), "loop")
    assert sum(1 for m in messages if m["role"] == "assistant") == 3
    assert seen[-1].startswith("stopped after 3 model calls in one turn")
    assert durability.unanswered(messages) == []  # the last reply's call was answered before the stop


def test_a_print_run_without_resume_writes_no_log(monkeypatch):
    monkeypatch.setattr(session, "QUIET", True)  # what chat() sets for -p without --resume
    session.save([{"role": "user", "content": "hi"}])
    session.rewind_to(0)
    assert not session.path_for(session.CURRENT).exists() and not session.SESSION_DIR.exists()
