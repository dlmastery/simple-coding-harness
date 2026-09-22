import json
import os
import runpy
import subprocess
import sys
from types import SimpleNamespace

import openai

import commands
import context
import session
import tools
from ui import ui


def fresh(monkeypatch, tmp_path):
    """A new process: nothing on disk, nothing seen."""
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "s1")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(session, "SEEN_SAVED", {})
    monkeypatch.setattr(context, "SEEN", {})
    monkeypatch.setattr(ui, "clear", lambda: None)


def pick(monkeypatch, choice, seen_rows):
    def fake_pick(title, rows):
        seen_rows[:] = rows
        return choice
    monkeypatch.setattr(ui, "pick", fake_pick)


def call(cid, name, arguments):
    return {"id": cid, "type": "function", "function": {"name": name, "arguments": arguments}}


def test_save_is_append_only_and_reloads(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "run it"}]
    session.save(messages)
    messages.append({"role": "assistant", "content": "ok"})
    session.save(messages)
    assert session.load("s1") == messages
    assert session.all_sessions() == [{"id": "s1", "title": "run it"}]
    assert session.path_for("s1").read_text().count("\n") == 3


def test_rewind_offers_only_user_rows_and_never_strands_a_tool_call(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": None, "tool_calls": [call("c1", "bash", '{"command": "ls"}')]},
        {"role": "tool", "tool_call_id": "c1", "content": "x"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": "d"},
    ]
    session.save(messages)
    rows = []
    pick(monkeypatch, 1, rows)                            # the second of your messages: "c"
    kept = commands.handle("/rewind", messages)
    assert len(rows) == 2 and rows[1].endswith(" c")      # only user rows are offered
    assert [m["content"] for m in kept] == ["s", "a", None, "x", "b"]   # cut just before "c"
    log = session.path_for("s1").read_text()
    assert '"rewind_to": 5' in log and '"d"' in log       # a marker, not a delete
    kept.append({"role": "user", "content": "e"})
    session.save(kept)
    assert [m["content"] for m in session.load("s1")] == ["s", "a", None, "x", "b", "e"]


def test_rewind_as_the_first_command_of_a_fresh_chat(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)                          # the session directory does not exist yet
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}]
    pick(monkeypatch, 0, [])
    kept = commands.handle("/rewind", messages)
    assert [m["role"] for m in kept] == ["system"]
    kept.append({"role": "user", "content": "b"})
    session.save(kept)
    assert [m["content"] for m in session.load("s1")] == ["s", "b"]   # the system prompt survived


def test_load_repairs_a_dangling_tool_call_and_replay_survives_bad_arguments(monkeypatch, tmp_path, capsys):
    fresh(monkeypatch, tmp_path)
    session.SESSION_DIR.mkdir(parents=True)
    crashed = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [call("c1", "bash", "{not json"), call("c2", "bash", "{}")]},
        {"role": "tool", "tool_call_id": "c1", "content": "Error: the arguments of bash are not a JSON object: x"},
    ]                                                     # the harness died before c2 ran
    session.path_for("old").write_text("".join(json.dumps(m) + "\n" for m in crashed), encoding="utf-8")

    loaded = session.load("old")
    assert loaded[-1] == {"role": "tool", "tool_call_id": "c2", "content": session.INTERRUPTED}
    ui.replay(loaded)                                     # broken JSON in the log is shown, not raised
    assert "{not json" in capsys.readouterr().out

    messages = session.open_session("old")
    assert messages == loaded and session.CURRENT == "old"
    assert session.path_for("old").read_text().count("\n") == 5       # the repair went on disk
    assert session.all_sessions()[0]["title"] == "go"


def test_seen_is_content_based_git_labelled_and_survives_a_restart(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    subprocess.run("git init -q && git config user.email t@t && git config user.name t", shell=True, check=True)
    (tmp_path / "a.txt").write_text("one")
    subprocess.run("git add . && git commit -qm init", shell=True, check=True)
    path = os.path.abspath("a.txt")

    tools.write_file("a.txt", "one")
    assert context.changes_note() == ""                   # the agent's own write is not a change
    (tmp_path / "a.txt").write_text("two")
    assert f"modified: {path}" in context.changes_note()
    assert f"modified: {path}" in context.changes_note()  # still stale until it is read again
    tools.read_file("a.txt")
    assert context.changes_note() == ""
    (tmp_path / "a.txt").write_text("one")
    assert f"modified: {path}" in context.changes_note()  # a revert is a change too
    tools.read_file("a.txt")

    session.save([{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}])
    assert '"seen"' in session.path_for("s1").read_text()
    monkeypatch.setattr(context, "SEEN", {})              # a new process
    session.open_session("s1")
    assert list(context.SEEN) == [path]                   # what the chat had read comes back with it

    os.remove("a.txt")
    assert f"deleted: {path}" in context.changes_note()
    assert context.changes_note() == ""                   # reported once, then forgotten
    assert context.reminder()["content"].startswith("<env>")


class Call(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return call(self.id, self.function.name, self.function.arguments)


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))],
                               usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1,
                                                     completion_tokens_details=None, prompt_tokens_details=None))


def test_the_loop_saves_as_it_goes_and_bad_calls_get_results(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    fake = FakeClient([
        SimpleNamespace(content=None, tool_calls=[Call(id="c1", function=SimpleNamespace(name="nope", arguments="{}"))]),
        SimpleNamespace(content="fine", tool_calls=None),
    ])
    inputs = iter(["/what", "go"])

    def read_line(_):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError                                # ctrl-d ends the chat cleanly

    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", read_line)
    monkeypatch.setattr(sys, "argv", ["agent.py"])
    sys.modules.pop("llm", None)
    runpy.run_path("agent.py", run_name="__main__")

    saved = session.load("s1")
    assert [m["role"] for m in saved] == ["system", "user", "assistant", "tool", "assistant"]
    assert saved[3]["content"] == "Error: no tool named 'nope'."
    assert "/what" not in json.dumps(saved)               # a slash command never reaches the transcript


def test_unknown_command_prints_help(capsys):
    assert commands.handle("/what", []) == []
    assert "/rewind" in capsys.readouterr().out
