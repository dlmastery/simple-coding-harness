# Step 03 - The token benchmark, reproduced

**What this step adds:** the numbers behind the report's "most
token-efficient format" claim, recomputed here. The seven scenario programs
the report's benchmark recorded (`samples/*.oui`, the model's own OpenUI Lang
output) are parsed with the step 01 parser and projected into the three
other formats the report compared: Thesys C1 JSON (the legacy nested shape),
json-render's element map (and the RFC 6902 patch stream it is sent as),
and YAML. Every text is counted with `tiktoken`'s `o200k_base` encoding and
compared, cell by cell, with the report's table. Latency is the token count
at 60 tokens per second. No model call, no browser.

## Quick demo

```
python demo.py
```

```text
tokens (o200k_base); * = differs from the report's table, [n] = the report's number
scenario              OpenUI    YAML  C1 JSON  patches    map  vs YAML   vs C1  vs patches
simple-table             148     316      357      340    257   -53.2%  -58.5%      -56.5%
chart-with-data          231     464      516      520    396   -50.2%  -55.2%      -55.6%
contact-form             294     762      849      893    666   -61.4%  -65.4%      -67.1%
dashboard               1226    2128     2261     2247   1738   -42.4%  -45.8%      -45.4%
pricing-page            1195    2230     2379     2487   1950   -46.4%  -49.8%      -52.0%
settings-panel           540    1077     1205     1244    946   -49.9%  -55.2%      -56.6%
e-commerce-product      1166    2145     2381     2449   1920   -45.6%  -51.0%      -52.4%
TOTAL                   4800    9122     9948    10180   7873   -47.4%  -51.7%      -52.8%
report TOTAL            4800    9122     9948    10180      -

seconds at 60 tokens/s: complete (first paint)
scenario                    OpenUI          YAML       C1 JSON       patches
simple-table             2.5 (0.1)     5.3 (5.3)     6.0 (6.0)     5.7 (5.7)
chart-with-data          3.9 (0.2)     7.7 (7.7)     8.6 (8.6)     8.7 (8.7)
contact-form             4.9 (0.2)   12.7 (12.7)   14.2 (14.2)   14.9 (14.9)
dashboard               20.4 (0.5)   35.5 (35.5)   37.7 (37.7)   37.5 (37.5)
pricing-page            19.9 (0.4)   37.2 (37.2)   39.6 (39.6)   41.5 (41.5)
settings-panel           9.0 (0.2)   17.9 (17.9)   20.1 (20.1)   20.7 (20.7)
e-commerce-product      19.4 (0.2)   35.8 (35.8)   39.7 (39.7)   40.8 (40.8)

the report's own committed files (report/), counted as checked in: C1 JSON, YAML
simple-table               322*[357]       317*[316]
chart-with-data            498*[516]       465*[464]
contact-form               824*[849]       763*[762]
dashboard                2182*[2261]     2129*[2128]
pricing-page             2285*[2379]     2231*[2230]
settings-panel           1195*[1205]     1078*[1077]
e-commerce-product       2344*[2381]     2146*[2145]
```

### What reproduces and what does not

- **Every cell of the report's token table reproduces exactly**: OpenUI
  Lang 4800, YAML 9122, Thesys C1 JSON 9948, json-render patches 10180 in
  total, and all 28 per-scenario numbers. The projections written by
  `convert.py` are byte-identical to the benchmark artifacts in the OpenUI
  repository (`report/`, MIT), which `test_step.py` checks.
- **The report's latency claims reproduce**: contact form 4.9 s against
  14.9 s for patches ("a 3.04x difference": 893 / 294 = 3.04), e-commerce
  19.4 s against 40.8 s (patches) and 39.7 s (C1 JSON).
- **Two of the repository's committed artifacts do not count like its
  table.** The `.c1.json` files were reformatted by prettier after the
  numbers were taken (short arrays on one line) and count 10 to 94 tokens
  fewer than tabled; the table's C1 numbers are the raw
  `JSON.stringify(x, null, 2)` text. The `.yaml` files end with a newline
  the table did not count (+1 each). The `.oui` and `.vercel.jsonl` files
  count exactly as tabled. Formatting alone moves C1 by up to 10 %, which
  is a caution about how much the exact serialisation matters.
- **Not reproduced:** the model run. The `.oui` samples are the ones the
  report's benchmark generated with `gpt-5.2` at temperature 0; this step
  does not regenerate them. The OpenUI Lang column measures the model's
  actual output; the other three columns measure projections of the same
  tree, which is also how the report produced them.
- **Not in the report:** the `map` column (json-render's element map as one
  compact JSON document rather than a patch stream). It sits between OpenUI
  Lang and YAML: the map pays for keys and quotes but not for one patch
  envelope per element.

## The idea

The State of Generative UI report puts OpenUI Lang, json-render and A2UI in
the same declarative slot and separates them on cost: "JSON pays for keys,
quotes, and brackets on every field, while a line-oriented DSL does not."
The step makes that sentence checkable. Because all four texts are
projections of one parsed tree, the only variable is the syntax.

Two of the numbers are worth reading twice. The first is the ratio, which
is stable around 2x across scenarios of very different size: the overhead
is per field, so it scales with the UI. The second is first paint. At 60
tokens per second a nested document is not renderable until its last
bracket arrives; an OpenUI Lang program is renderable after its first line.
The patch stream in the report's projection inserts children before
parents (`stack-1` is the last line), so its first paint is also the whole
stream. Sub-theme 05 shows json-render streaming root-first, where the
patch shape pays off.

