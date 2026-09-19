"""Record the demo: bundle @ag-ui/client if needed, start the server with a
fresh work directory, drive the page in headless Chromium through one
coding task, print a folded event log, list the work directory and save
demo.png. Needs a model key; the tests do not.

    python demo.py
"""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

STEP = Path(__file__).resolve().parent
WORKDIR = STEP / "workdir"
shutil.rmtree(WORKDIR, ignore_errors=True)
os.environ["HARNESS_WORKDIR"] = str(WORKDIR)

import uvicorn  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from server import BUNDLE, PORT, app  # noqa: E402

URL = f"http://127.0.0.1:{PORT}"
PROMPTS = [
    "Create hello.py that prints 'hello from AG-UI', then run it with python and report the output.",
    "Plan this with write_todos first: add a function greet(name) to hello.py, call it with 'AG-UI', run the file again.",
]


def ensure_bundle():
    npm = shutil.which("npm")
    if not (STEP / "node_modules").exists():
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True)
    if not BUNDLE.exists():
        subprocess.run([npm, "run", "build"], cwd=STEP, check=True)


def start_server():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return server
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"server did not start on port {PORT} (in use?)")


def folded(events):
    """One line per event, with runs of ARGS and CONTENT deltas folded into one."""
    lines, run = [], None
    for e in events:
        if e["type"] in ("TOOL_CALL_ARGS", "TEXT_MESSAGE_CONTENT"):
            if run and run[0] == e["type"]:
                run[1] += 1
                run[2] += e["delta"]
            else:
                run = [e["type"], 1, e["delta"]]
                lines.append(run)
            continue
        run = None
        detail = {
            "TOOL_CALL_START": lambda: e["toolCallName"],
            "TOOL_CALL_RESULT": lambda: e["content"].strip().replace("\n", " | ")[:60],
            "CUSTOM": lambda: f"{e['name']}: {e['value']['reason']} -> {e['value']['decision']}",
            "STATE_DELTA": lambda: ", ".join(f"{op['op']} {op['path']} ({len(op['value'])} todos)" for op in e["delta"]),
            "STATE_SNAPSHOT": lambda: f"{len(e['snapshot'].get('todos', []))} todos",
            "RUN_FINISHED": lambda: f"usage {e['usage'][0]['inputTokens']} in, {e['usage'][0]['outputTokens']} out",
            "RUN_ERROR": lambda: e["message"],
        }.get(e["type"], lambda: "")()
        lines.append([e["type"], 0, detail])
    return [f"{t:<20} {d if not n else f'{n} events: {d[:60]}'}".rstrip() for t, n, d in lines]


def drive():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL)
        for prompt in PROMPTS:
            print(f"> {prompt}")
            page.fill("#prompt", prompt)
            page.click("button[type=submit]")
            page.wait_for_function("document.getElementById('status').textContent !== 'running'", timeout=180000)
            events = [json.loads(line) for line in page.text_content("#wire").splitlines() if line.strip()]
            for line in folded(events):
                print("  " + line)
        page.wait_for_timeout(200)
        page.screenshot(path=str(STEP / "demo.png"))
        print(f"status: {page.text_content('#status')}; todos: {page.locator('#todos li').all_text_contents()}")
        browser.close()
    print(f"workdir: {sorted(p.name for p in WORKDIR.iterdir())}")
    print("saved demo.png")


if __name__ == "__main__":
    ensure_bundle()
    server = start_server()
    drive()
    server.should_exit = True
    sys.exit(0)
