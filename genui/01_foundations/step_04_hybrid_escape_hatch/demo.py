"""Step 04 demo: a catalog layout with one GeneratedView, then a click that closes the loop.

Runs the hybrid prompt in the headless page, saves demo.png, clicks the
first catalog Button, waits for the model's second turn, prints what the
event was and which elements changed, and saves demo_after_action.png.
Needs an API key.
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
PROMPT = "show me a dashboard for a lemonade stand, with a gauge for today's sales goal and a button to restock lemons"


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


def wait_done(page):
    page.wait_for_selector("body[data-state=done]", timeout=180_000)
    return [e for e in page.evaluate("window.__events") if e.get("done")][-1]


def describe(spec):
    """One line per element: id, type, and the prop that identifies it."""
    lines = []
    for element_id, element in spec["elements"].items():
        props = element["props"]
        label = props.get("title") or props.get("label") or props.get("text") or ""
        if element["type"] == "GeneratedView":
            label = f"{len(props['html'])} chars of html"
        if element["type"] == "Button":
            label = f"{props['label']!r} -> action {props['action']!r}"
        lines.append(f"  {element_id:<14} {element['type']:<14} {label}")
    return lines


def changed(before, after):
    """Element ids whose node differs between the two layouts, plus added and removed ids."""
    a, b = before["elements"], after["elements"]
    same = [k for k in a if k in b and a[k] == b[k]]
    diff = [k for k in a if k in b and a[k] != b[k]]
    return diff, [k for k in b if k not in a], [k for k in a if k not in b], len(same)


def main():
    port = free_port()
    serve(port)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 820})
        page.goto(f"http://127.0.0.1:{port}/")
        page.select_option("#mode", "flat")
        page.fill("#prompt", PROMPT)
        page.click("#run")
        first = wait_done(page)
        page.wait_for_timeout(400)
        page.screenshot(path=str(HERE / "demo.png"), full_page=False)

        buttons = page.locator("#dashboard button.action")
        clicked = buttons.first.text_content() if buttons.count() else None
        second = None
        if clicked:
            buttons.first.click()
            page.wait_for_selector("body[data-state=running]", timeout=10_000)
            second = wait_done(page)
            page.wait_for_timeout(400)
            page.screenshot(path=str(HERE / "demo_after_action.png"), full_page=False)
        inbox = page.evaluate("window.__inbox")
        browser.close()

    print(f"prompt: {PROMPT}")
    print(f"turn 1: session {first['session']}, valid={first['valid']}, {len(first['spec']['elements'])} elements:")
    print("\n".join(describe(first["spec"])))
    if not clicked:
        print("the model put no Button in the layout, so there was nothing to click")
        return
    print(f"clicked {clicked!r}; the page sent: {json.dumps(inbox[0])}")
    diff, added, removed, same = changed(first["spec"], second["spec"])
    print(f"turn 2: valid={second['valid']}, {same} elements unchanged, changed {diff}, added {added}, removed {removed}")
    for element_id in diff[:4]:
        print(f"  {element_id}: {json.dumps(first['spec']['elements'][element_id]['props'])[:70]}")
        print(f"  {'':>{len(element_id)}}  -> {json.dumps(second['spec']['elements'][element_id]['props'])[:70]}")
    print("saved demo.png, demo_after_action.png")


if __name__ == "__main__":
    main()
