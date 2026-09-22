# Step 24 - Computer use

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 23 - Browser use](../step_23_browser_use/README.md). Next: [Step 25 - Persistent memory](../step_25_memory/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** three tools that give the agent the desktop.
`computer_screen` reports the screen size. `computer_screenshot` captures
the screen to a PNG. `computer_act` clicks, drags, types, presses keys and
scrolls. A screenshot does not come back as text: the tool result carries a
marker, and the loop turns that marker into an image message the model can
look at. The picture is scaled down to at most 1280 pixels wide before the
model sees it, and the model's coordinates are scaled back up before the
mouse moves. Every act asks for approval unless `COMPUTER_AUTO=1`.

## Why the screen, and what breaks without it

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
shared; only the call site is repeated. The browse subagent gains from it
at once: `browser_screenshot` now returns the marker too, so the browse
subagent can look at the page it is driving.

The computer tools are offered to the main agent directly, not behind a
subagent like the browser. A browse task can be described in advance: open
this URL, read, click that link. A desktop task cannot. Every step depends
on what the last screenshot showed, and the user is the one who has to
approve each click. Both of those want the main context, not a report.

What breaks without the scaling: a vision model shrinks a large picture
before it looks at it, and then answers with coordinates in the picture
it saw. On a 2560x1440 or 4K desktop the model's `(640, 400)` is nowhere
near the screen's `(640, 400)`, and every click lands in the wrong place.
The fix is to do the shrinking ourselves, remember the factor, and
multiply the model's numbers back.

## The code, piece by piece

### 1. Capturing the screen

`harness/computer.py`:

```python
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
```

`ImageGrab.grab()` from Pillow captures the whole screen on Windows and
macOS, and on Linux under X11. `pyautogui.screenshot()` is the fallback
and returns the same kind of object. Both imports sit inside the function.
The harness and its tests import `computer.py` without either library.

The `pyautogui` import at the top is not for the capture. On a Windows
display scaled to 125% or 150%, a process that is not DPI-aware sees
logical pixels and one that is sees physical pixels - and importing
`pyautogui` flips the process to DPI-aware. If that happened between the
first screenshot and the first click, the two would be in different pixel
spaces. Importing it before the first capture keeps them the same.

### 2. Shrinking, and remembering the scale

`harness/computer.py`:

```python
MAX_WIDTH = 1280  # the picture the model sees is at most this wide
SCALE = 1.0       # screen pixels per picture pixel, as of the last screenshot
```

```python
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
```

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

    global SCALE
    shown, SCALE = shrink(image)
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"shot-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.png"
    shown.save(path, format="PNG")
    size = f"{shown.width}x{shown.height}"
    if SCALE != 1.0:
        size += f", scaled down from {image.width}x{image.height}"
    return f"[[image:{path}]] Screenshot saved to {path} ({size}). Give coordinates as you see them in this picture."
```

A 2560x1440 screen becomes a 1280x720 picture and `SCALE` becomes `2.0`.
The PNG lands under `~/.simple-harness/shots/` with a timestamp in its
name, already shrunk, so the session file and the request carry the small
version. The result string starts with the marker and ends with a note
that tells the model which pixels to answer in. A 1280-wide or smaller
screen is sent as it is, with `SCALE` at `1.0`. A missing library or a
machine without a display comes back as an `Error:` result, the same rule
as the browser tools.

### 3. Acting

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
```

One tool, eight actions. The `action` string picks the `pyautogui` call.
`x` and `y` are pixels in the last screenshot; `to_screen` turns them
into screen pixels just before the mouse moves, and the result string
echoes the model's own numbers so it can reason in one space. `text` is
what to type, or the scroll amount. `keys` is a list, so `["ctrl", "s"]`
becomes a chord and `["enter"]` a single press. `drag` moves from the
current mouse position to the point given, so a drag is a `move` followed
by a `drag`. The result tells the model to take another screenshot,
because the tool cannot see whether the click did what was wanted.

`pyautogui` has a fail-safe: moving the mouse to a screen corner raises
an exception and stops the automation. That exception is caught and
returned as a result, like every other failure.

### 4. The image message

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

### 5. Both loops expand the marker

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
        outcomes = execute_all(message.tool_calls, allowed)
        pictures = []
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            result, paths = split_images(result)
            pictures += [(tool_call.function.name, path) for path in paths]
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        for name, path in pictures:  # same expansion as agent.turn, after the last result
            messages.append(image_message(path, f"screenshot from tool {name}"))
```

The subagent loop does the same thing with the same helper. The browse
subagent uses it: `browser_screenshot` now returns the marker, so the
picture of the page comes back to the subagent that asked for it. The
`task` subagent does not get the screen at all:

`harness/subagent.py`:

```python
# the computer tools too: an explorer reads and reports, it does not click
WITHHELD = {"task", "browse", "write_todos", "str_replace", "write_file", "computer_act", "computer_screenshot"}
```

### 6. Pictures in the budget

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

A 1280x720 PNG of a desktop is a few hundred kilobytes of base64; before
the shrink, a 4K screenshot was several megabytes. Kept for the whole
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

### 7. Every act asks, and acts run in order

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

`harness/tools.py`:

```python
SERIAL = {"task", "browse", *browser.TOOLS, *computer.COMPUTER_TOOLS}
```

The prompt says "act, then take a new screenshot", and step 22's prompt
says to batch independent calls, so `[computer_act, computer_screenshot]`
in one reply is a normal thing for the model to send. Through the pool
the screenshot could come before the click. The computer tools join
`SERIAL`, so such a batch runs in the model's order on the calling
thread.

## Run it

Install the optional group and start the harness. Bash:

```bash
pip install -e ".[computer]"
MODEL=openai/gpt-4o-mini harness
```

PowerShell:

```powershell
pip install -e ".[computer]"
$env:MODEL = "openai/gpt-4o-mini"; harness
```

The default `MODEL` (`deepseek/deepseek-v4-flash`) does not take images;
pick one that does. Then:

```text
> take a screenshot and tell me what is open
```

The tool panel shows the note, `Screenshot saved to ... (1280x720, scaled
down from 2560x1440)`, and the next model call carries the picture. The
model describes the screen. Ask it to act:

```text
> open the start menu and type notepad
```

Each `computer_act` stops at an `allow? (y/n)` prompt naming the action and
the coordinates. After every act the model takes a new screenshot to check
the result. Set `COMPUTER_AUTO=1` to skip the prompts.

The screenshots stay under `~/.simple-harness/shots/`. Delete the
directory when you are done; nothing else reads it.

Run the offline tests from the repository root. They replace the screen
with a small image and `pyautogui` with a recorder, so nothing moves:

```bash
python run_tests.py 24
```

### Expected output

```text
> open the start menu and type notepad

  ┌─────────────────────────────────────────────────────────────────┐
  │ computer_screen {}                                              │
  │ Screen size: 2560x1440 pixels. (0, 0) is the top left corner.   │
  │ Screenshots are shown at most 1280 wide; give coordinates as    │
  │ you see them in the picture.                                    │
  └─────────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────────┐
  │ computer_screenshot {}                                          │
  │ Screenshot saved to C:\Users\you\.simple-harness\shots\shot-... │
  │ (1280x720, scaled down from 2560x1440). Give coordinates as     │
  │ you see them in this picture.                                   │
  └─────────────────────────────────────────────────────────────────┘

  computer: click at (12, 708)
  allow? (y/n)> y

  ┌─────────────────────────────────────────────────────────────────┐
  │ computer_act {"action": "click", "x": 12, "y": 708}             │
  │ Done: click at (12, 708). Take a screenshot to see the result.  │
  └─────────────────────────────────────────────────────────────────┘
  ...
  computer: type 'notepad'
  allow? (y/n)> y

  agent

  The Start menu is open and "notepad" is typed into the search box; Notepad is the first result.
```

The click went to screen pixel `(24, 1416)`: the model's numbers times
`SCALE`.

## Error handling

- **A bad tool call.** `Error: the arguments of computer_act are not a
  JSON object: ...`, `Error: no tool named ...`, `Error: unknown action
  'teleport'. Use one of: ...`, `Error: click needs x and y.` Each is
  the call's result; the loop goes on.
- **No display, no library.** `Error: no screenshot library (...). pip
  install pillow`, `Error: could not capture the screen: ...`, `Error:
  pyautogui is not installed. pip install pyautogui`. A missing PNG at
  expansion time becomes a text user message saying so instead of a
  crash.
- **A text-only model.** The provider rejects the request with an
  `image_url` part. That is an `openai.BadRequestError`, which ends the
  turn with `model call failed: ...`; the transcript keeps the image
  message, and `strip()` reduces it to its caption at the end of the
  turn, so the next turn with a vision model - or `--resume` - works.
  Set `MODEL` before you start.
- **ctrl-c** during a batch of computer calls: they run serially, so the
  interrupt lands between two of them; the unrun ones get `(interrupted
  before this tool ran)` and the prompt returns. The mouse stays where
  it was.
- **The fail-safe.** Move the mouse into a screen corner while an action
  runs: `pyautogui` raises, and the tool returns `Error: click failed:
  PyAutoGUI fail-safe triggered ...`.
- **Leaving.** `/exit`, `/quit`, ctrl-d, or ctrl-z then enter on
  Windows.

## Gotchas / What this is not

- **A screenshot leaves the machine.** It captures the whole desktop -
  other windows, notifications, a password manager - and sends it to the
  model provider as part of the request. `computer_screenshot` is rated
  `allow`. Close what should not be seen before you ask.
- **The scale is per screenshot.** `SCALE` is what the last
  `computer_screenshot` set. A click before any screenshot uses `1.0`.
  Tested with a 2560x1440 fake screen in `test_step.py`; on a real
  high-DPI Windows display verify the first click with `COMPUTER_AUTO`
  unset, so you see the coordinates before they happen.
- **`type` is ASCII only.** `pyautogui.write()` skips characters it
  cannot type from the keyboard layout; accented letters and emoji are
  dropped silently. Paste from the clipboard is not implemented.
- **`scroll` puts the amount in `text`.** Negative scrolls down; a
  non-numeric `text` is `Error: ValueError: ...`.
- **Multiple monitors** are captured as one wide image by Pillow on
  Windows only with `all_screens=True`, which this code does not pass:
  you get the primary screen.
- **The `task` subagent cannot see or touch the screen** (`WITHHELD`).
  The browse subagent gets `browser_screenshot` with the marker, nothing
  else.
- **No sandbox for the desktop, and `bash` is still `cmd.exe` on
  Windows.** `COMPUTER_AUTO=1` is a decision to trust the model with the
  mouse.
- **Not accessibility-tree based.** Only pixels and coordinates. A model
  that misreads a small button misses it; look, act, look is the whole
  method.

## What to notice

- The model needs vision. Set `MODEL` to one that takes images; the
  default does not.
- A tool result is a string, so the picture travels beside it, in a user
  message. The marker is the only contract between a tool and the loop.
  Any tool can use it - `browser_screenshot` does - and nothing in the
  loop knows about `computer.py`.
- Look, act, look. The prompt tells the model to take a screenshot after
  every action, because the action result cannot say whether it worked.
  Expect three tool calls per step.
- The picture and the coordinates share one space, the 1280-wide
  picture. The model never has to know the real screen size; `SCALE`
  does the translation at the last moment, on the way to `pyautogui`.
- Old pictures are stripped to a caption at the end of the turn, exactly
  when old tool output is stripped to a stub. The context stays small and
  the cached prefix survives, for the same reason as in step 14.

## Files

```text
step_24_computer_use/
├── harness/
│   ├── computer.py    computer_screen, computer_screenshot (shrunk to 1280 wide), computer_act (scaled back)
│   ├── agent.py       an [[image:PATH]] marker in a result becomes an image message
│   ├── subagent.py    the subagent loop shows pictures too; task is not given the screen
│   ├── tools.py       the registry gains the computer; the computer tools are SERIAL
│   ├── permissions.py allow / ask / deny rules, now including the computer
│   ├── llm.py         streams; the system prompt says how to use the screen
│   ├── history.py     keeps the transcript small, pictures included
│   ├── compact.py     the compaction agent reads an image message by its caption
│   ├── ui.py          replay draws an image message by its caption; streaming as in 21
│   ├── browser.py     six browser tools from step 23; browser_screenshot returns the marker
│   ├── browse.py      the browse subagent from step 23
│   ├── commands.py    slash commands: /rewind /sessions /compact /exit
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py     the late injection block, unchanged since stage 10
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash
│   ├── session.py     append-only JSONL session log; load() repairs a cut-off turn
│   ├── skills.py      skills, unchanged since stage 9
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests; ImageGrab and pyautogui are replaced by fakes
├── pyproject.toml     package metadata; version 0.24.0; optional group `computer`
└── README.md          this file
```

## Diff from step 23

```bash
diff -r ../step_23_browser_use/harness harness
```

Added: `computer.py`. Changed: `history.py` (`IMAGE`, `IMAGE_TOKENS`,
`split_images`, `image_message`, `caption_of`, image-aware `strip` and
`estimate`), `agent.py` and `subagent.py` (marker expansion after the
results; the computer tools withheld from `task`), `tools.py` (three
computer tools in `TOOLS` and `TOOL_SCHEMAS`, and in `SERIAL`),
`permissions.py` (`computer_auto`, the `computer_act` rule), `llm.py`
(system prompt), `browser.py` (`browser_screenshot` returns the marker),
`ui.py` and `compact.py` (an image message is shown by its caption).
`pyproject.toml` gains the `computer` optional group.

## What the next step adds

Step 25 gives the agent a memory that outlives the session: `remember`,
`recall` and `forget` over markdown files, an index in the late block,
and a handoff note saved at every compaction.

<!-- harness-learning-check -->
## Check your understanding

Why inspect the screen again after an action changes a window?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

Coordinates and visible state may have changed. The next action needs current evidence rather than an old screenshot assumption.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