## The code, piece by piece

The parser is `openui_parse.py` from step 01, unchanged; the benchmark
schema (`samples/schema.json`, the default library's `toJSONSchema()`)
supplies the positional-to-named mapping for its 53 components.

The C1 projection is the legacy nested shape: every node becomes
`{"component", "props"}` and children stay inside the props they came from:

`convert.py`:

```python
def to_c1(tree: dict) -> dict:
    """The legacy nested shape: every node is {"component": name, "props": {...}}."""
    def convert(value):
        if isinstance(value, list):
            return [convert(v) for v in value]
        if is_element(value):
            return {"component": value["typeName"], "props": convert(value["props"])}
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items() if k != "__typename"}
        return value
    return {"component": convert(js_numbers(tree)), "error": None}
```

The json-render projection flattens the tree into an element map. Any prop
that holds element nodes becomes `children`; ids are numbered in pre-order
and inserted in post-order, which decides the patch order:

`convert.py`:

```python
    def process(node):
        nonlocal counter
        if not is_element(node):
            return None
        counter += 1
        element_id = f"{node['typeName'].lower()}-{counter}"
        props, children = {}, []
        for key, value in node["props"].items():
            if isinstance(value, list):
                if any(is_element(v) for v in value):
                    children.extend(cid for cid in (process(v) for v in value) if cid)
                else:
                    props[key] = value
                continue
            child_id = process(value)
            if child_id:
                children.append(child_id)
            else:
                props[key] = value
        elements[element_id] = {"type": node["typeName"], "props": props, "children": children}
        return element_id
```

The patch stream is one `add` per element, root pointer first:

`convert.py`:

```python
def to_jsonl(spec: dict) -> str:
    """The json-render stream: one RFC 6902 `add` per line, root first."""
    lines = [compact({"op": "add", "path": "/root", "value": spec["root"]})]
    for element_id, element in spec["elements"].items():
        lines.append(compact({"op": "add", "path": f"/elements/{element_id}", "value": element}))
    return "\n".join(lines)
```

YAML needs the most care, because the report's numbers were taken on the
`yaml` npm package's output: strings that would parse as numbers are
quoted, strings containing `: ` are quoted, long plain strings are folded
at 80 columns, multi-line strings become `|-` blocks. The emitter ports
those rules, and the tests prove the port on the seven real files:

`convert.py`:

```python
def scalar(value, indent: str, indent_at_start: int | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(js_numbers(value))
    if NOT_PLAIN.search(value):
        return quoted(value, indent) if "\n" not in value else block_scalar(value, indent)
    if "\n" in value:
        return block_scalar(value, indent)
    if LOOKS_TYPED.match(value):
        return quoted(value, indent)
    return fold(value, indent, indent_at_start)
```

Counting and comparing. The encoder is `o200k_base`, which is what
`encoding_for_model("gpt-5")` resolves to in the report's script:

`benchmark.py`:

```python
ENCODING = tiktoken.get_encoding("o200k_base")
...
def count(text: str) -> int:
    return len(ENCODING.encode(text))
```

First paint is the token count a renderer needs before it can draw
anything. Only OpenUI Lang has a renderable prefix in these projections:

`benchmark.py`:

```python
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
```

The ground-truth test: the Python projections must equal the repository's
artifacts byte for byte (C1 compared as raw `JSON.stringify` text and as
parsed value, YAML without the trailing newline):

`test_step.py`:

```python
def test_yaml_projection_matches_the_report_files():
    for scenario in SCENARIOS:
        assert benchmark.projections(sample(scenario))["yaml"] == report(f"{scenario}.yaml").rstrip("\n"), scenario
```

## Run it

```
python demo.py                 # or python benchmark.py: the three tables
python benchmark.py --write    # also writes generated/<scenario>.{yaml,c1.json,vercel.jsonl,map.json}
python -m pytest -q            # offline; needs tiktoken's o200k_base (cached after first use)
```

Files: `samples/` holds the seven `.oui` programs and `schema.json` from
the OpenUI repository's `benchmarks/` directory (MIT, commit `8bd2e27`);
`report/` holds that directory's committed projections, kept only as the
ground truth for the tests; `generated/` holds this step's projections.

## What to notice

- The savings column is nearly flat: 42 % to 67 % against YAML, 45 % to
  65 % against C1. The overhead of JSON is proportional to the number of
  fields, not to the size of the strings, so the ratio does not shrink for
  big UIs.
- YAML is the cheapest of the three JSON-shaped formats (9122 against
  9948 and 10180): it drops the quotes and most brackets but still pays for
  every key name. OpenUI Lang drops the key names too, because the catalog
  supplies them positionally.
- The patch stream is the most expensive format and the report's chosen
  comparison for json-render. The element map alone (`map`) is 23 % cheaper
  than the patches: the `{"op":"add","path":"/elements/...","value":...}`
  envelope costs about 11 tokens per element (2307 tokens over the 212
  elements of the seven scenarios).
- "3.04x" in the report is a ratio of complete-render times at a constant
  token rate. First paint is a different quantity and favours OpenUI Lang
  far more, but only when the program is written root-first, which is why
  the generated prompt in step 02 insists on it.

## Diff from the previous step

- No page, no server, no model: `benchmark.py`, `convert.py`, `demo.py`
  and the sample data replace step 02's `server.py`, `llm.py`, `app.mjs`
  and `library.mjs`.
- `openui_parse.py` returns, copied from step 01 without changes.
- `package.json` is gone; the step is Python only (`tiktoken` is the one
  dependency beyond the standard library).
