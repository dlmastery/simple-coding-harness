"""Step 24 offline tests. Nothing here touches the real screen, mouse or keyboard:
PIL.ImageGrab.grab and pyautogui are replaced by fakes.
"""

import base64
import io
import json
import os
import sys
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from PIL import Image, ImageGrab  # noqa: E402

from harness import agent, computer, history, llm, permissions, session, subagent, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments="{}"):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def tiny_image():
    """A 2x2 RGB picture: red, green / blue, white."""
    image = Image.new("RGB", (2, 2))
    image.putdata([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)])
    return image


class FakePyautogui:
    """Records every call instead of moving anything."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return record


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)


@pytest.fixture
def fake_screen(monkeypatch, tmp_path):
    """Screenshots come from a 2x2 image and land in a temp directory."""
    monkeypatch.setattr(ImageGrab, "grab", lambda *a, **k: tiny_image())
    monkeypatch.setattr(computer, "SHOTS", tmp_path / "shots")
    return tmp_path / "shots"


@pytest.fixture
def fake_gui(monkeypatch):
    gui = FakePyautogui()
    monkeypatch.setitem(sys.modules, "pyautogui", gui)
    return gui


# ------------------------------------------------------------------- tools


def test_screenshot_writes_a_png_and_returns_the_marker(fake_screen):
    result = computer.computer_screenshot()
    paths = history.IMAGE.findall(result)
    assert len(paths) == 1
    saved = fake_screen / os.path.basename(paths[0])
    assert saved.exists() and saved.suffix == ".png"
    assert Image.open(saved).size == (2, 2)
    assert "2x2" in result


def test_screen_reports_the_size(fake_screen):
    assert computer.computer_screen().startswith("Screen size: 2x2")


def test_screenshot_without_a_display_is_a_result_not_a_crash(monkeypatch):
    def broken(*a, **k):
        raise OSError("no display")
    monkeypatch.setattr(ImageGrab, "grab", broken)
    assert computer.computer_screenshot().startswith("Error: could not capture the screen")


def test_act_calls_pyautogui_with_the_right_arguments(fake_gui):
    assert computer.computer_act("click", 10, 20).startswith("Done: click at (10, 20)")
    assert computer.computer_act("double_click", 1, 2).startswith("Done")
    assert computer.computer_act("right_click", 3, 4).startswith("Done")
    assert computer.computer_act("move", 5, 6).startswith("Done")
    assert computer.computer_act("drag", 7, 8).startswith("Done")
    assert computer.computer_act("type", text="hello").startswith("Done: type 'hello'")
    assert computer.computer_act("key", keys=["ctrl", "s"]).startswith("Done: key ctrl+s")
    assert computer.computer_act("key", keys=["enter"]).startswith("Done: key enter")
    assert computer.computer_act("scroll", 30, 40, text="-3").startswith("Done: scroll")
    assert fake_gui.calls == [
        ("click", (10, 20), {}),
        ("doubleClick", (1, 2), {}),
        ("rightClick", (3, 4), {}),
        ("moveTo", (5, 6), {}),
        ("dragTo", (7, 8), {"duration": 0.3, "button": "left"}),
        ("write", ("hello",), {"interval": 0.02}),
        ("hotkey", ("ctrl", "s"), {}),
        ("press", ("enter",), {}),
        ("scroll", (-3,), {"x": 30, "y": 40}),
    ]


def test_act_rejects_bad_input_without_touching_the_gui(fake_gui):
    assert computer.computer_act("teleport", 1, 1).startswith("Error: unknown action")
    assert computer.computer_act("click").startswith("Error: click needs x and y")
    assert computer.computer_act("type").startswith("Error: type needs text")
    assert computer.computer_act("key").startswith("Error: key needs keys")
    assert fake_gui.calls == []


def test_act_without_pyautogui_is_a_result(monkeypatch):
    monkeypatch.setitem(sys.modules, "pyautogui", None)  # makes the import fail
    assert computer.computer_act("click", 1, 1).startswith("Error: pyautogui is not installed")


# ---------------------------------------------------------------- history


def test_image_message_carries_the_png_as_a_data_url(tmp_path):
    path = tmp_path / "pic.png"
    tiny_image().save(path)
    message = history.image_message(path, "screenshot from tool computer_screenshot")
    assert message["role"] == "user"
    text, image = message["content"]
    assert text == {"type": "text", "text": "screenshot from tool computer_screenshot"}
    url = image["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")
    decoded = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert decoded.size == (2, 2) and decoded.getpixel((0, 0)) == (255, 0, 0)


def test_split_images_strips_the_marker():
    clean, paths = history.split_images("[[image:C:/x/a.png]] Screenshot saved")
    assert clean == "Screenshot saved" and paths == ["C:/x/a.png"]
    assert history.split_images("plain") == ("plain", [])


def test_strip_shrinks_old_image_messages_and_estimate_counts_them_flat(tmp_path):
    path = tmp_path / "pic.png"
    tiny_image().save(path)
    message = history.image_message(path, "screenshot from tool computer_screenshot")
    messages = [{"role": "system", "content": "s"}, message]
    assert history.estimate(messages) < history.IMAGE_TOKENS + 100
    history.strip(messages)
    assert messages[1] == {"role": "user", "content": "[screenshot from tool computer_screenshot - no longer shown]"}


# ------------------------------------------------------------- permissions


def test_act_asks_by_default_and_screenshot_allows(monkeypatch):
    monkeypatch.delenv("COMPUTER_AUTO", raising=False)
    action, reason = permissions.check("computer_act", {"action": "click", "x": 1, "y": 2})
    assert action == "ask" and "click" in reason
    assert permissions.check("computer_screenshot", {}) == ("allow", None)
    assert permissions.check("computer_screen", {}) == ("allow", None)
    monkeypatch.setenv("COMPUTER_AUTO", "1")
    assert permissions.check("computer_act", {"action": "click", "x": 1, "y": 2})[0] == "allow"


# --------------------------------------------------------------------- loop


def test_turn_expands_the_marker_into_an_image_message(quiet, fake_screen, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("t1", "computer_screenshot")]),
               FakeMessage(content="I see a 2x2 desktop.", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 5, "completion_tokens": 2}

    monkeypatch.setattr(agent, "call_llm", fake)
    out = agent.turn([{"role": "system", "content": "s"}], "what is on screen?")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "user", "assistant"]
    assert "[[image:" not in out[3]["content"] and "Screenshot saved" in out[3]["content"]
    sent = requests[1][4]  # the second request carried the picture
    assert sent["role"] == "user" and sent["content"][0]["text"] == "screenshot from tool computer_screenshot"
    assert sent["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert out[4]["content"] == "[screenshot from tool computer_screenshot - no longer shown]"  # stripped after the turn


def test_subagent_expands_the_marker_too(quiet, fake_screen, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "computer_screenshot")]),
               FakeMessage(content="report: 2x2", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(llm, "call_llm", fake)
    assert subagent.task("look at the screen") == "report: 2x2"
    roles = [m["role"] for m in requests[1]]
    assert roles == ["system", "user", "assistant", "tool", "user"]
    assert requests[1][4]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert "[[image:" not in requests[1][3]["content"]


def test_parallel_results_stay_together_and_pictures_follow(quiet, fake_screen, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("a", "computer_screenshot"), call("b", "computer_screen")]),
               FakeMessage(content="done", tool_calls=None)]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))
    out = agent.turn([{"role": "system", "content": "s"}], "look")
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "tool", "user", "assistant"]
    assert [m["tool_call_id"] for m in out if m["role"] == "tool"] == ["a", "b"]


def test_computer_tools_are_registered():
    names = {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert {"computer_screen", "computer_screenshot", "computer_act"} <= names
    assert all(name in tools.TOOLS for name in ("computer_screen", "computer_screenshot", "computer_act"))
