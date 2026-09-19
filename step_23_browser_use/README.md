# Step 23 - Browser use

**What this step adds:** six browser tools that drive one Chromium page
through Playwright, a `browse` subagent that holds those tools, and a
permission rule for opening URLs. The main agent gets only `browse`. It
never sees a page dump. The tools run on one browser thread, in the
order the model asked, and every failure inside the browser comes back
as an `Error:` line.

## Why a browser, and what breaks without it

A coding agent that can only read files stops at the edge of the disk.
Documentation, issue trackers, package indexes and the app under test all
live in a browser. This step gives the harness a real one: headless
Chromium, opened on first use, alive until the session ends. Without it,
"check what the docs say about X" means the user copies a page into the
chat by hand, and "does the sign-up form still work" cannot be asked at
all.

A page is a bad thing to put in the main context. The visible text of one
documentation page is often ten thousand characters. A task that reads
five pages fills a large part of the window with text the model needed
once. So the browser tools go to a subagent, built exactly like the
exploration subagent from step 15. The main agent sends a task in one
sentence and gets back a report under two hundred words. Every page the
subagent read stays in the subagent's transcript, which is thrown away at
the return. This is the same reason `task` exists: the search costs one
answer instead of dozens of tool results.

## The code, piece by piece

### 1. One page, one thread

`harness/browser.py`:

```python
def on_worker(fn, *args):
    """Run fn on the browser thread and wait for its result."""
    global _worker
    with _worker_lock:
        if _worker is None:
            _worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="browser")
    return _worker.submit(fn, *args).result()


def dead():
    """True when the window was closed or the browser process is gone."""
    try:
        return _page.is_closed() or not _browser.is_connected()
    except Exception:  # noqa: BLE001 - even asking failed: treat it as dead
        return True


def page():
    """The page, launched on first use - or again, after the window was closed or the browser died.

    Only ever called on the browser thread.
    """
    global _playwright, _browser, _page
    if _page is not None and dead():
        try:
            _forget()
        except Exception:  # noqa: BLE001 - it is already gone; start over anyway
            pass
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
```

Playwright is imported inside `page()`. The harness and its tests import
without it. The page is created on the first tool call and reused by
every later one, so a login state or a scroll position survives from one
call to the next. `BROWSER_HEADLESS=0` shows the window. If that window
is closed by hand, or Chromium crashes, `dead()` notices on the next
call and `page()` launches a fresh one instead of handing out a dead
handle forever.

Playwright's sync API belongs to the thread that started it. A call from
any other thread fails with a greenlet error. Step 22 runs the tool calls
of one reply from a thread pool, so a browser tool may arrive on any
thread. The module keeps one worker thread of its own, created under a
lock so two first calls cannot start two, and sends every call there.

### 2. Errors are results

`harness/browser.py`:

```python
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
```

Every tool is wrapped this way. A selector that never appears, a host
that does not resolve, a missing Playwright install: each comes back as
one line starting with `Error:`. The model reads it and tries another
way. Playwright's own messages run to many lines with a call log, so only
the first line crosses.

### 3. The tools

`harness/browser.py`:

```python
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
```

`browser_click` accepts either a CSS selector or visible text. It tries
the selector first. When nothing matches, or the selector engine rejects
the string, it falls back to `get_by_text`. The model can say "Sign up"
without knowing the markup. `browser_open` navigates and reports the
final URL and title. `browser_type` fills a field and presses Enter when
`submit` is set. `browser_screenshot` saves a PNG and refuses any path
outside the project; **the model never sees that PNG** - it is a file
for the user, and the tool description says so. Step 24 adds the image
path. `browser_close` drops the page; the next call starts a fresh one.

```python
@tool
def browser_read() -> str:
    """The page's title, URL and visible text, capped like any tool output."""
    current = page()
    lines = (line.strip() for line in current.inner_text("body").splitlines())
    text = "\n".join(line for line in lines if line)  # visible text, blank lines dropped
    return history.cap(f"Title: {current.title()}\nURL: {current.url}\n\n{text}")
```

`inner_text` returns what a person sees: no scripts, no hidden nodes.
Blank lines and indentation go. The result passes through `history.cap`,
so a long page is cut at ten thousand characters and spilled to a temp
file, like any other tool output.

