"""Step 44 - trace: the session log as one HTML page, one row per model call.

calls() walks the events of replay.timeline() and builds a Call per
assistant message: its text, its tool calls with the results that came
back for them, the images those results produced, and the usage entry
that session.save wrote next to it: tokens, cost and the seconds the
call took. A call from a log without usage entries is priced from the
tokens it has, when it has any.

html() renders the calls as a table. The page is one file: the styles
and the script are inline, nothing is fetched. Every string from the log
goes through escape() before it reaches the page; an image is inlined
only when its data URL is a PNG or JPEG in base64.
"""

import html as html_
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import replay
from . import session
from . import stop
from .ui import ui

DATA_URL = re.compile(r"^data:image/(?:png|jpeg);base64,[A-Za-z0-9+/=\s]+$")  # the only images the page inlines
RESULT_CHARS = 20_000  # per tool result; the log has the rest


@dataclass
class Call:
    """One model call: the reply and everything it led to."""
    number: int
    turn: int                       # the user message this call answered
    ts: float | None = None
    content: str = ""
    tool_calls: list = field(default_factory=list)   # {"id", "name", "arguments", "result"}
    images: list = field(default_factory=list)       # (caption, data url)
    usage: dict = field(default_factory=dict)
    seconds: float | None = None
    cost: float | None = None


@dataclass
class Trace:
    """The calls of one session, with the turn prompts and the log markers between them."""
    session_id: str
    rows: list = field(default_factory=list)   # Call objects and ("user"|"note", text) tuples, in order
    calls: list = field(default_factory=list)  # the Call objects alone


def calls(events, session_id=""):
    """Group the events of a log into model calls. Returns a Trace."""
    trace = Trace(session_id)
    current = None
    turn = 0
    by_id = {}  # tool call id -> the dict in current.tool_calls waiting for a result
    for event in events:
        data = event.data
        if event.kind == "user":
            turn += 1
            trace.rows.append(("user", str(data.get("content") or "")))
        elif event.kind == "assistant":
            current = Call(len(trace.calls) + 1, turn, event.ts, data.get("content") or "")
            by_id = {}
            for call in data.get("tool_calls") or []:
                entry = {"id": call["id"], "name": call["function"]["name"], "arguments": call["function"]["arguments"] or "{}", "result": None}
                current.tool_calls.append(entry)
                by_id[call["id"]] = entry
            trace.calls.append(current)
            trace.rows.append(current)
        elif event.kind == "tool" and data.get("tool_call_id") in by_id:
            by_id[data["tool_call_id"]]["result"] = str(data.get("content") or "")
        elif event.kind == "image" and current is not None:
            for part in data["parts"]:
                url = (part.get("image_url") or {}).get("url", "") if part.get("type") == "image_url" else ""
                if DATA_URL.match(url):
                    current.images.append((data["caption"], url))
        elif event.kind == "usage" and current is not None:
            current.usage = data.get("usage") or {}
            current.seconds = data.get("seconds")
            current.cost = data.get("cost")
            if current.cost is None and any(current.usage.get(k) for k in ("prompt_tokens", "completion_tokens", "cost")):
                current.cost = stop.cost_of(current.usage)[0]
        elif event.kind == "rewind":
            trace.rows.append(("note", f"rewind to {data['count']} messages"))
        elif event.kind == "handoff":
            trace.rows.append(("note", f"handoff {data['previous']} -> {data['name']}"))
        elif event.kind == "compacted":
            trace.rows.append(("note", f"compacted to {data['count']} messages"))
    return trace


def escape(text):
    """Every string from the log passes through here before it reaches the page."""
    return html_.escape(str(text), quote=True)


