"""Step 23 - browser tools: one Chromium page, driven through Playwright.

The page is created on first use and lives until browser_close() or the end
of the session. Playwright's sync API is bound to the thread that started it,
and the harness runs the tool calls of one reply from a thread pool, so this
module keeps one worker thread of its own and sends every Playwright call
there. Each tool returns a short string. An error is a result, not an
exception, so the model can read it and try something else.

Playwright is imported inside page(), not at the top: it is an optional
dependency, and the rest of the harness must import without it.
"""

import functools
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import history
from .permissions import PROJECT, inside_project

TIMEOUT_MS = 15_000  # how long one click, fill or press may wait for its element

_playwright = None
_browser = None
_page = None
_worker = None  # the one thread every Playwright object belongs to
_worker_lock = threading.Lock()  # two parallel browse calls must not each start a worker


def headless():
    """Headless unless BROWSER_HEADLESS=0, which shows the window."""
    return os.environ.get("BROWSER_HEADLESS", "1") != "0"


def on_worker(fn, *args):
    """Run fn on the browser thread and wait for its result."""
    global _worker
    with _worker_lock:
        if _worker is None:
            _worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="browser")
    return _worker.submit(fn, *args).result()


def page():
    """The page, launched on first use. Only ever called on the browser thread."""
    global _playwright, _browser, _page
    if _page is not None and _page.is_closed():  # the window was closed by hand: start over
        _page = None
    if _page is None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("playwright is not installed: pip install playwright && playwright install chromium")
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=headless())
        _page = _browser.new_page()
        _page.set_default_timeout(TIMEOUT_MS)
    return _page


def tool(fn):
    """Run a tool body on the browser thread and turn any exception into a result."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return on_worker(lambda: fn(*args, **kwargs))
        except Exception as error:  # a failed click is information, not a crash
            first_line = str(error).strip().splitlines()[0] if str(error).strip() else type(error).__name__
            return f"Error: {first_line}"

    return wrapper


@tool
def browser_open(url: str) -> str:
    """Open a URL in the page and report where it landed."""
    current = page()
    current.goto(url, wait_until="domcontentloaded")
    return f"Opened {current.url} - title: {current.title()!r}"


@tool
def browser_click(target: str) -> str:
    """Click a CSS selector, or the first element showing the given text."""
    current = page()
    located = current.locator(target)
    try:
        found = located.count()
    except Exception:  # not a valid selector, so it must be text
        found = 0
    if found == 0:
        located = current.get_by_text(target)
    located.first.click(timeout=TIMEOUT_MS)
    current.wait_for_load_state("domcontentloaded")
    return f"Clicked {target!r} - now at {current.url}"


@tool
def browser_type(selector: str, text: str, submit: bool = False) -> str:
    """Fill a field and, with submit, press Enter in it."""
    current = page()
    current.fill(selector, text, timeout=TIMEOUT_MS)
    if not submit:
        return f"Typed {len(text)} chars into {selector!r}"
    current.press(selector, "Enter", timeout=TIMEOUT_MS)
    current.wait_for_load_state("domcontentloaded")
    return f"Typed {len(text)} chars into {selector!r} and pressed Enter - now at {current.url}"


@tool
def browser_read() -> str:
    """The page's title, URL and visible text, capped like any tool output."""
    current = page()
    lines = (line.strip() for line in current.inner_text("body").splitlines())
    text = "\n".join(line for line in lines if line)  # visible text, blank lines dropped
    return history.cap(f"Title: {current.title()}\nURL: {current.url}\n\n{text}")


@tool
def browser_screenshot(path: str = "screenshot.png") -> str:
    """Save a PNG of the viewport. The path must be inside the project."""
    target = Path(path).resolve().with_suffix(".png")
    if not inside_project(target):
        return f"Error: {path} is outside the project. Screenshots stay under {PROJECT}."
    target.parent.mkdir(parents=True, exist_ok=True)
    page().screenshot(path=str(target))
    return f"Saved screenshot to {target}"


@tool
def browser_close() -> str:
    """Close the browser. The next browser tool call starts a fresh one."""
    global _playwright, _browser, _page
    if _page is None:
        return "No browser was open."
    try:
        if _browser is not None:
            _browser.close()
        if _playwright is not None:
            _playwright.stop()
    finally:
        _playwright = _browser = _page = None  # a close that failed halfway must not leave a dead page behind
    return "Browser closed."


TOOLS = {
    "browser_open": browser_open,
    "browser_click": browser_click,
    "browser_type": browser_type,
    "browser_read": browser_read,
    "browser_screenshot": browser_screenshot,
    "browser_close": browser_close,
}


def schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


SCHEMAS = [
    schema(
        "browser_open",
        "Open a URL in the browser page. Returns the final URL and the page title.",
        {"url": {"type": "string", "description": "Full URL, including https://"}},
        ["url"],
    ),
    schema(
        "browser_click",
        "Click an element. Give a CSS selector, or the visible text of a link or button.",
        {"target": {"type": "string", "description": "CSS selector, or visible text"}},
        ["target"],
    ),
    schema(
        "browser_type",
        "Type into a field found by CSS selector. Set submit to press Enter afterwards.",
        {
            "selector": {"type": "string", "description": "CSS selector of the input"},
            "text": {"type": "string", "description": "Text to type; replaces what was there"},
            "submit": {"type": "boolean", "description": "Press Enter after typing"},
        },
        ["selector", "text"],
    ),
    schema(
        "browser_read",
        "Return the current page's title, URL and visible text. Long pages are cut and spilled to a file.",
        {},
        [],
    ),
    schema(
        "browser_screenshot",
        "Save a PNG of the current viewport to a path inside the project.",
        {"path": {"type": "string", "description": "Where to save the PNG, relative to the project"}},
        [],
    ),
    schema("browser_close", "Close the browser and drop its state.", {}, []),
]
