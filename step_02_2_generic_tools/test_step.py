import runpy
import sys
from types import SimpleNamespace

import openai

import tools


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=self.replies.pop(0))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1,
                                  completion_tokens_details=None, prompt_tokens_details=None),
        )


def call(name, arguments):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=arguments))


def test_registry_and_schemas_agree():
    assert set(tools.TOOLS) == {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert tools.bash("echo ok").strip() == "ok"


def test_dispatch_by_name(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content=None, tool_calls=[call("bash", '{"command": "echo via-table"}')])])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: "list files")
    runpy.run_path("llm.py", run_name="__main__")
    out = capsys.readouterr().out
    assert "Tool:  bash {'command': 'echo via-table'}" in out and "via-table" in out


def test_run_tool_never_raises():
    assert tools.run_tool(call("bash", '{"command": ')) == ({}, "Error: the arguments of bash are not a JSON object: Expecting value: line 1 column 13 (char 12)")
    assert tools.run_tool(call("bash", '"just a string"'))[1].startswith("Error: the arguments of bash are not a JSON object")
    assert tools.run_tool(call("nope", "{}")) == ({}, "Error: no tool named 'nope'.")
    args, result = tools.run_tool(call("bash", '{"cmd": "ls"}'))                 # wrong keyword
    assert args == {"cmd": "ls"} and result.startswith("Error: TypeError:")
    tools.TOOLS["boom"] = lambda: 1 / 0
    assert tools.run_tool(call("boom", "{}"))[1] == "Error: ZeroDivisionError: division by zero"
    tools.TOOLS["none"] = lambda: None
    assert tools.run_tool(call("none", "{}"))[1] == "(no output)"                  # non-text results become text
    del tools.TOOLS["boom"], tools.TOOLS["none"]


def test_bash_utf8_stdin_and_timeout(monkeypatch):
    py = sys.executable
    utf8 = "import sys; sys.stdout.buffer.write(b'caf\\xc3\\xa9 \\xe2\\x9c\\x93')"
    assert tools.bash(f'{py} -c "{utf8}"') == "café ✓"                      # utf-8 decodes
    assert tools.bash(f'{py} -c "import sys; print(repr(sys.stdin.read()))"').strip() == "''"  # stdin closed: no hang
    monkeypatch.setattr(tools, "TIMEOUT", 1)
    assert tools.bash(f'{py} -c "import time; time.sleep(30)"') == "Error: command timed out after 1s"
