"""Step 02 demo: the generated prompt, a live model call, the rendered page.

    python demo.py

Part 1 prints the component signatures from the generated system prompt.
Part 2 builds the bundle, starts the server, opens the page in headless
Chromium, runs the lemonade-stand prompt against the real model, prints the
OpenUI Lang the model streamed, and saves demo.png.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from nodetools import ensure_bundle, ensure_prompt
from server import LAST, make_server

HERE = Path(__file__).parent
PROMPT = "show me a dashboard for a lemonade stand"


def part_1_prompt():
    print("== 1. the system prompt library.prompt() generates (signatures section) ==")
    text = ensure_prompt()
    section = text.split("## Component Signatures")[1].split("## Hoisting")[0]
    print("\n".join(line for line in section.strip().splitlines() if "(" in line))
    print(f"({len(text.splitlines())} lines, {len(text)} characters in prompt.txt)")


def part_2_browser():
    print("\n== 2. the model streams OpenUI Lang into <Renderer> ==")
    from playwright.sync_api import sync_playwright

    ensure_bundle()
    server = make_server()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(f"http://127.0.0.1:{server.server_port}/")
        page.fill("#prompt", PROMPT)
        page.click("#generate")
        page.wait_for_selector('#status[data-streaming="true"]')
        page.wait_for_selector('#status[data-streaming="false"]', timeout=120_000)
        page.screenshot(path=str(HERE / "demo.png"))
        print(f"prompt: {PROMPT}")
        print(LAST["program"].strip())
        print("status:", page.locator("#status").inner_text(), "-> demo.png")
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the prompt contains an em dash
    part_1_prompt()
    part_2_browser()
