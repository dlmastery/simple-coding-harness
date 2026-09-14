"""Step 01 demo: parse program.oui, stream it, screenshot the skeleton and the result.

    python demo.py

Part 1 parses the whole program in Python and prints the tree.
Part 2 streams it line by line through StreamingParser and prints what is
resolved after each line.
Part 3 starts server.py, opens the page in headless Chromium, pushes the
same lines into the page's parser, and saves demo_partial.png after three
lines (forward references still skeletons) and demo.png at the end.
"""

from __future__ import annotations

import threading
from pathlib import Path

from openui_parse import StreamingParser, load_catalog, parse
from server import make_server, program_lines

HERE = Path(__file__).parent
CATALOG = load_catalog(HERE / "catalog.json")
SKELETON_AFTER = 3  # lines pushed before the first screenshot


def outline(node, depth=0):
    """One line per element: indentation, component, statement name."""
    pad = "  " * depth
    if node.get("type") == "placeholder":
        return [f"{pad}? {node['name']}  (placeholder)"]
    lines = [f"{pad}{node['typeName']}  <- {node.get('statementId', '')}"]
    for value in node["props"].values():
        for child in value if isinstance(value, list) else [value]:
            if isinstance(child, dict) and child.get("type") in ("element", "placeholder"):
                lines += outline(child, depth + 1)
    return lines


def part_1_parse():
    print("== 1. parse the whole program ==")
    result = parse((HERE / "program.oui").read_text(encoding="utf-8"), CATALOG)
    print("\n".join(outline(result.root)))
    print(f"unresolved: {result.unresolved}  errors: {result.errors}")


def part_2_stream():
    print("\n== 2. stream it line by line ==")
    parser = StreamingParser(CATALOG)
    for number, line in enumerate(program_lines(), 1):
        result = parser.push(line + "\n")
        print(f"line {number:>2}: {line[:34]:<34} unresolved={result.unresolved}")


def part_3_browser():
    print("\n== 3. the page, headless ==")
    from playwright.sync_api import sync_playwright

    server = make_server()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/"
    lines = program_lines()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(url)
        page.wait_for_function("window.openui !== undefined")
        page.evaluate("window.openui.reset()")
        for line in lines[:SKELETON_AFTER]:
            page.evaluate("line => window.openui.push(line + '\\n')", line)
        skeletons = page.locator(".skeleton").count()
        page.screenshot(path=str(HERE / "demo_partial.png"))
        print(f"after {SKELETON_AFTER} lines: {skeletons} skeleton boxes -> demo_partial.png")
        for line in lines[SKELETON_AFTER:]:
            page.evaluate("line => window.openui.push(line + '\\n')", line)
        page.evaluate("window.openui.finish()")
        skeletons = page.locator(".skeleton").count()
        page.screenshot(path=str(HERE / "demo.png"))
        print(f"after {len(lines)} lines: {skeletons} skeleton boxes -> demo.png")
        print("status:", page.locator("#status").inner_text())
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    part_1_parse()
    part_2_stream()
    part_3_browser()
