"""Step 01 offline tests: the catalog validator, the render_ui tool, both surfaces, the loop.

No model is called: the loop runs against demo.scripted_model(), the web
surface is exercised with http.client against a server on an ephemeral port.
"""

import copy
import http.client
import io
import json
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "offline")
sys.argv.append("--offline")  # demo.py reads this before importing the harness

from rich.console import Console  # noqa: E402

import demo  # noqa: E402
from harness import genui, llm, subagent, tools, web  # noqa: E402
from harness.ui import ui  # noqa: E402

SPEC = demo.SAMPLE_SPEC


def call(name, arguments):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def broken(edit):
    spec = copy.deepcopy(SPEC)
    edit(spec["elements"])
    return spec


# ------------------------------------------------------------- the catalog

def test_sample_spec_is_valid():
    assert genui.validate(SPEC) == []
    assert [eid for _, eid, _ in genui.walk(SPEC)] == ["dash", "kpis", "revenue", "sold", "margin", "sales", "cups"]


def test_validator_names_each_problem():
    assert genui.validate({"root": "x"}) == ["spec must be an object with 'root' and 'elements'"]
    assert "unknown type 'Gauge'" in genui.validate(broken(lambda e: e["sold"].update(type="Gauge")))[0]
    assert "needs prop 'value'" in genui.validate(broken(lambda e: e["sold"]["props"].pop("value")))[0]
    assert "has no prop 'colour'" in genui.validate(broken(lambda e: e["sold"]["props"].update(colour="red")))[0]
    assert "must be a list" in genui.validate(broken(lambda e: e["cups"]["props"].update(rows="no")))[0]
    assert "child 'ghost' is not an element id" in genui.validate(broken(lambda e: e["kpis"]["children"].append("ghost")))[0]
    assert "takes no children" in genui.validate(broken(lambda e: e["sold"].update(children=["revenue"])))[0]
    assert "same length" in genui.validate(broken(lambda e: e["sales"]["props"].update(values=[1])))[0]
    assert genui.validate(broken(lambda e: e["kpis"]["children"].append("dash"))) == ["dash: element contains itself"]


def test_catalog_reaches_the_model_as_prompt_and_schema():
    for name in genui.CATALOG:
        assert f"- {name}(" in llm.SYSTEM_PROMPT
    schema = next(s for s in tools.TOOL_SCHEMAS if s["function"]["name"] == "render_ui")
    assert schema["function"]["parameters"]["required"] == ["spec"]
    assert "render_ui" in subagent.WITHHELD  # the explorer reports; it does not draw


# ------------------------------------------------------------ the tool

def test_render_ui_rejects_bad_specs_and_publishes_good_ones(monkeypatch):
    monkeypatch.setattr(web, "latest", None)
    args, result = tools.execute(call("render_ui", {"spec": broken(lambda e: e["sold"].update(type="Gauge"))}))
    assert result.startswith("Invalid spec, nothing rendered:") and "Gauge" in result
    assert web.latest is None

    args, result = tools.execute(call("render_ui", {"spec": SPEC}))
    assert result == "Rendered 7 elements from root 'dash'."
    assert web.latest == SPEC


# ------------------------------------------------------- terminal surface

def test_terminal_surface_draws_every_element(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(ui, "console", Console(file=buffer, width=100, force_terminal=False, color_system=None))
    ui.tool("render_ui", {"spec": SPEC}, "Rendered 7 elements from root 'dash'.")
    text = buffer.getvalue()
    for piece in ("render_ui · 7 elements", "Lemonade stand - this week", "Revenue", "$184", "+12%", "Cups per day", "Wed", "Flavour", "Classic"):
        assert piece in text
    assert "████" in text  # the bar chart is drawn, not described


def test_line_chart_becomes_a_sparkline(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(ui, "console", Console(file=buffer, width=100, force_terminal=False, color_system=None))
    ui.render({"root": "c", "elements": {"c": {"type": "Chart", "props": {"kind": "line", "labels": ["a", "b", "c"], "values": [1, 3, 2]}}}})
    assert "a b c ▃█▆" in buffer.getvalue()


# ------------------------------------------------------------ web surface

def test_web_surface_serves_page_and_replays_latest_spec_over_sse(monkeypatch):
    server, url = web.serve(0)
    host, port = server.server_address
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/")
        page = conn.getresponse()
        assert page.status == 200 and b'id="surface"' in page.read()
        conn.request("GET", "/app.js")
        assert b"EventSource" in conn.getresponse().read()
        conn.request("GET", "/nope.txt")
        assert conn.getresponse().status == 404
        conn.close()

        web.publish(SPEC)
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/events")
        stream = conn.getresponse()
        assert stream.getheader("Content-Type") == "text/event-stream"
        line = stream.fp.readline().decode()
        assert line.startswith("data: ") and json.loads(line[6:]) == SPEC
        conn.close()
    finally:
        server.shutdown()


# ---------------------------------------------------------------- the loop

def test_scripted_loop_renders_then_answers(monkeypatch):
    monkeypatch.setattr(llm, "call_llm", demo.scripted_model())
    monkeypatch.setattr(ui, "console", Console(file=io.StringIO(), width=100, force_terminal=False, color_system=None))
    messages = demo.run_turn("show me a dashboard for a lemonade stand")
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant"]
    assert messages[3]["content"] == "Rendered 7 elements from root 'dash'."
    assert web.latest == SPEC
