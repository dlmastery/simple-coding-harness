"""Step 03 - the two halves of the report: a static spec and one generated region.

`components_for` builds the declarative half: a list of `{"component",
"props"}` messages in the shape of sub-theme 01's static step. The view
renders them with its own four renderers (Metric, Table, BarChart, Text),
so their cost is a few hundred bytes of JSON and no model call.

`generate_region` builds the open-ended half: one small HTML document the
model writes for a region the catalog does not cover. The server, not the
host, makes that call: MCP Apps keeps credentials on the server side. When
there is no key, or the call fails, a hand-written fallback with the same
contract takes its place, so the tool never fails because of the model.
"""

import json
import re

import data
import llm

DEFAULT_FOCUS = "a what-if price slider"

FENCE = re.compile(r"^\s*```(?:html)?\s*|\s*```\s*$")

GENERATED_PROMPT = """You write one small self-contained HTML document for one region of a sales report.
The rest of the report (the headline numbers, the chart, the table) is already drawn by other code.
Your region shows: {focus}.
Rules:
- A complete document: <!doctype html>, <html>, <head> with one <style>, <body>, one <script> at the end.
- Everything inline. No external stylesheets, scripts, fonts or images: the frame that runs you blocks all network access.
- Keep it compact: at most 60 lines, system-ui font, no headings larger than 14px, fits in 260px of height.
- It must be interactive: include at least one <input type="range">. On every input event, recompute what is shown and call
  parent.postMessage({{type: "event", name: "<what changed>", payload: {{...the new values...}}}}, "*")
  so the report hears it. Use numbers, not strings, in the payload.
- Output only the HTML document. No code fence, no prose."""

GENERATED_DATA = """Lemonade stand, last {days} days. The price was ${price:.2f} per cup. The rows (day, temperature in C, cups sold, revenue in dollars):
{rows}
Total: {cups} cups, ${revenue:.2f}. Assume that each $0.50 of price change moves demand by about 15 percent in the opposite direction."""

# The offline stand-in: the same contract as the prompt asks for, written by hand.
FALLBACK_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; padding: 10px; font: 13px system-ui, sans-serif; color: #1a1a1a; }
  label { display: flex; align-items: center; gap: 10px; }
  input[type=range] { flex: 1; }
  .out { margin-top: 8px; font-size: 14px; }
  .out b { font-size: 18px; }
  .muted { color: #6b7280; font-size: 11px; margin-top: 4px; }
</style>
</head>
<body>
<label>price <input type="range" id="price" min="0.5" max="3" step="0.1" value="1.5"> <span id="shown">$1.50</span></label>
<div class="out">projected revenue <b id="revenue"></b> from <span id="cups"></span> cups</div>
<div class="muted">what-if: each $0.50 moves demand by 15% the other way (offline fallback, not model-written)</div>
<script>
  const baseCups = __CUPS__, basePrice = __PRICE__;
  const slider = document.getElementById("price");
  function update() {
    const price = Number(slider.value);
    const cups = Math.round(baseCups * (1 - 0.3 * (price - basePrice)));
    const revenue = Math.round(cups * price * 100) / 100;
    document.getElementById("shown").textContent = "$" + price.toFixed(2);
    document.getElementById("cups").textContent = cups;
    document.getElementById("revenue").textContent = "$" + revenue.toFixed(2);
    return { price, cups, revenue };
  }
  slider.addEventListener("input", () => parent.postMessage({ type: "event", name: "price_changed", payload: update() }, "*"));
  update();
</script>
</body>
</html>
"""


def components_for(days, rows):
    """The declarative half: metrics, a chart, a table and one line of text, from the same rows as step 01."""
    totals = data.summary(rows)
    best = max(rows, key=lambda row: row["cups"])
    return [
        {"component": "Metric", "props": {"title": "cups sold", "value": str(totals["total_cups"]), "delta": f"{totals['total_cups'] / days:.1f} per day"}},
        {"component": "Metric", "props": {"title": "revenue", "value": f"${totals['total_revenue']:.2f}", "delta": f"${data.PRICE:.2f} per cup"}},
        {"component": "Metric", "props": {"title": "best day", "value": totals["best_day"], "delta": f"{best['cups']} cups at {best['temperature']} C"}},
        {"component": "BarChart", "props": {"labels": [row["day"] for row in rows], "values": [row["cups"] for row in rows]}},
        {"component": "Table", "props": {"columns": ["day", "temp", "cups", "revenue"], "rows": [[row["day"], f"{row['temperature']} C", str(row["cups"]), f"${row['revenue']:.2f}"] for row in rows]}},
        {"component": "Text", "props": {"text": f"Last {days} days. The region below was written by the model for this call; everything above came from the catalog."}},
    ]


def generation_messages(days, rows, focus):
    """The server's prompt: the contract as the system message, the data as the user message."""
    totals = data.summary(rows)
    listing = "\n".join(f"{row['day']}, {row['temperature']}, {row['cups']}, {row['revenue']:.2f}" for row in rows)
    return [
        {"role": "system", "content": GENERATED_PROMPT.format(focus=focus)},
        {"role": "user", "content": GENERATED_DATA.format(days=days, price=data.PRICE, rows=listing, cups=totals["total_cups"], revenue=totals["total_revenue"])},
    ]


def fallback_html(rows):
    totals = data.summary(rows)
    return FALLBACK_HTML.replace("__CUPS__", str(totals["total_cups"])).replace("__PRICE__", str(data.PRICE))


def generate_region(days, rows, focus=DEFAULT_FOCUS):
    """The open-ended half: {"html", "source", "usage", "bytes"}, from the model or from the fallback."""
    if llm.client is None:
        html, source, usage, note = fallback_html(rows), "fallback", None, "no API key on the server"
    else:
        try:
            reply = llm.generate(generation_messages(days, rows, focus))
            html, source, usage, note = FENCE.sub("", reply["content"]).strip(), "model", reply["usage"], ""
        except Exception as error:  # the report still renders; the note says why the region is the stand-in
            html, source, usage, note = fallback_html(rows), "fallback", None, f"model call failed: {error}"
    return {"html": html, "source": source, "usage": usage, "bytes": len(html.encode("utf-8")), "note": note}
