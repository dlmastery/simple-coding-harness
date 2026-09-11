import subprocess
import sys
from pathlib import Path

import commands
import context
import session
from ui import ui


def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "CURRENT", "s1")
    monkeypatch.setattr(session, "WRITTEN", 0)


def test_save_is_append_only_and_reloads(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "run it"}]
    session.save(messages)
    messages.append({"role": "assistant", "content": "ok"})
    session.save(messages)
    assert session.load("s1") == messages
    assert session.all_sessions() == [{"id": "s1", "title": "run it"}]
    assert session.path_for("s1").read_text().count("\n") == 3


def test_rewind_is_an_entry_not_a_delete(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    session.save(messages)
    monkeypatch.setattr(ui, "pick", lambda title, rows: 1)
    monkeypatch.setattr(ui, "clear", lambda: None)
    kept = commands.handle("/rewind", messages)
    assert [m["content"] for m in kept] == ["s", "a"]
    assert '"rewind_to": 2' in session.path_for("s1").read_text() and '"b"' in session.path_for("s1").read_text()
    kept.append({"role": "assistant", "content": "c"})
    session.save(kept)
    assert [m["content"] for m in session.load("s1")] == ["s", "a", "c"]


def test_git_status_reminder_reports_a_change_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run("git init -q && git config user.email t@t && git config user.name t", shell=True, check=True)
    (tmp_path / "a.txt").write_text("one")
    subprocess.run("git add . && git commit -qm init", shell=True, check=True)
    context.LAST_STATUS = context.git_status()
    assert context.changes_note() == ""
    (tmp_path / "a.txt").write_text("two")
    assert "modified: a.txt" in context.changes_note()
    assert context.changes_note() == ""                    # reported once, then quiet
    assert context.reminder()["content"].startswith("<env>")


def test_unknown_command_prints_help(capsys):
    assert commands.handle("/what", []) == []
    assert "/rewind" in capsys.readouterr().out
