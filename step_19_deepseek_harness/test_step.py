"""Offline tests: the patch, the client config, the renderer, and the plugin
(syntax-checked and unit-tested with node). The dsh runtime is never launched."""

import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("deepseek_harness")

import harness  # noqa: E402
from deepseek_harness import Notification  # noqa: E402
from deepseek_harness.errors import TransportClosedError  # noqa: E402

PLUGIN_DIR = Path(__file__).parent / "plugin" / "simple-harness-plugin"


def event(kind, data):
    """A notification the way the runtime sends it: method session.event, the event under payload."""
    return Notification(method="session.event", payload={"sessionId": "s", "event": {"type": kind, "seq": 1, "data": data}})


def test_patch_mounts_the_plugin_by_absolute_path():
    text = harness.make_patch(Path("/abs/plugin/src/index.js"), minimal=False)
    assert text.startswith("- insert:") and "name: '/abs/plugin/src/index.js'" in text
    assert "str-replace-editor" not in text
    minimal = harness.make_patch(Path("/abs/plugin/src/index.js"), minimal=True)
    assert "@deepseek-ai/dsh-tool-str-replace-editor" in minimal and "@deepseek-ai/dsh-fs-local" in minimal


def test_client_builds_without_launching(tmp_path):
    h = harness.build(minimal=True, model="deepseek-v4-flash", patch=tmp_path / "p.yml")
    assert h.config.profile == "sdk-minimal" and h.config.model == "deepseek-v4-flash"
    assert h.config.patches == (str(tmp_path / "p.yml"),)
    assert h.config.dsh_home == str(harness.HOME)
    assert h.config.request_timeout_seconds == harness.REQUEST_TIMEOUT


def test_summarize_reads_the_runtime_event_shapes():
    call = event("tool/call", {"callId": "c1", "name": "bash", "arguments": '{"command": "ls"}'})
    assert harness.summarize(call) == '  tool> bash {"command": "ls"}'
    # the tool message lives under data.message, as the session log stores it
    result = event("tool/result", {"callId": "c1", "message": {"role": "tool", "content": [{"type": "text", "text": "a.py\nb.py"}]}})
    assert harness.summarize(result).strip() == "a.py b.py"
    failed = event("tool/result", {"callId": "c1", "message": {"role": "tool", "content": [{"type": "text", "text": "no such file"}]}, "error": {"name": "ENOENT", "code": "fs"}})
    assert harness.summarize(failed).strip() == "error ENOENT: no such file"
    end = event("turn/end", {"turn": 1, "reason": {"kind": "completed"}})
    assert harness.summarize(end) == "  turn ended: completed"
    assert harness.summarize(event("compaction/end", {"compactionId": "x", "turn": 1})) == "  compacted"
    assert harness.summarize(event("compaction/start", {"compactionId": "x", "turn": 1})) is None
    assert harness.summarize(Notification(method="session.status", payload={"sessionId": "s", "status": "busy"})) is None


def test_turn_survives_a_dead_runtime(capsys):
    class DeadHarness:
        def run(self, text, **kwargs):
            raise TransportClosedError("runtime exited")

    harness.turn(DeadHarness(), "hi", "s1")  # no exception escapes
    assert "TransportClosedError: runtime exited" in capsys.readouterr().out


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_plugin_is_valid_javascript_and_its_rules_match_step_12():
    for f in ("src/index.js", "src/rules.js"):
        subprocess.run(["node", "--check", f], cwd=PLUGIN_DIR, check=True)
    out = subprocess.run(["node", "src/rules.test.js"], cwd=PLUGIN_DIR, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "rules.js ok" in out.stdout and "index.js gate ok" in out.stdout
