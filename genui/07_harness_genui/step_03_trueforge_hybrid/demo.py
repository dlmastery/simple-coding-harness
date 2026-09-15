"""Generative UI step 03 - two prompts on TrueForge, catalog first, then the hybrid.

    python demo.py               # live: two turns on http://localhost:8790, then the page
    python demo.py --offline     # the recorded replies in sample_*.md, no server needed

Prompt 1 asks for a report: the agent must answer with catalog components
only (demo_catalog.png). Prompt 2 asks for something interactive: the agent
answers with a TextContent intro and one HtmlArtifact; the page is captured
while the document is still streaming (demo_streaming.png) and, after a
headless keystroke inside the sandboxed iframe has proved that the
document's script runs under the CSP, with the changed state (demo.png).
For both prompts the demo prints the program, the token counts from
turn.done, and the share of the reply the artifact document took.
"""

import argparse
import sys
from pathlib import Path

import artifact
import openui_parse
import server
from client import genui

HERE = Path(__file__).resolve().parent
PROMPTS = [
    ("catalog", "Show a lemonade stand report with a table of the top three flavours and a status tag"),
    ("artifact", "Build me an interactive lemonade price calculator I can play with, with a short intro"),
]


def capture(name, prompt, offline, attempts=3):
    """The raw reply: streamed from TrueForge, or read back from the recording.

    Live, a reply is accepted when it has an HtmlArtifact exactly for the
    artifact prompt and none for the catalog prompt; otherwise a new session
    is asked again, up to `attempts` times, and every attempt is printed.
    """
    sample = HERE / f"sample_{name}.md"
    if offline:
        return sample.read_text(encoding="utf-8"), {}
    for attempt in range(1, attempts + 1):
        print(f"> {prompt}\n")
        _, reply, metrics = genui.ask(prompt)
        print()
        program = genui.extract_program(reply) or ""
        wanted, got = name == "artifact", len(artifact.find_artifacts(program))
        if got == int(wanted):
            break
        print(f"attempt {attempt}: {got} HtmlArtifact statement(s), expected {int(wanted)}; asking a new session\n")
    sample.write_text(reply, encoding="utf-8")
    return reply, metrics


def report(program, reply, metrics):
    """The parsed program as a tree, the token counts, the artifact's share."""
    parsed = openui_parse.parse(program)
    print(f"--- program: {len(program.splitlines())} lines, {len(parsed.statements)} statements ---")
    print("\n".join(line if len(line) <= 160 else line[:157] + "..." for line in openui_parse.outline(parsed.tree())))
    if parsed.errors:
        print("parse errors:", *parsed.errors, sep="\n  ")
    if parsed.pending():
        print("unresolved references:", ", ".join(parsed.pending()))
    if metrics:
        calls = metrics.get("calls", [])
        loaded = " and ".join(metrics.get("tools", [])) or "no tool"
        print(f"[{metrics.get('total_input_tokens', 0):,} input, {metrics.get('total_output_tokens', 0):,} output tokens over "
              f"{len(calls)} model calls; {loaded} called]")
    artifacts = artifact.find_artifacts(parsed)
    reply_tokens = artifact.count_tokens(reply)
    if artifacts:
        for a in artifacts:
            doc_tokens = artifact.count_tokens(a.document)
            problems = artifact.check_document(a.document)
            print(f"artifact `{a.name}` \"{a.title}\": {len(a.document):,} characters, {doc_tokens:,} of {reply_tokens:,} reply tokens "
                  f"({100 * doc_tokens / reply_tokens:.0f}%), checks: {problems or 'none'}")
    else:
        print(f"no HtmlArtifact; {reply_tokens:,} reply tokens")
    return parsed, artifacts


