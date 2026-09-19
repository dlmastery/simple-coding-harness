"""Generative UI step 02 - TrueForge writes the UI, this page draws it.

    python demo.py               # live: one turn on http://localhost:8790, then the page
    python demo.py --offline     # the recorded reply in sample_reply.md, no server needed
    python demo.py --prompt ...  # a different request

Prints the raw reply as it streams, the extracted OpenUI Lang program as a
tree, then streams the program line by line to web/ and saves two
screenshots: demo_stream.png while references are still pending, demo.png
when the program is complete.
"""

import argparse
import sys
from pathlib import Path

import openui_parse
import server
from client import genui

HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample_reply.md"
PROMPT = (
    "Show a lemonade stand report: a table of the top three flavours with cups and price, "
    "a line chart of weekly revenue for four weeks, two KPI numbers, a status tag, and a closing sentence."
)


def capture(prompt, offline):
    """The raw reply: streamed from TrueForge, or read back from the recording."""
    if offline:
        return SAMPLE.read_text(encoding="utf-8"), {}
    print(f"TrueForge at {genui.BASE_URL}, model {genui.MODEL}")
    print(f"> {prompt}\n")
    _, reply, metrics = genui.ask(prompt)
    print()
    program = genui.extract_program(reply)
    if program is not None and not openui_parse.parse(program).errors:
        SAMPLE.write_text(reply, encoding="utf-8")  # the recording the tests replay: only a clean reply replaces it
    else:
        print("(the reply did not parse cleanly; sample_reply.md was left as it was)")
    return reply, metrics


def screenshots(url):
    """demo_stream.png while the page still waits for a line, demo.png once it has them all."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 720})
        page.goto(url)
        try:
            page.wait_for_selector("#surface .pending", timeout=3_000)
            page.screenshot(path=str(HERE / "demo_stream.png"))
            print("saved demo_stream.png (forward references still pending)")
        except Exception:
            print("no pending state was visible; demo_stream.png not taken")
        page.wait_for_selector("#surface[data-done]", timeout=15_000)
        page.screenshot(path=str(HERE / "demo.png"), full_page=True)
        print("saved demo.png (program complete)")
        browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="use sample_reply.md instead of the server")
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--no-screenshot", action="store_true")
    cli = parser.parse_args(argv)

    reply, metrics = capture(cli.prompt, cli.offline)
    if cli.offline:
        print("--- raw reply (sample_reply.md) ---")
        print(reply)
    if metrics:
        print(f"[{metrics.get('total_input_tokens', 0):,} input, {metrics.get('total_output_tokens', 0):,} output tokens]")

    program = genui.extract_program(reply)
    if program is None:
        print("no ```openui block in the reply; nothing to render")
        return 1
    parsed = openui_parse.parse(program)
    print(f"\n--- extracted program: {len(program.splitlines())} lines, {len(parsed.statements)} statements ---")
    print("\n".join(openui_parse.outline(parsed.tree())))
    if parsed.errors:
        print("parse errors:", *parsed.errors, sep="\n  ")
    if parsed.pending():
        print("unresolved references:", ", ".join(parsed.pending()))

    _, url = server.serve(program, reply, port=0)
    print(f"\npage: {url}")
    if not cli.no_screenshot:
        screenshots(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
