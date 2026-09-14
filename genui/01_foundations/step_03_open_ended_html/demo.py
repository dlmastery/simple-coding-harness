"""Step 03 demo: the same prompt in static, flat and html mode, and the token bill.

Runs the three modes in the headless page, counts what the model wrote in
each with tiktoken (and prints the API's completion_tokens next to it),
clicks a button inside the sandboxed iframe to show the postMessage bridge,
and saves demo.png with the generated HTML mounted. Needs an API key.
"""

import json
import socket
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

import server
import tokens

HERE = Path(__file__).parent
PROMPT = "show me a dashboard for a lemonade stand"
WHAT = {"static": "tool calls (name + args)", "flat": "JSON element map", "html": "HTML document"}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def serve(port):
    """Run uvicorn on a daemon thread and return once it accepts connections."""
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    instance = uvicorn.Server(config)
    threading.Thread(target=instance.run, daemon=True).start()
    while not instance.started:
        time.sleep(0.05)
    return instance


def run_mode(page, mode):
    """One run in the page. Returns the done message and the seconds it took."""
    page.select_option("#mode", mode)
    page.fill("#prompt", PROMPT)
    started = time.perf_counter()
    page.click("#run")
    page.wait_for_selector("body[data-state=done]", timeout=180_000)
    return page.evaluate("window.__events")[-1], time.perf_counter() - started


def main():
    port = free_port()
    serve(port)
    done, seconds = {}, {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 760})
        page.goto(f"http://127.0.0.1:{port}/")
        for mode in ("static", "flat", "html"):
            done[mode], seconds[mode] = run_mode(page, mode)

        # The generated document is in the sandbox now. Photograph it, then click
        # its first button and read what came over the bridge.
        page.wait_for_timeout(500)
        page.screenshot(path=str(HERE / "demo.png"), full_page=False)
        buttons = page.frame_locator("#frame").locator("button")
        clicked = buttons.count()
        if clicked:
            buttons.first.click()
            page.wait_for_timeout(300)
        inbox = page.evaluate("window.__inbox")
        browser.close()

    print(f"prompt: {PROMPT}")
    rows = [(mode, WHAT[mode], done[mode]["raw"], (done[mode].get("usage") or {}).get("completion_tokens")) for mode in done]
    for line in tokens.table(rows):
        print(line)
    if tokens.encoding() is None:
        print("tiktoken (or its vocabulary) unavailable: the 'vs flat' column uses the API's completion_tokens")
    print("time to the last byte: " + ", ".join(f"{mode} {seconds[mode]:.1f}s" for mode in done))
    html = done["html"]["html"]
    print(f"html: {len(html)} chars, {html.count('<')} tags, {clicked} button(s) in the sandbox")
    print(f"clicked the first button; the host received: {json.dumps(inbox) if inbox else 'nothing'}")
    print("saved demo.png")


if __name__ == "__main__":
    main()
