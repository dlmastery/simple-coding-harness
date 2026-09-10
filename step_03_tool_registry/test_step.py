from types import SimpleNamespace

import agent


def fake_call(name, arguments):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=arguments))


def test_registry_dispatches_read_file(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("contents here")
    args, result = agent.execute(fake_call("read_file", f'{{"path": "{f.as_posix()}"}}'))
    assert args == {"path": f.as_posix()}
    assert result == "contents here"


def test_registry_dispatches_bash():
    _, result = agent.execute(fake_call("bash", '{"command": "echo ok"}'))
    assert result.strip() == "ok"


def test_schemas_cover_every_tool():
    assert {s["function"]["name"] for s in agent.TOOL_SCHEMAS} == set(agent.TOOLS)
