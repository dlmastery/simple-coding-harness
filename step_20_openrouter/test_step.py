import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, llm, openrouter, session  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


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


def test_call_llm_without_cost_or_details(monkeypatch):
    usage = SimpleNamespace(prompt_tokens=5, completion_tokens=1)  # a provider that reports the bare minimum
    monkeypatch.setattr(llm, "client", fake_client(openrouter_response(None, usage)))
    _, stats = llm.call_llm([{"role": "user", "content": "hi"}])
    assert stats["cost"] is None and stats["model"] is None
    assert stats["reasoning_tokens"] is None and stats["cached_tokens"] is None


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


# ------------------------------------------------------------- the loop


def test_agent_loop_still_runs_on_top_of_the_gateway(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    seen = []
    replies = [
        FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "echo fine"}')]),
        FakeMessage(content="done", tool_calls=None),
    ]

    def fake(messages, **kw):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.0001, "model": "p/primary"}

    monkeypatch.setattr(agent, "call_llm", fake)  # agent.py binds call_llm by name at import
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    inputs = iter(["go", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(sys, "argv", ["harness"])
    ui._totals = {}
    agent.main()

    results = [m["content"] for m in seen[1] if m["role"] == "tool"]
    assert results[0].strip() == "fine"
    assert [m["role"] for m in seen[1]] == ["system", "user", "assistant", "tool", "user"]  # the trailing user turn is the late injection
    assert ui._totals["cost"] == 0.0002 and "model" not in ui._totals
