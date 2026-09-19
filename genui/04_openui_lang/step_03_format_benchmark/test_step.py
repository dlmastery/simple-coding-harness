"""Step 03 tests. Offline: samples on disk, tiktoken's cached encoding, no model.

The ground truth is the OpenUI repository's own benchmark artifacts in
report/: the Python projections must reproduce them byte for byte, and the
token counts must reproduce the report's table.
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import benchmark  # noqa: E402
from convert import c1_text, js_numbers, to_jsonl, to_spec, to_yaml  # noqa: E402
from openui_parse import parse  # noqa: E402

SCENARIOS = benchmark.SCENARIOS


def need_encoding():
    """tiktoken fetches o200k_base from the network the first time; offline, the token tests are skipped, not failed."""
    try:
        benchmark.encoding()
    except Exception as error:  # noqa: BLE001 - whatever the download raised
        pytest.skip(f"o200k_base is not available: {type(error).__name__}")


def sample(scenario):
    return (HERE / "samples" / f"{scenario}.oui").read_text(encoding="utf-8")


def report(name):
    return (HERE / "report" / name).read_text(encoding="utf-8")


def test_every_sample_parses_cleanly():
    for scenario in SCENARIOS:
        result = parse(sample(scenario) + "\n", benchmark.CATALOG)
        assert result.root is not None and result.unresolved == [] and result.errors == [], scenario


def test_c1_projection_matches_the_report_files():
    for scenario in SCENARIOS:
        texts = benchmark.projections(sample(scenario))
        # the committed file was reformatted by prettier; compare the parsed value
        # and the raw JSON.stringify(x, null, 2) text the report counted
        assert json.loads(texts["c1"]) == json.loads(report(f"{scenario}.c1.json")), scenario
        assert texts["c1"] == json.dumps(json.loads(report(f"{scenario}.c1.json")), indent=2, ensure_ascii=False)


def test_jsonl_projection_matches_the_report_files():
    for scenario in SCENARIOS:
        assert benchmark.projections(sample(scenario))["jsonl"] == report(f"{scenario}.vercel.jsonl"), scenario


def test_yaml_projection_matches_the_report_files():
    for scenario in SCENARIOS:
        assert benchmark.projections(sample(scenario))["yaml"] == report(f"{scenario}.yaml").rstrip("\n"), scenario


def test_token_counts_reproduce_the_report_table():
    need_encoding()
    for scenario in SCENARIOS:
        texts = benchmark.projections(sample(scenario))
        counted = {fmt: benchmark.count(texts[fmt]) for fmt in ("oui", "yaml", "c1", "jsonl")}
        assert counted == benchmark.REPORT[scenario], scenario


def test_generated_files_are_current():
    """generated/ is committed; it must match what the code produces now."""
    for scenario in SCENARIOS:
        texts = benchmark.projections(sample(scenario))
        for fmt, ext in [("yaml", "yaml"), ("c1", "c1.json"), ("jsonl", "vercel.jsonl"), ("map", "map.json")]:
            assert (HERE / "generated" / f"{scenario}.{ext}").read_text(encoding="utf-8") == texts[fmt] + "\n"


def test_first_paint_is_one_line_for_openui_lang_only():
    need_encoding()
    texts = benchmark.projections(sample("contact-form"))
    paint = benchmark.first_paint_tokens(texts)
    assert paint["oui"] == benchmark.count('root = Stack([title, form], "column", "l")\n')
    assert paint["oui"] < 20
    for fmt in ("yaml", "c1", "jsonl", "map"):
        assert paint[fmt] == benchmark.count(texts[fmt])


# ── the converters on a small tree ──────────────────────────────────────────

TREE = parse('root = Card([t, b], "card")\nt = TextContent("Hi", "large-heavy")\nb = Button("Go", "action:go")\n', benchmark.CATALOG).root


def test_spec_ids_are_preorder_and_insertion_is_postorder():
    spec = to_spec(TREE)
    assert spec["root"] == "card-1"
    assert list(spec["elements"]) == ["textcontent-2", "button-3", "card-1"]
    assert spec["elements"]["card-1"] == {"type": "Card", "props": {"variant": "card"}, "children": ["textcontent-2", "button-3"]}


def test_jsonl_has_root_first_then_one_add_per_element():
    lines = to_jsonl(to_spec(TREE)).splitlines()
    assert json.loads(lines[0]) == {"op": "add", "path": "/root", "value": "card-1"}
    assert [json.loads(l)["path"] for l in lines[1:]] == ["/elements/textcontent-2", "/elements/button-3", "/elements/card-1"]


def test_c1_nests_components_and_drops_nothing():
    c1 = json.loads(c1_text(TREE))
    assert c1["error"] is None
    assert c1["component"]["component"] == "Card"
    assert c1["component"]["props"]["children"][1] == {"component": "Button", "props": {"label": "Go", "action": "action:go"}}


def test_yaml_removes_empty_children_and_quotes_like_the_yaml_package():
    text = to_yaml(to_spec(TREE))
    assert "children: []" not in text
    assert "children:\n      - textcontent-2\n      - button-3" in text
    tricky = to_spec(parse('root = TextContent("10", "Includes:")\n', benchmark.CATALOG).root)
    yaml = to_yaml(tricky)
    assert 'text: "10"' in yaml and 'size: "Includes:"' in yaml


def test_yaml_folds_long_strings_at_80_columns():
    long = "ARR shown as 12×MRR for directional tracking; replace with contracted ARR if you track annual commitments."
    yaml = to_yaml(to_spec(parse(f'root = TextContent("{long}")\n', benchmark.CATALOG).root))
    assert "      text: ARR shown as 12×MRR for directional tracking; replace with contracted ARR\n        if you track annual commitments." in yaml


def test_yaml_multiline_string_is_a_literal_block():
    source = r'root = MarkDownRenderer("- one\n- two")' + "\n"  # the string holds a \n escape
    yaml = to_yaml(to_spec(parse(source, benchmark.CATALOG).root))
    assert "textMarkdown: |-\n        - one\n        - two" in yaml


def test_a_sample_that_does_not_parse_is_one_clear_error():
    with pytest.raises(ValueError, match="did not parse cleanly"):
        benchmark.projections("root = Stack([missing])\n")


def test_numbers_print_like_javascript():
    assert js_numbers([5.0, 6.5, 118500, {"a": 2.0}]) == [5, 6.5, 118500, {"a": 2}]
    assert json.dumps(js_numbers(5.0)) == "5"
