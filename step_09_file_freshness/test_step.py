import os
import subprocess

from harness import context


def test_changes_are_reported_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run("git init -q && git config user.email t@t && git config user.name t", shell=True, check=True)
    (tmp_path / "a.txt").write_text("one")
    subprocess.run("git add . && git commit -qm init", shell=True, check=True)

    context.LAST = context.git_state()
    assert context.changes_note() == ""            # nothing moved yet

    (tmp_path / "a.txt").write_text("two")         # someone edits the file
    note = context.changes_note()
    assert "modified: a.txt" in note and "<system-reminder>" in note

    assert context.changes_note() == ""            # reported once, then quiet

    (tmp_path / "b.txt").write_text("new")
    assert "new: b.txt" in context.changes_note()


def test_content_hash_catches_edits_git_status_would_not_distinguish(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run("git init -q", shell=True, check=True)
    (tmp_path / "x.txt").write_text("v1")
    context.LAST = context.git_state()             # x.txt is already "new"
    (tmp_path / "x.txt").write_text("v2")          # still "new", but different
    assert "x.txt" in context.changes_note()
