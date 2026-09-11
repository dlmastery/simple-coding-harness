"""Offline tests: the patch, the client config, the renderer, and the plugin
(syntax-checked and unit-tested with node). The dsh runtime is never launched."""

import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("deepseek_harness")

import harness  # noqa: E402
from deepseek_harness import Notification  # noqa: E402

PLUGIN_DIR = Path(__file__).parent / "plugin" / "simple-harness-plugin"


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


def test_summarize_picks_the_events_worth_showing():
    call = Notification(method="session/event", payload={"event": {"type": "tool/call", "data": {"name": "bash", "arguments": {"command": "ls"}}}})
    assert harness.summarize(call) == "  tool> bash {'command': 'ls'}"
    result = Notification(method="session/event", payload={"event": {"type": "tool/result", "data": {"content": [{"type": "text", "text": "a.py\nb.py"}]}}})
    assert harness.summarize(result).strip() == "a.py b.py"
    end = Notification(method="session/event", payload={"event": {"type": "turn/end", "data": {"reason": {"kind": "completed"}}}})
    assert harness.summarize(end) == "  turn ended: completed"
    assert harness.summarize(Notification(method="agent/status", payload={"state": "busy"})) is None


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_plugin_is_valid_javascript_and_its_rules_match_step_12():
    for f in ("src/index.js", "src/rules.js"):
        subprocess.run(["node", "--check", f], cwd=PLUGIN_DIR, check=True)
    out = subprocess.run(["node", "src/rules.test.js"], cwd=PLUGIN_DIR, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "rules.js ok" in out.stdout
