"""Step 03 - the token benchmark: one UI, four formats, seven scenarios.

    python benchmark.py            # the tables (this is the demo output)
    python benchmark.py --write    # also write generated/<scenario>.<format>

For every scenario the OpenUI Lang sample (samples/<scenario>.oui, the
model output the report's benchmark recorded) is parsed and projected into
Thesys C1 JSON, json-render patches (JSONL), json-render's element map and
YAML. Each text is counted with tiktoken's o200k_base encoding, the encoder
of the GPT-5 family that the report used, and the counts are compared with
the report's table. Latency is the token count at 60 tokens per second.
"""

from __future__ import annotations

import sys
from pathlib import Path

import tiktoken

from convert import c1_text, compact, to_jsonl, to_spec, to_yaml
from openui_parse import load_catalog, parse

HERE = Path(__file__).parent
SCENARIOS = ["simple-table", "chart-with-data", "contact-form", "dashboard",
             "pricing-page", "settings-panel", "e-commerce-product"]
FORMATS = ["oui", "yaml", "c1", "jsonl", "map"]
TPS = 60  # tokens per second, the report's assumption

# The table in the report and in the OpenUI repository's benchmarks/README.md
# (commit 8bd2e27, September 2026): yaml, json-render patches, C1, OpenUI Lang.
REPORT = {
    "simple-table": {"yaml": 316, "jsonl": 340, "c1": 357, "oui": 148},
    "chart-with-data": {"yaml": 464, "jsonl": 520, "c1": 516, "oui": 231},
    "contact-form": {"yaml": 762, "jsonl": 893, "c1": 849, "oui": 294},
    "dashboard": {"yaml": 2128, "jsonl": 2247, "c1": 2261, "oui": 1226},
    "pricing-page": {"yaml": 2230, "jsonl": 2487, "c1": 2379, "oui": 1195},
    "settings-panel": {"yaml": 1077, "jsonl": 1244, "c1": 1205, "oui": 540},
    "e-commerce-product": {"yaml": 2145, "jsonl": 2449, "c1": 2381, "oui": 1166},
}

CATALOG = load_catalog(HERE / "samples" / "schema.json")
_encoding = None


def encoding():
    """o200k_base, loaded on first use: tiktoken downloads the vocabulary once and caches it."""
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding("o200k_base")
    return _encoding


def count(text: str) -> int:
    return len(encoding().encode(text))


def projections(oui: str) -> dict[str, str]:
    """The same UI in every format. The .oui text is the model's own output."""
    result = parse(oui if oui.endswith("\n") else oui + "\n", CATALOG)
    if result.root is None or result.unresolved or result.errors:
        raise ValueError(f"sample did not parse cleanly: {result.unresolved} {result.errors}")
    spec = to_spec(result.root)
    return {
        "oui": oui,
        "yaml": to_yaml(spec),
        "c1": c1_text(result.root),
        "jsonl": to_jsonl(spec),
        "map": compact(spec),
    }


def first_paint_tokens(texts: dict[str, str]) -> dict[str, int]:
    """Tokens that must arrive before a renderer can draw anything.

    OpenUI Lang: the first line (`root = ...`) is a complete statement.
    json-render patches: the `/root` patch names an element that arrives in
    the last line (children are added before parents), so the whole stream.
    C1 and YAML are one nested document: the whole text.
    """
    first_line = texts["oui"].split("\n", 1)[0] + "\n"
    return {"oui": count(first_line), "yaml": count(texts["yaml"]), "c1": count(texts["c1"]),
            "jsonl": count(texts["jsonl"]), "map": count(texts["map"])}


def run(write: bool = False) -> dict[str, dict[str, int]]:
    tokens: dict[str, dict[str, int]] = {}
    paint: dict[str, dict[str, int]] = {}
    for scenario in SCENARIOS:
        texts = projections((HERE / "samples" / f"{scenario}.oui").read_text(encoding="utf-8"))
        tokens[scenario] = {fmt: count(text) for fmt, text in texts.items()}
        paint[scenario] = first_paint_tokens(texts)
        if write:
            out = HERE / "generated"
            out.mkdir(exist_ok=True)
            for fmt, ext in [("yaml", "yaml"), ("c1", "c1.json"), ("jsonl", "vercel.jsonl"), ("map", "map.json")]:
                (out / f"{scenario}.{ext}").write_text(texts[fmt] + "\n", encoding="utf-8")
    print_tokens(tokens)
    print_latency(tokens, paint)
    print_report_files()
    return tokens


