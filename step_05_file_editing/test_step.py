import os
from types import SimpleNamespace

import tools


def call(name, arguments):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=arguments))


def test_write_then_replace(tmp_path):
    f = (tmp_path / "hello.txt").as_posix()
    assert tools.write_file(f, "hello world\n" * 5) == f"Wrote {f}"
    assert "matches 5 times" in tools.str_replace(f, "hello world", "goodbye")     # ambiguous: refused
    assert "Replaced 5" in tools.str_replace(f, "hello world", "goodbye", allow_multi_edit=True)
    assert tools.read_file(f) == "goodbye\n" * 5
    assert "not found" in tools.str_replace(f, "hello", "x")


def test_edits_never_raise(tmp_path):
    f = (tmp_path / "a.txt").as_posix()
    tools.write_file(f, "x = 1\n")
    assert tools.str_replace(f, "", "y") == "Error: old_str is empty"            # would match between every character
    missing = (tmp_path / "missing.txt").as_posix()
    assert tools.str_replace(missing, "a", "b") == f"Error: {missing} does not exist"
    nested = (tmp_path / "new" / "deep" / "file.txt").as_posix()
    assert tools.write_file(nested, "made the folders too") == f"Wrote {nested}"  # parent dirs are created
    assert tools.read_file(nested) == "made the folders too"
    _, result = tools.run_tool(call("read_file", '{"path": "%s"}' % missing))    # anything else: an Error: string
    assert result.startswith("Error: FileNotFoundError:")


def test_utf8_and_line_endings_survive_a_round_trip(tmp_path):
    f = (tmp_path / "u.py")
    tools.write_file(f.as_posix(), "# café ✓ —\r\nx = 1\r\ny = 2\n")
    assert f.read_bytes() == "# café ✓ —\r\nx = 1\r\ny = 2\n".encode("utf-8")  # utf-8, no newline translation
    assert "Replaced 1" in tools.str_replace(f.as_posix(), "x = 1", "x = 10")
    assert f.read_bytes() == "# café ✓ —\r\nx = 10\r\ny = 2\n".encode("utf-8")  # CRLF lines are still CRLF
    assert tools.read_file(f.as_posix()) == "# café ✓ —\r\nx = 10\r\ny = 2\n"
    show = f"import sys; sys.stdout.buffer.write(open(r'{f}', 'rb').read()[:11])"
    assert tools.bash(f'{os.sys.executable} -c "{show}"') == "# café ✓"     # the bash tool decodes utf-8 too


def test_registry_has_five_tools():
    assert set(tools.TOOLS) == {"bash", "read_file", "write_file", "str_replace", "read_skill"}
    assert set(tools.TOOLS) == {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
