import runpy
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


def test_read_file_tool(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("contents")
    assert tools.read_file(f.as_posix()) == "contents"
    assert {s["function"]["name"] for s in tools.TOOL_SCHEMAS} == {"bash", "read_file"} == set(tools.TOOLS)


def test_read_file_is_utf8_and_keeps_line_endings(tmp_path):
    f = tmp_path / "u.txt"
    f.write_bytes("café ✓\r\nline two\n".encode("utf-8"))
    assert tools.read_file(f.as_posix()) == "café ✓\r\nline two\n"   # not the console code page, CRLF kept
    f.write_bytes(b"ok \xff bad byte")
    assert tools.read_file(f.as_posix()) == "ok � bad byte"                 # replaced, not raised


def test_missing_file_is_an_error_string(tmp_path):
    args, result = tools.run_tool(call("read_file", '{"path": "%s"}' % (tmp_path / "nope.txt").as_posix()))
    assert result.startswith("Error: FileNotFoundError:")


def test_script_reads_itself(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content=None, tool_calls=[call("read_file", '{"path": "llm.py"}')])])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: "can you read the llm.py file")
    runpy.run_path("llm.py", run_name="__main__")
    out = capsys.readouterr().out
    assert "Tool:  read_file {'path': 'llm.py'}" in out and "Stage 2.3" in out
