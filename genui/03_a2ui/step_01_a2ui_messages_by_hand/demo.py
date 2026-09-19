"""Step 01 demo: validate the spec's stream, replay it through the Python
surface state, then through the browser renderer; save demo.png.

    python demo.py
"""

import json
import threading
import time
from pathlib import Path

import uvicorn

import a2ui
import server

HERE = Path(__file__).parent


def validate_and_repair(messages):
    print(f"contact_form.jsonl: {len(messages)} messages from the spec's Example Stream")
    for index, message in enumerate(messages, 1):
        kind = a2ui.message_type(message)
        problem = a2ui.validate(message)
        print(f"  {index} {kind:<17} {'valid' if problem is None else 'INVALID at ' + problem['path'] + ': ' + problem['message']}")
        if problem:
            fixed = a2ui.repair_checks(message)
            print(f"    repair_checks: {fixed} rules rewritten to {{condition, message}} -> {'valid' if a2ui.validate(message) is None else 'still invalid'}")


def replay_in_python(messages):
    store = a2ui.SurfaceStore()
    for message in messages:
        surface = store.apply(message)
        kind = a2ui.message_type(message)
        if kind == "updateComponents":
            print(f"python  after {kind}: root={surface.tree()['component']}, {len(surface.components)} components, missing refs={surface.missing_ids()}")
        elif kind == "updateDataModel":
            print(f"python  after {kind}: /contact/firstName = {a2ui.pointer_get(surface.data, '/contact/firstName')!r}, /contact/subscribe = {a2ui.pointer_get(surface.data, '/contact/subscribe')!r}")
        else:
            print(f"python  after {kind}: surfaces = {list(store.surfaces)}")


def replay_in_browser():
    from playwright.sync_api import sync_playwright

    server.GAP = 0.3
    config = uvicorn.Config(server.app, host="127.0.0.1", port=server.PORT, log_level="warning")
    web = uvicorn.Server(config)
    thread = threading.Thread(target=web.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not web.started:
        if not thread.is_alive() or time.monotonic() > deadline:  # port in use: the thread just ends
            raise RuntimeError(f"the server did not start on port {server.PORT} (in use?)")
        time.sleep(0.05)
    url = f"http://127.0.0.1:{server.PORT}/?all=1"
    print(f"browser {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 720, "height": 760})
        page.goto(url)
        page.wait_for_function("document.querySelector('input[data-field=first_name_field]')?.value === 'John'")
        print(f"browser after updateDataModel: {page.locator('input').count()} inputs, first name = {page.input_value('input[data-field=first_name_field]')!r}, subscribe checked = {page.is_checked('.a2ui-check input')}")
        page.fill("input[data-field=first_name_field]", "Jane")
        page.click("button.a2ui-primary")
        page.screenshot(path=str(HERE / "demo.png"))
        log = page.evaluate("window.a2uiLog")
        action = next(line for line in log if line.startswith("action"))
        print(f"browser click Send Message -> {action[:150]}")
        page.wait_for_function("document.querySelectorAll('.a2ui-surface').length === 0")
        print(f"browser after deleteSurface: surfaces on page = {page.locator('.a2ui-surface').count()}")
        print("browser log:")
        for line in log:
            if not line.startswith("data model"):
                print(f"  {line[:110]}")
        browser.close()
    web.should_exit = True
    print("screenshot: demo.png")


if __name__ == "__main__":
    messages = a2ui.read_stream(HERE / "contact_form.jsonl")
    validate_and_repair(messages)
    replay_in_python(messages)
    replay_in_browser()
