from types import SimpleNamespace

from harness import agent, context, llm, session, todos

USAGE = {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None}
PLAN = [
    {"content": "Read the file", "active": "Reading the file", "status": "done"},
    {"content": "Add the test", "active": "Adding the test", "status": "in_progress"},
    {"content": "Run it", "active": "Running it", "status": "pending"},
]


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_write_todos_validates_and_renders():
    assert "Error: 2 items" in todos.write_todos([dict(PLAN[1]), dict(PLAN[1])])
    out = todos.write_todos(PLAN)
    assert out == "[x] Read the file\n[~] Add the test\n[ ] Run it"
    assert todos.active_form() == "Adding the test"
    todos.write_todos([])
    assert todos.active_form() == "thinking"


def test_plan_rides_in_the_late_block(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    seen = []
    replies = [
        (SimpleNamespace(content=None, tool_calls=[call("c1", "write_todos", __import__("json").dumps({"todos": PLAN}))]), USAGE),
        (SimpleNamespace(content="ok", tool_calls=None), USAGE),
    ]

    def fake(messages, tools=None):
        seen.append(messages[-1]["content"])
        return replies.pop(0)

    monkeypatch.setattr(llm, "complete", fake)
    agent.turn([{"role": "system", "content": "s"}], "do three things")
    assert "<todos>" not in seen[0]                       # nothing planned yet
    assert "<todos>\n[x] Read the file\n[~] Add the test" in seen[1]
    assert "<todos>" in context.reminder()["content"]
    todos.write_todos([])


def test_console_script_is_declared():
    text = open("pyproject.toml").read()
    assert 'harness = "harness.agent:main"' in text
