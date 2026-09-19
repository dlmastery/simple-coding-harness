"""Step 32 offline tests. A big fake tool joins the registry so a deferred
tool exists whatever the real schemas measure. The breakdown is checked
on a transcript that has every category in it; the warnings are checked
through budget.check and through the loop with a fake model that reports
a large prompt.
"""

import io
import json
import os
import sys
from types import SimpleNamespace

import pytest
from rich.console import Console

os.environ.setdefault("API_KEY", "x")

from harness import agent, budget, commands, config, context, hooks, instructions, jobs, llm, memory, plan, session, skills, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


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


BIG_SCHEMA = {
    "type": "function",
    "function": {
        "name": "big_tool",
        "description": "A tool with a long description. " * 60,  # well over DEFER_OVER tokens
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "What to echo back"}},
            "required": ["text"],
        },
    },
}


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Act mode, no hooks, no jobs, no real home, and a registry with one deferred tool."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(instructions, "LOADED", [])
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(budget, "WARNED", set())
    monkeypatch.setattr(tools, "LOADED", set())
    monkeypatch.setattr(tools, "TOOL_SCHEMAS", [*tools.TOOL_SCHEMAS, BIG_SCHEMA])
    monkeypatch.setitem(tools.TOOLS, "big_tool", lambda text: f"big: {text}")
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    jobs.kill_all()
    yield
    jobs.kill_all()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def names(schemas):
    return [s["function"]["name"] for s in schemas]


# ---------------------------------------------------------------- breakdown


def test_breakdown_has_every_category_and_sums_to_the_total(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the breakdown discovers the instruction files where the loop runs
    monkeypatch.setattr(instructions, "git_root", lambda cwd=None: tmp_path.resolve())
    (tmp_path / "AGENTS.md").write_text("# Guide\n\nRun pytest.\n" * 20, encoding="utf-8")
    monkeypatch.setattr(skills, "SKILLS", {"deploy": {"description": "ship it " * 30, "path": tmp_path}})
    system = llm.build_system_prompt()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "look at the screen"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "x" * 4000},
        {"role": "user", "content": [{"type": "text", "text": "screenshot"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]},
    ]
    counts = budget.breakdown(messages)
    assert list(counts) == [*budget.CATEGORIES, "total", "window"]
    assert counts["total"] == sum(counts[c] for c in budget.CATEGORIES)
    assert counts["window"] == config.CONTEXT_WINDOW
    assert all(counts[c] > 0 for c in budget.CATEGORIES if c != "memory index")
    assert counts["instruction files"] == budget.tokens(instructions.instructions_prompt())
    assert counts["skills index"] == budget.tokens(skills.skills_prompt())
    assert counts["system prompt"] + counts["instruction files"] + counts["skills index"] == budget.tokens(system)
    assert counts["images"] == budget.IMAGE_TOKENS
    assert counts["tool results"] >= 1000
    assert counts["tool schemas"] == sum(budget.schema_tokens(s) for s in tools.active_schemas())


def test_render_draws_one_bar_per_category_and_the_share_of_the_window(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 10_000)
    messages = [{"role": "system", "content": "s" * 20_000}, {"role": "user", "content": "hi"}]
    text = budget.render(messages)
    lines = text.splitlines()
    assert [line.split("  ")[0].strip() for line in lines[:-1]] == list(budget.CATEGORIES)
    assert lines[0].endswith("#" * budget.BAR)  # the system prompt is the largest category here
    assert lines[-1].startswith("total") and "% of the 10,000 token window" in lines[-1]
    counts = budget.breakdown(messages)
    assert f"{100 * counts['total'] / 10_000:.0f}%" in lines[-1]


def test_context_command_prints_the_breakdown(monkeypatch):
    drawn = []
    monkeypatch.setattr(ui, "context", lambda text: drawn.append(text))
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/context", messages) is messages
    assert drawn and drawn[0].startswith("system prompt")
    assert "/context" in commands.COMMANDS


# ------------------------------------------------------------ deferred tools


