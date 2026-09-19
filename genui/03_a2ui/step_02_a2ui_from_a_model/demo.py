"""Step 02 demo: a live model call, the messages as they stream into the page,
typing into the generated form, a click, the server's answer; demo.png.

    python demo.py            (needs API_KEY; see llm.py)
"""

import json
import threading
import time
from pathlib import Path

import uvicorn

import llm
import prompt
import server

HERE = Path(__file__).parent
PROMPT = "Make a contact form with first name, email, a newsletter checkbox and a send button."


def main():
    from playwright.sync_api import sync_playwright

    print(f"system prompt: {len(prompt.system_prompt())} chars (role + SDK workflow rules + Basic Catalog schema); model {llm.MODEL}")
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
    print(f"browser {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 720, "height": 720})
        page.goto(url)
        page.fill("input[name=prompt]", PROMPT)
        page.click("#prompt-form button")
        page.wait_for_function("window.a2uiDone === true", timeout=120_000)
        log = page.evaluate("window.a2uiLog")
        updates = [line for line in log if "updateComponents" in line]
        for line in log:
            if "updateComponents" in line and line not in updates[:3] + updates[-1:]:
                continue
            if line == updates[-1] and len(updates) > 4:
                print(f"  ... {len(updates) - 4} more progressive updateComponents ...")
            print(f"  {line[:150]}")

        # two-way binding: type, then read the local data model
        fields = page.locator("input[data-field]")
        names = [fields.nth(i).get_attribute("data-field") for i in range(fields.count())]
        fields.nth(0).fill("Ada")
        if fields.count() > 1:
            fields.nth(1).fill("ada@example.com")
        checks = page.locator(".a2ui-check input")
        if checks.count():
            checks.nth(0).check()
        data = page.evaluate("[...window.store.surfaces.values()][0].data")
        print(f"typed into {names}: data model = {json.dumps(data)[:150]}")

        # the action round trip
        page.click(".a2ui-button")
        page.wait_for_function("[...document.querySelectorAll('.a2ui-text')].some(t => t.textContent.startsWith('Server got'))")
        status = page.evaluate("[...document.querySelectorAll('.a2ui-text')].find(t => t.textContent.startsWith('Server got')).textContent")
        print(f"click -> {[line for line in page.evaluate('window.a2uiLog') if 'action' in line][0][:120]}")
        print(f"the status Text now reads: {status[:140]}")
        page.screenshot(path=str(HERE / "demo.png"))
        browser.close()
    web.should_exit = True
    print("screenshot: demo.png")


if __name__ == "__main__":
    main()
