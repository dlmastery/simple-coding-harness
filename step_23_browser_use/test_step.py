import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import browse, browser, llm, permissions, session, subagent, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


class FakeLocator:
    """Stands in for a Playwright locator: count(), .first, click()."""

    def __init__(self, page, target, found):
        self.page, self.target, self.found = page, target, found
        self.first = self

    def count(self):
        if self.target.endswith("!"):
            raise ValueError("bad selector")  # what Playwright does with text that is not CSS
        return self.found

    def click(self, timeout=None):
        self.page.log.append(("click", self.target))
        self.page.url = "https://example.test/next"


class FakePage:
    """A page object with just the methods the tools use. No browser anywhere."""

    def __init__(self, text="Hello\n\n\n  world  \n", raise_on_goto=None):
        self.url, self.text, self.log = "about:blank", text, []
        self.raise_on_goto = raise_on_goto

    def goto(self, url, wait_until=None):
        if self.raise_on_goto:
            raise self.raise_on_goto
        self.url = url
        self.log.append(("goto", url))

    def title(self):
        return "Fake Title"

    def locator(self, target):
        return FakeLocator(self, target, found=1 if target.startswith("#") else 0)

    def get_by_text(self, target):
        self.log.append(("by_text", target))
        return FakeLocator(self, target, found=1)

    def fill(self, selector, text, timeout=None):
        self.log.append(("fill", selector, text))

    def press(self, selector, key, timeout=None):
        self.log.append(("press", selector, key))

    def wait_for_load_state(self, state=None):
        pass

    def inner_text(self, selector):
        return self.text

    def screenshot(self, path):
        Path(path).write_bytes(b"\x89PNG fake")
        self.log.append(("screenshot", path))


@pytest.fixture
def fake_page(monkeypatch):
    page = FakePage()
    monkeypatch.setattr(browser, "_page", page)
    monkeypatch.setattr(browser, "page", lambda: page)
    return page


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "subagent", lambda description: None)


# ------------------------------------------------------------------- tools


def test_open_read_and_close_against_a_fake_page(fake_page):
    assert browser.browser_open("https://example.test/") == "Opened https://example.test/ - title: 'Fake Title'"
    text = browser.browser_read()
    assert text.startswith("Title: Fake Title\nURL: https://example.test/\n\nHello\nworld")
    assert "\n\n\n" not in text  # blank lines are dropped, indentation stripped
    assert browser.browser_close() == "Browser closed." and browser._page is None
    assert browser.browser_close() == "No browser was open."


def test_click_uses_the_selector_when_it_matches_and_text_otherwise(fake_page):
    assert browser.browser_click("#go") == "Clicked '#go' - now at https://example.test/next"
    assert ("click", "#go") in fake_page.log and ("by_text", "#go") not in fake_page.log
    browser.browser_click("Sign up")
    assert ("by_text", "Sign up") in fake_page.log
    browser.browser_click("Go!")  # a target the selector engine rejects still works as text
    assert ("by_text", "Go!") in fake_page.log


def test_type_fills_and_submit_presses_enter(fake_page):
    assert browser.browser_type("input[name=q]", "harness") == "Typed 7 chars into 'input[name=q]'"
    assert ("press", "input[name=q]", "Enter") not in fake_page.log
    out = browser.browser_type("input[name=q]", "harness", submit=True)
    assert out.startswith("Typed 7 chars into 'input[name=q]' and pressed Enter")
    assert fake_page.log[-1] == ("press", "input[name=q]", "Enter")


