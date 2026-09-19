import json
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, compact, history, llm, openrouter, permissions, session, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    pass


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


class FakeCompletions:
    """Records the request and answers with a canned OpenRouter-shaped response."""

    def __init__(self, response):
        self.response = response
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        return self.response


def fake_client(response):
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(response)))


def openrouter_response(model, usage):
    return SimpleNamespace(model=model, choices=[SimpleNamespace(message=FakeMessage(content="hi", tool_calls=None))], usage=usage)


# ------------------------------------------------------------- the route


def test_route_parses_from_env_and_falls_back_to_the_default():
    assert openrouter.parse_route("a/b, c/d,,e/f ") == ["a/b", "c/d", "e/f"]
    assert openrouter.parse_route("") == openrouter.DEFAULT_MODELS
    assert openrouter.parse_route(None) == openrouter.DEFAULT_MODELS
    assert openrouter.parse_route("") is not openrouter.DEFAULT_MODELS  # a copy, so /route cannot corrupt the default


def test_provider_sort_parses_or_is_none():
    assert openrouter.parse_provider("price") == {"sort": "price"}
    assert openrouter.parse_provider(" Throughput ") == {"sort": "throughput"}
    assert openrouter.parse_provider("") is None
    assert openrouter.parse_provider("cheapest") is None


def test_request_extras_shape(monkeypatch):
    monkeypatch.setattr(openrouter, "MODELS", ["p/primary", "f/fallback"])
    monkeypatch.setattr(openrouter, "PROVIDER", None)
    extras = openrouter.request_extras()
    assert extras["extra_headers"]["X-Title"] == "simple-coding-harness" and "HTTP-Referer" in extras["extra_headers"]
    assert extras["extra_body"] == {"models": ["p/primary", "f/fallback"], "usage": {"include": True}}
    assert "provider" not in extras["extra_body"]

    monkeypatch.setattr(openrouter, "PROVIDER", {"sort": "price"})
    assert openrouter.request_extras()["extra_body"]["provider"] == {"sort": "price"}


# ----------------------------------------------------------------- cost


def test_cost_of_reads_usage_cost_or_none():
    assert openrouter.cost_of(SimpleNamespace(prompt_tokens=1, cost=0.00042)) == 0.00042
    assert openrouter.cost_of(SimpleNamespace(prompt_tokens=1)) is None
    assert openrouter.cost_of({"cost": "0.5"}) == 0.5
    assert openrouter.cost_of(SimpleNamespace(cost="not a number")) is None
    assert openrouter.cost_of(None) is None


def test_list_models_is_defensive():
    catalogue = {"data": [
        {"id": "a/b", "context_length": 128000, "pricing": {"prompt": "0.0000001", "completion": "0.0000004"}},
        {"id": "c/d"},                       # no pricing at all
        {"name": "no id"},                   # skipped
        "garbage",                           # skipped
    ]}
    client = SimpleNamespace(get=lambda path, cast_to: catalogue)
    assert openrouter.list_models(client) == [("a/b", 128000, 1e-7, 4e-7), ("c/d", None, None, None)]

    def boom(path, cast_to):
        raise RuntimeError("offline")

    assert openrouter.list_models(SimpleNamespace(get=boom)) == []


# ------------------------------------------------------------- call_llm


def test_call_llm_sends_the_route_and_returns_cost_and_model(monkeypatch):
    monkeypatch.setattr(openrouter, "MODELS", ["p/primary", "f/fallback"])
    monkeypatch.setattr(openrouter, "PROVIDER", {"sort": "price"})
    usage = SimpleNamespace(prompt_tokens=120, completion_tokens=8, cost=0.00042,
                            completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
                            prompt_tokens_details=SimpleNamespace(cached_tokens=100))
    client = fake_client(openrouter_response("f/fallback", usage))  # the primary failed; OpenRouter served the fallback
    monkeypatch.setattr(llm, "client", client)

    message, stats = llm.call_llm([{"role": "user", "content": "hi"}], tools=[])

    request = client.chat.completions.requests[0]
    assert request["model"] == "p/primary"
    assert request["extra_body"]["models"] == ["p/primary", "f/fallback"]
    assert request["extra_body"]["usage"] == {"include": True}
    assert request["extra_body"]["provider"] == {"sort": "price"}
    assert request["extra_headers"]["X-Title"] == "simple-coding-harness"
    assert "tools" not in request
    assert message.content == "hi"
    assert stats["cost"] == 0.00042 and stats["model"] == "f/fallback"
    assert stats["prompt_tokens"] == 120 and stats["cached_tokens"] == 100


