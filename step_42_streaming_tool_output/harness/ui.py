"""Step 42 - a running tool has a panel of its own while it runs.
ToolStream holds the last STREAM_LINES lines of one call; ui.streaming()
opens one, tool_line() adds a line to it, and a rich Live redraws every
open panel as lines arrive from the reader threads. The panel is
transient: when the call ends it disappears, and ui.tool() prints the
finished panel with the capped result as before. One live display at a
time: a panel that opens while the spinner turns stops it, and a spinner
started while a panel is open shows nothing.
The rest is step 40: handoff() draws the "handoff -> name" line when the
conversation moves to another agent. The banner names /agent and /handoff.
The rest is step 36: pipeline() draws the summary table of a /pipeline run: one
row per step with its attempts and its verdict. The banner names the
command. The rest is step 35: the approve prompt takes four answers and returns the one
given: y, n, a (always, for this session) or never. question() prints a
question from the model with its numbered options, for the ask_user tool.
interrupted() says that Ctrl-C was seen and how to use the steer prompt.
The rest is step 32: the usage line carries the estimate, and context()
draws the breakdown /context asks for.
"""

import json
import sys
import threading
from collections import deque

from rich.console import Console, Group
from rich.errors import LiveError
from rich.json import JSON
from rich.live import Live
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from . import prompt
from .history import caption_of
from .todos import MARKS

ACCENT = "#7aa2f7"
USER = "#9ece6a"
TOOL = "#e0af68"
MUTED = "#565f89"

MAX_TOOL_OUTPUT_LINES = 12
STREAM_LINES = 8  # lines of live output a running tool's panel shows
REFRESH_PER_SECOND = 8  # how often the live display redraws the open panels, whatever the line rate

TODO_STYLES = {"completed": f"{MUTED} strike", "in_progress": f"bold {ACCENT}", "pending": MUTED}


class ToolStream:
    """The live view of one running tool call: its header and the last STREAM_LINES lines.

    Use it as a context manager around the call, and call it with each line
    as the line arrives. It is a callable so it can be handed straight to a
    Reader as on_line. The panel opens on enter and disappears on exit; the
    finished panel with the capped result is printed by ui.tool() as before.
    """

    def __init__(self, ui, name, args):
        self.ui = ui
        self.name = name
        self.args = args
        self.lines = deque(maxlen=STREAM_LINES)
        self.count = 0  # every line seen, including the ones that scrolled off

    def __call__(self, line):
        self.ui.tool_line(self, line)

    def __enter__(self):
        self.ui.stream_open(self)
        return self

    def __exit__(self, *exc):
        self.ui.stream_close(self)
        return False

    def render(self):
        """The panel: header, rule, the last lines, with a count of the ones above."""
        header = Text.assemble((f"{self.name} ", f"bold {TOOL}"), (self.ui._format_args(self.args), MUTED))
        body = Text()
        hidden = self.count - len(self.lines)
        if hidden > 0:
            body.append(f"… {hidden} earlier lines\n", style=f"italic {TOOL}")
        body.append("\n".join(self.lines) if self.lines else "(no output yet)", style=MUTED)
        title = Text(f"running · {self.count} lines", style=f"italic {MUTED}")
        return Padding(
            Panel(Group(header, Rule(style=MUTED), body), title=title, title_align="left", border_style=TOOL, padding=(0, 1)),
            (1, 2, 0, 2),
        )


class Spinner:
    """The spinner, made to step aside: a tool panel that opens while it turns stops it and takes the screen.

    The UI keeps the Spinner that is on in ui._spinner, so the first panel
    can stop it. stop() is safe to call twice: the owner calls it at the
    first delta or on exit, and a panel may have called it before.
    """

    def __init__(self, ui, status):
        self.ui = ui
        self.status = status
        self.on = False

    def __enter__(self):
        try:
            self.status.start()
            self.on = True
            self.ui._spinner = self
        except LiveError:
            pass  # a tool panel has the screen; it stands in for the spinner
        return self

    def __exit__(self, *exc):
        self.stop()
        return False

    def stop(self):
        if self.on:
            self.on = False
            self.status.stop()
        if self.ui._spinner is self:
            self.ui._spinner = None