def stamp(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else "-"


def number(value, digits=0):
    """A token count or a duration as text; a missing value is a dash."""
    if value is None:
        return "-"
    return f"{value:,.{digits}f}"


def dollars(value):
    return "-" if value is None else f"${value:.4f}"


def render_call(call):
    """One <tr> per model call: the numbers, then the reply with its tool calls folded away."""
    usage = call.usage
    cells = [
        f'<td class="n">{call.number}</td>',
        f'<td class="n">{escape(stamp(call.ts))}</td>',
        f'<td class="n">{escape(number(call.seconds, 1))}</td>',
        f'<td class="n">{escape(number(usage.get("prompt_tokens")))}</td>',
        f'<td class="n">{escape(number(usage.get("completion_tokens")))}</td>',
        f'<td class="n">{escape(number(usage.get("cached_tokens")))}</td>',
        f'<td class="n">{escape(dollars(call.cost))}</td>',
    ]
    body = []
    if call.content:
        body.append(f'<div class="reply">{escape(call.content)}</div>')
    for tool_call in call.tool_calls:
        result = tool_call["result"]
        shown = "(no result recorded)" if result is None else (result[:RESULT_CHARS] + ("\n[... trimmed]" if len(result) > RESULT_CHARS else "")) or "(no output)"
        body.append(
            "<details>"
            f'<summary><span class="tool">{escape(tool_call["name"])}</span> <span class="args">{escape(tool_call["arguments"])}</span></summary>'
            f'<pre class="result">{escape(shown)}</pre>'
            "</details>"
        )
    for caption, url in call.images:
        body.append(f'<figure><img src="{escape(url)}" alt="{escape(caption)}"><figcaption>{escape(caption)}</figcaption></figure>')
    cells.append(f'<td class="body">{"".join(body)}</td>')
    return f'<tr class="call">{"".join(cells)}</tr>'


def render_row(row):
    if isinstance(row, Call):
        return render_call(row)
    kind, text = row
    return f'<tr class="{escape(kind)}"><td colspan="8">{escape(text)}</td></tr>'


def totals(trace):
    """The last row: every token, every dollar, every second, summed."""
    def total(key):
        values = [c.usage.get(key) for c in trace.calls if c.usage.get(key) is not None]
        return sum(values) if values else None
    seconds = [c.seconds for c in trace.calls if c.seconds is not None]
    costs = [c.cost for c in trace.calls if c.cost is not None]
    return {
        "calls": len(trace.calls),
        "seconds": sum(seconds) if seconds else None,
        "prompt": total("prompt_tokens"),
        "completion": total("completion_tokens"),
        "cached": total("cached_tokens"),
        "cost": sum(costs) if costs else None,
        "tools": sum(len(c.tool_calls) for c in trace.calls),
    }


STYLE = """
:root { --bg: #1a1b26; --fg: #c0caf5; --muted: #565f89; --accent: #7aa2f7; --user: #9ece6a; --tool: #e0af68; --line: #292e42; }
body { margin: 0; padding: 1.5rem; background: var(--bg); color: var(--fg); font: 14px/1.45 ui-monospace, Menlo, Consolas, monospace; }
h1 { color: var(--accent); font-size: 1.2rem; font-weight: 600; margin: 0 0 .25rem; }
.meta { color: var(--muted); margin-bottom: 1rem; }
.meta button { background: none; border: 1px solid var(--muted); color: var(--fg); font: inherit; padding: .1rem .5rem; margin-left: .5rem; cursor: pointer; }
table { border-collapse: collapse; width: 100%; }
th, td { border-top: 1px solid var(--line); padding: .4rem .5rem; vertical-align: top; text-align: left; }
th { color: var(--muted); font-weight: 500; }
td.n { color: var(--muted); white-space: nowrap; text-align: right; }
tr.user td { color: var(--user); font-weight: 600; background: #16161e; white-space: pre-wrap; }
tr.note td { color: var(--muted); font-style: italic; }
.reply { white-space: pre-wrap; margin-bottom: .4rem; }
details { margin: .2rem 0; border-left: 2px solid var(--line); padding-left: .5rem; }
summary { cursor: pointer; color: var(--muted); }
.tool { color: var(--tool); font-weight: 600; }
.args { color: var(--muted); }
pre.result { margin: .3rem 0 .5rem; padding: .5rem; background: #16161e; color: var(--fg); white-space: pre-wrap; word-break: break-word; max-height: 24rem; overflow: auto; }
figure { margin: .5rem 0; }
figure img { max-width: 100%; border: 1px solid var(--line); }
figcaption { color: var(--muted); }
tfoot td { color: var(--accent); font-weight: 600; }
"""

SCRIPT = """
function fold(open) { document.querySelectorAll('details').forEach(function (d) { d.open = open; }); }
"""


def html(trace):
    """The page. One table: a header, one row per prompt, call or marker, a totals row."""
    sums = totals(trace)
    head = "".join(f"<th>{escape(h)}</th>" for h in ("#", "time", "sec", "prompt", "compl", "cached", "cost", "reply and tool calls"))
    rows = "".join(render_row(row) for row in trace.rows)
    foot = (
        f'<tr><td class="n">{sums["calls"]}</td><td class="n">calls</td><td class="n">{escape(number(sums["seconds"], 1))}</td>'
        f'<td class="n">{escape(number(sums["prompt"]))}</td><td class="n">{escape(number(sums["completion"]))}</td>'
        f'<td class="n">{escape(number(sums["cached"]))}</td><td class="n">{escape(dollars(sums["cost"]))}</td>'
        f'<td>{sums["tools"]} tool calls</td></tr>'
    )
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>trace {escape(trace.session_id)}</title><style>{STYLE}</style></head>\n<body>"
        f"<h1>trace {escape(trace.session_id)}</h1>"
        f'<div class="meta">{sums["calls"]} model calls · {sums["tools"]} tool calls · {escape(dollars(sums["cost"]))}'
        '<button onclick="fold(true)">expand all</button><button onclick="fold(false)">collapse all</button></div>\n'
        f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody><tfoot>{foot}</tfoot></table>\n"
        f"<script>{SCRIPT}</script></body></html>\n"
    )


def write(session_id, path):
    """Build the trace of `session_id` and write it to `path`. Returns the Trace."""
    trace = calls(replay.timeline(replay.entries(session_id)), session_id)
    Path(path).write_text(html(trace), encoding="utf-8")
    return trace


def main(cli):
    """`harness trace <session id> [--html FILE]`. Returns the exit code."""
    session_id = replay.resolve(cli.session)
    path = Path(cli.html or f"trace-{session_id}.html")
    trace = write(session_id, path)
    sums = totals(trace)
    ui.note(f"wrote {path} · {sums['calls']} model calls · {sums['tools']} tool calls · {dollars(sums['cost'])}")
    return 0
