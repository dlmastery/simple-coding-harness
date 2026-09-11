import os

os.environ.setdefault("API_KEY", "x")

from harness import context, todos, tools  # noqa: E402

PLAN = [
    {"content": "Write hello.txt", "activeForm": "Writing hello.txt", "status": "completed"},
    {"content": "Write the star pattern", "activeForm": "Writing the star pattern", "status": "in_progress"},
    {"content": "Write fibonacci", "activeForm": "Writing fibonacci", "status": "pending"},
]


def test_write_todos_replaces_the_list_and_validates():
    assert "Only one may be" in todos.write_todos([dict(PLAN[1]), dict(PLAN[1])])
    assert todos.write_todos(PLAN) == "[x] Write hello.txt\n[~] Write the star pattern\n[ ] Write fibonacci"
    assert todos.active_form() == "Writing the star pattern"
    assert "<todos>\n[x] Write hello.txt" in context.reminder()["content"]   # re-injected every call
    todos.write_todos([])
    assert todos.active_form() == "thinking" and "<todos>" not in context.reminder()["content"]


def test_it_is_a_tool():
    assert tools.TOOLS["write_todos"] is todos.write_todos
    assert "write_todos" in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
