"""The deterministic gate: a Claude Code PreToolUse hook that blocks the two calls a skill may never make.

Shipped in every lesson's `.claude/settings.json`:

    {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
      "command": "python \\"$CLAUDE_PROJECT_DIR/../hooks/gate.py\\""}]}]}}

Claude Code pipes the tool call as JSON on stdin; exit 2 blocks it and the
message on stderr goes back to the agent. The hook blocks:

- `score_test.py` while the arm it names is not frozen (fits remain) or has
  scored the test already - the locked test, before the script runs;
- `apply.py`, and `patch_pack.py --proposal` (its second stage), without
  `--approved "<words>"` - the approval cycle, before the script runs.

Everything else passes (exit 0). The scripts refuse the same calls on their
own, so an agent without hooks (this repo's harness, Antigravity, Codex)
gets the script-level refusal instead; the hook is the playbook's
"advisory skill + deterministic gate" split made visible, and the root
codelab's step 27 shape.
"""

import json
import re
import shlex
import sys
from pathlib import Path


def argv_of(command):
    if "\\" in command and '\\"' not in command:   # Windows paths: a backslash is a separator here, not an escape
        command = command.replace("\\", "/")
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def option(args, name):
    for i, a in enumerate(args):
        if a == name and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(name + "="):
            return a[len(name) + 1:]
    return None


def state_for(args, cwd):
    """The arm entry score_test.py would touch, read the way the script reads it (same defaults)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    from _lib.state import Run, fix_path

    pack, task = option(args, "--pack"), option(args, "--task")
    if not pack or not task:
        return None
    pack, task = fix_path(pack), fix_path(task)
    run = Run(Path(cwd) / pack if not Path(pack).is_absolute() else pack, Path(cwd) / task if not Path(task).is_absolute() else task,
              option(args, "--arm") or "memory", int(option(args, "--seed") or 0), option(args, "--run"))
    return run.all_state["arms"].get(run.key)


def verdict(command, cwd):
    """(block: bool, reason)"""
    if "score_test.py" not in command and "apply.py" not in command and "patch_pack.py" not in command:
        return False, None
    for part in re.split(r"\s*(?:&&|\|\||;)\s*", command):
        args = argv_of(part)
        script = next((a for a in args if a.endswith(("score_test.py", "apply.py", "patch_pack.py"))), None)
        if not script:
            continue
        name = Path(script).name
        if name == "score_test.py":
            try:
                s = state_for(args, cwd)
            except Exception as e:      # an unreadable state is the script's problem, not the hook's
                return False, f"gate: could not read the state ({e}); the script decides"
            if s is None:
                return True, "gate: score_test.py needs --pack and --task, and an arm opened by load_splits.py"
            if not s["frozen"]:
                return True, f"gate: the test split is locked until FREEZE - {s['n_fits'] - s['fits_used']} fits remain on arm {s['arm']}"
            if s["test_scored"]:
                return True, "gate: the test split was scored once already; there is no second look"
        elif name == "apply.py":
            words = option(args, "--approved")
            if not words or not words.strip():
                return True, 'gate: apply.py needs --approved "<the user\'s exact words>" - show the proposal and ask first'
        elif name == "patch_pack.py" and option(args, "--proposal"):
            words = option(args, "--approved")
            if not words or not words.strip():
                return True, 'gate: patch_pack.py --proposal needs --approved "<the user\'s exact words>" - show the diff and ask first'
    return False, None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    block, reason = verdict(command, event.get("cwd") or Path.cwd())
    if block:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