def test_screenshot_stays_inside_the_project(fake_page, tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT", tmp_path)
    monkeypatch.setattr(browser, "PROJECT", tmp_path)
    inside = tmp_path / "shots" / "page"
    result = browser.browser_screenshot(str(inside))
    assert result == f"Saved screenshot to {inside.with_suffix('.png')}" and inside.with_suffix(".png").exists()
    outside = browser.browser_screenshot(str(tmp_path.parent / "escape.png"))
    assert outside.startswith("Error:") and "outside the project" in outside


def test_errors_come_back_as_results(monkeypatch):
    broken = FakePage(raise_on_goto=RuntimeError("net::ERR_NAME_NOT_RESOLVED at https://nope.test/\nCall log:\n  - navigating"))
    monkeypatch.setattr(browser, "_page", broken)
    monkeypatch.setattr(browser, "page", lambda: broken)
    assert browser.browser_open("https://nope.test/") == "Error: net::ERR_NAME_NOT_RESOLVED at https://nope.test/"


def test_long_page_text_is_capped_like_any_tool_output(monkeypatch):
    long_page = FakePage(text="word " * 5000)
    monkeypatch.setattr(browser, "_page", long_page)
    monkeypatch.setattr(browser, "page", lambda: long_page)
    monkeypatch.setattr(browser.history, "spill", lambda text: "SPILLED")
    out = browser.browser_read()
    assert len(out) < 12_000 and browser.history.TRIMMED in out


# ---------------------------------------------------------------- toolsets


def test_browse_toolset_is_browser_tools_plus_read_file_only():
    names = {s["function"]["name"] for s in browse.toolset()}
    assert names == set(browser.TOOLS) | {"read_file"}
    assert {"bash", "write_file", "str_replace", "write_todos", "task", "browse"}.isdisjoint(names)


def test_main_agent_gets_browse_but_not_the_raw_browser_tools():
    offered = {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert "browse" in offered and offered.isdisjoint(browser.TOOLS)
    assert set(browser.TOOLS) <= set(tools.TOOLS) and tools.TOOLS["browse"] is browse.browse
    assert "browse" not in {s["function"]["name"] for s in subagent.toolset()}  # one subagent deep


# -------------------------------------------------------------- permissions


def test_browser_open_asks_unless_the_host_is_allow_listed(monkeypatch):
    monkeypatch.setattr(permissions, "BROWSER_ALLOW", {"docs.python.org"})
    assert permissions.check("browser_open", {"url": "https://docs.python.org/3/"}) == ("allow", None)
    assert permissions.check("browser_open", {"url": "https://DOCS.python.org:443/x"})[0] == "allow"
    action, reason = permissions.check("browser_open", {"url": "https://example.com/"})
    assert action == "ask" and reason == "open in the browser: https://example.com/"
    assert permissions.check("browser_open", {"url": "about:blank"})[0] == "ask"
    for name in ("browser_read", "browser_click", "browser_type", "browser_screenshot", "browser_close"):
        assert permissions.check(name, {})[0] == "allow"


# --------------------------------------------------------------- the loop


def test_browse_runs_the_subagent_loop_and_returns_only_the_report(fake_page, quiet, monkeypatch):
    requests = []
    replies = [
        FakeMessage(content=None, tool_calls=[call("b1", "browser_open", '{"url": "https://example.test/"}'), call("b2", "browser_read", "{}")]),
        FakeMessage(content="The page says: Hello world (https://example.test/)", tool_calls=None),
    ]

    def fake(messages, tools=None, on_delta=None):
        requests.append(([dict(m) for m in messages], tools))
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(llm, "call_llm", fake)
    monkeypatch.setattr(permissions, "BROWSER_ALLOW", {"example.test"})
    assert browse.browse("read https://example.test/") == "The page says: Hello world (https://example.test/)"
    first, offered = requests[0]
    assert [m["role"] for m in first] == ["system", "user"] and "credentials" in first[0]["content"]
    assert {s["function"]["name"] for s in offered} == set(browser.TOOLS) | {"read_file"}
    second = requests[1][0]
    assert second[3]["role"] == "tool" and second[3]["content"].startswith("Opened https://example.test/")
    assert second[4]["role"] == "tool" and "Hello\nworld" in second[4]["content"]
    assert ("goto", "https://example.test/") in fake_page.log


def test_runaway_browse_is_cut_off_at_its_own_limit(fake_page, quiet, monkeypatch):
    monkeypatch.setattr(browse, "MAX_TURNS", 2)
    monkeypatch.setattr(llm, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content="still reading", tool_calls=[call("x", "browser_read", "{}")]), {}))
    out = browse.browse("q")
    assert out.startswith("(stopped after 2 turns") and "still reading" in out
    assert subagent.MAX_TURNS == 12 and browse.TOOLS  # task keeps its own cap


# ----------------------------------------------------------------- live


@pytest.mark.skipif(os.environ.get("HARNESS_LIVE_BROWSER") != "1", reason="set HARNESS_LIVE_BROWSER=1 to launch Chromium")
def test_live_chromium_opens_about_blank():
    pytest.importorskip("playwright")
    try:
        assert browser.browser_open("about:blank") == "Opened about:blank - title: ''"
        assert browser.browser_read().startswith("Title: \nURL: about:blank")
    finally:
        assert browser.browser_close() in ("Browser closed.", "No browser was open.")
