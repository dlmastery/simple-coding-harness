# Step 24 - Computer use

**What this step adds:** three tools that give the agent the desktop.
`computer_screen` reports the screen size. `computer_screenshot` captures
the screen to a PNG. `computer_act` clicks, drags, types, presses keys and
scrolls. A screenshot does not come back as text: the tool result carries a
marker, and the loop turns that marker into an image message the model can
look at. Every act asks for approval unless `COMPUTER_AUTO=1`.

## Why the screen, and why as a picture

Step 23 gave the agent a browser. That covers web pages, but not the rest
of the machine: a desktop application, a system dialog, an installer with
no command line. For those the only interface is the screen and the mouse.

A screen is a picture, and a picture cannot go through the tool result
path. Tool results are strings. A model that supports vision takes an
image only inside a user message, as an `image_url` content part. So this
step adds a small bridge. A tool that produced a picture writes it to disk
and puts a marker, `[[image:PATH]]`, in its result string. The loop looks
for that marker after it appends the result, strips it, and appends one
more message: a user message with a caption and the PNG as a base64 data
URL. The model sees a normal tool result followed by the picture.

The bridge lives in `history.py` and both loops call it. The main agent and
the subagents append tool results in two places, `agent.turn()` and
`subagent.loop()`, so the expansion has to happen in both. The helper is
shared; only the call site is repeated.

The computer tools are offered to the main agent directly, not behind a
subagent like the browser. A browse task can be described in advance: open
this URL, read, click that link. A desktop task cannot. Every step depends
on what the last screenshot showed, and the user is the one who has to
approve each click. Both of those want the main context, not a report.

## The code, piece by piece

### 1. Capturing the screen

`harness/computer.py`:

```python
def grab():
    """Capture the whole screen as a PIL image. PIL first, pyautogui as the fallback."""
    try:
        from PIL import ImageGrab

        return ImageGrab.grab()
    except ImportError:
        import pyautogui

        return pyautogui.screenshot()
```

`ImageGrab.grab()` from Pillow captures the whole screen on Windows and
macOS, and on Linux under X11. `pyautogui.screenshot()` is the fallback
and returns the same kind of object. Both imports sit inside the function.
The harness and its tests import `computer.py` without either library.

`harness/computer.py`:

```python
def computer_screenshot() -> str:
    """Capture the screen to a PNG and return an image marker plus a note."""
    try:
        image = grab()
    except ImportError as missing:
        return f"Error: no screenshot library ({missing}). pip install pillow"
    except Exception as failed:
        return f"Error: could not capture the screen: {failed}"

    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"shot-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.png"
    image.save(path, format="PNG")
    width, height = image.size
    return f"[[image:{path}]] Screenshot saved to {path} ({width}x{height}). Coordinates below are screen pixels."
```

The PNG lands under `~/.simple-harness/shots/` with a timestamp in its
name. The result string starts with the marker and ends with a note. The
note is what the model sees as the tool result once the marker is gone. A
missing library or a machine without a display comes back as an `Error:`
result, the same rule as the browser tools.

### 2. Acting

`harness/computer.py`:

```python
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

    try:
        if action == "click":
            pyautogui.click(x, y)
        elif action == "double_click":
            pyautogui.doubleClick(x, y)
        elif action == "right_click":
            pyautogui.rightClick(x, y)
        elif action == "move":
            pyautogui.moveTo(x, y)
        elif action == "drag":
            pyautogui.dragTo(x, y, duration=0.3, button="left")
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
            pyautogui.scroll(amount, x=x, y=y) if x is not None and y is not None else pyautogui.scroll(amount)
    except Exception as failed:  # pyautogui's fail-safe corner, off-screen point, ...
        return f"Error: {action} failed: {failed}"
```

One tool, eight actions. The `action` string picks the `pyautogui` call.
`x` and `y` are screen pixels. `text` is what to type, or the scroll
amount. `keys` is a list, so `["ctrl", "s"]` becomes a chord and
`["enter"]` a single press. `drag` moves from the current mouse position to
the point given, so a drag is a `move` followed by a `drag`. The result
tells the model to take another screenshot, because the tool cannot see
whether the click did what was wanted.

`pyautogui` has a fail-safe: moving the mouse to a screen corner raises
an exception and stops the automation. That exception is caught and
returned as a result, like every other failure.

### 3. The image message

`harness/history.py`:

```python
def split_images(result):
    """Take the image markers out of a tool result. Returns (clean text, paths)."""
    paths = IMAGE.findall(result)
    if not paths:
        return result, []
    return IMAGE.sub("", result).strip(), paths


def image_message(path, caption):
    """A user message that shows the model one PNG next to a line of text.

    The chat completions API takes a picture as an image_url part; a data URL
    keeps the file out of any server. The caption says which tool made it.
    """
    try:
        data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    except OSError as failed:  # a marker whose file is gone: say so, keep the loop alive
        return {"role": "user", "content": f"[{caption}: the image at {path} could not be read: {failed}]"}
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": caption},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}},
        ],
    }
```

`split_images` finds every `[[image:PATH]]` in a result and returns the
text without them, plus the paths. `image_message` builds the message that
carries one picture. Its content is a list of two parts: a text part with
the caption, and an `image_url` part whose URL is the PNG encoded as
base64. Nothing is uploaded anywhere; the bytes travel inside the request.

### 4. Both loops expand the marker

`harness/agent.py`:

```python
        outcomes = execute_all(message.tool_calls)
        pictures = []  # (tool name, PNG path) for every image a result asked to show
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            result, paths = history.split_images(result)
            pictures += [(tool_call.function.name, path) for path in paths]
            ui.tool(tool_call.function.name, args, result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            session.save(messages)  # after every message, so a crash loses nothing

        # the pictures go after the last result, so no tool message is orphaned
        for name, path in pictures:
            messages.append(history.image_message(path, f"screenshot from tool {name}"))
            session.save(messages)
```

The order matters. An assistant message with tool calls must be followed
by one tool message per call, with nothing in between. So the loop first
appends every result, collecting the pictures as it goes, and only then
appends the image messages. A reply with two tool calls and one screenshot
produces: assistant, tool, tool, user. The tool result keeps the note and
loses the marker.

`harness/subagent.py`:

```python
        outcomes = execute_all(message.tool_calls)
        pictures = []
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            result, paths = split_images(result)
            pictures += [(tool_call.function.name, path) for path in paths]
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        for name, path in pictures:  # same expansion as agent.turn, after the last result
            messages.append(image_message(path, f"screenshot from tool {name}"))
```

The subagent loop does the same thing with the same helper. The task
subagent has no computer tools, but the code is one loop shared by `task`
and `browse`, and a later step may give a subagent a screen.

### 5. Pictures in the budget

`harness/history.py`:

```python
    shrunk = 0
    for message in messages:
        content = message.get("content") or ""
        if isinstance(content, list):  # an image message: keep its caption, drop the picture
            message["content"] = f"[{caption_of(content)} - no longer shown]"
            shrunk += 1
            continue
```

A full-screen PNG is a few hundred kilobytes of base64. Kept for the whole
session it would fill the context window in a dozen screenshots. So
`strip()`, which already shrinks old tool results at the end of every
turn, shrinks old image messages to their caption. The model still knows a
screenshot was taken; it no longer carries the pixels. Compaction and
replay read the same caption.

`harness/history.py`:

```python
    total = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            total += IMAGE_TOKENS * sum(1 for part in content if part.get("type") == "image_url")
            total += sum(len(part.get("text", "")) for part in content) // 4
        else:
            total += len(json.dumps(message)) // 4
    return total
```

`estimate()` counts a picture as a flat `IMAGE_TOKENS`, not as a quarter
of its base64 length. A model bills an image by its size on screen, not by
the length of its encoding, and the old estimate would have panicked and
dropped tool results for nothing.

### 6. Every act asks

`harness/permissions.py`:

```python
    if name == "computer_act" and not computer_auto():
        where = f" at ({args.get('x')}, {args.get('y')})" if args.get("x") is not None else ""
        detail = args.get("text") if args.get("text") is not None else args.get("keys")
        return "ask", f"computer: {args.get('action')}{where}" + (f" {detail!r}" if detail is not None else "")

    return "allow", None
```

The sandbox protects the file system from `bash`. Nothing protects the
desktop from a click. So `computer_act` asks before every action, and the
prompt says what and where: `computer: click at (640, 400)` or
`computer: type 'hello'`. `COMPUTER_AUTO=1` turns the prompt off for a
session where the user is watching the screen anyway. `computer_screen`
and `computer_screenshot` are read-only and allow.

## Run it

Install the optional group and start the harness:

```bash
pip install -e ".[computer]"
harness
> take a screenshot and tell me what is open
```

The tool panel shows the note, `Screenshot saved to ...`, and the next
model call carries the picture. The model describes the screen. Ask it to
act:

```bash
> open the start menu and type notepad
```

Each `computer_act` stops at an `allow? (y/n)` prompt naming the action and
the coordinates. After every act the model takes a new screenshot to check
the result. Set `COMPUTER_AUTO=1` to skip the prompts.

The screenshots stay under `~/.simple-harness/shots/`. Delete the
directory when you are done; nothing else reads it.

Run the offline tests from the repository root. They replace the screen
with a 2x2 image and `pyautogui` with a recorder, so nothing moves:

```bash
python run_tests.py 24
```

## What to notice

- The model needs vision. A text-only model gets the image message and
  either errors or ignores it. Set `MODEL` to one that takes images.
- A tool result is a string, so the picture travels beside it, in a user
  message. The marker is the only contract between a tool and the loop.
  Any tool can use it; nothing in the loop knows about `computer.py`.
- Look, act, look. The prompt tells the model to take a screenshot after
  every action, because the action result cannot say whether it worked.
  Expect three tool calls per step.
- Old pictures are stripped to a caption at the end of the turn, exactly
  when old tool output is stripped to a stub. The context stays small and
  the cached prefix survives, for the same reason as in step 14.
- The desktop has no sandbox. `COMPUTER_AUTO=1` is a decision to trust the
  model with the mouse. Keep the fail-safe: move the mouse into a screen
  corner and `pyautogui` stops.

## Diff from step 23

```bash
diff -r ../step_23_browser_use/harness harness
```

Added: `computer.py`. Changed: `history.py` (`IMAGE`, `IMAGE_TOKENS`,
`split_images`, `image_message`, `caption_of`, image-aware `strip` and
`estimate`), `agent.py` and `subagent.py` (marker expansion after the
results), `tools.py` (three computer tools in `TOOLS` and `TOOL_SCHEMAS`),
`permissions.py` (`computer_auto`, the `computer_act` rule), `llm.py`
(system prompt), `ui.py` and `compact.py` (an image message is shown by
its caption). `pyproject.toml` gains the `computer` optional group.
