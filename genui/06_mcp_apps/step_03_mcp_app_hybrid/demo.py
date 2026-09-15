"""Step 03 - the recorded demo: both processes, a headless browser, two screenshots.

Starts the MCP server (which holds the key for the generated region) and
the host, opens the host page, runs one turn (the model picks the tool when
a key is present; the tool is called directly otherwise), then moves the
slider inside the generated region, one frame below the app, so the inner
script proves it ran and its event climbs back up: region -> app -> host.
Saves demo.png (the host page) and demo_generated.png (the inner region),
prints the chat, the cost of the server's model call, the size of the
generated fragment and a condensed bridge log.

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
SERVER_URL = "http://127.0.0.1:8767/mcp"
HOST_URL = "http://127.0.0.1:8768/"
PROMPT = "show me the lemonade stand report for the last 5 days with a what-if price slider"

# Set the slider three quarters of the way up its range and fire the events a user would.
MOVE_SLIDER = """() => {
  const slider = document.querySelector('input[type=range]');
  if (!slider) return null;
  const min = Number(slider.min || 0), max = Number(slider.max || 100), step = Number(slider.step || 1);
  slider.value = String(Math.round((min + 0.75 * (max - min)) / step) * step);
  slider.dispatchEvent(new Event('input', { bubbles: true }));
  slider.dispatchEvent(new Event('change', { bubbles: true }));
  return slider.value;
}"""


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
        if message["method"] == "tools/call":
            detail = f"{params['name']}({json.dumps(params.get('arguments', {}))})"
        elif message["method"] == "ui/notifications/tool-input":
            detail = json.dumps(params["arguments"])
        elif message["method"] == "ui/notifications/size-changed":
            detail = f"{params['width']}x{params['height']}"
        elif message["method"] == "ui/update-model-context":
            detail = params["content"][0]["text"][:60]
        elif message["method"] == "initialize":
            detail = "extensions: " + ", ".join(params["capabilities"].get("extensions", {}))
        return f"{direction:<10} {message['method']:<32} {detail}".rstrip()
    result = message.get("result") or {}
    kind = "structuredContent + content" if "structuredContent" in result else \
        "contents[0].mimeType=" + result["contents"][0]["mimeType"] if "contents" in result else \
        f"{len(result['tools'])} tool(s)" if "tools" in result else \
        f"{len(result['resources'])} resource(s)" if "resources" in result else \
        "hostContext + hostCapabilities" if "hostCapabilities" in result else \
        f"serverInfo.name={result['serverInfo']['name']}" if "serverInfo" in result else "{}"
    return f"{direction:<10} {'response #' + str(message['id']):<32} {kind}"


def frames_below(page, parent):
    return [frame for frame in page.frames if frame.parent_frame == parent]


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
        query = f"?prompt={urllib.parse.quote(PROMPT)}" if with_model else "?call=lemonade_report"
        print(f"host page: {HOST_URL}{query}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 1180})
            page.goto(HOST_URL + query)
            page.wait_for_function("window.host.log.some((l) => l.includes('ui/notifications/tool-result'))", timeout=120_000)
            if with_model:
                page.wait_for_function("document.querySelectorAll('.bubble.assistant').length >= 1", timeout=60_000)
            app = frames_below(page, page.main_frame)[0]              # the app: host -> app iframe
            app.wait_for_function("window.app.latest !== null")
            region = frames_below(page, app)[0]                         # the region: app iframe -> generated iframe
            region.wait_for_selector("input[type=range]", timeout=10_000)
            page.wait_for_timeout(300)

            value = region.evaluate(MOVE_SLIDER)                        # the headless interaction, two frames down
            app.wait_for_function("window.app.events.length >= 1", timeout=10_000)
            page.wait_for_function("window.host.log.some((l) => l.includes('ui/update-model-context'))", timeout=10_000)
            page.wait_for_timeout(400)
            log = page.evaluate("window.host.log")
            page.screenshot(path=str(HERE / "demo.png"))
            app.locator("iframe.generated").screenshot(path=str(HERE / "demo_generated.png"))

            latest = app.evaluate("window.app.latest")
            events = app.evaluate("window.app.events")
            print()
            for bubble in page.evaluate("[...document.querySelectorAll('.bubble')].map((b) => b.className.split(' ')[1] + ': ' + b.textContent)"):
                print(bubble)
            generated = latest["generated"]
            print()
            print(f"components: {len(latest['components'])} ({', '.join(c['component'] for c in latest['components'])}), {len(json.dumps(latest['components']))} bytes of JSON")
            print(f"generated region: {generated['bytes']} bytes of HTML, {generated['html'].count(chr(10)) + 1} lines, source={generated['source']}"
                  + (f", note: {generated['note']}" if generated["note"] else ""))
            if generated["usage"]:
                print(f"server model call: {generated['usage']['prompt_tokens']} prompt + {generated['usage']['completion_tokens']} completion tokens")
            last = events[-1]  # the model's script may also post once on load; the last event is the slider move
            print(f"slider moved to {value} inside the generated region -> event: {last['name']} {json.dumps(last['payload'])}")
            print()
            print("bridge log (condensed, from the tool call on):")
            start = next(i for i, line in enumerate(log) if '"tools/call"' in line)
            for line in log[start:]:
                print("  " + condense(line))
            browser.close()
        print("\nscreenshots: demo.png, demo_generated.png")
    finally:
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
