"""Shared plumbing for the lab scripts: paths, mode banner, small report helpers."""

import os
import sys
from pathlib import Path

RSI = Path(__file__).resolve().parents[1]
RUNS = RSI / "runs"
H0 = RSI / "harnesses" / "h0"
I0 = RSI / "improvers" / "i0"


def banner(lab):
    if not (os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY")):
        os.environ.setdefault("RSI_LLM", "replay")
    mode = os.environ.get("RSI_LLM", "auto")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"== {lab}  (model calls: {mode}{'; replaying the recorded runs' if mode == 'replay' else ''})\n")


def table(rows, headers):
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    line = lambda r: "  ".join(str(x).ljust(w) for x, w in zip(r, widths))
    print(line(headers))
    print(line(["-" * w for w in widths]))
    for r in rows:
        print(line(r))
    print()


def spend():
    from . import llm
    u = llm.USAGE
    print(f"model calls this run: {u['calls']} live, {u['cached']} replayed; "
          f"tokens {u['prompt_tokens'] + u['completion_tokens']:,}")
