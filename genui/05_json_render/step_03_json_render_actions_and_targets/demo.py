"""Run the step end to end: stream one dashboard into the page, press every
button it contains, print what each press did, save demo.png, then render the
final spec a second time in the terminal with @json-render/ink.

    python demo.py
"""

import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

import httpx
import uvicorn

import server

STEP = Path(__file__).resolve().parent
PORT = 8057


def start_server():
    config = uvicorn.Config(server.app, host="127.0.0.1", port=PORT, log_level="warning")
    instance = uvicorn.Server(config)
    threading.Thread(target=instance.run, daemon=True).start()
    while not instance.started:
        time.sleep(0.05)
    return instance


def press_every_button(url):
    """Stream with ?auto=1, then click each Button once and wait for its log line."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 900})
        page.goto(url)
        page.wait_for_function("document.querySelector('#status').textContent.includes('complete')", timeout=120_000)
        print(f"page: {page.text_content('#status')}")
        buttons = page.locator("#surface button.button")
        count = buttons.count()
        print(f"{count} buttons, {page.locator('#surface .card').count()} cards visible")
        for i in range(count):
            label = buttons.nth(i).text_content()
            lines_before = len([l for l in page.text_content("#log").splitlines() if l])
            buttons.nth(i).click()
            page.wait_for_function(
                "n => document.querySelector('#log').textContent.split('\\n').filter(Boolean).length >= n"
                " && !document.querySelector('#log').textContent.trim().endsWith('-> server')",
                arg=lines_before + 1, timeout=120_000,
            )
            new_lines = [l for l in page.text_content("#log").splitlines() if l][lines_before:]
            print(f"press '{label}':")
            for line in new_lines:
                print(f"  {line}")
            print(f"  {page.locator('#surface .card').count()} cards visible")
        page.wait_for_timeout(300)
        page.screenshot(path=str(STEP / "demo.png"), full_page=True)
        browser.close()


def main():
    instance = start_server()
    press_every_button(f"http://127.0.0.1:{PORT}/?auto=1")
    with httpx.Client(base_url=f"http://127.0.0.1:{PORT}", timeout=30) as client:
        last = client.get("/last").json()
    for turn in last["turns"]:
        usage = turn["usage"] or {}
        print(f"turn {turn['label']}: {len(turn['patches'])} patches in {turn['seconds']} s, "
              f"{usage.get('completion_tokens')} completion tokens")
        if turn["label"] != "generate":
            for patch in turn["patches"][:4]:
                line = json.dumps(patch)
                print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
    print(f"catalog check: {last['problems'] or 'ok'}; skipped lines: {len(last['skipped'])}")
    (STEP / "demo_spec.json").write_text(json.dumps(last["spec"], indent=2), encoding="utf-8")
    print("saved demo_spec.json and demo.png")
    instance.should_exit = True

    node = shutil.which("node")
    if node is None:
        print("node is not on PATH; the terminal render was skipped")
        return
    print("the same spec in the terminal (node ink_render.mjs demo_spec.json):")
    result = subprocess.run([node, "ink_render.mjs", "demo_spec.json"], cwd=STEP, capture_output=True, text=True, encoding="utf-8")
    print(result.stdout.rstrip())


if __name__ == "__main__":
    main()
