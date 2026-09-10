from types import SimpleNamespace

from harness import tools


def call(name, arguments):
    return SimpleNamespace(id="c", function=SimpleNamespace(name=name, arguments=arguments))


def test_write_then_str_replace(tmp_path):
    f = (tmp_path / "a.py").as_posix()
    assert "Wrote" in tools.write_file(f, "x = 1\ny = 2\n")
    assert "Replaced 1" in tools.str_replace(f, "y = 2", "y = 3")
    assert open(f).read() == "x = 1\ny = 3\n"


def test_str_replace_refuses_ambiguous_and_missing(tmp_path):
    f = (tmp_path / "a.txt").as_posix()
    tools.write_file(f, "a\na\n")
    assert "matches 2 times" in tools.str_replace(f, "a", "b")
    assert "Replaced 2" in tools.str_replace(f, "a", "b", allow_multi=True)
    assert "not found" in tools.str_replace(f, "zzz", "b")


def test_execute_never_raises():
    _, r = tools.execute(call("bash", "{not json"))
    assert r.startswith("Error: arguments were not valid JSON")
    _, r = tools.execute(call("teleport", "{}"))
    assert "no tool named 'teleport'" in r
    _, r = tools.execute(call("read_file", '{"nope": 1}'))
    assert "wrong arguments" in r
    _, r = tools.execute(call("read_file", '{"path": "/definitely/missing.txt"}'))
    assert "FileNotFoundError" in r


def test_optional_param_is_not_required():
    s = tools.TOOLS["str_replace"][1]["function"]["parameters"]
    assert s["properties"]["allow_multi"]["type"] == "boolean"
    assert "allow_multi" not in s["required"]
