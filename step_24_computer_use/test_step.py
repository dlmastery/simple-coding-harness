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

from harness import agent, commands, computer, history, llm, permissions, session, subagent, todos, tools  # noqa: E402
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


def test_a_wide_screen_is_scaled_down_and_clicks_are_scaled_back(monkeypatch, tmp_path, fake_gui):
    monkeypatch.setattr(ImageGrab, "grab", lambda *a, **k: Image.new("RGB", (2560, 1440)))
    monkeypatch.setattr(computer, "SHOTS", tmp_path)
    result = computer.computer_screenshot()
    saved = tmp_path / os.path.basename(history.IMAGE.findall(result)[0])
    assert Image.open(saved).size == (1280, 720) and "scaled down from 2560x1440" in result
    assert computer.SCALE == 2.0
    assert "shown at most 1280 wide" in computer.computer_screen()
    computer.computer_act("click", 100, 50)  # the model saw the 1280-wide picture
    assert fake_gui.calls == [("click", (200, 100), {})]
    monkeypatch.setattr(computer, "SCALE", 1.0)


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
    offered = [s for s in computer.COMPUTER_SCHEMAS if s["function"]["name"] == "computer_screenshot"]
    assert subagent.loop("look", "look at the screen", offered, 3) == "report: 2x2"
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


def test_the_task_subagent_is_not_given_the_screen(quiet, monkeypatch):
    offered = {s["function"]["name"] for s in subagent.toolset()}
    assert not {"computer_act", "computer_screenshot"} & offered
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "computer_act", '{"action": "click", "x": 1, "y": 1}')]),
               FakeMessage(content="refused", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {}

    monkeypatch.setattr(llm, "call_llm", fake)
    subagent.task("click something")
    assert [m["content"] for m in requests[1] if m["role"] == "tool"] == ["Blocked by policy: computer_act is not available to this agent"]


def test_act_and_screenshot_in_one_reply_run_in_order(quiet, fake_screen, fake_gui, monkeypatch):
    monkeypatch.setenv("COMPUTER_AUTO", "1")
    order = []
    monkeypatch.setitem(tools.TOOLS, "computer_act", lambda **a: order.append("act") or "Done")
    monkeypatch.setitem(tools.TOOLS, "computer_screenshot", lambda: order.append("shot") or "Screenshot saved")
    tools.execute_all([call("a", "computer_act", '{"action": "click", "x": 1, "y": 1}'), call("b", "computer_screenshot")])
    assert order == ["act", "shot"]


# ------------------------------------------------------- the usual failures


def test_every_tool_call_gets_a_tool_message_even_when_it_fails(quiet, monkeypatch):
    replies = [
        FakeMessage(content=None, tool_calls=[call("a", "bash", '{"command": "ls'), call("b", "nope", "{}"), call("c", "read_file", '{"path": "missing.txt"}')]),
        FakeMessage(content="all failed", tool_calls=None),
    ]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {}))
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    fed = [(m["tool_call_id"], m["content"]) for m in out if m["role"] == "tool"]
    assert [i for i, _ in fed] == ["a", "b", "c"] and all(c.startswith("Error") for _, c in fed)
    assert out[-1]["content"] == "all failed"


def test_write_todos_rejects_bad_items_and_session_load_repairs(tmp_path, monkeypatch):
    todos.TODOS[:] = [{"content": "old", "activeForm": "Old", "status": "pending"}]
    assert todos.write_todos([{"content": "a", "activeForm": "A", "status": "done"}]).startswith("Error: item 0")
    assert todos.TODOS[0]["content"] == "old"
    todos.TODOS.clear()
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    lines = [{"role": "user", "content": "go"}, {"role": "assistant", "content": None, "tool_calls": [{"id": "t9", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]}]
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    assert session.load("x")[-1] == {"role": "tool", "tool_call_id": "t9", "content": session.UNANSWERED}


def test_rewind_cuts_before_a_user_message_never_inside_an_exchange(monkeypatch):
    monkeypatch.setattr(session, "save", lambda messages: None)
    cuts = []
    monkeypatch.setattr(session, "rewind_to", cuts.append)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "a", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "a", "content": "ok"},
        {"role": "user", "content": "two"},
    ]
    monkeypatch.setattr(ui, "pick", lambda title, rows: 1)
    out = commands.rewind(messages)
    assert cuts == [4] and [m["role"] for m in out] == ["system", "user", "assistant", "tool"]


def test_utf8_round_trip_and_hardened_permissions(tmp_path):
    target = tmp_path / "sub" / "n.txt"
    tools.write_file(str(target), "héllo ✓\r\n")
    assert tools.read_file(str(target)) == "héllo ✓\r\n"
    assert permissions.decide("cat a > b") == "ask" and permissions.decide("ls $(x)") == "ask" and permissions.decide("ls 2>&1") == "allow"