`harness/browser.py`:

```python
def _forget():
    """Drop the handles, whatever state they are in. Runs on the browser thread."""
    global _playwright, _browser, _page
    try:
        if _browser is not None:
            _browser.close()
        if _playwright is not None:
            _playwright.stop()
    finally:
        _playwright = _browser = _page = None  # even when close() raised: never keep a dead page


def browser_close() -> str:
    """Close the browser. The next browser tool call starts a fresh one."""
    if _page is None:
        return "No browser was open."  # without touching the browser thread, which may not exist
    return tool(_close)()
```

`browser_close` is the one tool that must work when the browser is
already broken. The handles are dropped in a `finally`, so a `close()`
that raises still leaves the module clean, and the answer is the error
line. When nothing was ever opened it answers without starting the
worker thread, which is what `main()` relies on at exit.

### 4. The browse subagent

`harness/browse.py`:

```python
MAX_TURNS = 20  # a page visit takes more steps than a grep
...
def toolset():
    """The browser tool schemas plus read_file, nothing else."""
    from .browser import SCHEMAS
    from .tools import TOOL_SCHEMAS

    return [s for s in SCHEMAS + TOOL_SCHEMAS if s["function"]["name"] in TOOLS]


def browse(task: str) -> str:
    """Run a browser subagent on one task and return only its report."""
    from .subagent import loop  # here, not at the top: tools imports us, subagent imports tools

    return loop(SYSTEM_PROMPT, task, toolset(), MAX_TURNS, label="subagent browsing")
```

The loop from step 15 moves into `subagent.loop()`, which takes a system
prompt, a request, a tool set and a turn cap. `task` calls it with the
exploration prompt and twelve turns. `browse` calls it with the browser
prompt and twenty turns, because opening, reading and clicking take more
steps than a grep. The tool set is the six browser tools plus
`read_file`. No `bash`, no edits, no `task`, no `browse`: one subagent
deep, and a page can never talk the subagent into running a command.
`loop()` passes the names it offered as `allowed` to `execute_all`, so
naming `bash` in a tool call gets `Blocked by policy: bash is not
available to this agent`, not a shell.

The system prompt sets the rules: open, read, act, read again; prefer
visible text for clicks; treat `Error:` as information; never enter
credentials or personal data; report under 200 words.

### 5. What the main agent is offered, and what runs in order

`harness/tools.py`:

```python
TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "read_skill": read_skill,
    "write_todos": write_todos,
    "task": task,
    "browse": browse,
    **browser.TOOLS,  # runnable, but offered only to the browse subagent
}
```

`TOOLS` is what can run. `TOOL_SCHEMAS` is what the main agent is
offered. The browser tools are in the first and not the second. The
browse subagent builds its own schema list from `browser.SCHEMAS`, and
`execute_all` finds the function in `TOOLS` like any other. The main
agent sees one new schema, `browse`. `subagent.WITHHELD` gains `browse`,
so the exploration subagent cannot start a browser either.

`harness/tools.py`:

```python
# Tools whose order matters, or that talk to the user themselves: a reply
# that holds one of these runs sequentially, on the calling thread. The
# browser is one page: open must finish before read.
SERIAL = {"task", "browse", *browser.TOOLS}
```

The browser tools are strictly ordered: open, then read, then click. A
reply of `[browser_open, browser_read]` through the step 22 pool would
reach the browser thread in whichever order two workers got there, and
the read could see `about:blank`. So every browser tool, and `browse`
itself, is in `SERIAL`: a batch that holds one runs one call after
another on the calling thread, in the model's order.

### 6. Opening a URL asks

`harness/permissions.py`:

```python
BROWSER_ALLOW = {host.strip().lower() for host in os.environ.get("BROWSER_ALLOW", "").split(",") if host.strip()}
...
    if name == "browser_open":
        url = args.get("url", "")
        if not url:
            return "deny", f"{name}: missing argument 'url'"
        host = (urlparse(url).hostname or "").lower()
        if host in BROWSER_ALLOW:
            return "allow", None
        return "ask", f"open in the browser: {url}"
```

