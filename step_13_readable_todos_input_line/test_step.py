import os

os.environ.setdefault("API_KEY", "x")

from harness import prompt  # noqa: E402
from harness.ui import ui  # noqa: E402


def test_todos_render_as_a_checklist_not_raw_output(capsys):
    plan = [{"content": "Read it", "activeForm": "Reading", "status": "completed"},
            {"content": "Edit it", "activeForm": "Editing", "status": "in_progress"}]
    ui.tool("write_todos", {"todos": plan}, "raw text that must not be shown")
    out = capsys.readouterr().out
    assert "todos 1/2" in out and "Edit it" in out and "raw text" not in out


def test_input_line_module_is_wired():
    assert prompt.HISTORY.name == "history"
    assert ui.ask.__code__.co_names and "prompt" in ui.ask.__code__.co_names  # ask() goes through prompt.read