def screenshot_catalog(url):
    """demo_catalog.png once the program is complete; no artifact must be on the page."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 400})
        page.goto(url)
        page.wait_for_selector("#surface[data-done]", timeout=15_000)
        count = page.locator(".artifact").count()
        page.screenshot(path=str(HERE / "demo_catalog.png"), full_page=True)
        print(f"artifacts on the page: {count}, status: {page.locator('#status').inner_text()} -> demo_catalog.png")
        browser.close()


def screenshot_artifact(url):
    """demo_streaming.png while the document streams, then a keystroke in the iframe and demo.png."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 560})
        page.goto(url)
        try:
            page.wait_for_selector('.artifact[data-state="streaming"]', timeout=10_000)
            page.wait_for_function("document.querySelector('.artifact-raw').textContent.length > 300", timeout=10_000)
            page.screenshot(path=str(HERE / "demo_streaming.png"))
            print(f"mid-stream: {page.locator('.artifact-status').inner_text()} -> demo_streaming.png")
        except Exception:
            print("the streaming state was not visible; demo_streaming.png not taken")
        page.wait_for_selector("#surface[data-done]", timeout=20_000)
        page.wait_for_selector("iframe.artifact-frame", timeout=5_000)
        srcdoc = page.get_attribute("iframe.artifact-frame", "srcdoc")
        head = srcdoc.lower().find("<head>")
        first = srcdoc[head + 6:].startswith(artifact.META) if head >= 0 else srcdoc.startswith(artifact.META)
        print(f"iframe: sandbox={page.get_attribute('iframe.artifact-frame', 'sandbox')!r}, "
              f"referrerpolicy={page.get_attribute('iframe.artifact-frame', 'referrerpolicy')!r}, CSP meta first in <head>: {first}")

        # Keystrokes inside the sandbox: every number field gets a 9 (a slider
        # its maximum); if the text did not change, the first button is
        # clicked too, for documents that compute on click. The document's
        # own script must update its text under the CSP.
        frame = page.frame_locator("iframe.artifact-frame")
        body = frame.locator("body")
        before = body.inner_text()
        fields = frame.locator("input[type=number], input[type=range], input[type=text]")
        acted = []
        for i in range(fields.count()):
            field = fields.nth(i)
            if field.evaluate("el => el.type") == "range":
                field.evaluate("el => { el.value = el.max; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            else:
                field.fill("9")
        if fields.count():
            acted.append(f"set {fields.count()} input field(s)")
        page.wait_for_timeout(300)
        button = frame.locator("button").first
        if body.inner_text() == before and button.count():
            button.click()
            acted.append("clicked " + button.inner_text().strip())
            page.wait_for_timeout(300)
        after = body.inner_text()
        changed = [line for line in after.splitlines() if line not in before.splitlines()]
        print(f"inside the sandbox: {', '.join(acted) or 'no control found'}; document text changed: {before != after} {changed}")
        page.screenshot(path=str(HERE / "demo.png"), full_page=True)
        print(f"status: {page.locator('#status').inner_text()} -> demo.png")
        browser.close()


def main(argv=None):
    cli = argparse.ArgumentParser()
    cli.add_argument("--offline", action="store_true", help="use sample_*.md instead of the server")
    cli.add_argument("--no-screenshot", action="store_true")
    args = cli.parse_args(argv)
    if not args.offline:
        print(f"TrueForge at {genui.BASE_URL}, model {genui.MODEL}")

    for name, prompt in PROMPTS:
        print(f"\n== {name}: {'catalog components only' if name == 'catalog' else 'catalog components plus one HtmlArtifact'} ==")
        reply, metrics = capture(name, prompt, args.offline)
        if args.offline:
            print(reply)
        program = genui.extract_program(reply)
        if program is None:
            print("no ```openui block in the reply; nothing to render")
            return 1
        parsed, artifacts = report(program, reply, metrics)
        if (name == "artifact") != bool(artifacts):
            print(f"unexpected: {len(artifacts)} artifact(s) for the {name} prompt; no screenshot")
            continue
        httpd, url = server.serve(program, reply, port=0)
        print(f"page: {url}")
        if not args.no_screenshot:
            (screenshot_artifact if name == "artifact" else screenshot_catalog)(url)
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
