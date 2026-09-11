import os
import subprocess

os.environ.setdefault("API_KEY", "x")

from harness import sandbox, tools  # noqa: E402


def test_sandbox_name_and_run():
    assert sandbox.name() in {"seatbelt", "bubblewrap", "none"}
    assert sandbox.run("echo boxed").stdout.strip() == "boxed"


def test_timeout_is_a_result_not_a_crash(monkeypatch):
    def slow(command, timeout=60):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(sandbox, "run", slow)
    assert tools.bash("sleep 999").startswith("Timed out after 60s")
