"""Step 03 demo: a live model call carried as AG-UI events into the official
Lit renderer, typing, a click, the action run, and the raw wire of that run.

    python demo.py            (needs API_KEY; see llm.py; runs `npm run build` if needed)
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

HERE = Path(__file__).parent
PROMPT = "Make a contact form with first name, email, a newsletter checkbox and a send button."


def bundle_is_stale():
    """No bundle yet, or src/ changed since it was built."""
    bundle = HERE / "static" / "bundle.js"
    return not bundle.exists() or any(f.stat().st_mtime > bundle.stat().st_mtime for f in (HERE / "src").glob("*.mjs"))


def build_bundle():
    if bundle_is_stale():
        subprocess.run([shutil.which("npm"), "run", "build"], cwd=HERE, check=True)


def main():
    from playwright.sync_api import sync_playwright

    build_bundle()
    config = uvicorn.Config(server.app, host="127.0.0.1", port=server.PORT, log_level="warning")
    web = uvicorn.Server(config)
    thread = threading.Thread(target=web.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not web.started:
        if not thread.is_alive() or time.monotonic() > deadline:  # port in use: the thread just ends
            raise RuntimeError(f"the server did not start on port {server.PORT} (in use?)")
        time.sleep(0.05)
    url = f"http://127.0.0.1:{server.PORT}/"
    print(f"browser {url}  (renderer: @a2ui/lit 0.11.0 over @a2ui/web_core; transport: AG-UI CUSTOM events named a2ui)")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 720, "height": 720})
        page.goto(url)
        page.fill("input[name=prompt]", PROMPT)
        page.click("#prompt-form button")
        page.wait_for_function("window.a2uiDone === true", timeout=120_000)
        log = page.evaluate("window.a2uiLog")
        if not any("RUN_FINISHED" in line for line in log):  # RUN_ERROR, or the run failed before any event
            raise SystemExit("the run did not finish:\n  " + "\n  ".join(log[-3:]))
        updates = [line for line in log if "updateComponents" in line]
        for line in log:
            if "updateComponents" in line and line not in updates[:2] + updates[-1:]:
                continue
            if line == updates[-1] and len(updates) > 3:
                print(f"  ... {len(updates) - 3} more CUSTOM a2ui updateComponents ...")
            print(f"  {line[:150]}")

        # the Lit TextField writes into web_core's DataModel as the user types
        inputs = page.locator("#app input[type=text], #app input:not([type])")
        inputs.nth(0).fill("Ada")
        if inputs.count() > 1:
            inputs.nth(1).fill("ada@example.com")
        checkbox = page.locator("#app input[type=checkbox]")
        if checkbox.count():
            checkbox.nth(0).check()
        print(f"typed: data model = {json.dumps(page.evaluate('window.dataModel(\"main\")'))[:150]}")

        # the action: a second AG-UI run with forwardedProps.a2ui. The renderer
        # dispatches the action after the click returns, so the flag is lowered first.
        page.evaluate("window.a2uiDone = false")
        page.click("#app button")
        page.wait_for_function("window.a2uiDone === true")
        status = page.locator("a2ui-basic-text", has_text="Server got")  # Playwright pierces the shadow roots
        status.wait_for()
        action_lines = [line for line in page.evaluate("window.a2uiLog") if "action" in line or "RUN_FINISHED" in line]
        print(f"click -> {action_lines[-2][:130]}")
        print(f"        {action_lines[-1][:130]}")
        print(f"the status Text now reads: {status.inner_text().strip()[:150]}")
        page.screenshot(path=str(HERE / "demo.png"))
        browser.close()

    # the wire of an action run, as AG-UI frames
    action = {"name": "submit", "surfaceId": "main", "sourceComponentId": "send", "timestamp": "2026-09-14T00:00:00Z",
              "context": {"email": "ada@example.com"}}
    body = {"threadId": "t1", "runId": "r2", "messages": [], "tools": [], "context": [],
            "forwardedProps": {"a2ui": {"action": action, "a2uiClientDataModel": {"version": "v0.9.1", "surfaces": {"main": {"form": {"email": "ada@example.com"}}}}}}}
    print("wire of an action run (POST /agent), one AG-UI event per data: line:")
    with httpx.Client(base_url=url) as client:
        for line in client.post("/agent", json=body).text.splitlines():
            if line.strip():
                print(f"  {line[:140]}")
    web.should_exit = True
    print("screenshot: demo.png")


if __name__ == "__main__":
    main()