def test_call_llm_without_cost_or_details_or_usage(monkeypatch):
    usage = SimpleNamespace(prompt_tokens=5, completion_tokens=1)  # a provider that reports the bare minimum
    monkeypatch.setattr(llm, "client", fake_client(openrouter_response(None, usage)))
    _, stats = llm.call_llm([{"role": "user", "content": "hi"}])
    assert stats["cost"] is None and stats["model"] is None
    assert stats["reasoning_tokens"] is None and stats["cached_tokens"] is None

    monkeypatch.setattr(llm, "client", fake_client(openrouter_response(None, None)))  # no usage at all
    _, stats = llm.call_llm([{"role": "user", "content": "hi"}])
    assert stats["prompt_tokens"] is None and stats["cost"] is None

    empty = SimpleNamespace(model=None, choices=[], usage=None, error={"message": "provider down"})
    monkeypatch.setattr(llm, "client", fake_client(empty))
    try:
        llm.call_llm([{"role": "user", "content": "hi"}])
    except RuntimeError as failure:
        assert "provider down" in str(failure)
    else:
        raise AssertionError("an empty reply must raise, not IndexError later")


def test_entry_keeps_only_role_content_and_tool_calls():
    reply = FakeMessage(content=None, reasoning="secret thoughts", tool_calls=[call("c1", "bash", "{}")])
    assert llm.entry(reply) == {"role": "assistant", "content": None, "tool_calls": [call("c1", "bash", "{}").model_dump()]}
    assert llm.entry(FakeMessage(content="hi", tool_calls=None, annotations=[])) == {"role": "assistant", "content": "hi"}


# --------------------------------------------------------------- the UI


def test_usage_line_shows_model_and_cost_and_totals_skip_the_model(capsys):
    ui._totals = {}
    ui.usage({"prompt_tokens": 1200, "completion_tokens": 30, "cached_tokens": 1000, "cost": 0.00042, "model": "p/primary"})
    ui.usage({"prompt_tokens": 10, "completion_tokens": 3, "cost": None, "model": None})
    out = capsys.readouterr().out
    assert "p/primary" in out and "$0.0004" in out
    assert ui._totals == {"prompt_tokens": 1210, "completion_tokens": 33, "cached_tokens": 1000, "cost": 0.00042}
    assert "model" not in ui._totals


# ------------------------------------------------------------- commands


def test_route_command_swaps_models_at_runtime(monkeypatch):
    monkeypatch.setattr(openrouter, "MODELS", ["old/model"])
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/route new/primary, new/fallback", messages) is messages
    assert openrouter.MODELS == ["new/primary", "new/fallback"]
    assert openrouter.request_extras()["extra_body"]["models"] == ["new/primary", "new/fallback"]
    assert "/models" in commands.COMMANDS and "/route" in commands.COMMANDS


def test_models_command_prints_route_and_cheapest_first(monkeypatch, capsys):
    monkeypatch.setattr(openrouter, "MODELS", ["p/primary", "f/fallback"])
    catalogue = [("dear/one", 8000, 1e-5, 2e-5), ("cheap/one", 128000, 1e-7, 4e-7), ("free/one", 4000, None, None)]
    monkeypatch.setattr(openrouter, "list_models", lambda client: catalogue)
    commands.handle("/models", [])
    out = capsys.readouterr().out
    assert "primary   p/primary" in out and "fallback  f/fallback" in out
    assert out.index("cheap/one") < out.index("dear/one") and "free/one" not in out  # unpriced rows are left out


# ---------------------------------------------------- tools never raise


def test_execute_turns_every_failure_into_a_result(monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    _, bad_json = tools.execute(call("c1", "bash", '{"command": '))
    assert bad_json.startswith("Error: the arguments of bash are not a JSON object")
    _, not_object = tools.execute(call("c2", "bash", '["ls"]'))
    assert not_object.startswith("Error: the arguments of bash are not a JSON object")
    _, unknown = tools.execute(call("c3", "teleport", "{}"))
    assert unknown == "Error: no tool named 'teleport'."
    _, missing = tools.execute(call("c4", "bash", "{}"))
    assert missing == "Blocked by policy: bash: missing argument 'command'"
    _, raised = tools.execute(call("c5", "read_file", json.dumps({"path": str(tmp_path / "nope.txt")})))
    assert raised.startswith("Error:") and "nope.txt" in raised
    _, withheld = tools.execute(call("c6", "write_file", json.dumps({"path": "x", "content": ""})), allowed={"bash"})
    assert withheld == "Blocked by policy: write_file is not available to this agent"


def test_file_tools_round_trip_utf8(tmp_path):
    path = str(tmp_path / "deep" / "u.txt")
    assert tools.write_file(path, "café → …\r\nline 2\n").startswith("Wrote")   # parent dir created
    assert tools.read_file(path) == "café → …\r\nline 2\n"                       # bytes and line endings kept
    assert tools.str_replace(path, "→", "->") == f"Replaced 1 match(es) in {path}"
    assert tools.str_replace(path, "", "x").startswith("Error: old_str is empty")
    # -X utf8 makes the child write UTF-8 on Windows too; bash() decodes it, and never raises on odd bytes
    assert "café" in tools.bash(f'python -X utf8 -c "print(open(r\'{path}\', encoding=\'utf-8\').read())"')


def test_permissions_see_through_shell_tricks():
    assert permissions.decide("cat f 2>&1") == "allow"
    assert permissions.decide("cat a > b") == "ask" and permissions.decide("ls | tee f") == "ask"
    assert permissions.decide("find . -name x -delete") == "ask" and permissions.decide("find . -name x") == "allow"
    assert permissions.decide("echo $(rm -rf /)") == "ask"
    assert permissions.decide("git status\nrm -rf /") == "deny"
    assert permissions.decide("env") == "ask"
    assert permissions.check("write_file", {"path": ".git/config"})[0] == "ask"


def test_write_todos_rejects_bad_lists_and_keeps_the_old_one():
    todos.write_todos([{"content": "a", "activeForm": "Doing a", "status": "in_progress"}])
    assert todos.write_todos([{"content": "b", "activeForm": "Doing b", "status": "done"}]).startswith("Error: item 0")
    assert todos.write_todos([{"content": "b"}]).startswith("Error: item 0")
    assert todos.write_todos("not a list").startswith("Error")
    assert todos.TODOS[0]["content"] == "a" and todos.active_form() == "Doing a"
    todos.write_todos([])


def test_subagent_cannot_run_a_withheld_tool_by_naming_it(monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "write_file", '{"path": "x", "content": "y"}')]),
               FakeMessage(content="done", tool_calls=None)]
    seen = []

    def fake(messages, tools=None):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {}

    monkeypatch.setattr(llm, "call_llm", fake)
    assert subagent.task("q") == "done"
    assert seen[1][3]["content"] == "Blocked by policy: write_file is not available to this agent"


