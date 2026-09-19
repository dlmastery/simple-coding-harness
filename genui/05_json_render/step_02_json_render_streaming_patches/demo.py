"""Run the step end to end: start the server, open the page so that it streams
one dashboard, take a screenshot at the first paint and one at the end, then
print what the server saw: the timings, the patches and the token usage.

    python demo.py
"""

import json
import threading
import time
from pathlib import Path

import httpx
import uvicorn

import server

STEP = Path(__file__).resolve().parent
PORT = 8056
STEP_1_FIRST_PAINT = 5.8  # the complete-spec number recorded in step 1's README


def start_server():
    config = uvicorn.Config(server.app, host="127.0.0.1", port=PORT, log_level="warning")
    instance = uvicorn.Server(config)
    thread = threading.Thread(target=instance.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not instance.started:  # uvicorn exits its thread when the port is taken: never spin on a dead thread
        if not thread.is_alive() or time.time() > deadline:
            raise RuntimeError(f"the server did not start on 127.0.0.1:{PORT}; is the port free?")
        time.sleep(0.05)
    return instance


def stream_in_browser(url):
    """Open the page with ?auto=1, screenshot the first paint and the end."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 720})
        page.goto(url)
        page.wait_for_selector("#surface .card", timeout=60_000)
        page.screenshot(path=str(STEP / "demo_first_paint.png"), full_page=True)
        page.wait_for_function("document.querySelector('#status').textContent.includes('complete')", timeout=120_000)
        page.wait_for_timeout(300)
        page.screenshot(path=str(STEP / "demo.png"), full_page=True)
        status = page.text_content("#status")
        browser.close()
    return status


def main():
    instance = start_server()
    status = stream_in_browser(f"http://127.0.0.1:{PORT}/?auto=1")
    print(f"page: {status}")
    with httpx.Client(base_url=f"http://127.0.0.1:{PORT}", timeout=30) as client:
        last = client.get("/last").json()
    t = last["timings"]
    print(f"server: first chunk {t['first_chunk']} s, first paint possible {t['first_paint']} s, complete {t['complete']} s")
    print(f"step 1 for comparison: first paint {STEP_1_FIRST_PAINT} s (the complete spec, nothing earlier)")
    usage = last["usage"] or {}
    print(f"{len(last['patches'])} patches, {len(last['spec']['elements'])} elements, "
          f"{usage.get('prompt_tokens')} prompt tokens, {usage.get('completion_tokens')} completion tokens")
    for patch in last["patches"][:6]:
        line = json.dumps(patch)
        print(f"  {line[:96]}{'...' if len(line) > 96 else ''}")
    if len(last["patches"]) > 6:
        print(f"  ... {len(last['patches']) - 6} more")
    if last["skipped"]:
        print(f"skipped lines: {last['skipped']}")
    print(f"catalog check: {last['problems'] or 'ok'}")
    (STEP / "demo_spec.json").write_text(json.dumps(last["spec"], indent=2), encoding="utf-8")
    print("saved demo_spec.json, demo_first_paint.png and demo.png")
    instance.should_exit = True


if __name__ == "__main__":
    main()
