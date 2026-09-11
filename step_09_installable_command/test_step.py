import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, config, llm, session  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content}


def test_console_script_entry_point_runs_the_same_loop(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    replies = [FakeMessage(content="hello from main", tool_calls=None)]
    # agent.py binds call_llm by name at import, so patch it where the loop looks it up
    monkeypatch.setattr(agent, "call_llm", lambda messages, **kw: (replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))
    inputs = iter(["hi", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(sys, "argv", ["harness"])

    agent.main()

    assert "hello from main" in capsys.readouterr().out
    assert len(list(tmp_path.glob("*.jsonl"))) == 1        # the session was saved under the home dir


def test_config_reads_env_and_the_home_file():
    assert config.MODEL and config.BASE_URL and config.ENV_FILE.name == "env"
    text = open("pyproject.toml").read()
    assert 'harness = "harness.agent:main"' in text
