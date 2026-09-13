"""Step 32 offline tests. A big fake tool joins the registry so a deferred
tool exists whatever the real schemas measure. The breakdown is checked
on a transcript that has every category in it; the warnings are checked
through budget.check and through the loop with a fake model that reports
a large prompt.
"""

import io
import json
import os
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
    assert names(offered) == ["bash", "read_file", "read_skill", "task", "submit_plan"]  # nothing deferred: no load_tool
    monkeypatch.setattr(plan, "READ_ONLY", (*plan.READ_ONLY, "big_tool"))
    offered = tools.active_schemas(plan.toolset())
    assert names(offered) == ["bash", "read_file", "read_skill", "task", "big_tool", "submit_plan", "load_tool"]
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