def print_tokens(tokens: dict[str, dict[str, int]]) -> None:
    print("tokens (o200k_base); * = differs from the report's table, [n] = the report's number")
    print(f"{'scenario':<20}{'OpenUI':>8}{'YAML':>8}{'C1 JSON':>9}{'patches':>9}{'map':>7}{'vs YAML':>9}{'vs C1':>8}{'vs patches':>12}")
    totals = {fmt: 0 for fmt in FORMATS}
    for scenario, row in tokens.items():
        for fmt in FORMATS:
            totals[fmt] += row[fmt]
        cells = [mark(row[fmt], REPORT[scenario].get(fmt)) for fmt in FORMATS]
        print(f"{scenario:<20}{cells[0]:>8}{cells[1]:>8}{cells[2]:>9}{cells[3]:>9}{cells[4]:>7}"
              f"{saving(row['oui'], row['yaml']):>9}{saving(row['oui'], row['c1']):>8}{saving(row['oui'], row['jsonl']):>12}")
    t = totals
    print(f"{'TOTAL':<20}{t['oui']:>8}{t['yaml']:>8}{t['c1']:>9}{t['jsonl']:>9}{t['map']:>7}"
          f"{saving(t['oui'], t['yaml']):>9}{saving(t['oui'], t['c1']):>8}{saving(t['oui'], t['jsonl']):>12}")
    report_totals = {fmt: sum(REPORT[s][fmt] for s in SCENARIOS) for fmt in ("oui", "yaml", "c1", "jsonl")}
    print(f"{'report TOTAL':<20}{report_totals['oui']:>8}{report_totals['yaml']:>8}{report_totals['c1']:>9}{report_totals['jsonl']:>9}{'-':>7}")


def mark(value: int, expected: int | None) -> str:
    if expected is None:
        return str(value)
    return str(value) if value == expected else f"{value}*[{expected}]"


def saving(ours: int, theirs: int) -> str:
    return f"-{(theirs - ours) / theirs * 100:.1f}%"


def print_latency(tokens: dict[str, dict[str, int]], paint: dict[str, dict[str, int]]) -> None:
    print(f"\nseconds at {TPS} tokens/s: complete (first paint)")
    print(f"{'scenario':<20}{'OpenUI':>14}{'YAML':>14}{'C1 JSON':>14}{'patches':>14}")
    for scenario, row in tokens.items():
        cells = [f"{row[fmt] / TPS:.1f} ({paint[scenario][fmt] / TPS:.1f})" for fmt in ("oui", "yaml", "c1", "jsonl")]
        print(f"{scenario:<20}{cells[0]:>14}{cells[1]:>14}{cells[2]:>14}{cells[3]:>14}")


def print_report_files() -> None:
    """The repository's checked-in projections do not all count like its table.

    The table's C1 numbers are raw JSON.stringify(x, null, 2); the committed
    .c1.json files were reformatted by prettier afterwards (short arrays on
    one line) and count fewer tokens. The committed .yaml files end with a
    newline the table did not count. The .oui and .vercel.jsonl files count
    exactly as tabled.
    """
    print("\nthe report's own committed files (report/), counted as checked in: C1 JSON, YAML")
    for scenario in SCENARIOS:
        c1 = count((HERE / "report" / f"{scenario}.c1.json").read_text(encoding="utf-8"))
        yaml = count((HERE / "report" / f"{scenario}.yaml").read_text(encoding="utf-8"))
        print(f"{scenario:<20}{mark(c1, REPORT[scenario]['c1']):>16}{mark(yaml, REPORT[scenario]['yaml']):>16}")


if __name__ == "__main__":
    try:
        run(write="--write" in sys.argv)
    except Exception as error:  # noqa: BLE001 - a missing vocabulary (offline) or a bad sample: one line, no traceback
        sys.exit(f"benchmark failed: {type(error).__name__}: {error}")
