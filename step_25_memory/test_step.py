import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, compact, context, llm, memory, session, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


@pytest.fixture
def memory_dirs(tmp_path, monkeypatch):
    """Memories go to a temp dir, never to ~/.simple-harness."""
    dirs = [tmp_path / "project", tmp_path / "_user"]
    monkeypatch.setattr(memory, "MEMORY_DIRS", dirs)
    return dirs


@pytest.fixture
def quiet(monkeypatch):
    """Keep tests off the disk and off the terminal."""
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)


# ------------------------------------------------------------------- tests


def test_remember_recall_forget_round_trip(memory_dirs):
    out = memory.remember("editor", "which editor the user likes", "The user edits in Neovim.", type="user", scope="user")
    assert out.startswith("Saved user memory 'editor' (user)")
    path = memory_dirs[1] / "editor.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\nname: editor\n")
    assert "type: user" in text

    assert memory.recall("editor") == "The user edits in Neovim."
    assert memory.remember("editor", "which editor", "Now Emacs.", type="user", scope="user").startswith("Replaced")
    assert memory.recall("editor") == "Now Emacs."

    assert memory.forget("editor") == "Forgot 'editor'."
    assert not path.exists()
    assert memory.recall("editor") == "No memory named 'editor'."
    assert memory.forget("editor") == "No memory named 'editor'."


def test_scope_picks_the_directory_and_bad_values_are_errors(memory_dirs):
    memory.remember("build", "how to build", "Run make.", type="project", scope="project")
    assert (memory_dirs[0] / "build.md").exists()
    assert not (memory_dirs[1] / "build.md").exists()
    assert memory.remember("x", "d", "c", type="nope").startswith("Error: type must be one of")
    assert memory.remember("x", "d", "c", scope="nope").startswith("Error: scope must be one of")
    assert memory.find_memories()["build"]["scope"] == "project"


def test_index_lists_name_and_description(memory_dirs):
    assert memory.memory_index() == ""
    memory.remember("build", "how to build", "Run make.")
    memory.remember("editor", "the editor the user likes", "Neovim.", type="user", scope="user")
    assert memory.memory_index() == "- build: how to build\n- editor: the editor the user likes"


def test_front_matter_tolerates_a_missing_description(memory_dirs):
    memory_dirs[0].mkdir(parents=True)
    (memory_dirs[0] / "bare.md").write_text("---\nname: bare\n---\n\nJust a body.\n", encoding="utf-8")
    (memory_dirs[0] / "no-front.md").write_text("A body with no front matter at all.\n", encoding="utf-8")
    found = memory.find_memories()
    assert found["bare"]["description"] == "" and found["bare"]["type"] == "project"
    assert found["no-front"]["description"] == ""
    assert memory.recall("bare") == "Just a body."
    assert memory.recall("no-front") == "A body with no front matter at all."
    assert memory.memory_index() == "- bare: \n- no-front: "


def test_late_block_carries_the_index_only_when_non_empty(memory_dirs, monkeypatch):
    monkeypatch.setattr(context, "changes_note", lambda: "")
    assert "<memory>" not in context.reminder()["content"]
    memory.remember("build", "how to build", "Run make.")
    content = context.reminder()["content"]
    assert "<memory>\n- build: how to build\n</memory>" in content
    assert content.index("</env>") < content.index("<memory>")


def test_memory_block_comes_after_todos(memory_dirs, monkeypatch):
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(context, "todos_prompt", lambda: "[ ] a task")
    memory.remember("build", "how to build", "Run make.")
    content = context.reminder()["content"]
    assert content.index("</todos>") < content.index("<memory>")


def test_memory_command_lists_scope_and_type(memory_dirs, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/memory", messages) is messages
    assert notes == ["no memories yet"]
    memory.remember("build", "how to build", "Run make.")
    memory.remember("editor", "the editor", "Neovim.", type="user", scope="user")
    commands.handle("/memory", messages)
    listing = notes[-1]
    assert "build" in listing and "project" in listing
    assert "editor" in listing and "user" in listing
    assert "/memory" in commands.COMMANDS


def test_compaction_saves_the_handoff_note_as_a_memory(memory_dirs, monkeypatch):
    monkeypatch.setattr(session, "compacted", lambda messages: None)
    monkeypatch.setattr(ui, "compacted", lambda before, messages: None)
    monkeypatch.setattr(session, "CURRENT", "20260912-101010")
    monkeypatch.setattr(compact.config, "CONTEXT_WINDOW", 400)
    note = "## Goal\nFinish the memory step.\n\n## Next\nWrite the README."
    monkeypatch.setattr(llm, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content=note, tool_calls=None), {}))

    messages = [{"role": "system", "content": "s"}]
    for i in range(12):
        messages.append({"role": "user", "content": f"question {i} " + "x" * 200})
        messages.append({"role": "assistant", "content": f"answer {i} " + "y" * 200})

    out = commands.compact(messages)
    assert len(out) < len(messages)
    assert "handoff-20260912-101010" in memory.find_memories()
    assert memory.find_memories()["handoff-20260912-101010"]["type"] == "project"
    assert memory.recall("handoff-20260912-101010") == note
    assert "handoff-20260912-101010" in memory.memory_index()


def test_memory_tools_are_registered_and_allowed():
    names = {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert {"remember", "recall", "forget"} <= names
    assert tools.TOOLS["remember"] is memory.remember
    assert tools.TOOLS["recall"] is memory.recall
    assert tools.TOOLS["forget"] is memory.forget
    _, action, _ = tools.decide(call("m1", "recall", {"name": "build"}))
    assert action == "allow"


def test_system_prompt_tells_the_model_when_to_remember():
    assert "remember" in llm.SYSTEM_PROMPT and "recall" in llm.SYSTEM_PROMPT


def test_loop_smoke_remember_then_recall(quiet, memory_dirs, monkeypatch):
    replies = [
        FakeMessage(content=None, tool_calls=[call("t1", "remember", {"name": "editor", "description": "the editor", "content": "Neovim.", "type": "user", "scope": "user"})]),
        FakeMessage(content=None, tool_calls=[call("t2", "recall", {"name": "editor"})]),
        FakeMessage(content="you use Neovim", tool_calls=None),
    ]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)
    out = agent.turn([{"role": "system", "content": "s"}], "remember my editor, then tell me what it is")
    assert out[3]["content"].startswith("Saved user memory 'editor'")
    assert out[5] == {"role": "tool", "tool_call_id": "t2", "content": "Neovim."}
    assert out[-1]["content"] == "you use Neovim"
    # by the second request the late block already lists the new memory
    assert "<memory>\n- editor: the editor\n</memory>" in requests[1][-1]["content"]
    assert (memory_dirs[1] / "editor.md").exists()
