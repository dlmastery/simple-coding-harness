"""Step 47 - demo: a coding turn on TrueForge with the tools server and the approval prompt.

    python demo.py "add a docstring to hello.py"

Creates a temp project with one file, starts `tools_server.py` on port 8931
for it, registers `s47-tools`, opens a session with the tools attached, and
runs the prompt through the approval loop. Read-only calls run on their
own; the first write pauses the turn and asks on the terminal. The temp
project is printed at the end and removed, and the tools server is stopped.
`--project DIR` uses a directory of your own and keeps it.
"""

import argparse
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from client import approve
from client.connect import BASE_URL, REQUEST_ERRORS, connect, describe_error
from register import TOOLS_URL, list_tools, print_tools, register

HERE = Path(__file__).parent
PORT = 8931
HELLO = 'def hello():\n    print("hello")\n'


def wait_for_port(port: int, seconds: float = 15) -> None:
    """Block until something accepts connections on the port, or raise."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"tools server did not come up on port {port}")


def start_tools_server(project: Path) -> subprocess.Popen:
    """Run tools_server.py as a child process rooted at the project."""
    command = [sys.executable, str(HERE / "tools_server.py"), "--project", str(project), "--port", str(PORT)]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for_port(PORT)
    return process


def short(path: Path) -> str:
    """The path with the home directory shown as `~`."""
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(path)


def ask(prompt: str) -> str:
    """input() that echoes the answer when stdin is piped, so a recording shows it."""
    answer = input(prompt)
    if not sys.stdin.isatty():
        print(answer)
    return answer


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One coding turn on TrueForge through s47-tools.")
    parser.add_argument("prompt")
    parser.add_argument("--project", help="use this directory instead of a temp project (kept afterwards)")
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args(argv)

    temporary = args.project is None
    project = Path(tempfile.mkdtemp(prefix="s47_")) if temporary else Path(args.project).resolve()
    if temporary:
        (project / "hello.py").write_text(HELLO, encoding="utf-8")
    print(f"project: {short(project)}")

    server = None
    try:
        server = start_tools_server(project)
        client = connect(args.base_url)
        register(client, TOOLS_URL)
        tools = list_tools(client)
        print(f"registered s47-tools with {len(tools)} tools:")
        print_tools(tools)

        session = client.sessions.create(agent=approve.agent_spec())
        print(f"session: {session.data.id}")
        print(f"> {args.prompt}")
        result = approve.chat(client, session.data.id, args.prompt, approve.Approver(ask))
        m = result.metrics or {}
        print(f"[turn {result.status}] in={m.get('total_input_tokens')} out={m.get('total_output_tokens')}")
        if temporary:
            print("hello.py now:")
            print((project / "hello.py").read_text(encoding="utf-8").rstrip())
        return 0 if result.status == "done" else 1
    except REQUEST_ERRORS as error:  # server down or a refused request: one line, exit 1
        print(f"request failed: {describe_error(error, args.base_url)}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.terminate()
        if temporary:
            shutil.rmtree(project, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
