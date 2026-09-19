"""Stage 20 - usage() shows which model answered and what the call cost.
"""

import json
import sys
from contextlib import contextmanager

from rich.console import Console, Group
from rich.json import JSON
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from . import prompt
from .todos import MARKS

ACCENT = "#7aa2f7"
USER = "#9ece6a"
TOOL = "#e0af68"
MUTED = "#565f89"

MAX_TOOL_OUTPUT_LINES = 12

TODO_STYLES = {"completed": f"{MUTED} strike", "in_progress": f"bold {ACCENT}", "pending": MUTED}


class UI:
    def __init__(self):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        self.console = Console()
        self._totals = {}

    # ---------------------------------------------------------------- input

    def banner(self, sandbox_name="none"):
        self.console.print()
        self.console.print(Rule(Text(" coding agent ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(Text(f"sandbox: {sandbox_name}  ·  /sessions  /rewind  /models  /route  ·  alt-enter for a newline  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave", style=MUTED), (0, 0, 0, 2)))

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
                self.user(str(message.get("content") or ""))
            elif message["role"] == "assistant":
                if message.get("content"):
                    self.agent(message["content"])
                for call in message.get("tool_calls") or []:
                    self.tool(call["function"]["name"], self._parse_args(call["function"]["arguments"]), results.get(call["id"], ""))

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
        """Stage 11: stop and ask before a tool call the rules rate as 'ask'."""
        self.console.print(Padding(Text(reason, style=f"bold {TOOL}"), (1, 0, 0, 2)))
        try:
            answer = prompt.read("  allow? (y/n)> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.lower().startswith("y")

    def ask(self):
        """One line from the user; None when they are leaving (ctrl-d, ctrl-c)."""
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
        self.console.print(
            Padding(Group(Text("agent", style=f"bold {ACCENT}"), Padding(Markdown(text.strip()), (1, 0, 0, 0))), (1, 2, 0, 2))
        )

    def tool(self, name, args, result, nested=False):
        # the one place the UI knows a tool by name - and only when the plan was accepted
        if name == "write_todos" and args.get("todos") and not result.startswith("Error"):
            return self.todos(args["todos"])
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
        self.console.print(
            Padding(Panel(Group(header, Rule(style=MUTED), self._format_result(result)), border_style=MUTED, padding=(0, 1)), (1, 2, 0, 6 if nested else 2))
        )

    def subagent(self, description):
        """Shown to you, never to the main agent - it only gets the report."""
        self.console.print(
            Padding(Panel(Text(description.strip(), style=MUTED), title=Text("subagent · own context", style=f"bold {ACCENT}"), title_align="left", border_style=ACCENT, padding=(0, 1)), (1, 2, 0, 4))
        )

    def todos(self, todos):
        """The plan as a checklist. The raw tool output is never worth showing."""
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

    @contextmanager
    def working(self, label="thinking"):
        with self.console.status(Text(label, style=MUTED), spinner="dots", spinner_style=ACCENT):
            yield

    # ---------------------------------------------------------------- usage

    def usage(self, stats):
        """One muted line per call: tokens, then the model that answered, then its cost."""
        for key, value in stats.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._totals[key] = self._totals.get(key, 0) + value  # "model" is a string: not summed
        parts = [f"{value:,} {key.replace('_tokens', '')}" for key, value in stats.items() if key not in ("model", "cost") and value]
        if stats.get("model"):
            parts.append(str(stats["model"]))
        if stats.get("cost") is not None:
            parts.append(f"${stats['cost']:.4f}")
        self.console.print(Padding(Text(" · ".join(parts), style=MUTED), (1, 0, 0, 2)))

    def models(self, route, catalogue):
        """The route in use, then the cheapest models OpenRouter lists (prices per 1M tokens)."""
        self.console.print(Padding(Text(f"primary   {route[0]}", style=f"bold {ACCENT}"), (1, 0, 0, 2)))
        for fallback in route[1:]:
            self.console.print(Padding(Text(f"fallback  {fallback}", style=MUTED), (0, 0, 0, 2)))
        if not catalogue:
            return
        table = Table.grid(padding=(0, 2))
        table.add_column(style=MUTED)
        table.add_column(style=MUTED, justify="right")
        table.add_column(style=MUTED, justify="right")
        table.add_column(style=MUTED, justify="right")
        table.add_row("model", "context", "$/1M in", "$/1M out")
        for model_id, context, prompt_price, completion_price in catalogue:
            table.add_row(model_id, f"{context:,}" if context else "-", self._per_million(prompt_price), self._per_million(completion_price))
        self.console.print(Padding(table, (1, 2, 0, 2)))

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

    def _per_million(self, price_per_token):
        return f"{price_per_token * 1_000_000:.2f}" if price_per_token is not None else "-"

    def _parse_args(self, arguments):
        """Stored arguments may be broken JSON (a cut-off reply); show them raw then."""
        try:
            args = json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return {"raw": arguments}
        return args if isinstance(args, dict) else {"raw": arguments}

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
