"""Step 01 tests. Offline: no model, no network.

The Python parser is tested directly. The JavaScript twin runs through
`node --test` when node is on the PATH, and the two are compared on
program.oui through tree_js.mjs.
"""

import json
import shutil
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from openui_parse import (  # noqa: E402
    ParseError, StreamingParser, load_catalog, parse, parse_program, split_statements, tokenize,
)

CATALOG = load_catalog(HERE / "catalog.json")
NODE = shutil.which("node")


def kinds(text):
    return [t.kind for t in tokenize(text)]


def test_tokenize_strings_numbers_words():
    assert kinds('a = Text("say \\"hi\\"", -2.5, true, null)') == [
        "IDENT", "EQUALS", "TYPE", "LPAREN", "STR", "COMMA", "NUM", "COMMA", "BOOL", "COMMA", "NULL", "RPAREN", "EOF",
    ]
    assert tokenize('"say \\"hi\\""')[0].value == 'say "hi"'
    assert [t.value for t in tokenize("1 2.5 -3 1e3")[:4]] == [1, 2.5, -3, 1000.0]


def test_unclosed_string_is_closed_for_streaming():
    assert tokenize('"Lemo')[0].value == "Lemo"


def test_split_statements_holds_back_the_unfinished_line():
    complete, pending = split_statements('root = Stack([a])\na = Text("un')
    assert complete == ["root = Stack([a])"]
    assert pending == 'a = Text("un'


def test_newline_inside_brackets_does_not_end_the_statement():
    complete, pending = split_statements("root = Stack([\n  a,\n  b\n])\n")
    assert complete == ["root = Stack([\n  a,\n  b\n])"]
    assert pending == ""


def test_stray_quote_ends_with_its_line():
    """One unclosed string must not swallow the rest of the program."""
    result = parse('root = Stack([a, b])\na = Text("unclosed\nb = Text("B")\n', CATALOG)
    children = result.root["props"]["children"]
    assert children[0] == {"type": "placeholder", "name": "a"}  # the broken line is an error, not a sink
    assert children[1]["props"]["text"] == "B"
    assert len(result.errors) == 1 and result.errors[0].startswith("'a = Text(\"unclosed'")


def test_deep_nesting_is_an_error_line_not_a_crash():
    program = parse_program("x = " + "[" * 5000 + "]" * 5000 + "\n")
    assert program.statements == {} and len(program.errors) == 1


def test_shared_reference_is_resolved_once():
    result = parse('root = Stack([a, a])\na = Text("A")\n', CATALOG)
    first, second = result.root["props"]["children"]
    assert first is second and first["statementId"] == "a"


def test_stream_delay_is_clamped():
    from server import clamp_delay

    assert clamp_delay("400") == 0.4 and clamp_delay("abc") == 0.0 and clamp_delay("99999") == 5.0


def test_forward_reference_resolves_and_missing_becomes_placeholder():
    result = parse('root = Stack([a, b])\na = Text("A")\n', CATALOG)
    children = result.root["props"]["children"]
    assert children[0]["typeName"] == "Text"
    assert children[0]["statementId"] == "a"
    assert children[1] == {"type": "placeholder", "name": "b"}
    assert result.unresolved == ["b"]


def test_positional_arguments_map_to_catalog_names():
    result = parse('root = Metric("Revenue", 482, "+12%")\n', CATALOG)
    assert result.root["props"] == {"label": "Revenue", "value": 482, "delta": "+12%"}


def test_optional_trailing_arguments_can_be_omitted():
    result = parse('root = Text("hi")\n', CATALOG)
    assert result.root["props"] == {"text": "hi"}


def test_unknown_component_is_reported_and_dropped():
    result = parse("root = Stack([x])\nx = Gauge(1)\n", CATALOG)
    assert result.root["props"]["children"] == []
    assert result.errors == ["unknown component Gauge"]


def test_too_many_arguments_is_reported():
    result = parse('root = Text("a", "body", "extra")\n', CATALOG)
    assert result.errors == ["Text takes 2 arguments, got 3"]


def test_objects_and_lists():
    program = parse_program('x = {a: 1, "b": [1, -2.5e3, true, null]}\n')
    assert program.statements["x"] == {"k": "Obj", "entries": [
        ("a", {"k": "Num", "v": 1}),
        ("b", {"k": "Arr", "els": [{"k": "Num", "v": 1}, {"k": "Num", "v": -2500.0}, {"k": "Bool", "v": True}, {"k": "Null"}]}),
    ]}


def test_fences_and_comments_are_ignored():
    program = parse_program('```openui\nroot = Text("a") // note\n# a comment line\n```\n')
    assert list(program.statements) == ["root"]
    assert program.statements["root"]["args"][0]["v"] == "a"


def test_hash_inside_a_string_is_not_a_comment():
    program = parse_program('root = Text("#1 flavour")\n')
    assert program.statements["root"]["args"][0]["v"] == "#1 flavour"


def test_bad_statement_is_recorded_not_raised():
    program = parse_program('this is not a statement\nroot = Text("a")\n')
    assert list(program.statements) == ["root"]
    assert program.errors == ["'this is not a statement': expected EQUALS, got IDENT"]


def test_cycle_becomes_placeholder():
    result = parse("root = Stack([root])\n", CATALOG)
    assert result.root["props"]["children"] == [{"type": "placeholder", "name": "root"}]


def test_streaming_parser_grows_the_tree():
    sp = StreamingParser(CATALOG)
    result = sp.push('root = Stack([t])\nt = Text("Lemo')
    assert result.incomplete and result.unresolved == ["t"]
    result = sp.push('nade")\n')
    assert not result.incomplete
    assert result.root["props"]["children"][0]["props"]["text"] == "Lemonade"
    assert sp.finish().unresolved == []


def test_finish_parses_a_last_line_without_newline():
    sp = StreamingParser(CATALOG)
    assert sp.push('root = Text("a")').root is None
    assert sp.finish().root["typeName"] == "Text"


def test_program_oui_resolves_completely():
    result = parse((HERE / "program.oui").read_text(encoding="utf-8"), CATALOG)
    assert result.unresolved == [] and result.errors == []
    assert result.statement_count == 12
    assert [c["typeName"] for c in result.root["props"]["children"]] == ["Text", "Stack", "BarChart", "Table", "Card"]


def test_stream_route_sends_one_line_per_event():
    from server import make_server

    server = make_server()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/stream") as response:
            body = response.read().decode()
    finally:
        server.shutdown()
    events = [line for line in body.splitlines() if line.startswith("data: ")]
    assert json.loads(events[0][6:]).startswith("root = Stack(")
    assert len(events) == 13  # 12 lines and the done event
    assert "event: done" in body


# ── the JavaScript twin ─────────────────────────────────────────────────────

def need_node():
    if NODE is None:
        pytest.skip("node is not installed")


def test_node_suite_passes():
    need_node()
    result = subprocess.run([NODE, "--test", "tests/parse.test.mjs"], cwd=HERE, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


def test_python_and_javascript_build_the_same_tree():
    need_node()
    result = subprocess.run([NODE, "tree_js.mjs", "program.oui", "catalog.json"], cwd=HERE, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    py = parse((HERE / "program.oui").read_text(encoding="utf-8"), CATALOG)
    assert json.loads(result.stdout) == {"root": py.root, "unresolved": py.unresolved, "errors": py.errors}
