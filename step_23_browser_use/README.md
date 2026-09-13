# Step 23 - Browser use

**What this step adds:** six browser tools that drive one Chromium page
through Playwright, a `browse` subagent that holds those tools, and a
permission rule for opening URLs. The main agent gets only `browse`. It
never sees a page dump.

## Why a browser, and why behind a subagent

A coding agent that can only read files stops at the edge of the disk.
Documentation, issue trackers, package indexes and the app under test all
live in a browser. This step gives the harness a real one: headless
Chromium, opened on first use, alive until the session ends.

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
    if _worker is None:
        _worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="browser")
    return _worker.submit(fn, *args).result()


def page():
    """The page, launched on first use. Only ever called on the browser thread."""
    global _playwright, _browser, _page
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
call to the next. `BROWSER_HEADLESS=0` shows the window.

Playwright's sync API belongs to the thread that started it. A call from
any other thread fails with a greenlet error. Step 22 runs the tool calls
of one reply from a thread pool, so a browser tool may arrive on any
thread. The module keeps one worker thread of its own and sends every
call there. Two browser calls in one reply run one after the other on
that thread, in the order the pool submits them.

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
outside the project. `browser_close` drops the page; the next call
starts a fresh one.

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

The system prompt sets the rules: open, read, act, read again; prefer
visible text for clicks; treat `Error:` as information; never enter
credentials or personal data; report under 200 words.

### 5. What the main agent is offered

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

### 6. Opening a URL asks

`harness/permissions.py`:

```python
BROWSER_ALLOW = {host.strip().lower() for host in os.environ.get("BROWSER_ALLOW", "").split(",") if host.strip()}
...
    if name == "browser_open":
        host = (urlparse(args["url"]).hostname or "").lower()
        if host in BROWSER_ALLOW:
            return "allow", None
        return "ask", f"open in the browser: {args['url']}"
```

`browser_open` asks unless the URL's host is on the allow list. The
other browser tools allow: the question was answered when the page
opened. `BROWSER_ALLOW=docs.python.org,pypi.org` lets the subagent read
those sites without a prompt. The list is empty by default. The prompt
appears on the main thread before anything runs, in order, because
`execute_all` decides every call first.

## Run it

```bash
pip install playwright && playwright install chromium
harness
> use the browser to read https://docs.python.org/3/library/pathlib.html and tell me what Path.resolve does
```

The main agent calls `browse` with a task. A blue panel shows the task.
The prompt `open in the browser: https://docs.python.org/...` appears;
answer `y`. The subagent's `browser_open` and `browser_read` calls print
indented beneath the panel. The `browser_read` result is the page text,
cut at ten thousand characters. Then the subagent's report prints, and
the main agent answers from it. Set `BROWSER_ALLOW=docs.python.org` to
skip the prompt, or `BROWSER_HEADLESS=0` to watch the window.

Tests:

```bash
python -m pytest -q test_step.py                          # offline, fake page
HARNESS_LIVE_BROWSER=1 python -m pytest -q test_step.py   # also launches Chromium once
```

## What to notice

- The main agent's transcript holds the task and the report. The page
  text, often ten thousand characters, lives and dies in the subagent.
- The offline tests never start a browser. A `FakePage` with the eight
  methods the tools use is patched in as `browser._page` and
  `browser.page()`. The tools run unchanged on top of it.
- The tools return strings in every case. The subagent loop appends them
  as tool results, and the model reads `Error:` like any other output.
- Two browser calls in one reply reach the pool from step 22, and the
  pool hands both to the one browser thread. Nothing in `execute_all`
  knows about the browser.
- `browser_screenshot` keeps PNGs inside the project. `permissions.py`
  already had `inside_project` for edits; the browser reuses it.

## Diff from step 22

```bash
diff -r ../step_22_parallel_tools/harness harness
```

New: `browser.py` (the tools), `browse.py` (the subagent). Changed:
`subagent.py` (the loop is `loop()`, `task` calls it, `browse` is
withheld), `tools.py` (`browse` offered, browser tools registered),
`permissions.py` (`BROWSER_ALLOW`, the `browser_open` rule), `llm.py`
(the system prompt says when to browse), `agent.py` (closes the browser
on exit), `pyproject.toml` (optional dependency group `browser`).
