"""Step 49 - Demo: an agent that asks before it acts, then the token breakdown of the turn.

    python demo.py                       # asks on the terminal
    python demo.py --answer python       # answers the question without a prompt
    python demo.py "make me a website"   # another prompt
"""

from __future__ import annotations

import argparse
import sys

from client import context, questions
from trueforge_sdk.core.api_error import ApiError

INSTRUCTIONS = (
    "You set up new projects. Before you plan anything, call ask_user_question once "
    "to ask which kind of project the user wants, with exactly two options: "
    "'python' and 'node'. Then list the files you would create, one per line, "
    "at most four lines. Do not create anything."
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Step 49 demo")
    parser.add_argument("prompt", nargs="?", default="set up a project for me")
    parser.add_argument("--answer", help="answer every question with this text instead of asking")
    parser.add_argument("--base-url", default=context.BASE_URL)
    args = parser.parse_args(argv)

    try:
        return run(args)
    except context.REQUEST_ERRORS as error:  # server down, or a request it refused: one line, exit 1
        detail = f"answered {error.status_code}: {str(error.body)[:200]}" if isinstance(error, ApiError) else f"is not answering ({type(error).__name__}: {error})"
        print(f"request failed: {args.base_url} {detail}", file=sys.stderr)
        return 1


def run(args) -> int:
    client = context.connect(args.base_url)
    spec = context.build_spec(INSTRUCTIONS)
    print(context.describe_spec(spec))
    session_id = context.open_session(client, spec)
    print(f"session           {session_id}\n")
    print(f"> {args.prompt}")

    read = scripted(args.answer) if args.answer else input
    turns = questions.run(client, session_id, args.prompt, read=read,
                          on_delta=lambda text: print(text, end="", flush=True))
    print()

    messages = [message for turn in turns for message in turn.messages]
    print(f"\n{len(turns)} turn(s), {len(messages)} model call(s)")
    print(context.usage_table(messages))
    print(context.metrics_line(context.sum_metrics(turns)))  # every turn of this run added up
    print(context.status_line(turns[-1].state))
    return 0 if turns[-1].status == "done" else 1


def scripted(answer: str):
    """A stand-in for `input` that prints the scripted answer after the prompt."""
    def read(prompt: str) -> str:
        print(f"{prompt}{answer}")
        return answer
    return read


if __name__ == "__main__":
    sys.exit(main())