`browser_open` asks unless the URL's host is on the allow list. The
other browser tools allow: the question was answered when the page
opened. `BROWSER_ALLOW=docs.python.org,pypi.org` lets the subagent read
those sites without a prompt. The list is empty by default. The prompt
appears on the main thread before anything runs, in order, because
`execute_all` decides every call first. A call with no `url` at all is
denied with a message, not a `KeyError`.

## Run it

Bash:

```bash
pip install -e ".[browser]" && playwright install chromium
harness
```

PowerShell:

```powershell
pip install -e ".[browser]"; playwright install chromium
harness
```

Then:

```text
> use the browser to read https://docs.python.org/3/library/pathlib.html and tell me what Path.resolve does
```

The main agent calls `browse` with a task. A blue panel shows the task.
The prompt `open in the browser: https://docs.python.org/...` appears;
answer `y`. The subagent's `browser_open` and `browser_read` calls print
indented beneath the panel. The `browser_read` result is the page text,
cut at ten thousand characters. Then the subagent's report prints, and
the main agent answers from it. Set `BROWSER_ALLOW=docs.python.org` to
skip the prompt, or `BROWSER_HEADLESS=0` to watch the window.

Tests, from the repository root:

```bash
python run_tests.py 23
```

Or from this directory, with the live test that launches Chromium once:

```bash
HARNESS_LIVE_BROWSER=1 python -m pytest -q test_step.py
```

```powershell
$env:HARNESS_LIVE_BROWSER = "1"; python -m pytest -q test_step.py
```

### Expected output

```text
> use the browser to read https://docs.python.org/3/library/pathlib.html and tell me what Path.resolve does

  ┌─ subagent · own context ──────────────────────────────────────────┐
  │ Open https://docs.python.org/3/library/pathlib.html and report     │
  │ what Path.resolve() does.                                          │
  └───────────────────────────────────────────────────────────────────┘

  open in the browser: https://docs.python.org/3/library/pathlib.html
  allow? (y/n)> y

      ┌──────────────────────────────────────────────────────────────┐
      │ browser_open {"url": "https://docs.python.org/3/library/..."} │
      │ Opened https://docs.python.org/3/library/pathlib.html - title: │
      │ pathlib — Object-oriented filesystem paths                     │
      └──────────────────────────────────────────────────────────────┘
      ┌──────────────────────────────────────────────────────────────┐
      │ browser_read {}                                              │
      │ Title: pathlib — Object-oriented filesystem paths            │
      │ URL: https://docs.python.org/3/library/pathlib.html          │
      │ ...                                                          │
      │ [output capped: 31,204 of 41,204 chars cut. The whole ...    │
      └──────────────────────────────────────────────────────────────┘

  agent

  Path.resolve() makes the path absolute, resolving any symlinks ...
```

## Error handling

- **A bad tool call.** Same strings as step 22: `Error: the arguments of
  browser_open are not a JSON object: ...`, `Error: no tool named ...`,
  and `Blocked by policy: browser_open: missing argument 'url'`. Every
  call gets one tool message.
- **A failing browser action.** One `Error:` line - `Error: Timeout
  15000ms exceeded.`, `Error: net::ERR_NAME_NOT_RESOLVED at ...`,
  `Error: playwright is not installed: ...`. The subagent reads it and
  tries something else, or reports that it could not.
- **The browser died.** The window was closed under `BROWSER_HEADLESS=0`,
  or Chromium crashed: the next browser call relaunches. `browser_close`
  on a dead browser returns the error line and still resets, so nothing
  is stuck.
- **A dead model call** in the subagent propagates to the main loop like
  any other exception in a tool: `run()` turns it into `Error:
  APIConnectionError: Connection error.`, the `browse` call has a result,
  and the main agent's turn goes on. A dead call in the main loop ends the turn with
  `model call failed: ...`.
- **ctrl-c** during a browse: the subagent's loop is cut, the main turn
  answers its pending calls with `(interrupted before this tool ran)`,
  and the prompt returns. The browser stays open for the next call;
  `main()` closes it on exit.
- **Leaving.** `/exit`, `/quit`, ctrl-d, or ctrl-z then enter on
  Windows. `main()` closes the browser on the way out, whichever way it
  leaves.

## Gotchas / What this is not

