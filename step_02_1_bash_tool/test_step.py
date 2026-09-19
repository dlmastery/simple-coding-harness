import runpy
import sys
import time
from types import SimpleNamespace

import openai
import pytest


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


def run(monkeypatch, fake, prompt="what is your current directory?"):
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: prompt)
    return runpy.run_path("llm.py", run_name="__main__")


def test_tool_call_is_parsed_and_executed(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content=None, tool_calls=[call("bash", '{"command": "echo from-bash"}')])])
    run(monkeypatch, fake)
    out = capsys.readouterr().out
    assert "Tool: bash echo from-bash" in out and "from-bash" in out
    assert fake.requests[0]["tools"][0]["function"]["name"] == "bash"


def test_malformed_arguments_are_an_error_not_a_traceback(monkeypatch):
    fake = FakeClient([SimpleNamespace(content=None, tool_calls=[call("bash", '{"command": ')])])
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, fake)
    assert "Error: the arguments of bash are not a JSON object" in str(exit_info.value)


def test_bash_survives_utf8_stdin_and_timeouts(monkeypatch):
    fake = FakeClient([SimpleNamespace(content="x", tool_calls=None)])
    module = run(monkeypatch, fake)
    bash = module["bash"]
    py = sys.executable
    utf8 = "import sys; sys.stdout.buffer.write(b'caf\\xc3\\xa9 \\xe2\\x9c\\x93')"
    assert bash(f'{py} -c "{utf8}"') == "café ✓"                        # utf-8 output decodes
    assert bash(f'{py} -c "import sys; print(repr(sys.stdin.read()))"').strip() == "''"  # stdin is closed: no hang
    bash.__globals__["TIMEOUT"] = 1  # run_path hands back a copy of the globals
    started = time.time()
    assert bash(f'{py} -c "import time; time.sleep(30)"') == "Error: command timed out after 1s"
    assert time.time() - started < 10  # the tree was killed; we did not wait for the sleep
