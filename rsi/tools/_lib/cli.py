"""How every tool script talks: arguments in, one JSON object out, exit 0.

A refusal is a result (`{"error": "..."}`), never a traceback and never a
non-zero exit: the agent reads it and decides what to do next, the same way
the root codelab's `execute()` turns a bad call into an `Error:` string.

Values that are JSON (`--recipe`, `--card`, `--payload`, ...) may be given
three ways, because shells quote differently:
  --recipe '{"model": "logreg", "hyper": 1, ...}'      JSON on the line (bash)
  --recipe model=logreg,hyper=1,scale=yes,...          key=value pairs (any shell)
  --recipe @recipe.json                                 a file (PowerShell-safe)
  --payload @rendered/                                  a directory -> {path: text} (a pack proposal)
"""

import argparse
import json
import sys
import traceback
from pathlib import Path


def value(text):
    """A JSON value from the command line: JSON, `@file`, or `k=v,k=v` (numbers and null parsed)."""
    if text is None:
        return None
    if isinstance(text, (dict, list)):
        return text
    text = text.strip()
    if text.startswith("@"):
        target = Path(text[1:])
        if target.is_dir():          # a directory of files -> {path: text}, the shape of a pack proposal
            from _lib import packs
            return packs.read_pack(target)
        return json.loads(target.read_text(encoding="utf-8"))
    if text[:1] in "{[":
        return json.loads(text)
    if "=" in text:
        out = {}
        for pair in text.split(","):
            k, _, v = pair.partition("=")
            out[k.strip()] = scalar(v.strip())
        return out
    return scalar(text)


def scalar(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def parser(doc, **args):
    """An argument parser from {name: help}; every tool takes --pack and --task unless it says otherwise."""
    p = argparse.ArgumentParser(description=doc.strip().splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=doc)
    for name, spec in args.items():
        if isinstance(spec, dict):
            p.add_argument(f"--{name}", **spec)
        else:
            p.add_argument(f"--{name}", help=spec)
    return p


def common(p, task=True, arm=True):
    p.add_argument("--pack", required=True, help="the skill pack directory (holds SKILL.md)")
    if task:
        p.add_argument("--task", required=True, help="the task.json of the problem")
    if arm:
        p.add_argument("--arm", default="memory", help="memory (default) or control: the arm whose budget this is")
        p.add_argument("--seed", type=int, default=0, help="the split seed (default 0)")
    p.add_argument("--run", default=None, help="where runs/ is (default: <lesson>/runs, or $RSI_RUNS)")
    return p


def emit(result):
    sys.stdout.write(json.dumps(result, indent=1, default=str) + "\n")
    sys.stdout.flush()


def main(fn, argv=None):
    """Run `fn(args) -> dict`; any exception is `{"error": "..."}`, exit 0. RSI_TRACEBACK=1 shows the traceback."""
    try:
        result = fn(argv)
    except SystemExit:
        raise
    except Exception as e:   # every refusal and every bug is a result the agent reads
        result = {"error": f"{e}" if isinstance(e, (ValueError, KeyError, FileNotFoundError)) else f"{type(e).__name__}: {e}"}
        import os
        if os.environ.get("RSI_TRACEBACK") == "1":
            result["traceback"] = traceback.format_exc()
    emit(result)
    return result


def call(fn, argv):
    """`main` without the printing: the tests call a script in-process and read the dict."""
    try:
        return fn(argv)
    except Exception as e:
        return {"error": f"{e}" if isinstance(e, (ValueError, KeyError, FileNotFoundError)) else f"{type(e).__name__}: {e}"}


BOOT = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
"""