- **The browser is a hole in the sandbox story.** `bash` runs with no
  network on macOS and Linux, but the browse subagent has `read_file`
  (any path on disk) and `browser_type(..., submit=True)`, which is
  `allow` once the page is open. A subagent talked into it by a page
  could paste a file into a form and submit it, and `browser_click` can
  navigate to any other host without asking again. The prompt forbids
  entering credentials; the code does not. Keep `BROWSER_ALLOW` short.
- **`browser_screenshot` is for you, not the model.** It writes a PNG
  inside the project and returns the path. Nothing shows the picture to
  the model in this step; step 24 does.
- **Ordering inside one reply is guaranteed only because of `SERIAL`.**
  A batch with a browser tool runs sequentially. That also means it
  runs with no parallelism at all: `[browser_read, read_file, read_file]`
  is three calls one after the other.
- **`BROWSER_HEADLESS=0` on Windows shows a window you should not
  close.** If you do, the next call relaunches a fresh page and the
  login state is gone.
- **`bash` is `cmd.exe` on Windows, with no sandbox**, as before. The
  browser itself is never sandboxed on any platform.
- **Playwright is optional.** The harness imports and runs without it;
  the first browser call returns `Error: playwright is not installed`.
  The tests use a fake page and never launch Chromium unless
  `HARNESS_LIVE_BROWSER=1`.
- **Not a scraper.** One page, `inner_text` only, no cookies persisted
  across sessions, no downloads.

## What to notice

- The main agent's transcript holds the task and the report. The page
  text, often ten thousand characters, lives and dies in the subagent.
- The offline tests never start a browser. A `FakePage` with the methods
  the tools use is patched in as `browser._page` and `browser.page()`.
  The tools run unchanged on top of it, and its `inner_text` returns
  nothing until a page was opened, so the ordering test means something.
- The tools return strings in every case. The subagent loop appends them
  as tool results, and the model reads `Error:` like any other output.
- Two browser calls in one reply never reach the pool from step 22.
  `SERIAL` sends the whole batch down the direct path, in order, and the
  browser thread does the rest.
- `browser_screenshot` keeps PNGs inside the project. `permissions.py`
  already had `inside_project` for edits; the browser reuses it.

## Files

```text
step_23_browser_use/
├── harness/
│   ├── browser.py     six browser tools: one Chromium page, one thread; relaunches after a crash
│   ├── browse.py      the browse subagent: fresh history, the browser tools, one report
│   ├── subagent.py    the subagent loop, shared by task and browse; runs only what it offered
│   ├── tools.py       the registry gains the browser; browse and browser_* are SERIAL
│   ├── permissions.py allow / ask / deny rules, now with a rule for opening URLs
│   ├── llm.py         streams; the system prompt says when to send the browser subagent
│   ├── agent.py       main() closes the browser on the way out; the turn loop is unchanged
│   ├── ui.py          streaming panels and headless() from step 21
│   ├── commands.py    slash commands: /rewind /sessions /compact /exit
│   ├── compact.py     the compaction agent from stage 14
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py     the late injection block, unchanged since stage 10
│   ├── history.py     keeps the transcript small: caps, strips and drops old tool output
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash
│   ├── session.py     append-only JSONL session log; load() repairs a cut-off turn
│   ├── skills.py      skills, unchanged since stage 9
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests with a fake page; Playwright is never launched
├── pyproject.toml     package metadata; version 0.23.0; optional group `browser`
└── README.md          this file
```

## Diff from step 22

```bash
diff -r ../step_22_parallel_tools/harness harness
```

New: `browser.py` (the tools), `browse.py` (the subagent). Changed:
`subagent.py` (the loop is `loop()`, `task` calls it, `browse` is
withheld), `tools.py` (`browse` offered, browser tools registered and
`SERIAL`), `permissions.py` (`BROWSER_ALLOW`, the `browser_open` rule),
`llm.py` (the system prompt says when to browse), `agent.py` (closes the
browser on exit), `pyproject.toml` (optional dependency group `browser`).

## What the next step adds

Step 24 lets a tool result carry a picture: `computer_screenshot` and
`browser_screenshot` return an `[[image:PATH]]` marker that the loop turns
into an image message, and `computer_act` clicks where the model points.
