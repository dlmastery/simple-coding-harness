"""Step 33 offline tests. The checkpoint store and the session store live in
a temp directory; the working directory is a temp workspace. The loop
tests drive agent.turn with a fake model that writes and edits files, then
undo and rewind through commands.handle, and check the files on disk and
the rewind markers in the session file.
"""

import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, checkpoint, commands, context, hooks, instructions, jobs, llm, memory, permissions, plan, sandbox, session, todos, tools  # noqa: E402
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
    """A temp workspace as cwd, a temp checkpoint store and session store, no hooks, no jobs."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(permissions, "PROJECT", workspace.resolve())  # edits inside the workspace never ask
    monkeypatch.setattr(sandbox, "PROJECT", workspace.resolve())
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    monkeypatch.setattr(ui, "resumed", lambda *a, **k: None)
    monkeypatch.setattr(ui, "replay", lambda *a, **k: None)
    jobs.kill_all()
    yield workspace
    jobs.kill_all()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def scripted(steps):
    """A fake call_llm that answers with steps[n] on its n-th call."""
    replies = iter(steps)

    def fake(messages, tools=None, on_delta=None):
        return next(replies), USAGE

    return fake


def transcript():
    return session.path_for(session.CURRENT).read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------- capture and undo


def test_edit_then_undo_restores_the_file(fresh):
    target = fresh / "a.txt"
    target.write_text("before")
    checkpoint.begin_turn(3)
    assert tools.execute(call("w1", "write_file", {"path": "a.txt", "content": "after"}))[1] == "Wrote a.txt"
    assert target.read_text() == "after"

    [entry] = checkpoint.manifest(1)
    assert entry["existed"] is True and entry["tool"] == "write_file" and entry["path"] == str(target.resolve())
    assert (checkpoint.turn_dir(1) / entry["blob"]).read_text() == "before"

    assert checkpoint.undo_turn() == (1, 3, [str(target.resolve())])
    assert target.read_text() == "before"
    assert checkpoint.turns() == [] and checkpoint.undo_turn() is None  # gone: it cannot be undone twice


def test_a_new_file_that_is_undone_is_deleted(fresh):
    checkpoint.begin_turn(1)
    tools.execute(call("w1", "write_file", {"path": "first.txt", "content": "x"}))
    tools.execute(call("w2", "write_file", {"path": "second.txt", "content": "x"}))
    assert (fresh / "first.txt").exists() and (fresh / "second.txt").exists()

    entries = checkpoint.manifest(1)
    assert [e["existed"] for e in entries] == [False, False]
    assert not (checkpoint.turn_dir(1) / entries[1]["blob"]).exists()  # nothing to copy for a new file

    turn, start, restored = checkpoint.undo_turn()
    assert restored == [str((fresh / "second.txt").resolve()), str((fresh / "first.txt").resolve())]  # reverse order
    assert not (fresh / "first.txt").exists() and not (fresh / "second.txt").exists()


def test_a_file_is_captured_once_per_turn_and_the_first_state_wins(fresh):
    target = fresh / "a.txt"
    target.write_text("v0")
    checkpoint.begin_turn(1)
    tools.execute(call("w1", "write_file", {"path": "a.txt", "content": "v1"}))
    tools.execute(call("r1", "str_replace", {"path": "a.txt", "old_str": "v1", "new_str": "v2"}))
    assert target.read_text() == "v2" and len(checkpoint.manifest(1)) == 1

    checkpoint.begin_turn(5)  # a new turn captures the file again
    tools.execute(call("w2", "write_file", {"path": "a.txt", "content": "v3"}))
    assert len(checkpoint.manifest(2)) == 1 and checkpoint.summary() == [
        "turn 1    from message 1         1 file(s)  a.txt",
        "turn 2    from message 5         1 file(s)  a.txt",
    ]
    checkpoint.undo_turn()
    assert target.read_text() == "v2"
    checkpoint.undo_turn()
    assert target.read_text() == "v0"


def test_the_capture_is_a_built_in_hook_that_runs_before_configured_hooks(fresh, tmp_path, monkeypatch):
    (tmp_path / "hooks.json").write_text(json.dumps({"PreToolUse": [{"matcher": "write_file", "python": "blocker:block"}]}))
    (fresh / "blocker.py").write_text("def block(event):\n    return {'block': 'not today'}\n")
    (fresh / "a.txt").write_text("before")
    checkpoint.begin_turn(1)

    assert hooks.BUILTIN["PreToolUse"] == [{"matcher": "write_file|str_replace", "python": "harness.checkpoint:pre_tool_use"}]
    assert hooks.matches(hooks.BUILTIN["PreToolUse"][0], "str_replace") and not hooks.matches(hooks.BUILTIN["PreToolUse"][0], "read_file")

    args, result = tools.execute(call("w1", "write_file", {"path": "a.txt", "content": "after"}))
    assert result == "Blocked by hook: not today" and (fresh / "a.txt").read_text() == "before"
    assert [e["path"] for e in checkpoint.manifest(1)] == [str((fresh / "a.txt").resolve())]  # captured first, then blocked

    tools.execute(call("r1", "read_file", {"path": "a.txt"}))
    tools.execute(call("b1", "bash", {"command": "echo hi"}))
    assert len(checkpoint.manifest(1)) == 1  # only the edit tools are captured

    seen = notes(monkeypatch)
    commands.handle("/hooks", [])
    first, second = seen[0].splitlines()
    assert first.split() == ["PreToolUse", "write_file|str_replace", "harness.checkpoint:pre_tool_use", "(built-in)"]
    assert second.split() == ["PreToolUse", "write_file", "blocker:block"]


def test_the_manifest_survives_a_restart(fresh, monkeypatch):
    (fresh / "a.txt").write_text("before")
    checkpoint.begin_turn(1)
    tools.execute(call("w1", "write_file", {"path": "a.txt", "content": "after"}))

    monkeypatch.setattr(checkpoint, "TURN", 0)  # a new process knows nothing but the disk
    assert checkpoint.begin_turn(4) == 2       # numbering continues; turn 1 is not reused
    tools.execute(call("w2", "write_file", {"path": "b.txt", "content": "new"}))

    assert checkpoint.undo_turn() == (2, 4, [str((fresh / "b.txt").resolve())])
    assert checkpoint.undo_turn() == (1, 1, [str((fresh / "a.txt").resolve())])
    assert (fresh / "a.txt").read_text() == "before" and not (fresh / "b.txt").exists()


def test_undo_since_takes_the_turns_that_began_at_or_after_a_point(fresh):
    target = fresh / "a.txt"
    target.write_text("v0")
    for start, content in ((1, "v1"), (4, "v2"), (7, "v3")):
        checkpoint.begin_turn(start)
        tools.execute(call(f"w{start}", "write_file", {"path": "a.txt", "content": content}))

    undone = checkpoint.undo_since(4)
    assert [(turn, start) for turn, start, _ in undone] == [(3, 7), (2, 4)]  # newest first
    assert target.read_text() == "v1" and checkpoint.turns() == [1]
    assert checkpoint.undo_since(10) == [] and target.read_text() == "v1"


def test_compaction_moves_the_recorded_starts_with_the_transcript(fresh):
    checkpoint.begin_turn(1)
    checkpoint.begin_turn(7)
    checkpoint.begin_turn(12)
    # 15 messages became a summary plus the tail from index 10 on: [system+summary, m10, m11, m12, m13, m14]
    checkpoint.compacted(15, 6)
    assert [checkpoint.start_of(t) for t in checkpoint.turns()] == [None, None, 3]
    assert checkpoint.summary()[0].startswith("turn 1    position unknown")


# ------------------------------------------------------------- the commands


def test_undo_command_reverts_the_files_and_rewinds_the_transcript(fresh, monkeypatch):
    seen = notes(monkeypatch)
    messages = [{"role": "system", "content": "s"}]
    fake = scripted([
        use(call("w1", "write_file", {"path": "a.txt", "content": "one"})), say("wrote a"),
        use(call("r1", "str_replace", {"path": "a.txt", "old_str": "one", "new_str": "two"})), say("edited a"),
    ])
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)

    messages = agent.turn(messages, "make a.txt")
    messages = agent.turn(messages, "edit it")
    assert (fresh / "a.txt").read_text() == "two" and len(messages) == 9
    assert checkpoint.summary() == ["turn 1    from message 1         1 file(s)  a.txt (new)", "turn 2    from message 5         1 file(s)  a.txt"]

    messages = commands.handle("/undo", messages)
    assert (fresh / "a.txt").read_text() == "one"
    assert len(messages) == 5 and messages[-1]["content"] == "wrote a"
    assert json.loads(transcript()[-1]) == {"rewind_to": 5}
    assert seen[-1] == f"turn 2 undone: {(fresh / 'a.txt').resolve()}"

    messages = commands.handle("/undo", messages)
    assert not (fresh / "a.txt").exists() and messages == [{"role": "system", "content": "s"}]
    assert json.loads(transcript()[-1]) == {"rewind_to": 1}

    assert commands.handle("/undo", messages) == messages and seen[-1] == "nothing to undo"
    assert session.load(session.CURRENT) == messages  # the log replays to the same place


def test_rewind_command_restores_the_files_to_the_chosen_point(fresh, monkeypatch):
    seen = notes(monkeypatch)
    messages = [{"role": "system", "content": "s"}]
    fake = scripted([
        use(call("w1", "write_file", {"path": "a.txt", "content": "one"})), say("wrote a"),
        use(call("w2", "write_file", {"path": "b.txt", "content": "b"})), say("wrote b"),
        use(call("w3", "write_file", {"path": "a.txt", "content": "three"})), say("edited a"),
    ])
    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    for prompt in ("make a", "make b", "edit a"):
        messages = agent.turn(messages, prompt)
    assert len(messages) == 13 and (fresh / "a.txt").read_text() == "three"

    monkeypatch.setattr(ui, "pick", lambda title, rows: 4)  # keep messages 0..4: turn 1 stays, turns 2 and 3 go
    messages = commands.handle("/rewind", messages)
    assert len(messages) == 5 and messages[-1]["content"] == "wrote a"
    assert (fresh / "a.txt").read_text() == "one" and not (fresh / "b.txt").exists()
    assert checkpoint.turns() == [1] and seen[-1] == "2 turn(s) undone, 2 file(s) restored"
    assert json.loads(transcript()[-1]) == {"rewind_to": 5}

    monkeypatch.setattr(ui, "pick", lambda title, rows: None)  # cancelled: nothing moves
    assert commands.handle("/rewind", messages) is messages and (fresh / "a.txt").read_text() == "one"


def test_checkpoints_command_lists_turns_and_files(fresh, monkeypatch):
    seen = notes(monkeypatch)
    commands.handle("/checkpoints", [])
    assert seen[-1] == "no checkpoints in this chat yet"
    (fresh / "old.txt").write_text("x")
    checkpoint.begin_turn(1)
    tools.execute(call("w1", "write_file", {"path": "old.txt", "content": "y"}))
    tools.execute(call("w2", "write_file", {"path": "new.txt", "content": "y"}))
    checkpoint.begin_turn(6)
    commands.handle("/checkpoints", [])
    assert seen[-1] == "turn 1    from message 1         2 file(s)  old.txt, new.txt (new)\nturn 2    from message 6         0 file(s)  -"
    assert "/undo" in commands.COMMANDS and "/checkpoints" in commands.COMMANDS


def test_an_eval_run_leaves_no_checkpoints_behind(fresh, tmp_path, monkeypatch):
    from harness import evaluate

    checkpoint.begin_turn(1)
    (tmp_path / "eval_ws").mkdir()
    with evaluate.isolated(tmp_path / "eval_ws", tmp_path / "eval_sessions", "eval-x-1", {}):
        checkpoint.begin_turn(1)
        tools.execute(call("w1", "write_file", {"path": "made.txt", "content": "x"}))
        assert checkpoint.session_dir().name == "eval-x-1" and checkpoint.turns() == [1]
    assert not checkpoint.session_dir("eval-x-1").exists()
    assert session.CURRENT == "test-session" and checkpoint.TURN == 1 and checkpoint.turns() == [1]


# ---------------------------------------------------------------- the loop


def test_loop_smoke_a_subagent_edit_lands_in_the_same_turn_and_undo_takes_it_back(fresh, monkeypatch):
    """The main agent delegates; the subagent writes a file; one /undo reverts both the file and the turn."""
    (fresh / "notes.md").write_text("draft")
    main = iter([use(call("t1", "task", {"description": "rewrite notes.md"})), say("delegated")])
    sub = iter([use(call("s1", "write_file", {"path": "notes.md", "content": "final"})), say("rewritten")])

    def fake(messages, tools=None, on_delta=None):
        if "subagent" in messages[0]["content"]:
            return next(sub), USAGE
        return next(main), USAGE

    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)

    messages = agent.turn([{"role": "system", "content": "s"}], "please rewrite notes.md")
    assert (fresh / "notes.md").read_text() == "final" and messages[-1]["content"] == "delegated"
    assert checkpoint.turns() == [1] and [e["path"] for e in checkpoint.manifest(1)] == [str((fresh / "notes.md").resolve())]

    messages = commands.handle("/undo", messages)
    assert (fresh / "notes.md").read_text() == "draft" and messages == [{"role": "system", "content": "s"}]
    assert checkpoint.turns() == []
