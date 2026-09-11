import tools


def test_write_then_replace(tmp_path):
    f = (tmp_path / "hello.txt").as_posix()
    assert tools.write_file(f, "hello world\n" * 5) == f"Wrote {f}"
    assert "matches 5 times" in tools.str_replace(f, "hello world", "goodbye")     # ambiguous: refused
    assert "Replaced 5" in tools.str_replace(f, "hello world", "goodbye", allow_multi_edit=True)
    assert tools.read_file(f) == "goodbye\n" * 5
    assert "not found" in tools.str_replace(f, "hello", "x")


def test_registry_has_five_tools():
    assert set(tools.TOOLS) == {"bash", "read_file", "write_file", "str_replace", "read_skill"}
    assert set(tools.TOOLS) == {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
