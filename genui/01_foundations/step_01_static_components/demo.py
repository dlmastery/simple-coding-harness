"""Step 01 demo: start the server, open the page headlessly, run the prompt, save demo.png.

Prints every SSE message the page received, in order. Needs an API key.
"""

import json
import socket
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

import server

HERE = Path(__file__).parent
PROMPT = "show me a dashboard for a lemonade stand"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def serve(port):
    """Run uvicorn on a daemon thread and return once it accepts connections, or fail loudly."""
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    instance = uvicorn.Server(config)
    thread = threading.Thread(target=instance.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not instance.started:
        if not thread.is_alive() or time.monotonic() > deadline:  # bind failure: the thread just ends
            raise RuntimeError(f"the server did not start on port {port}")
        time.sleep(0.05)
    return instance


def short(message, width=110):
    line = json.dumps(message)
    return line if len(line) <= width else line[: width - 3] + "..."


def main():
    port = free_port()
    serve(port)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 640})
        page.goto(f"http://127.0.0.1:{port}/")
        page.fill("#prompt", PROMPT)
        started = time.perf_counter()
        page.click("#run")
        page.wait_for_selector("body[data-state=done]", timeout=120_000)
        elapsed = time.perf_counter() - started
        events = page.evaluate("window.__events")
        page.screenshot(path=str(HERE / "demo.png"), full_page=True)
        browser.close()

    print(f"prompt: {PROMPT}")
    print(f"{len(events)} SSE messages in {elapsed:.1f}s:")
    for message in events:
        print("  " + short(message))
    print("saved demo.png")


if __name__ == "__main__":
    main()
