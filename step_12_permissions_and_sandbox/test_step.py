from types import SimpleNamespace

from harness import permissions, sandbox, tools
from harness.ui import ui


def call(name, arguments):
    return SimpleNamespace(id="c", function=SimpleNamespace(name=name, arguments=arguments))


def test_split_respects_quotes():
    assert permissions.split_command('grep "a|b" f | sort && echo x; ls') == ['grep "a|b" f', "sort", "echo x", "ls"]


def test_verdicts():
    assert permissions.decide("ls -la") == "allow"
    assert permissions.decide("git status && git diff") == "allow"
    assert permissions.decide("ls | python setup.py") == "ask"       # unknown part -> ask
    assert permissions.decide("cat f; rm -rf /") == "deny"           # strictest wins
    assert permissions.decide("curl http://x") == "deny"


def test_edit_outside_project_asks(tmp_path):
    assert permissions.check("write_file", {"path": "harness/tools.py", "content": ""})[0] == "allow"
    assert permissions.check("write_file", {"path": str(tmp_path / "x"), "content": ""})[0] == "ask"
    assert permissions.check("read_file", {"path": str(tmp_path / "x")})[0] == "allow"


def test_execute_enforces_policy(monkeypatch):
    _, r = tools.execute(call("bash", '{"command": "sudo ls"}'))
    assert r.startswith("Blocked by policy")

    monkeypatch.setattr(ui, "approve", lambda reason: False)
    _, r = tools.execute(call("bash", '{"command": "python -c \\"print(1)\\""}'))
    assert r == "The user declined this tool call."

    monkeypatch.setattr(ui, "approve", lambda reason: True)
    _, r = tools.execute(call("bash", '{"command": "python -c \\"print(1)\\""}'))
    assert r.strip() == "1"

    _, r = tools.execute(call("bash", '{"command": "echo silent"}'))  # allow: no prompt
    assert r.strip() == "silent"


def test_timeout_is_a_result_not_a_crash(monkeypatch):
    import subprocess

    def slow(command, timeout=60):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(sandbox, "run", slow)
    assert tools.bash("sleep 999").startswith("Timed out after 60s")


def test_sandbox_name_is_a_known_value():
    assert sandbox.name() in {"seatbelt", "bubblewrap", "none"}
