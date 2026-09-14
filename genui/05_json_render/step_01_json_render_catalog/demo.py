"""Run the step end to end: start the server, ask for one complete spec, print
it as a tree, open the page on it headlessly and save demo.png.

    python demo.py
"""

import json
import threading
import time
from pathlib import Path

import httpx
import uvicorn

import server
from spec import walk

STEP = Path(__file__).resolve().parent
PORT = 8055
PROMPT = "Show me a dashboard for a lemonade stand: this week's sales, the best days, and what sold."


def start_server():
    config = uvicorn.Config(server.app, host="127.0.0.1", port=PORT, log_level="warning")
    instance = uvicorn.Server(config)
    threading.Thread(target=instance.run, daemon=True).start()
    while not instance.started:
        time.sleep(0.05)
    return instance


def screenshot(url, path):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 720})
        page.goto(url)
        page.wait_for_selector("#surface .card", timeout=60_000)
        page.wait_for_timeout(300)
        page.screenshot(path=str(path), full_page=True)
        browser.close()


def main():
    instance = start_server()
    print(f"prompt: {PROMPT}")
    with httpx.Client(base_url=f"http://127.0.0.1:{PORT}", timeout=120) as client:
        response = client.post("/generate", json={"prompt": PROMPT})
        response.raise_for_status()
        body = response.json()
    spec, usage = body["spec"], body["usage"]
    print(f"complete spec after {body['seconds']} s: {len(spec['elements'])} elements, "
          f"{usage['prompt_tokens']} prompt tokens, {usage['completion_tokens']} completion tokens")
    print(f"first paint: {body['seconds']} s (nothing renders before the whole object arrives)")
    for depth, element_id, element in walk(spec):
        props = {k: v for k, v in element["props"].items() if v is not None}
        summary = json.dumps(props)
        print(f"{'  ' * depth}{element['type']} #{element_id}  {summary[:70]}{'...' if len(summary) > 70 else ''}")
    if spec.get("state"):
        print(f"state: {json.dumps(spec['state'])[:100]}")
    (STEP / "demo_spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    screenshot(f"http://127.0.0.1:{PORT}/?last=1", STEP / "demo.png")
    print("saved demo_spec.json and demo.png")
    instance.should_exit = True


if __name__ == "__main__":
    main()