# ------------------------------------------------- history and sessions


def test_strip_and_fit_act_on_capped_results(monkeypatch):
    monkeypatch.setattr(history, "SPILLS", [])
    capped = history.cap("x" * 20_000)
    assert history.CAPPED in capped and history.TRIMMED not in capped
    messages = [{"role": "tool", "tool_call_id": "c", "content": capped}]
    assert history.strip(messages) == 1 and history.TRIMMED in messages[0]["content"] and len(messages[0]["content"]) < 400
    assert history.strip(messages) == 0  # twice is a no-op
    history.sweep()


def test_rewind_only_cuts_before_a_user_message(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [call("c1", "bash", "{}").model_dump()]},
        {"role": "tool", "tool_call_id": "c1", "content": "out"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "fine"},
    ]
    monkeypatch.setattr(ui, "pick", lambda title, rows: len(rows) - 1)  # the last user turn
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    kept = commands.rewind(messages)
    assert [m["role"] for m in kept] == ["system", "user", "assistant", "tool", "assistant"]
    assert session.load(session.CURRENT) == kept


def test_session_load_repairs_a_dangling_tool_call(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "go"},
                {"role": "assistant", "content": None, "tool_calls": [call("c1", "bash", "{}").model_dump()]}]
    session.save(messages)
    reopened = session.open_session(session.CURRENT)
    assert reopened[-1] == {"role": "tool", "tool_call_id": "c1", "content": session.STOPPED}
    session.save(reopened)  # the repair reaches the file, so the next open needs none
    assert session.load(session.CURRENT)[-1]["role"] == "tool"


def test_compaction_boundary_is_a_user_message():
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "c"}]}, {"role": "tool", "tool_call_id": "c", "content": "r"},
                {"role": "assistant", "content": "done"}, {"role": "user", "content": "b"}]
    assert compact.safe_boundary(messages, 2) == 5
    assert compact.needed({"prompt_tokens": 10**9}, messages) is True
    compact.COMPACTED_AT = len(messages)
    assert compact.needed({"prompt_tokens": 10**9}, messages) is False  # nothing grew since the last try
    compact.COMPACTED_AT = 0


# ------------------------------------------------------------- the loop


def test_agent_loop_still_runs_on_top_of_the_gateway(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    seen = []
    replies = [
        FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "echo fine"}'), call("c2", "nope", "{"), call("c3", "read_file", "{}")]),
        FakeMessage(content="done", tool_calls=None),
    ]

    def fake(messages, **kw):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.0001, "model": "p/primary"}

    monkeypatch.setattr(agent, "call_llm", fake)  # agent.py binds call_llm by name at import
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    inputs = iter(["", "go", "/exit"])  # an empty line is not an exit
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(sys, "argv", ["harness"])
    ui._totals = {}
    agent.main()

    results = [m["content"] for m in seen[1] if m["role"] == "tool"]
    assert results[0].strip() == "fine"
    assert results[1].startswith("Error: the arguments of nope are not a JSON object")
    assert results[2].startswith("Error: TypeError")  # read_file() without its path
    assert [m["role"] for m in seen[1]] == ["system", "user", "assistant", "tool", "tool", "tool", "user"]  # the trailing user turn is the late injection
    assert ui._totals["cost"] == 0.0002 and "model" not in ui._totals


def test_a_failed_model_call_leaves_a_valid_transcript(monkeypatch, tmp_path):
    import openai

    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)

    def boom(messages, **kw):
        raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(agent, "call_llm", boom)
    inputs = iter(["go", None])
    monkeypatch.setattr(ui, "ask", lambda: next(inputs))
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()
    assert [m["role"] for m in session.load(session.CURRENT)] == ["system", "user"]
