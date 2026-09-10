"""Offline tests: policy, hooks and config. The runtime binary is never started."""

import asyncio
import inspect
from pathlib import Path

import pytest

pytest.importorskip("google.antigravity")

import harness  # noqa: E402
from google.antigravity.hooks import HookContext  # noqa: E402
from google.antigravity.hooks.policy import Decision, enforce  # noqa: E402
from google.antigravity.types import ToolCall  # noqa: E402


def call(name, **args):
    return ToolCall(name=name, args=args, id="c1", step_id="s1")


def test_predicates_read_the_runtime_arguments():
    assert harness.is_denied(call("run_command", command="cat f; rm -rf /"))
    assert harness.needs_ask(call("run_command", CommandLine="python x.py"))
    assert harness.is_plain(call("run_command", cmd="git status"))
    assert harness.edit_inside(call("edit_file", path="harness.py"))
    assert harness.edit_outside(call("create_file", AbsolutePath=str(Path.home() / "x.txt")))


def test_policy_list_covers_every_builtin_we_care_about():
    policies = harness.build_policies(handler=lambda c: True)
    by_tool = {}
    for p in policies:
        by_tool.setdefault(p.tool, []).append(p.decision)
    assert Decision.APPROVE in by_tool["view_file"]
    assert by_tool["run_command"] == [Decision.DENY, Decision.ASK_USER, Decision.APPROVE]
    assert by_tool["search_web"] == [Decision.DENY]
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
    assert decide(call("run_command", command="ls")).allow is True
    assert decide(call("run_command", command="sudo ls")).allow is False
    assert decide(call("search_web", query="x")).allow is False
    assert decide(call("run_command", command="python x.py")).allow is False and answers["asked"] == 1
    assert decide(call("edit_file", path="harness.py")).allow is True
    assert decide(call("edit_file", path=str(Path.home() / "x"))).allow is False and answers["asked"] == 2


def test_structural_deny_hook_is_callable_directly():
    def run(c):
        out = harness.block_dangerous(c)  # decorated hooks stay callable; the wrapper is async
        return asyncio.run(out) if inspect.isawaitable(out) else out

    blocked = run(call("run_command", command="curl http://x"))
    assert blocked.allow is False and "Blocked by policy" in blocked.message
    assert run(call("run_command", command="ls")).allow is True
    assert run(call("view_file", path="x")).allow is True


def test_config_validates_offline():
    config = harness.build_config(resume=None, handler=lambda c: True)
    assert [t.__name__ for t in config.tools] == ["run_tests", "write_todos"]
    assert config.subagents[0].name == "explorer"
    assert "run_command" not in config.subagents[0].capabilities.enabled_tools
    assert config.capabilities.allowed_subagents == ["explorer"]
    assert config.skills_paths == [str(Path.cwd() / ".agents" / "skills")]
    assert len(config.hooks) == 3
    resumed = harness.build_config(resume="c" * 36, handler=lambda c: True)
    assert resumed.conversation_id == "c" * 36 and resumed.session_continuation_mode.value == "resume"


def test_our_tools_and_late_block():
    assert "Error" in harness.write_todos(["[~] a", "[~] b"])
    assert harness.write_todos(["[x] read", "[~] edit", "[ ] test"]).startswith("[x] read")
    block = harness.late_block()
    assert block.startswith("<env>") and "[~] edit" in block
    harness.write_todos([])
    assert "<todos>" not in harness.late_block()
