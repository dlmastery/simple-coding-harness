"""Terminal presentation. Knows nothing about models or tools.

It receives strings and dicts and decides how they look. Keeping it in one
module means the agent loop stays readable and the look can change without
touching the logic.
"""

import json
from contextlib import contextmanager

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

ACCENT = "#7aa2f7"
USER = "#9ece6a"
TOOL = "#e0af68"
MUTED = "#565f89"

MAX_TOOL_LINES = 12  # what you see; the model still gets the whole result


class UI:
    def __init__(self):
        self.console = Console()
        self.totals = {}

    # --- input -------------------------------------------------------------

    def banner(self):
        self.console.print()
        self.console.print(Rule(Text(" simple coding harness ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(Text("ctrl-d or an empty line to exit", style=MUTED), (0, 0, 0, 2)))

    def ask(self):
        self.console.print()
        try:
            return input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""

    def pick(self, title, rows):
        """Numbered list; returns the chosen index or None."""
        self.console.print(Padding(Text(title, style=f"bold {ACCENT}"), (1, 0, 0, 2)))
        for i, row in enumerate(rows):
            self.console.print(Padding(Text(f"{i:>3}  {row}", style=MUTED), (0, 0, 0, 2)))
        try:
            answer = input("  number> ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        return int(answer) if answer.isdigit() and int(answer) < len(rows) else None

    def clear(self):
        self.console.clear()

    def resumed(self, messages, label="resumed"):
        turns = sum(1 for m in messages if m["role"] == "user")
        self.console.print(
            Padding(Text(f"{label} · {len(messages)} messages · {turns} turns", style=MUTED), (0, 0, 0, 2))
        )

    def replay(self, messages):
        """Redraw a loaded transcript so the screen matches the history."""
        results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
        for message in messages:
            if message["role"] == "user":
                self.user(message["content"])
            elif message["role"] == "assistant":
                if message.get("content"):
                    self.agent(message["content"])
                for call in message.get("tool_calls") or []:
                    self.tool(
                        call["function"]["name"],
                        json.loads(call["function"]["arguments"]),
                        results.get(call["id"], ""),
                    )

    # --- output ------------------------------------------------------------

    def user(self, text):
        self.console.print(Padding(Text(text.strip(), style=f"bold {USER}"), (1, 0, 0, 2)))

    def agent(self, text):
        self.console.print(
            Padding(
                Group(Text("agent", style=f"bold {ACCENT}"), Padding(Markdown(text.strip()), (1, 0, 0, 0))),
                (1, 2, 0, 2),
            )
        )

    def tool(self, name, args, result):
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._args(args), MUTED))
        self.console.print(
            Padding(
                Panel(Group(header, Rule(style=MUTED), self._result(result)), border_style=MUTED, padding=(0, 1)),
                (1, 2, 0, 2),
            )
        )

    def note(self, text):
        self.console.print(Padding(Text(text, style=MUTED), (1, 0, 0, 2)))

    def injection(self, text):
        """The late block. Shown dimmed so you can see what the model sees."""
        self.console.print(
            Padding(
                Panel(
                    Text(text.strip(), style=MUTED),
                    title=Text("late injection", style=f"italic {MUTED}"),
                    title_align="left",
                    border_style=MUTED,
                    padding=(0, 1),
                ),
                (1, 2, 0, 2),
            )
        )

    @contextmanager
    def working(self, label="thinking"):
        with self.console.status(Text(label, style=MUTED), spinner="dots", spinner_style=ACCENT):
            yield

    # --- usage -------------------------------------------------------------

    def usage(self, stats):
        for key, value in stats.items():
            self.totals[key] = self.totals.get(key, 0) + (value or 0)
        line = " · ".join(f"{v:,} {k.replace('_tokens', '')}" for k, v in stats.items() if v)
        self.console.print(Padding(Text(line, style=MUTED), (1, 0, 0, 2)))

    def summary(self):
        if not self.totals:
            return
        table = Table.grid(padding=(0, 2))
        table.add_column(style=MUTED)
        table.add_column(style=f"bold {ACCENT}", justify="right")
        for key, value in self.totals.items():
            table.add_row(key.replace("_", " "), f"{value:,}")
        self.console.print(Padding(table, (1, 2)))
        self.console.print(Rule(style=MUTED))

    # --- helpers -----------------------------------------------------------

    def _args(self, args):
        if len(args) == 1:
            return str(next(iter(args.values())))
        return json.dumps(args)

    def _result(self, result):
        lines = result.strip().splitlines() or ["(no output)"]
        body = Text("\n".join(lines[:MAX_TOOL_LINES]), style=MUTED)
        hidden = len(lines) - MAX_TOOL_LINES
        if hidden > 0:
            body.append(f"\n… {hidden} more lines", style=f"italic {TOOL}")
        return body


ui = UI()
