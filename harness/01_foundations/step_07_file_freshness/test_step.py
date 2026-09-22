import os
import time

import context
import tools


def touch(path, text):
    """Someone else edits the file, with an mtime that has certainly moved."""
    with open(path, "w", encoding="utf-8") as h:
        h.write(text)
    later = time.time() + 5
    os.utime(path, (later, later))


def test_stale_note_appears_once_a_seen_file_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(context, "SEEN", {})
    f = (tmp_path / "a.txt").as_posix()
    tools.write_file(f, "one")                      # write records the mtime
    assert context.stale_note() == ""

    tools.read_file(f)                              # read records it too
    assert os.path.abspath(f) in context.SEEN and context.stale_note() == ""

    touch(f, "two")
    note = context.stale_note()
    assert "<system-reminder>" in note and os.path.abspath(f) in note
    assert "changed on disk since you read them" in context.reminder()["content"]
    assert "<system-reminder>" in context.stale_note()   # still stale until it is read again

    tools.read_file(f)                              # reading again clears it
    assert context.stale_note() == ""


def test_tools_record_what_they_touch_under_one_name(tmp_path, monkeypatch):
    monkeypatch.setattr(context, "SEEN", {})
    monkeypatch.chdir(tmp_path)
    tools.write_file("b.txt", "x = 1\n")
    tools.str_replace("./b.txt", "x = 1", "x = 2")  # a different spelling of the same file
    tools.read_file(str(tmp_path / "b.txt"))
    assert list(context.SEEN) == [os.path.abspath("b.txt")] and context.stale_note() == ""


def test_a_deleted_file_is_reported_once(tmp_path, monkeypatch):
    monkeypatch.setattr(context, "SEEN", {})
    f = (tmp_path / "gone.txt").as_posix()
    tools.write_file(f, "bye")
    os.remove(f)
    assert "(deleted)" in context.stale_note()
    assert context.stale_note() == ""                # forgotten: nothing left to re-read
