import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, compact, context, llm, memory, permissions, session, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [c.model_dump() for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


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
    found = memory.find_memories()
    assert list(found) == ["handoff-latest"]  # one note, whatever the session id
    assert found["handoff-latest"]["type"] == "project"
    assert memory.recall("handoff-latest") == note
    assert "- handoff-latest: where session 20260912-101010 left off: Finish the memory step." in memory.memory_index()

    # a later session overwrites it instead of adding a line to the index
    monkeypatch.setattr(session, "CURRENT", "20260913-090000")
    commands.compact(list(messages))
    assert list(memory.find_memories()) == ["handoff-latest"]
    assert "20260913-090000" in memory.memory_index()


def test_names_are_slugs_everywhere(memory_dirs):
    out = memory.remember("Build Cmd", "how to build", "Run make.")
    assert "'build-cmd'" in out and (memory_dirs[0] / "build-cmd.md").exists()
    assert memory.recall("build-cmd") == "Run make." and memory.recall("Build Cmd") == "Run make."
    assert memory.remember("build cmd", "how to build", "Run ninja.").startswith("Replaced")
    assert list(memory.find_memories()) == ["build-cmd"]  # one memory, not two
    assert memory.forget("BUILD CMD") == "Forgot 'build-cmd'."


def test_a_non_utf8_file_does_not_break_the_index(memory_dirs):
    memory_dirs[0].mkdir(parents=True)
    (memory_dirs[0] / "latin.md").write_bytes(b"---\nname: latin\ndescription: caf\xe9\n---\n\ncaf\xe9\n")
    memory.remember("fine", "a good one", "ok")
    assert set(memory.find_memories()) == {"latin", "fine"}
    assert "caf\ufffd" in memory.recall("latin")  # the bad byte is replaced, the rest is read


def test_bodies_are_bounded_on_the_way_in_and_capped_on_the_way_out(memory_dirs, monkeypatch):
    assert memory.remember("big", "too much", "x" * (memory.MAX_BODY + 1)).startswith("Error: the content is")
    assert not (memory_dirs[0] / "big.md").exists()
    monkeypatch.setattr(memory.history, "CAP", 100)
    monkeypatch.setattr(memory.history, "spill", lambda text: "SPILLED")
    memory.remember("long", "a long one", "y" * 500)
    out = memory.recall("long")
    assert out.startswith("y" * 100) and memory.history.CAPPED in out


def test_the_task_subagent_may_recall_but_not_remember_or_forget():
    offered = {s["function"]["name"] for s in subagent.toolset()}
    assert "recall" in offered and not {"remember", "forget"} & offered


# ------------------------------------------------------- the usual failures


def test_every_tool_call_gets_a_tool_message_even_when_it_fails(quiet, monkeypatch):
    replies = [
        FakeMessage(content=None, tool_calls=[
            FakeCall(id="a", function=SimpleNamespace(name="bash", arguments='{"command": "ls')),  # broken JSON, so not through call()
            call("b", "nope", {}),
            call("c", "read_file", {"path": "missing.txt"}),
        ]),
        FakeMessage(content="all failed", tool_calls=None),
    ]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {}))
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    fed = [(m["tool_call_id"], m["content"]) for m in out if m["role"] == "tool"]
    assert [i for i, _ in fed] == ["a", "b", "c"] and all(c.startswith("Error") for _, c in fed)
    assert out[-1]["content"] == "all failed"


def test_write_todos_rejects_bad_items_and_session_load_repairs(tmp_path, monkeypatch):
    todos.TODOS[:] = [{"content": "old", "activeForm": "Old", "status": "pending"}]
    assert todos.write_todos([{"content": "a", "activeForm": "A", "status": "done"}]).startswith("Error: item 0")
    assert todos.TODOS[0]["content"] == "old"
    todos.TODOS.clear()
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    lines = [{"role": "user", "content": "go"}, {"role": "assistant", "content": None, "tool_calls": [{"id": "t9", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]}]
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    assert session.load("x")[-1] == {"role": "tool", "tool_call_id": "t9", "content": session.STOPPED}


def test_rewind_cuts_before_a_user_message_never_inside_an_exchange(monkeypatch):
    monkeypatch.setattr(session, "save", lambda messages: None)
    cuts = []
    monkeypatch.setattr(session, "rewind_to", cuts.append)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "a", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "a", "content": "ok"},
        {"role": "user", "content": "two"},
    ]
    monkeypatch.setattr(ui, "pick", lambda title, rows: 1)
    out = commands.rewind(messages)
    assert cuts == [4] and [m["role"] for m in out] == ["system", "user", "assistant", "tool"]


def test_utf8_round_trip_and_hardened_permissions(tmp_path):
    target = tmp_path / "sub" / "n.txt"
    tools.write_file(str(target), "héllo ✓\r\n")
    assert tools.read_file(str(target)) == "héllo ✓\r\n"
    assert permissions.decide("cat a > b") == "ask" and permissions.decide("ls $(x)") == "ask" and permissions.decide("ls 2>&1") == "allow"


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
