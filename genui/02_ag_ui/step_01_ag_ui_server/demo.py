"""Record the demo: start the server, post one RunAgentInput and print the
wire format, then open the page in headless Chromium, run the same prompt
and save demo.png. Needs a model key; the tests do not.

    python demo.py
"""

import json
import threading
import time
import urllib.request
from uuid import uuid4

import httpx
import uvicorn
from playwright.sync_api import sync_playwright

from server import PORT, STEP, app
from sse import parse_sse

URL = f"http://127.0.0.1:{PORT}"
PROMPT = "In one short sentence, what makes good lemonade?"


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


def show_wire():
    """The exact bytes on the wire, one event per line, long runs of deltas folded."""
    body = {
        "threadId": str(uuid4()), "runId": str(uuid4()),
        "messages": [{"id": str(uuid4()), "role": "user", "content": PROMPT}],
        "tools": [], "context": [], "forwardedProps": {}, "state": {},
    }
    with httpx.stream("POST", f"{URL}/agent", json=body, headers={"accept": "text/event-stream"}, timeout=60) as r:
        print(f"POST /agent -> {r.status_code} {r.headers['content-type']}")
        raw = "".join(r.iter_text())
    lines = [line for line in raw.splitlines() if line.strip()]
    content = [i for i, line in enumerate(lines) if '"TEXT_MESSAGE_CONTENT"' in line]
    fold = len(content) > 5  # a short reply is printed whole
    for i, line in enumerate(lines):
        if fold and content[3] <= i <= content[-2]:
            if i == content[3]:
                print(f"... {len(content) - 4} more TEXT_MESSAGE_CONTENT events ...")
            continue
        print(line)
    text = "".join(e["delta"] for e in parse_sse(raw) if e["type"] == "TEXT_MESSAGE_CONTENT")
    print(f"assembled text: {text}")


def screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 600})
        page.goto(URL)
        page.fill("#prompt", PROMPT)
        page.click("button[type=submit]")
        page.wait_for_function("document.getElementById('status').textContent !== 'running'", timeout=60000)
        page.wait_for_timeout(200)
        page.screenshot(path=str(STEP / "demo.png"))
        print(f"page status: {page.text_content('#status')}; rendered: {page.text_content('.assistant')}")
        browser.close()
    print("saved demo.png")


if __name__ == "__main__":
    server = start_server()
    show_wire()
    screenshot()
    server.should_exit = True
