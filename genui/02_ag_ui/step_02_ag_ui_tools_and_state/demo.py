"""Record the demo: start the server, drive the page in headless Chromium
through two runs (build the dashboard; buy a cooler, which needs the page's
confirm_purchase tool), print a folded event log of each run, and save
demo.png. Needs a model key; the tests do not.

    python demo.py
"""

import json
import threading
import time
import urllib.request

import uvicorn
from playwright.sync_api import sync_playwright

from server import PORT, STEP, app

URL = f"http://127.0.0.1:{PORT}"
PROMPTS = ["Show me a dashboard for a lemonade stand.", "Buy a new cooler for $40."]


def start_server():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return server
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("server did not start")


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
            "TOOL_CALL_RESULT": lambda: e["content"],
            "STATE_DELTA": lambda: ", ".join(f"{op['op']} {op['path']}" for op in e["delta"]),
            "STATE_SNAPSHOT": lambda: f"{len(e['snapshot']['dashboard']['metrics'])} metrics, "
                                      f"{len(e['snapshot']['dashboard']['purchases'])} purchases",
        }.get(e["type"], lambda: "")()
        lines.append([e["type"], 0, detail])
    return [f"{t:<20} {d if not n else f'{n} events: {d[:60]}'}".rstrip() for t, n, d in lines]


def wait_finished(page):
    page.wait_for_function("document.getElementById('status').textContent !== 'running'", timeout=120000)
    events = [json.loads(line) for line in page.text_content("#wire").splitlines() if line.strip()]
    for line in folded(events):
        print("  " + line)


def drive():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL)
        for prompt in PROMPTS:
            print(f"> {prompt}")
            page.fill("#prompt", prompt)
            page.click("button[type=submit]")
            wait_finished(page)
        print("> [click Confirm]")
        page.click("button[data-answer=confirmed]")
        page.wait_for_function("document.getElementById('status').textContent === 'running'", timeout=10000)
        wait_finished(page)
        page.wait_for_timeout(200)
        page.screenshot(path=str(STEP / "demo.png"))
        metrics = page.locator(".metric-title").all_text_contents()
        purchases = page.locator(".purchases li").all_text_contents()
        print(f"dashboard: metrics={metrics} table={page.locator('table').count()} chart={page.locator('.chart').count()} purchases={purchases}")
        browser.close()
    print("saved demo.png")


if __name__ == "__main__":
    server = start_server()
    drive()
    server.should_exit = True
