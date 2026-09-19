"""Step 29 - a nested panel can carry a tag: the number of the subagent
that produced it, when several run at once. tool() puts the tag in the
panel title and subagent() in the header, so the interleaved panels of
parallel subagents can be told apart. The rest is step 28.
"""

import json
import sys
import threading

from rich.console import Console, Group
from rich.json import JSON
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

TODO_STYLES = {"completed": f"{MUTED} strike", "in_progress": f"bold {ACCENT}", "pending": MUTED}

APPROVE_LOCK = threading.Lock()  # one approval question at a time, whichever thread asks


class Idle:
    """A spinner that does nothing: used off the main thread, where rich cannot draw one."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def stop(self):
        pass


class UI:
    def __init__(self):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        self.console = Console()
        self.live = True  # False in headless mode: no streamed text, panels on stderr
        self._totals = {}

    def headless(self):
        """Print mode: progress goes to stderr, so stdout carries only the answer."""
        self.console = Console(stderr=True)
        self.live = False

    # ---------------------------------------------------------------- input

    def banner(self, sandbox_name="none", mode="act"):
        self.console.print()
        self.console.print(Rule(Text(" coding agent ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(Text(f"mode: {mode}  ·  sandbox: {sandbox_name}  ·  /plan  /act  /sessions  /rewind  ·  alt-enter for a newline  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave", style=MUTED), (0, 0, 0, 2)))

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
                    raw = call["function"]["arguments"]
                    try:
                        args = json.loads(raw)
                    except ValueError:  # the model once sent broken JSON; show it as it was
                        args = {"arguments": raw}
                    self.tool(call["function"]["name"], args, results.get(call["id"], ""))

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

    def approve(self, reason):
        """Stage 11: stop and ask before a tool call the rules rate as 'ask'.

        In print mode nothing may reach stdout, and without a terminal there
        is nobody to ask: the call is denied and stderr says so.
        """
        with APPROVE_LOCK:
            if not self.live and not sys.stdin.isatty():
                self.note(f"denied, no terminal to ask on: {reason}")
                return False
            self.console.print(Padding(Text(reason, style=f"bold {TOOL}"), (1, 0, 0, 2)))
            try:
                if self.live:
                    answer = prompt.read("  allow? (y/n)> ").strip()
                else:
                    sys.stderr.write("  allow? (y/n)> ")
                    sys.stderr.flush()
                    answer = input().strip()
            except (EOFError, KeyboardInterrupt):
                return False
            return answer.lower().startswith("y")

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

    def ask(self):
        """The next message; "" for an empty line, None when the input is closed."""
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
        if name == "write_todos" and args.get("todos") and not result.startswith("Error"):
            return self.todos(args["todos"])
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
        title = Text(f"subagent {tag}", style=f"italic {MUTED}") if tag is not None else None
        self.console.print(
            Padding(Panel(Group(header, Rule(style=MUTED), self._format_result(result)), title=title, title_align="left", border_style=MUTED, padding=(0, 1)), (1, 2, 0, 6 if nested else 2))
        )

    def subagent(self, description, tag=None):
        """Shown to you, never to the main agent - it only gets the report."""
        who = f"subagent {tag}" if tag is not None else "subagent"
        self.console.print(
            Padding(Panel(Text(description.strip(), style=MUTED), title=Text(f"{who} · own context", style=f"bold {ACCENT}"), title_align="left", border_style=ACCENT, padding=(0, 1)), (1, 2, 0, 4))
        )

    def todos(self, todos):
        """The plan as a checklist. The raw tool output is never worth showing."""
        done = sum(1 for t in todos if t.get("status") == "completed")
        rows = Table.grid(padding=(0, 1))
        rows.add_column(no_wrap=True)
        rows.add_column(overflow="fold")
        for todo in todos:
            status = todo.get("status")
            style = TODO_STYLES.get(status, MUTED)
            rows.add_row(Text(MARKS.get(status, "[?]"), style=style), Text(str(todo.get("content", "")), style=style))
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

        Only the main thread gets one: a second live display from a worker
        thread is an error in rich, and a subagent may run on a worker.
        """
        if threading.current_thread() is not threading.main_thread():
            return Idle()
        return self.console.status(Text(label, style=MUTED), spinner="dots", spinner_style=ACCENT)

    # ---------------------------------------------------------------- usage

    def usage(self, stats):
        for key, value in stats.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._totals[key] = self._totals.get(key, 0) + value
        parts = []
        for key, value in stats.items():
            if key == "cost" and value is not None:
                parts.append(f"${value:.4f}")
            elif isinstance(value, (int, float)) and value:
                parts.append(f"{value:,} {key.replace('_tokens', '')}")
        self.console.print(Padding(Text(" · ".join(parts), style=MUTED), (1, 0, 0, 2)))

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


ui = UI()
