"""Generative UI step 01 - one agent, two surfaces.

    python demo.py                 # the real model draws a lemonade-stand dashboard
    python demo.py --offline       # a scripted model call, no API key needed
    python demo.py --prompt "..."  # a different request

The loop is the stage 15 loop from harness/agent.py with the prompt given
here instead of typed. The render_ui tool draws in the terminal and on the
web page; Playwright opens the page headlessly and saves demo.png.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

if "--offline" in sys.argv:
    os.environ.setdefault("API_KEY", "offline")  # before harness.config reads the environment

from harness import llm, web  # noqa: E402
from harness.llm import SYSTEM_PROMPT  # noqa: E402
from harness.tools import execute  # noqa: E402
from harness.ui import ui  # noqa: E402

HERE = Path(__file__).resolve().parent
PROMPT = "show me a dashboard for a lemonade stand"

# What the model is expected to send: a json-render element map from the catalog.
SAMPLE_SPEC = {
    "root": "dash",
    "elements": {
        "dash": {"type": "Card", "props": {"title": "Lemonade stand - this week"}, "children": ["kpis", "sales", "cups"]},
        "kpis": {"type": "Stack", "props": {"direction": "row"}, "children": ["revenue", "sold", "margin"]},
        "revenue": {"type": "Metric", "props": {"label": "Revenue", "value": "$184", "delta": "+12%"}},
        "sold": {"type": "Metric", "props": {"label": "Cups sold", "value": "92", "delta": "+8"}},
        "margin": {"type": "Metric", "props": {"label": "Margin", "value": "61%", "delta": "-2%"}},
        "sales": {"type": "Chart", "props": {"kind": "bar", "title": "Cups per day", "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"], "values": [14, 18, 22, 17, 21]}},
        "cups": {"type": "Table", "props": {"columns": ["Flavour", "Cups", "Price"], "rows": [["Classic", 55, "$2"], ["Pink", 25, "$2.5"], ["Mint", 12, "$3"]]}},
    },
}


def scripted_model():
    """A stand-in for call_llm: one render_ui call, then a one-line reply."""
    call = SimpleNamespace(id="call_1", function=SimpleNamespace(name="render_ui", arguments=json.dumps({"spec": SAMPLE_SPEC})))
    turns = [
        SimpleNamespace(content=None, tool_calls=[call], model_dump=lambda exclude_none=True: {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "render_ui", "arguments": call.function.arguments}}]}),
        SimpleNamespace(content="Here is this week's lemonade stand at a glance.", tool_calls=None, model_dump=lambda exclude_none=True: {"role": "assistant", "content": "Here is this week's lemonade stand at a glance."}),
    ]
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    return lambda messages, tools=None: (turns.pop(0), usage)


def run_turn(prompt):
    """The agent loop for one user message: call, execute tools, repeat until text only."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    ui.user(prompt)
    while True:
        with ui.working():
            message, usage = llm.call_llm(messages)
        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)
        if message.content:
            ui.agent(message.content)
        if not message.tool_calls:
            return messages
        for tool_call in message.tool_calls:
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})


def screenshot(url, path):
    """Open the web surface headlessly, wait for the first render, save a PNG."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 640})
        page.goto(url)
        page.wait_for_selector("#surface [data-id]", timeout=10_000)
        page.screenshot(path=str(path), full_page=True)
        browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="scripted model, no API key")
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--no-screenshot", action="store_true")
    cli = parser.parse_args(argv)

    if cli.offline:
        llm.call_llm = scripted_model()

    _, url = web.serve(0)
    ui.banner()
    ui.note(f"web surface: {url}")
    run_turn(cli.prompt)

    if web.latest is None:
        ui.note("the model did not call render_ui; no screenshot")
        return 1
    if not cli.no_screenshot:
        screenshot(url, HERE / "demo.png")
        ui.note("saved demo.png from the web surface")
    return 0


if __name__ == "__main__":
    sys.exit(main())
