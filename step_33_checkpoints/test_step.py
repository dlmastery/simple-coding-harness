"""Step 33 offline tests. The checkpoint store and the session store live in
a temp directory; the working directory is a temp workspace. The loop
tests drive agent.turn with a fake model that writes and edits files, then
undo and rewind through commands.handle, and check the files on disk and
the rewind markers in the session file.
"""

import json
import os
import sys
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


def test_the_capture_is_a_built_in_hook_that_runs_only_for_a_call_that_is_allowed(fresh, tmp_path, monkeypatch):
    (tmp_path / "hooks.json").write_text(json.dumps({"PreToolUse": [{"matcher": "write_file", "python": "blocker:block"}]}))
    (fresh / "blocker.py").write_text("def block(event):\n    return {'block': 'not today'}\n")
    (fresh / "a.txt").write_text("before")
    checkpoint.begin_turn(1)

    assert hooks.BUILTIN["PreToolUse"] == [{"matcher": "write_file|str_replace", "python": "harness.checkpoint:pre_tool_use"}]
    assert hooks.matches(hooks.BUILTIN["PreToolUse"][0], "str_replace") and not hooks.matches(hooks.BUILTIN["PreToolUse"][0], "read_file")

    args, result = tools.execute(call("w1", "write_file", {"path": "a.txt", "content": "after"}))
    assert result == "Blocked by hook: not today" and (fresh / "a.txt").read_text() == "before"
    assert checkpoint.manifest(1) == []  # blocked before it could run: nothing to capture

    (tmp_path / "hooks.json").write_text("{}")
    tools.execute(call("w2", "str_replace", {"path": "a.txt", "old_str": "before", "new_str": "after"}))
    assert [e["path"] for e in checkpoint.manifest(1)] == [str((fresh / "a.txt").resolve())]
    assert (checkpoint.turn_dir(1) / checkpoint.manifest(1)[0]["blob"]).read_text() == "before"

    tools.execute(call("r1", "read_file", {"path": "a.txt"}))
    tools.execute(call("b1", "bash", {"command": "echo hi"}))
    assert len(checkpoint.manifest(1)) == 1  # only the edit tools are captured

    def broken(path, tool=None):
        raise OSError("disk full")

    seen = notes(monkeypatch)
    monkeypatch.setattr(checkpoint, "capture", broken)
    args, result = tools.execute(call("w3", "write_file", {"path": "b.txt", "content": "x"}))
    assert result == "Wrote b.txt" and seen[-1] == "checkpoint: could not capture b.txt (disk full); /undo will not restore it"

    (tmp_path / "hooks.json").write_text(json.dumps({"PreToolUse": [{"matcher": "write_file", "python": "blocker:block"}]}))
    commands.handle("/hooks", [])
    first, second = seen[-1].splitlines()
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

    picked = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: picked.append(rows) or 1)  # to before turn 2: turn 1 stays, turns 2 and 3 go
    messages = commands.handle("/rewind", messages)
    assert [row.split()[:2] for row in picked[0]] == [["turn", "1"], ["turn", "2"], ["turn", "3"]]  # only user turns are offered
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


def test_loop_smoke_a_subagent_cannot_edit_and_the_main_agent_edit_is_undone_with_the_turn(fresh, monkeypatch):
    """The subagent is read-only: naming write_file does not run it. The main agent's edit is captured and undone."""
    (fresh / "notes.md").write_text("draft")
    main = iter([
        use(call("t1", "task", {"description": "rewrite notes.md"})),
        use(call("w1", "write_file", {"path": "notes.md", "content": "final"})),
        say("done"),
    ])
    sub = iter([use(call("s1", "write_file", {"path": "notes.md", "content": "hacked"})), say("I could not write it")])

    def fake(messages, tools=None, on_delta=None):
        if "subagent" in messages[0]["content"]:
            return next(sub), USAGE
        return next(main), USAGE

    monkeypatch.setattr(agent, "call_llm", fake)
    monkeypatch.setattr(llm, "call_llm", fake)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)

    messages = agent.turn([{"role": "system", "content": "s"}], "please rewrite notes.md")
    assert messages[3]["content"] == "I could not write it"  # the subagent's report: its write_file was refused
    assert (fresh / "notes.md").read_text() == "final" and messages[-1]["content"] == "done"
    assert checkpoint.turns() == [1] and [e["path"] for e in checkpoint.manifest(1)] == [str((fresh / "notes.md").resolve())]

    messages = commands.handle("/undo", messages)
    assert (fresh / "notes.md").read_text() == "draft" and messages == [{"role": "system", "content": "s"}]
    assert checkpoint.turns() == []


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
    assert results["c3"].startswith("Error: no file at ")
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
    assert todos.write_todos([{"content": "b", "status": "pending"}]) == "Error: item 0 needs a non-empty 'activeForm'"
    assert todos.write_todos("not a list") == "Error: todos must be a list"
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
    assert len(offered[0]) == 2 and offered[0][0].startswith("turn 1") and "one" in offered[0][0]
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
    messages = [{"role": "system", "content": "s"}]
    with pytest.raises(KeyboardInterrupt):
        agent.turn(messages, "wait")
    out = agent.interrupted(messages)
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


def test_a_declined_write_is_not_captured(fresh, monkeypatch):
    (fresh / "a.txt").write_text("before")
    checkpoint.begin_turn(1)
    monkeypatch.setattr(permissions, "PROJECT", (fresh / "elsewhere").resolve())  # the write is now outside the project: it asks
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    assert tools.execute(call("w1", "write_file", {"path": "a.txt", "content": "after"}))[1] == tools.DENIED
    assert checkpoint.manifest(1) == [] and (fresh / "a.txt").read_text() == "before"