def test_a_big_schema_goes_out_as_a_stub_until_it_is_loaded():
    assert tools.deferred_names() == ["big_tool"]
    offered = tools.active_schemas()
    stub = next(s for s in offered if s["function"]["name"] == "big_tool")
    assert stub["function"] == {
        "name": "big_tool",
        "description": "deferred; call load_tool('big_tool') to enable",
        "parameters": {"type": "object", "properties": {}},
    }
    assert names(offered)[-1] == "load_tool"
    assert budget.schema_tokens(stub) <= budget.DEFER_OVER
    assert all(budget.schema_tokens(s) <= budget.DEFER_OVER for s in offered)

    args, result = tools.execute(call("c1", "big_tool", {}))
    assert result == "Error: big_tool is deferred. Call load_tool('big_tool') first, then call big_tool again with its full arguments."

    args, result = tools.execute(call("c2", "load_tool", {"name": "big_tool"}))
    assert result.startswith("big_tool is enabled for the rest of the session. Its schema:\n")
    assert json.loads(result.split("\n", 1)[1]) == BIG_SCHEMA["function"]
    assert tools.LOADED == {"big_tool"}

    offered = tools.active_schemas()
    assert next(s for s in offered if s["function"]["name"] == "big_tool") is BIG_SCHEMA
    assert "load_tool" not in names(offered)  # nothing left to load
    assert tools.execute(call("c3", "big_tool", {"text": "hello"}))[1] == "big: hello"

    assert tools.load_tool("bash") == "bash is not deferred; call it directly."
    assert tools.load_tool("nothing") == "Error: no tool named 'nothing'."


