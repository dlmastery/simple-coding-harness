"""Offline tests: the policy, the hooks and the configuration we own.

Nothing here launches Claude. The live path needs the `claude` CLI and a
login; run `python harness.py` for that.
"""

import asyncio
import os
from pathlib import Path

import pytest

pytest.importorskip("claude_agent_sdk")

import harness  # noqa: E402
import rules  # noqa: E402


def test_rules_are_the_step_12_rules():
    assert rules.decide("ls -la") == "allow"
    assert rules.decide("cat f; rm -rf /") == "deny"
    assert rules.decide("python setup.py") == "ask"
    assert rules.check_edit("harness.py")[0] == "allow"
    assert rules.check_edit(str(Path.home() / "elsewhere.txt"))[0] == "ask"


def test_pre_tool_use_hook_denies_structurally():
    denied = asyncio.run(harness.deny_dangerous({"tool_name": "Bash", "tool_input": {"command": "sudo rm -rf /"}}, "t1", None))
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert asyncio.run(harness.deny_dangerous({"tool_name": "Bash", "tool_input": {"command": "ls"}}, "t1", None)) == {}


def test_can_use_tool_allow_ask_deny(monkeypatch):
    allow = asyncio.run(harness.can_use_tool("Bash", {"command": "git status"}, None))
    assert allow.behavior == "allow"

    deny = asyncio.run(harness.can_use_tool("Bash", {"command": "curl http://x"}, None))
    assert deny.behavior == "deny" and "Blocked by policy" in deny.message

    monkeypatch.setattr(harness, "confirm", lambda reason: False)
    declined = asyncio.run(harness.can_use_tool("Bash", {"command": "python -c 1"}, None))
    assert declined.behavior == "deny" and "declined" in declined.message

    monkeypatch.setattr(harness, "confirm", lambda reason: True)
    assert asyncio.run(harness.can_use_tool("Bash", {"command": "python -c 1"}, None)).behavior == "allow"

    outside = asyncio.run(harness.can_use_tool("Write", {"file_path": str(Path.home() / "x.txt"), "content": ""}, None))
    assert outside.behavior == "allow"  # confirm is patched to True
    assert asyncio.run(harness.can_use_tool("Read", {"file_path": "/etc/hosts"}, None)).behavior == "allow"


def test_late_injection_hook_adds_env_block():
    out = asyncio.run(harness.env_context({"prompt": "hi"}, None, None))
    ctx = out["hookSpecificOutput"]
    assert ctx["hookEventName"] == "UserPromptSubmit"
    assert ctx["additionalContext"].startswith("<env>") and "git branch:" in ctx["additionalContext"]


def test_options_wire_everything_we_own():
    options = harness.build_options(resume="abc")
    assert options.resume == "abc"
    assert options.system_prompt["preset"] == "claude_code" and "explorer" in options.system_prompt["append"]
    assert options.setting_sources == ["project"] and options.skills == "all"
    assert "mcp__harness__run_tests" in options.allowed_tools
    assert options.can_use_tool is harness.can_use_tool
    assert set(options.hooks) == {"PreToolUse", "UserPromptSubmit", "PreCompact"}
    assert options.agents["explorer"].tools == ["Read", "Grep", "Glob", "Bash"]
    assert options.mcp_servers["harness"]["name"] == "harness"


def test_skill_fixture_exists():
    assert (Path(".claude/skills/explain-code/SKILL.md")).read_text().startswith("---\nname: explain-code")


def test_run_tests_tool_runs_pytest(tmp_path):
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    out = harness.run_tests_impl(str(tmp_path))
    assert "1 passed" in out


def test_run_tests_tool_reports_the_exit_code(tmp_path):
    (tmp_path / "test_bad.py").write_text("def test_bad():\n    assert False\n")
    out = harness.run_tests_impl(str(tmp_path))
    assert "1 failed" in out and out.endswith("exit code 1")


def test_the_two_policy_layers_agree_and_the_hook_wins_first():
    # a deny is final in the hook, before can_use_tool or any prompt is reached
    hook = asyncio.run(harness.deny_dangerous({"tool_name": "Bash", "tool_input": {"command": "cat f; sudo x"}}, "t", None))
    assert hook["hookSpecificOutput"]["permissionDecision"] == "deny"
    # read-only built-ins are pre-approved: they never reach can_use_tool at all
    assert {"Read", "Glob", "Grep"} <= set(harness.build_options().allowed_tools)


def test_turn_ends_on_result_or_compact_boundary_and_survives_sdk_errors(capsys):
    from claude_agent_sdk import ClaudeSDKError, ResultMessage, SystemMessage

    assert harness.ended(SystemMessage(subtype="compact_boundary", data={}))
    assert not harness.ended(SystemMessage(subtype="init", data={}))
    assert harness.ended(ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False, num_turns=1, session_id="s"))

    class DeadClient:
        async def query(self, text):
            raise ClaudeSDKError("the CLI went away")

    asyncio.run(harness.turn(DeadClient(), "hi"))  # no exception escapes
    assert "the CLI went away" in capsys.readouterr().out
