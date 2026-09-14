"""Step 01 - the recorded demo: both processes, a headless browser, demo.png.

Starts the MCP server and the host, opens the host page, runs one turn (the
model picks the tool when a key is present; the tool is called directly
otherwise), clicks a button inside the view so the interactive phase shows
in the log, saves demo.png and prints a condensed bridge log.

    python demo.py
"""

import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SERVER_URL = "http://127.0.0.1:8765/mcp"
HOST_URL = "http://127.0.0.1:8766/"
PROMPT = "show me the lemonade stand dashboard for the last 5 days"


def wait_for(url, seconds=20):
    """Poll until the URL answers anything at all (a 4xx counts: the process is up)."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except urllib.error.HTTPError:
            return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"{url} did not come up")


def condense(line):
    """One bridge-log line as `direction  method  detail`, short enough for a README."""
    direction, _, raw = line.partition(" ")
    message = json.loads(raw.strip())
    if "mount" in message:
        return f"host       mount {message['mount']}  csp: {message['csp'][:38]}..."
    if "method" in message:
        params = message.get("params") or {}
        detail = ""
        if message["method"] in ("tools/call",):
            detail = f"{params['name']}({json.dumps(params.get('arguments', {}))})"
        elif message["method"] == "ui/notifications/tool-input":
            detail = json.dumps(params["arguments"])
        elif message["method"] == "ui/notifications/size-changed":
            detail = f"{params['width']}x{params['height']}"
        elif message["method"] == "ui/message":
            detail = params["content"]["text"][:50]
        elif message["method"] == "initialize":
            detail = "extensions: " + ", ".join(params["capabilities"].get("extensions", {}))
        return f"{direction:<10} {message['method']:<32} {detail}".rstrip()
    result = message.get("result") or {}
    kind = "structuredContent + content" if "structuredContent" in result else \
        "contents[0].mimeType=" + result["contents"][0]["mimeType"] if "contents" in result else \
        f"{len(result['tools'])} tool(s)" if "tools" in result else         f"{len(result['resources'])} resource(s)" if "resources" in result else \
        "hostContext + hostCapabilities" if "hostCapabilities" in result else \
        f"serverInfo.name={result['serverInfo']['name']}" if "serverInfo" in result else "{}"
    return f"{direction:<10} {'response #' + str(message['id']):<32} {kind}"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(HERE))
    import llm
    from playwright.sync_api import sync_playwright

    processes = [
        subprocess.Popen([sys.executable, "server.py"], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
        subprocess.Popen([sys.executable, "host.py"], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
    ]
    try:
        wait_for(SERVER_URL)
        wait_for(HOST_URL)
        with_model = bool(llm.API_KEY)
        query = f"?prompt={urllib.parse.quote(PROMPT)}" if with_model else "?call=lemonade_dashboard"
        print(f"host page: {HOST_URL}{query}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 900})
            page.goto(HOST_URL + query)
            page.wait_for_function("window.host.log.some((l) => l.includes('ui/notifications/tool-result'))", timeout=60_000)
            if with_model:
                page.wait_for_function("document.querySelectorAll('.bubble.assistant').length >= 1", timeout=60_000)
            view = page.frames[1]
            view.click("button[data-days='14']")  # the interactive phase: the view calls the tool through the host
            page.wait_for_function("window.host.log.filter((l) => l.includes('tools/call')).length >= 3", timeout=10_000)
            page.wait_for_timeout(500)
            page.screenshot(path=str(HERE / "demo.png"))
            print()
            for bubble in page.evaluate("[...document.querySelectorAll('.bubble')].map((b) => b.className.split(' ')[1] + ': ' + b.textContent)"):
                print(bubble)
            print()
            print("bridge log (condensed):")
            for line in page.evaluate("window.host.log"):
                print("  " + condense(line))
            browser.close()
        print("\nscreenshot: demo.png")
    finally:
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
