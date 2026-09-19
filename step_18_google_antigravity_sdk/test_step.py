"""Offline tests: policy, hooks and config. The runtime binary is never started."""

import asyncio
import inspect
from pathlib import Path

import pytest

pytest.importorskip("google.antigravity")

import harness  # noqa: E402
from google.antigravity.hooks import HookContext  # noqa: E402
from google.antigravity.hooks.policy import Decision, enforce  # noqa: E402
from google.antigravity.types import AntigravityExecutionError, ToolCall, UsageMetadata  # noqa: E402


def call(name, **args):
    return ToolCall(name=name, args=args, id="c1", step_id="s1")


def test_predicates_read_the_runtime_arguments():
    assert harness.is_denied(call("run_command", CommandLine="cat f; rm -rf /"))
    assert harness.needs_ask(call("run_command", CommandLine="python x.py"))
    assert harness.is_plain(call("run_command", cmd="git status"))
    assert harness.edit_inside(call("edit_file", path="harness.py"))
    assert harness.edit_outside(call("create_file", TargetFile=str(Path.home() / "x.txt")))
    # the connection layer's canonical_path wins over any argument name
    canonical = ToolCall(name="edit_file", args={"path": "harness.py"}, canonical_path=str(Path.home() / "x.txt"))
    assert harness.edit_outside(canonical)


def test_policy_list_covers_every_builtin_we_care_about():
    policies = harness.build_policies(handler=lambda c: True)
    by_tool = {}
    for p in policies:
        by_tool.setdefault(p.tool, []).append(p.decision)
    assert Decision.APPROVE in by_tool["view_file"]
    assert by_tool["run_command"] == [Decision.DENY, Decision.ASK_USER, Decision.APPROVE]
    assert by_tool["search_web"] == [Decision.DENY]
    assert by_tool["read_url_content"] == [Decision.DENY]  # not in READ_ONLY, so never also allowed
    assert set(by_tool["edit_file"]) == {Decision.APPROVE, Decision.ASK_USER}


def test_enforced_policies_decide_like_step_12():
    answers = {"asked": 0}

    def handler(c):
        answers["asked"] += 1
        return False

    hook = enforce(harness.build_policies(handler))

    def decide(c):
        out = hook.run(HookContext(), c)
        return asyncio.run(out) if inspect.isawaitable(out) else out

    assert decide(call("view_file", path="x")).allow is True
    assert decide(call("run_command", CommandLine="ls")).allow is True
    assert decide(call("run_command", CommandLine="sudo ls")).allow is False
    assert decide(call("search_web", query="x")).allow is False
    assert decide(call("read_url_content", url="http://x")).allow is False
    assert decide(call("run_command", CommandLine="python x.py")).allow is False and answers["asked"] == 1
    assert decide(call("edit_file", path="harness.py")).allow is True
    assert decide(call("edit_file", path=str(Path.home() / "x"))).allow is False and answers["asked"] == 2


def test_confirm_runs_the_prompt_off_the_event_loop(monkeypatch):
    monkeypatch.setattr(harness, "prompt", lambda c: c.name == "run_command")
    assert asyncio.run(harness.confirm(call("run_command", CommandLine="python x.py"))) is True
    assert asyncio.run(harness.confirm(call("edit_file", path="x"))) is False


def test_structural_deny_hook_is_callable_directly():
    def run(c):
        out = harness.block_dangerous(c)  # decorated hooks stay callable; the wrapper is async
        return asyncio.run(out) if inspect.isawaitable(out) else out

    blocked = run(call("run_command", CommandLine="curl http://x"))
    assert blocked.allow is False and "Blocked by policy" in blocked.message
    assert run(call("run_command", CommandLine="ls")).allow is True
    assert run(call("view_file", path="x")).allow is True


def test_config_validates_offline():
    config = harness.build_config(resume=None, handler=lambda c: True)
    assert [t.__name__ for t in config.tools] == ["run_tests", "write_todos"]
    assert config.subagents[0].name == "explorer"
    enabled = config.subagents[0].capabilities.enabled_tools
    assert "run_command" not in enabled and "read_url_content" not in enabled and "view_file" in enabled
    assert config.capabilities.allowed_subagents == ["explorer"]
    assert config.skills_paths == [str(Path.cwd() / ".agents" / "skills")]
    assert len(config.hooks) == 3
    resumed = harness.build_config(resume="c" * 36, handler=lambda c: True)
    assert resumed.conversation_id == "c" * 36 and resumed.session_continuation_mode.value == "resume"


def test_our_tools_and_late_block(tmp_path):
    assert "Error" in harness.write_todos(["[~] a", "[~] b"])
    assert "Error" in harness.write_todos("[~] a")
    assert harness.write_todos(["[x] read", "[~] edit", "[ ] test"]).startswith("[x] read")
    block = harness.late_block()
    assert block.startswith("<env>") and "[~] edit" in block
    harness.write_todos([])
    assert "<todos>" not in harness.late_block()
    (tmp_path / "test_bad.py").write_text("def test_bad():\n    assert False\n")
    assert harness.run_tests(str(tmp_path)).endswith("exit code 1")


def test_usage_line_and_turn_survive_runtime_errors(capsys):
    assert harness.usage_line(None) == ""
    assert harness.usage_line(UsageMetadata(prompt_token_count=1200, candidates_token_count=30, cached_content_token_count=1000)) == "1,200 in · 30 out · 1,000 cached"

    class DeadAgent:
        async def chat(self, prompt):
            raise AntigravityExecutionError("the runtime went away")

    asyncio.run(harness.turn(DeadAgent(), "hi"))  # no exception escapes
    assert "the runtime went away" in capsys.readouterr().out