def test_active_schemas_composes_with_the_plan_tool_set_and_the_subagent_tool_set(monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    offered = tools.active_schemas(plan.toolset())
    assert names(offered) == ["bash", "read_file", "read_skill", "recall", "task", "submit_plan"]  # nothing deferred: no load_tool
    monkeypatch.setattr(plan, "READ_ONLY", (*plan.READ_ONLY, "big_tool"))
    offered = tools.active_schemas(plan.toolset())
    assert names(offered) == ["bash", "read_file", "read_skill", "recall", "task", "big_tool", "submit_plan", "load_tool"]
    assert next(s for s in offered if s["function"]["name"] == "big_tool")["function"]["description"].startswith("deferred")
    assert plan.offered("load_tool")  # allowed in plan mode, so the load can happen there too
    monkeypatch.setattr(plan, "MODE", "act")
    sub = subagent.toolset()
    assert "big_tool" in names(sub) and names(sub)[-1] == "load_tool" and "task" not in names(sub)


def test_the_system_prompt_lists_the_deferred_tools(tmp_path):
    prompt = llm.build_system_prompt(str(tmp_path))
    assert "Some tools are deferred" in prompt and "\n- big_tool\n" in prompt
    assert prompt.index("- big_tool") < prompt.index("Your current working directory")
    assert "Some tools are deferred" not in llm.build_system_prompt(str(tmp_path), schemas=tools.TOOL_SCHEMAS[:-1])


# ----------------------------------------------------------------- warnings


def test_warnings_fire_once_at_half_and_at_three_quarters(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 1000)
    assert budget.check(None) is None
    assert budget.check(400) is None
    assert budget.check(550) == "context window 55% full: 550 of 1,000 tokens. /context shows where it goes; /compact frees it"
    assert budget.check(600) is None
    assert budget.check(800).startswith("context window 80% full")
    assert budget.check(900) is None
    assert budget.WARNED == {0.5, 0.75}


def test_one_jump_past_both_lines_earns_one_warning(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 1000)
    assert budget.check(900).startswith("context window 90% full")
    assert budget.check(950) is None


def test_the_usage_line_shows_the_real_prompt_next_to_the_estimate(monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr(ui, "console", Console(file=out, width=200))
    ui.usage({"prompt_tokens": 1234, "completion_tokens": 56, "reasoning_tokens": None, "cached_tokens": None}, 1300)
    assert "1,234 prompt (estimate 1,300) · 56 completion" in out.getvalue()
    ui.usage({"prompt_tokens": None, "completion_tokens": 5, "reasoning_tokens": None, "cached_tokens": None}, 1300)
    assert "estimate 1,300 prompt · 5 completion" in out.getvalue()
    ui.usage({"prompt_tokens": 7, "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None})
    assert "7 prompt · 1 completion" in out.getvalue()


# ---------------------------------------------------------------- the loop


def test_loop_smoke_stub_then_load_then_call(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 1000)
    replies = [
        FakeMessage(content=None, tool_calls=[call("t1", "big_tool", {})]),
        FakeMessage(content=None, tool_calls=[call("t2", "load_tool", {"name": "big_tool"})]),
        FakeMessage(content=None, tool_calls=[call("t3", "big_tool", {"text": "now"})]),
        say("done"),
    ]
    prompts = iter([100, 200, 600, 650])
    offered = []
    usage_lines = []
    seen = notes(monkeypatch)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: usage_lines.append((stats["prompt_tokens"], estimate)))

    def fake(messages, tools=None, on_delta=None):
        offered.append(names(tools))
        return replies.pop(0), {"prompt_tokens": next(prompts), "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None}

    monkeypatch.setattr(agent, "call_llm", fake)
    out = agent.turn([{"role": "system", "content": "s"}], "use the big tool")

    assert out[3]["content"].startswith("Error: big_tool is deferred.")
    assert out[5]["content"].startswith("big_tool is enabled")
    assert out[7]["content"] == "big: now"
    assert out[-1]["content"] == "done"
    assert offered[0][-2:] == ["big_tool", "load_tool"] and offered[2][-1] == "big_tool"
    assert [real for real, _ in usage_lines] == [100, 200, 600, 650]
    assert all(isinstance(estimate, int) and estimate > 0 for _, estimate in usage_lines)
    assert [line for line in seen if line.startswith("context window")] == ["context window 60% full: 600 of 1,000 tokens. /context shows where it goes; /compact frees it"]


# ------------------------------------------------- robustness (shared by every step)

from harness import commands, permissions, prompt, subagent, tools  # noqa: E402 - the tests below need them whatever the step imports above

USAGE = {"prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": None, "cached_tokens": 3}


def _fake_model(replies):
    """A call_llm stand-in that answers with the next reply, whatever keywords the loop passes."""
    queue = list(replies)

    def fake(messages, tools=None, on_delta=None, **_):
        return queue.pop(0), USAGE

    return fake


def test_bad_arguments_an_unknown_tool_and_a_raising_tool_each_get_one_tool_message(monkeypatch, tmp_path):
    """The loop never dies on a tool call: every call gets exactly one result, then the model goes on."""
    monkeypatch.setattr(permissions, "PROJECT", tmp_path.resolve())
    broken = SimpleNamespace(id="c1", function=SimpleNamespace(name="bash", arguments='{"command": "echo hi"'))  # cut short
    unknown = call("c2", "no_such_tool", {"x": 1})
    raising = call("c3", "read_file", {"path": str(tmp_path / "missing.txt")})
    wrong = call("c4", "write_file", {"path": str(tmp_path / "a.txt")})  # content missing
    reply = FakeMessage(content=None, tool_calls=[broken, unknown, raising, wrong])
    monkeypatch.setattr(agent, "call_llm", _fake_model([reply, say("recovered")]))

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    results = {m["tool_call_id"]: m["content"] for m in out if m["role"] == "tool"}
    assert list(results) == ["c1", "c2", "c3", "c4"] and out[-1]["content"] == "recovered"
    assert results["c1"].startswith("Error: the arguments of bash are not a JSON object:")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: ") and results["c3"].endswith("missing.txt is not a file.")
    assert results["c4"].startswith("Error: TypeError:")
    assert tools.execute(call("c5", "bash", {}))[1] == "Blocked by policy: bash: missing argument 'command'"


def test_utf8_round_trip_through_write_file_read_file_and_bash(monkeypatch, tmp_path):
    monkeypatch.setattr(permissions, "PROJECT", tmp_path.resolve())
    target = tmp_path / "deep" / "unicode.txt"
    text = "naïve café — 日本語 ✓\r\nsecond line\n"
    assert tools.execute(call("w", "write_file", {"path": str(target), "content": text}))[1] == f"Wrote {target}"
    assert target.read_bytes() == text.encode("utf-8")  # parent made, line endings kept
    assert tools.execute(call("r", "read_file", {"path": str(target)}))[1] == text
    assert tools.execute(call("e", "str_replace", {"path": str(target), "old_str": "", "new_str": "x"}))[1].startswith("Error: old_str is empty")
    out = tools.bash(f"{sys.executable} -c \"print('日本語 ✓')\"")
    assert "日本語 ✓" in out


def test_write_todos_with_a_bad_status_returns_an_error_and_leaves_the_list_alone():
    todos.write_todos([{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b", "status": "pending"}]) == "Error: item 0 needs a non-empty 'activeForm'."
    assert todos.write_todos("not a list") == "Error: todos must be a list."
    assert todos.TODOS == before
    assert todos.write_todos([]) == "Todo list cleared."


def test_rewind_offers_only_user_turns_so_no_tool_call_is_orphaned(monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "ok"},
        {"role": "assistant", "content": "done one"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "done two"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.append(rows) or 1)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    monkeypatch.setattr(session, "rewind_to", lambda count: None)
    out = commands.handle("/rewind", messages)
    assert len(offered[0]) == 2 and offered[0][0].startswith("1 ") and "one" in offered[0][0]  # the index of the user message, never a tool call
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]  # cut before "two"
    for message in out:
        for tool_call in message.get("tool_calls") or []:
            assert any(m.get("tool_call_id") == tool_call["id"] for m in out)


def test_a_subagent_cannot_run_a_tool_it_was_not_offered(monkeypatch):
    seen = []
    monkeypatch.setitem(tools.TOOLS, "write_file", lambda path, content: seen.append(path) or "written")
    replies = [
        FakeMessage(content=None, tool_calls=[call("s1", "write_file", {"path": "x.txt", "content": "1"}), call("s2", "task", {"description": "again"})]),
        say("report"),
    ]
    monkeypatch.setattr(llm, "call_llm", _fake_model(replies))
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: None)
    assert subagent.task("look around") == "report" and seen == []


def test_ctrl_c_mid_turn_fills_the_missing_results_and_the_prompt_comes_back(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(session, "save", lambda messages: None)

    def boom(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(agent, "call_llm", _fake_model([FakeMessage(content=None, tool_calls=[call("c1", "bash", {"command": "sleep 60"})])]))
    out = agent.turn([{"role": "system", "content": "s"}], "wait")  # the turn catches ctrl-c and answers the pending call itself
    assert out[-1] == {"role": "tool", "tool_call_id": "c1", "content": agent.INTERRUPTED} and seen[-1] == "interrupted"


def test_ask_returns_none_to_leave_and_empty_to_continue(monkeypatch):
    def eof(text="> "):
        raise EOFError

    monkeypatch.setattr(prompt, "read", eof)
    assert ui.ask() is None
    monkeypatch.setattr(prompt, "read", lambda text="> ": "   ")
    assert ui.ask() == ""
    assert "/exit" in commands.COMMANDS


def test_bash_rules_ask_about_substitutions_redirections_and_env():
    assert permissions.decide("ls $(pwd)") == "ask" and permissions.decide("cat `which python`") == "ask"
    assert permissions.decide("echo hi > out.txt") == "ask" and permissions.decide("git log | tee log.txt") == "ask"
    assert permissions.decide("find . -name x -delete") == "ask" and permissions.decide("find . -name x") == "allow"
    assert permissions.decide("cat x 2>&1") == "allow" and permissions.split_command("cat x 2>&1") == ["cat x 2>&1"]
    assert permissions.decide("env") == "ask" and permissions.split_command("ls\nrm -rf /") == ["ls", "rm -rf /"]
    assert permissions.decide("ls\nrm -rf /") == "deny"
    assert permissions.check("write_file", {"path": ".git/config"})[0] == "ask"


def test_session_load_repairs_a_dangling_tool_call(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    session.SESSION_DIR.mkdir(parents=True)
    lines = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
    ]
    session.path_for("crashed").write_text("\n".join(json.dumps(line) for line in lines) + "\n{half a line", encoding="utf-8")
    messages = session.load("crashed")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": "(the harness stopped before this tool ran; no result was recorded)"}
    assert len(messages) == 4


def test_a_stub_from_the_plan_set_or_the_browse_set_is_loadable_and_never_runs_unloaded(monkeypatch):
    monkeypatch.setattr(budget, "DEFER_OVER", 100)  # submit_plan (plan mode) and browser_type (browse) are now over the line
    monkeypatch.setattr(tools, "STUBBED", {})
    monkeypatch.setattr(plan, "MODE", "plan")
    offered = tools.active_schemas(plan.toolset())
    stub = next(s for s in offered if s["function"]["name"] == "submit_plan")
    assert stub["function"]["description"].startswith("deferred") and "submit_plan" in tools.STUBBED

    args, result = tools.execute(call("p1", "submit_plan", {}), allowed={s["function"]["name"] for s in offered} | {"load_tool"})
    assert result.startswith("Error: submit_plan is deferred. Call load_tool('submit_plan') first")  # not a TypeError
    assert tools.execute(call("p2", "load_tool", {"name": "submit_plan"}))[1].startswith("submit_plan is enabled")
    assert next(s for s in tools.active_schemas(plan.toolset()) if s["function"]["name"] == "submit_plan") is plan.SUBMIT_PLAN_SCHEMA

    from harness import browse

    assert "browser_type" in [s["function"]["name"] for s in browse.toolset() if s["function"]["description"].startswith("deferred")]
    assert tools.load_tool("browser_type").startswith("browser_type is enabled")


def test_loaded_tools_are_relearned_from_a_resumed_transcript():
    messages = [
        {"role": "assistant", "content": None, "tool_calls": [{"id": "l1", "type": "function", "function": {"name": "load_tool", "arguments": json.dumps({"name": "big_tool"})}}]},
        {"role": "tool", "tool_call_id": "l1", "content": "big_tool is enabled for the rest of the session. Its schema:\n{}"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "l2", "type": "function", "function": {"name": "load_tool", "arguments": json.dumps({"name": "nothing"})}}]},
        {"role": "tool", "tool_call_id": "l2", "content": "Error: no tool named 'nothing'."},
    ]
    assert tools.relearn(messages) == {"big_tool"}


def test_compaction_clears_the_window_warnings(monkeypatch):
    budget.WARNED.update({0.5, 0.75})
    monkeypatch.setattr(commands.compaction, "compact", lambda messages: messages[:1])
    monkeypatch.setattr(session, "compacted", lambda messages: None)
    monkeypatch.setattr(ui, "compacted", lambda before, messages: None)
    commands.handle("/compact", [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}])
    assert budget.WARNED == set()