class UI:
    def __init__(self):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        self.console = Console()
        self.live = True  # False in headless mode: no streamed text, panels on stderr
        self._totals = {}
        self._streams = []                      # ToolStream objects on screen, in open order
        self._streams_lock = threading.RLock()  # lines arrive from reader threads
        self._live = None                       # the rich Live that draws them, while any is open
        self._spinner = None                    # the Spinner that is on, so a panel can take the screen from it

    def headless(self):
        """Print mode: progress goes to stderr, so stdout carries only the answer."""
        self.console = Console(stderr=True)
        self.live = False

    # ---------------------------------------------------------------- input

    def banner(self, sandbox_name="none", mode="act"):
        self.console.print()
        self.console.print(Rule(Text(" coding agent ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(Text(f"mode: {mode}  ·  sandbox: {sandbox_name}  ·  /mode  /plan  /act  /agent  /handoff  /init  /sessions  /rewind  /undo  /pipeline  ·  alt-enter for a newline  ·  ctrl-c to steer  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave", style=MUTED), (0, 0, 0, 2)))

    def clear(self):
        self.console.clear()

    def resumed(self, messages, label="resumed"):
        turns = sum(1 for m in messages if m["role"] == "user")
        self.console.print(Padding(Text(f"{label} · {len(messages)} messages · {turns} turns", style=MUTED), (0, 0, 0, 2)))

    def replay(self, messages):
        """Redraw a loaded transcript so the screen matches the history."""
        results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
        for message in messages:
            if message["role"] == "user":
                content = message["content"]
                self.user(caption_of(content) if isinstance(content, list) else content)
            elif message["role"] == "assistant":
                if message.get("content"):
                    self.agent(message["content"])
                for call in message.get("tool_calls") or []:
                    self.tool(call["function"]["name"], parse_args(call["function"].get("arguments")), results.get(call["id"], ""))

    def pick(self, title, rows):
        """Numbered list; returns the chosen index or None."""
        self.console.print(Padding(Text(title, style=f"bold {ACCENT}"), (1, 0, 0, 2)))
        for i, row in enumerate(rows):
            self.console.print(Padding(Text(f"{i:>3}  {row}", style=MUTED), (0, 0, 0, 2)))
        try:
            answer = prompt.read("  number> ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        return int(answer) if answer.isdigit() and int(answer) < len(rows) else None

    ANSWERS = {"y": "y", "yes": "y", "n": "n", "no": "n", "a": "a", "always": "a", "never": "never"}

    def approve(self, reason):
        """Stage 11, extended in step 35: stop and ask before a tool call the rules rate as 'ask'.

        Returns "y", "n", "a" or "never". Anything else typed, and Ctrl-C or
        Ctrl-D, is "n": the safe answer is the default.
        """
        self.console.print(Padding(Text(reason, style=f"bold {TOOL}"), (1, 0, 0, 2)))
        try:
            answer = prompt.read("  allow? (y/n/a=always/never)> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "n"
        return self.ANSWERS.get(answer, "n")

    def question(self, question, options=()):
        """Step 35: a question from the model, with its options numbered from 1."""
        self.console.print(Padding(Text(question, style=f"bold {ACCENT}"), (1, 0, 0, 2)))
        for i, option in enumerate(options, 1):
            self.console.print(Padding(Text(f"{i:>3}  {option}", style=MUTED), (0, 0, 0, 2)))
        if options:
            self.console.print(Padding(Text("a number picks an option; anything else is your answer", style=MUTED), (0, 0, 0, 2)))

    def interrupted(self, where):
        """Step 35: Ctrl-C was pressed during `where`; explain the steer prompt."""
        self.console.print()
        self.console.print(Padding(Text(f"interrupted {where}. Type a message to steer, press enter to go on, or ctrl-c again to exit", style=f"bold {TOOL}"), (0, 0, 0, 2)))

    def approve_plan(self):
        """Step 28: the plan is on screen; ask for a yes, or a no with feedback.

        Returns (approved, feedback). Feedback is empty on yes, and on a no
        it is whatever the user typed at the second prompt.
        """
        try:
            answer = prompt.read("  approve? (y/n)> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False, ""
        if answer.lower().startswith("y"):
            return True, ""
        try:
            return False, prompt.read("  feedback> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False, ""

    def confirm(self, reason):
        """Step 31: say what a command is about to do and ask approve? (y/n)."""
        self.console.print(Padding(Text(reason, style=f"bold {TOOL}"), (1, 0, 0, 2)))
        try:
            answer = prompt.read("  approve? (y/n)> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.lower().startswith("y")

    def ask(self):
        """The next line from the user: None when they want out (ctrl-d, ctrl-c), "" for an empty line."""
        self.console.print()
        try:
            return prompt.read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return None

    # --------------------------------------------------------------- output

    def user(self, text):
        self.console.print(Padding(Text(text.strip(), style=f"bold {USER}"), (1, 0, 0, 2)))

    def agent(self, text):
        """A finished reply, rendered as markdown. Used for replay."""
        self.console.print(
            Padding(Group(Text("agent", style=f"bold {ACCENT}"), Padding(Markdown(text.strip()), (1, 0, 0, 0))), (1, 2, 0, 2))
        )

    # ------------------------------------------------------------ streaming

    def stream_start(self):
        """The header, printed once, when the first piece of text arrives."""
        if not self.live:
            return
        self.console.print(Padding(Text("agent", style=f"bold {ACCENT}"), (1, 0, 1, 2)))

    def stream_delta(self, text):
        """One piece of text, written raw and flushed. No markdown: it is not finished yet."""
        if not self.live:
            return
        self.console.out(text, end="", highlight=False)
        self.console.file.flush()

    def stream_end(self):
        """The reply is complete: end the line."""
        if not self.live:
            return
        self.console.out("")

    def tool(self, name, args, result, nested=False, tag=None):
        """One tool call and its result. tag names the subagent, when several run at once."""
        result = result if isinstance(result, str) else str(result)
        args = args if isinstance(args, dict) else {"args": args}
        if name == "write_todos" and isinstance(args.get("todos"), list) and not result.startswith("Error"):
            return self.todos(args["todos"])
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
        title = Text(f"subagent {tag}", style=f"italic {MUTED}") if tag is not None else None
        self.console.print(
            Padding(Panel(Group(header, Rule(style=MUTED), self._format_result(result)), title=title, title_align="left", border_style=MUTED, padding=(0, 1)), (1, 2, 0, 6 if nested else 2))
        )

    def handoff(self, previous, name, reason=""):
        """Step 40: the conversation moved from one agent to another."""
        line = Text.assemble((f"handoff -> {name}", f"bold {ACCENT}"), (f"  (from {previous}" + (f": {reason}" if reason else "") + ")", MUTED))
        self.console.print(Padding(line, (1, 0, 0, 2)))

    def subagent(self, description, tag=None):
        """Shown to you, never to the main agent - it only gets the report."""
        who = f"subagent {tag}" if tag is not None else "subagent"
        self.console.print(
            Padding(Panel(Text(description.strip(), style=MUTED), title=Text(f"{who} · own context", style=f"bold {ACCENT}"), title_align="left", border_style=ACCENT, padding=(0, 1)), (1, 2, 0, 4))
        )

    def todos(self, todos):
        """The plan as a checklist. The raw tool output is never worth showing."""
        todos = [t for t in todos if isinstance(t, dict)]
        done = sum(1 for t in todos if t.get("status") == "completed")
        rows = Table.grid(padding=(0, 1))
        rows.add_column(no_wrap=True)
        rows.add_column(overflow="fold")
        for todo in todos:
            style = TODO_STYLES.get(todo.get("status"), MUTED)
            rows.add_row(Text(MARKS.get(todo.get("status"), "[?]"), style=style), Text(str(todo.get("content", "")), style=style))
        self.console.print(
            Padding(Panel(rows, title=Text(f"todos {done}/{len(todos)}", style=f"bold {TOOL}"), title_align="left", border_style=MUTED, padding=(0, 1)), (1, 2, 0, 2))
        )

    def plan(self, plan):
        """A submitted plan: goal, numbered steps with files and actions, risks."""
        body = Table.grid(padding=(0, 1))
        body.add_column(no_wrap=True)
        body.add_column(overflow="fold")
        body.add_row(Text("goal", style=f"bold {ACCENT}"), Text(plan["goal"], style=f"bold {ACCENT}"))
        for i, step in enumerate(plan["steps"], 1):
            body.add_row(Text(f"{i}.", style=f"bold {TOOL}"), Text(step["title"], style=f"bold {TOOL}"))
            if step["files"]:
                body.add_row("", Text("files: " + ", ".join(step["files"]), style=MUTED))
            for action in step["actions"]:
                body.add_row("", Text(f"- {action}", style=MUTED))
        for i, risk in enumerate(plan["risks"]):
            body.add_row(Text("risk" if i == 0 else "", style=f"bold {USER}"), Text(risk, style=MUTED))
        self.console.print(
            Padding(Panel(body, title=Text("plan", style=f"bold {ACCENT}"), title_align="left", border_style=ACCENT, padding=(0, 1)), (1, 2, 0, 2))
        )

    def compacted(self, before, messages):
        """Show the handoff note compaction folded into the system prompt."""
        system = messages[0]["content"]
        body = system[system.find("<summary>"):].replace("<summary>", "").replace("</summary>", "")
        self.console.print(
            Padding(Panel(Markdown(body), title=Text(f"compacted · {before} → {len(messages)} messages", style=f"bold {TOOL}"), title_align="left", border_style=TOOL, padding=(0, 1)), (1, 2, 0, 2))
        )

    def note(self, text):
        self.console.print(Padding(Text(text, style=MUTED), (1, 0, 0, 2)))

    def injection(self, text):
        """The late block, dimmed, so you can see what the model sees."""
        self._panel(text.strip(), "late injection", MUTED)

    def debug(self, data):
        self.console.print(
            Padding(Panel(JSON.from_data(data), title=Text("raw response", style=f"italic {MUTED}"), title_align="left", border_style=TOOL, padding=(0, 1)), (1, 2, 0, 2))
        )

    def working(self, label="thinking"):
        """The spinner. Use it as a context manager; call .stop() to end it early.

        One live display at a time: a tool panel that opens while the
        spinner turns stops it, and a spinner started while a panel is
        open shows nothing. The panel stands in for it either way. Off the
        main thread (a subagent in a pool) there is no spinner at all.
        """
        if threading.current_thread() is not threading.main_thread():
            return Quiet()
        return Spinner(self, self.console.status(Text(label, style=MUTED), spinner="dots", spinner_style=ACCENT))

    # ------------------------------------------------------- tool streaming

    def streaming(self, name, args):
        """A ToolStream for one call: `with ui.streaming("bash", args) as show:` then show(line) per line."""
        return ToolStream(self, name, args)

    def tool_line(self, stream, line):
        """One line of output from a running tool: it joins the stream's panel, which the live display redraws on its own clock."""
        with self._streams_lock:
            stream.lines.append(line)
            stream.count += 1

    def stream_open(self, stream):
        """Put a stream's panel on screen. The live display starts with the first one."""
        with self._streams_lock:
            self._streams.append(stream)
            self._redraw()
        return stream

    def stream_close(self, stream):
        """Take a stream's panel down. The live display stops with the last one."""
        with self._streams_lock:
            if stream in self._streams:
                self._streams.remove(stream)
            if not self._streams and self._live is not None:
                self._live.stop()
                self._live = None
            else:
                self._redraw()

    def _render_streams(self):
        with self._streams_lock:  # a reader thread may be appending
            return Group(*(stream.render() for stream in self._streams))

    def _redraw(self):
        """Start the live display when none is running and the screen is free, or refresh it now.

        The display pulls _render_streams itself, refresh_per_second times
        a second: a command that prints a million lines costs the screen
        eight redraws a second, not a million.
        """
        if not self.live or not self._streams:
            return
        if self._live is None:
            if self._spinner is not None:
                self._spinner.stop()  # the panel takes over from the spinner
            live = Live(get_renderable=self._render_streams, console=self.console, transient=True, refresh_per_second=REFRESH_PER_SECOND)
            try:
                live.start()
            except LiveError:
                return  # another live display has the screen for now; the next open or close tries again
            self._live = live
        self._live.refresh()

    # ---------------------------------------------------------------- usage

    def usage(self, stats, estimate=None, cost=None):
        """One line per model call. estimate is the harness's count of the prompt it sent; cost is its dollars."""
        stats = {k: v for k, v in (stats or {}).items() if k != "cost"}  # the API's own figure, when it sends one, is priced by stop and arrives as `cost`
        for key, value in stats.items():
            self._totals[key] = self._totals.get(key, 0) + (value or 0)
        parts = []
        for key, value in stats.items():
            if key == "prompt_tokens" and estimate is not None:
                parts.append(f"{value:,} prompt (estimate {estimate:,})" if value else f"estimate {estimate:,} prompt")
            elif value:
                parts.append(f"{value:,} {key.replace('_tokens', '')}")
        if cost is not None:
            self._totals["cost"] = self._totals.get("cost", 0.0) + cost
            parts.append(f"${cost:.4f}")
        self.console.print(Padding(Text(" · ".join(parts), style=MUTED), (1, 0, 0, 2)))

    def context(self, text):
        """The context budget: one bar per category, as budget.render draws it."""
        self._panel(text, "context budget", TOOL)

    def summary(self):
        if not self._totals:
            return
        table = Table.grid(padding=(0, 2))
        table.add_column(style=MUTED)
        table.add_column(style=f"bold {ACCENT}", justify="right")
        for key, value in self._totals.items():
            table.add_row(key.replace("_", " "), f"${value:.4f}" if key == "cost" else f"{value:,}")
        self.console.print(Padding(table, (1, 2)))
        self.console.print(Rule(style=MUTED))
        self.console.print()

    # ----------------------------------------------------------------- eval

    def eval_table(self, report):
        """One row per task, then a totals row. Goes to stdout, headless or not."""
        table = Table(title=f"eval {report['suite']} · {report['model']}", title_style=f"bold {ACCENT}", border_style=MUTED, padding=(0, 1))
        table.add_column("task", style=f"bold {TOOL}", no_wrap=True)
        for column in ("pass", "time", "prompt", "compl", "cached", "cost"):
            table.add_column(column, justify="right", style=MUTED, no_wrap=True)
        table.add_column("answer", style=MUTED, overflow="fold", ratio=1)
        for row in report["tasks"] + [report["summary"]]:
            passed = row["passed"] == row["runs"]
            answer = (row["results"][-1]["answer"] if row.get("results") else "").strip().splitlines()
            table.add_row(
                row["name"],
                Text(f"{row['passed']}/{row['runs']}", style=f"bold {USER}" if passed else f"bold {TOOL}"),
                f"{row['seconds']:.1f}s",
                f"{row['prompt_tokens']:,}",
                f"{row['completion_tokens']:,}",
                f"{row['cached_tokens']:,}",
                "-" if row["cost"] is None else f"${row['cost']:.4f}",
                (answer[0][:60] if answer else "")
            )
        Console().print(Padding(table, (1, 2)))

    def pipeline(self, rows):
        """One row per plan step: number, title, attempts, verdict and the reviewer's notes."""
        table = Table(title="pipeline", title_style=f"bold {ACCENT}", border_style=MUTED, padding=(0, 1))
        table.add_column("step", justify="right", style=MUTED, no_wrap=True)
        table.add_column("title", style=f"bold {TOOL}", overflow="fold", ratio=1)
        table.add_column("tries", justify="right", style=MUTED, no_wrap=True)
        table.add_column("verdict", no_wrap=True)
        table.add_column("notes", style=MUTED, overflow="fold", ratio=2)
        for number, title, attempts, verdict, notes in rows:
            style = f"bold {USER}" if verdict == "PASS" else f"bold {TOOL}"
            table.add_row(str(number), title, str(attempts), Text(verdict, style=style), notes[:160])
        self.console.print(Padding(table, (1, 2)))

    # -------------------------------------------------------------- helpers

    def _panel(self, text, title, border):
        self.console.print(
            Padding(Panel(Text(text, style=MUTED), title=Text(title, style=f"italic {MUTED}"), title_align="left", border_style=border, padding=(0, 1)), (1, 2, 0, 2))
        )

    def _format_args(self, args):
        if len(args) == 1:
            return str(next(iter(args.values())))
        return json.dumps(args)

    def _format_result(self, result):
        lines = str(result).strip().splitlines() or ["(no output)"]
        shown = lines[:MAX_TOOL_OUTPUT_LINES]
        body = Text("\n".join(shown), style=MUTED)
        hidden = len(lines) - len(shown)
        if hidden > 0:
            body.append(f"\n… {hidden} more lines", style=f"italic {TOOL}")
        return body


class Quiet:
    """A spinner that draws nothing: what working() returns off the main thread."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def stop(self):
        pass


def parse_args(arguments):
    """The arguments of a logged tool call as a dict; the raw text under "raw" when they are not JSON."""
    try:
        args = json.loads(arguments or "{}")
    except (ValueError, TypeError):
        return {"raw": str(arguments)}
    return args if isinstance(args, dict) else {"raw": str(arguments)}


ui = UI()
