"""Step 46 - A chat REPL on TrueForge, with a headless mode.

    python demo.py                          # REPL: type a prompt, /exit to leave
    python demo.py --resume <session id>    # continue an earlier session
    python demo.py -p "prompt"              # one turn, the reply on stdout, exit 0
"""

import argparse
import sys

from client import loop


def parse_args(argv):
    parser = argparse.ArgumentParser(description="chat with a TrueForge agent")
    parser.add_argument("-p", "--print", dest="prompt", metavar="PROMPT", help="run one turn and exit")
    parser.add_argument("--resume", metavar="SESSION_ID", help="continue this session")
    return parser.parse_args(argv)


def headless(prompt, session_id):
    """Stream one reply to stdout; the usage line goes to stderr so stdout stays pipeable.

    Exit 1 when the turn did not end in `done`: the error text goes to stderr
    too, so a script that pipes stdout sees an empty reply and a failing code.
    """
    session_id, text, metrics, status = loop.chat(prompt, session_id)
    print(flush=True)
    if status != "done":
        print(text, file=sys.stderr)
    print(f"[{loop.usage_line(metrics)} | session {session_id}]", file=sys.stderr)
    return 0 if status == "done" else 1


def repl(session_id):
    """Read a prompt, stream the reply, print the usage line, repeat."""
    print(f"TrueForge at {loop.BASE_URL}, model {loop.MODEL}. ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave.")
    if session_id:
        print(f"resuming session {session_id}")
    while True:
        try:
            prompt = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not prompt:
            continue
        if prompt in ("/exit", "/quit"):
            break
        try:
            session_id, text, metrics, status = loop.chat(prompt, session_id)
        except loop.REQUEST_ERRORS as error:  # the server is down or refused the turn; the REPL stays up
            print(f"\n  [request failed: {loop.describe_error(error)}]")
            continue
        except KeyboardInterrupt:  # ctrl-c while streaming; the turn keeps running on the server
            print("\n  [interrupted; the turn may still be running on the server]")
            continue
        print()
        if status != "done":
            print(f"  {text}")
        print(f"  [{loop.usage_line(metrics)}]")
    if session_id:
        print(f"session {session_id}  (python demo.py --resume {session_id})")
    return 0


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.prompt:
            return headless(args.prompt, args.resume)
        return repl(args.resume)
    except loop.REQUEST_ERRORS as error:  # one line instead of a traceback, exit 1
        print(f"request failed: {loop.describe_error(error)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
