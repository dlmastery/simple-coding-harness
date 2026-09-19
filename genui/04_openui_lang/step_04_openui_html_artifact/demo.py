"""Step 04 demo: two prompts against the live model, three screenshots.

    python demo.py

Prompt 1 asks for a dashboard: the model must answer with catalog components
only, no artifact (demo_catalog.png). Prompt 2 asks for something
interactive: the model answers with a Markdown intro and an HtmlArtifact;
the page is captured while the document is still streaming
(demo_streaming.png) and, after a headless click inside the mounted
iframe has proved that the document's script runs in the sandbox, with the
changed state (demo.png). For both prompts the demo prints the OpenUI Lang program,
the token usage from the API and the share of tokens the artifact took.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from artifact import count_tokens, find_artifacts
from nodetools import ensure_bundle, ensure_prompt
from server import LAST, make_server

HERE = Path(__file__).parent
CATALOG_PROMPT = "show me a dashboard for a lemonade stand"
ARTIFACT_PROMPT = "build me an interactive lemonade price calculator I can play with"


def report(prompt: str) -> None:
    program, usage = LAST["program"], LAST["usage"]
    print(f"prompt: {prompt}")
    print(program.strip())
    artifacts = find_artifacts(program)
    total = count_tokens(program)
    line = f"tokens (API): {usage.get('prompt_tokens', '?')} prompt, {usage.get('completion_tokens', '?')} completion"
    if artifacts:
        doc_tokens = sum(count_tokens(a.document) for a in artifacts)
        line += f"; artifact document {doc_tokens} of {total} program tokens ({100 * doc_tokens / total:.0f}%)"
    else:
        line += f"; no HtmlArtifact, {total} program tokens"
    print(line)


def run_prompt(page, text: str, streaming_shot: str | None = None) -> None:
    page.fill("#prompt", text)
    page.click("#generate")
    page.wait_for_selector('#status[data-streaming="true"]')
    if streaming_shot:
        page.wait_for_selector('.artifact[data-state="streaming"]', timeout=120_000)
        page.wait_for_function("document.querySelector('.artifact-raw').textContent.length > 400", timeout=120_000)
        page.screenshot(path=str(HERE / streaming_shot))
        print(f"mid-stream: {page.locator('.artifact-status').inner_text()} -> {streaming_shot}")
    page.wait_for_selector('#status[data-streaming="false"]', timeout=180_000)


def main() -> None:
    from playwright.sync_api import sync_playwright

    ensure_prompt()
    ensure_bundle()
    server = make_server()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(f"http://127.0.0.1:{server.server_port}/")

        print("== 1. a dashboard: catalog primitives only ==")
        run_prompt(page, CATALOG_PROMPT)
        page.screenshot(path=str(HERE / "demo_catalog.png"))
        report(CATALOG_PROMPT)
        print(f"artifacts on the page: {page.locator('.artifact').count()}, status: {page.locator('#status').inner_text()} -> demo_catalog.png")

        print("\n== 2. an interactive request: Markdown plus HtmlArtifact ==")
        run_prompt(page, ARTIFACT_PROMPT, streaming_shot="demo_streaming.png")
        page.wait_for_selector("iframe.artifact-frame")
        report(ARTIFACT_PROMPT)
        srcdoc = page.get_attribute("iframe.artifact-frame", "srcdoc")
        first = srcdoc.lstrip().lower().find("<meta http-equiv=\"content-security-policy\"")
        print(f"iframe: sandbox={page.get_attribute('iframe.artifact-frame', 'sandbox')!r}, "
              f"CSP meta before any element: {0 <= first <= len('<!doctype html>')}")

        # A click inside the sandbox: find the first button or range input in
        # the document, change it, and show that the document's text changed.
        frame = page.frame_locator("iframe.artifact-frame")
        before = frame.locator("body").inner_text()
        control = frame.locator("input[type=range], input[type=number], button").first
        tag = control.evaluate("el => el.tagName + (el.type ? ':' + el.type : '')")
        if tag.startswith("INPUT"):
            control.evaluate("el => { el.value = el.type === 'range' ? el.max : '9'; el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }")
        else:
            control.click()
        page.wait_for_timeout(300)
        after = frame.locator("body").inner_text()
        changed = [line for line in after.splitlines() if line not in before.splitlines()]
        print(f"moved {tag} inside the sandbox: document text changed: {before != after} {changed}")
        print(f"events accepted from the iframe: {page.locator('#events').inner_text()}")
        page.screenshot(path=str(HERE / "demo.png"))
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the prompt contains an em dash
    main()
