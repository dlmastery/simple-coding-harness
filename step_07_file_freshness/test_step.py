import os
import time

import context
import tools


def test_stale_note_appears_once_a_seen_file_changes(tmp_path):
    f = (tmp_path / "a.txt").as_posix()
    tools.write_file(f, "one")                      # write records the mtime
    assert context.stale_note() == ""

    tools.read_file(f)                              # read records it too
    assert f in context.SEEN and context.stale_note() == ""

    time.sleep(0.05)
    with open(f, "w") as h:                         # someone else edits it
        h.write("two")
    os.utime(f, (time.time() + 5, time.time() + 5))  # make sure the mtime moves on coarse filesystems
    note = context.stale_note()
    assert "<system-reminder>" in note and f in note
    assert "changed on disk since you read them" in context.reminder()["content"]

    tools.read_file(f)                              # reading again clears it
    assert context.stale_note() == ""


def test_tools_record_what_they_touch(tmp_path):
    f = (tmp_path / "b.txt").as_posix()
    tools.write_file(f, "x = 1\n")
    tools.str_replace(f, "x = 1", "x = 2")
    assert f in context.SEEN and context.stale_note() == ""
