"""Step 24 - computer use: the screen as a tool.

Three tools. computer_screen() reports the screen size. computer_screenshot()
captures the screen to a PNG and returns a marker the loop expands into an
image message, so the model can look at the picture. computer_act() moves
the mouse, clicks, drags, types, presses keys and scrolls through pyautogui.

The model never sees the screen at full size. A vision model shrinks a big
picture before it looks, and then answers with coordinates in the picture it
saw, so a 2560-wide desktop would put every click in the wrong place. The
screenshot is scaled down to MAX_WIDTH, the scale is remembered, and
computer_act multiplies the model's x and y back up to screen pixels.

PIL and pyautogui are imported inside the functions. The harness and the
tests work without them; a missing library comes back as a tool result.
"""

from datetime import datetime
from pathlib import Path

SHOTS = Path.home() / ".simple-harness" / "shots"  # every screenshot lands here

ACTIONS = ("click", "double_click", "right_click", "move", "drag", "type", "key", "scroll")

MAX_WIDTH = 1280  # the picture the model sees is at most this wide
SCALE = 1.0       # screen pixels per picture pixel, as of the last screenshot


def grab():
    """Capture the whole screen as a PIL image. PIL first, pyautogui as the fallback."""
    try:
        # On Windows, importing pyautogui makes the process DPI-aware. Doing it before
        # the first capture keeps screenshots and clicks in the same pixels.
        import pyautogui  # noqa: F401
    except Exception:  # noqa: BLE001 - not installed, or no display: the capture below decides
        pass
    try:
        from PIL import ImageGrab

        return ImageGrab.grab()
    except ImportError:
        import pyautogui

        return pyautogui.screenshot()


def shrink(image):
    """The image at most MAX_WIDTH wide, and how many screen pixels one of its pixels covers."""
    if image.width <= MAX_WIDTH:
        return image, 1.0
    scale = image.width / MAX_WIDTH
    return image.resize((MAX_WIDTH, round(image.height / scale))), scale


def to_screen(x, y):
    """Coordinates in the last screenshot, scaled back to screen pixels."""
    if x is None or y is None:
        return x, y
    return round(x * SCALE), round(y * SCALE)


def computer_screen() -> str:
    """Report the screen size in pixels."""
    try:
        width, height = grab().size
    except ImportError as missing:
        return f"Error: no screenshot library ({missing}). pip install pillow"
    except Exception as failed:  # no display, permission refused, ...
        return f"Error: could not read the screen: {failed}"
    shown = f" Screenshots are shown at most {MAX_WIDTH} wide; give coordinates as you see them in the picture." if width > MAX_WIDTH else ""
    return f"Screen size: {width}x{height} pixels. (0, 0) is the top left corner.{shown}"


def computer_screenshot() -> str:
    """Capture the screen to a PNG and return an image marker plus a note."""
    try:
        image = grab()
    except ImportError as missing:
        return f"Error: no screenshot library ({missing}). pip install pillow"
    except Exception as failed:
        return f"Error: could not capture the screen: {failed}"

    global SCALE
    shown, SCALE = shrink(image)
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"shot-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.png"
    shown.save(path, format="PNG")
    size = f"{shown.width}x{shown.height}"
    if SCALE != 1.0:
        size += f", scaled down from {image.width}x{image.height}"
    return f"[[image:{path}]] Screenshot saved to {path} ({size}). Give coordinates as you see them in this picture."


def computer_act(action: str, x: int | None = None, y: int | None = None, text: str | None = None, keys: list[str] | None = None) -> str:
    """Perform one input action. Returns a short result string; errors are results."""
    if action not in ACTIONS:
        return f"Error: unknown action {action!r}. Use one of: {', '.join(ACTIONS)}."
    try:
        import pyautogui
    except ImportError:
        return "Error: pyautogui is not installed. pip install pyautogui"

    needs_point = action in ("click", "double_click", "right_click", "move", "drag")
    if needs_point and (x is None or y is None):
        return f"Error: {action} needs x and y."
    sx, sy = to_screen(x, y)  # the model answered in the picture's pixels

    try:
        if action == "click":
            pyautogui.click(sx, sy)
        elif action == "double_click":
            pyautogui.doubleClick(sx, sy)
        elif action == "right_click":
            pyautogui.rightClick(sx, sy)
        elif action == "move":
            pyautogui.moveTo(sx, sy)
        elif action == "drag":
            pyautogui.dragTo(sx, sy, duration=0.3, button="left")
        elif action == "type":
            if text is None:
                return "Error: type needs text."
            pyautogui.write(text, interval=0.02)
        elif action == "key":
            if not keys:
                return "Error: key needs keys, e.g. [\"ctrl\", \"s\"] or [\"enter\"]."
            pyautogui.hotkey(*keys) if len(keys) > 1 else pyautogui.press(keys[0])
        elif action == "scroll":
            amount = int(text) if text not in (None, "") else -5
            pyautogui.scroll(amount, x=sx, y=sy) if sx is not None and sy is not None else pyautogui.scroll(amount)
    except Exception as failed:  # pyautogui's fail-safe corner, off-screen point, ...
        return f"Error: {action} failed: {failed}"

    where = f" at ({x}, {y})" if x is not None and y is not None else ""
    what = f" {text!r}" if action == "type" else f" {'+'.join(keys)}" if action == "key" else ""
    return f"Done: {action}{what}{where}. Take a screenshot to see the result."


COMPUTER_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "computer_screen",
            "description": "Report the screen size in pixels. Call it once before acting, so coordinates make sense.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "computer_screenshot",
            "description": (
                "Capture the whole screen. The picture comes back to you as an image "
                "in the next message. Use it to see the desktop before and after every action."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "computer_act",
            "description": (
                "Move the mouse, click, drag, type, press keys or scroll on the real desktop. "
                "Actions: click, double_click, right_click, move, drag (from the current mouse "
                "position to x,y), type (text), key (keys, e.g. [\"ctrl\", \"s\"]), scroll "
                "(text holds the amount: negative is down). Take a screenshot afterwards."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": list(ACTIONS), "description": "What to do"},
                    "x": {"type": "integer", "description": "x as seen in the last screenshot"},
                    "y": {"type": "integer", "description": "y as seen in the last screenshot"},
                    "text": {"type": "string", "description": "Text to type, or the scroll amount"},
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "Keys to press together"},
                },
                "required": ["action"],
            },
        },
    },
]

COMPUTER_TOOLS = {
    "computer_screen": computer_screen,
    "computer_screenshot": computer_screenshot,
    "computer_act": computer_act,
}
