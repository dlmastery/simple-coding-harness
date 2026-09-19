# Lesson 04 - Graph engineering with loops: the job is a DAG, a recipe is a path

The job becomes `graph.json`: nodes are the legal operators (`load`,
`scale`, `encode`, `model`, `fit`, `score_test`), edges are hard
dependencies, and the constraints say one scale, one encode and one model
per path, no cycles, and `score_test` a sink that opens only after FREEZE.
A recipe is a path with bindings; `paths.json` lists the 24 the loop walks;
`loop.json` now iterates over paths and the new tool `walk_path` fits what a
path binds. The rule that makes the file honest is the one for illegal
paths: skip and count, never repair, never invent. Both files are
`mutable: false`. Still harness engineering, still not RSI - but now the
whole search space is a picture a human can approve, which lesson 05 uses.

## Getting started

Lesson 03 left the writer and the approval cycle. This lesson adds
`skills/adult-income-graph/` (six files), the tool `walk_path`, and the
graph checks in `common/graph.py` (`why_illegal`, `lint_graph`) that
`lint_pack` now runs on any pack with a `graph.json`.

## How to execute it

1. Walk the graph on Adult:

   ```bash
   cd rsi/step_04_graph_harness
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_04_graph_harness
   $env:FAKE_MODEL = "1"; python run.py
   ```

2. Break a path by hand in `runs/work/adult-income-graph/paths.json`
   (drop `"encode"` from one path's `nodes`) and boot that copy: the path
   is skipped, the budget still counts it, and `paths.json` is not repaired.
   The test `test_illegal_path_is_skipped_and_counted_never_replaced` does
   exactly this.
3. No approval prompt: the pack changes nothing. Tests:
   `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-graph/graph.json`:

```json
{
 "mutable": false,
 "nodes": {
  "load": {"op": "load_splits"},
  "scale": {"op": "scale", "values": ["yes", "no"]},
  "encode": {"op": "encode", "values": ["onehot", "ordinal"]},
  "model": {"op": "model", "values": ["logreg", "rf", "hgb"], "binds": ["hyper", "class_weight"]},
  "fit": {"op": "fit_recipe"},
  "score_test": {"op": "score_test", "gate": "freeze_only", "sink": true}
 },
 "edges": [
  ["load", "scale"],
  ["scale", "encode"],
  ["encode", "model"],
  ["model", "fit"],
  ["fit", "score_test"]
 ],
 "constraints": {
  "one_of": ["scale", "encode", "model"],
  "no_cycles": true,
  "sink_after_freeze": "score_test"
 }
}
```

`skills/adult-income-graph/SKILL.md` - front matter and the one rule:

```markdown
---
name: adult-income-graph
description: Train a classifier for the Adult income problem by walking the paths of graph.json in the order of paths.json, one per loop iteration. Use when the pack has graph.json and no memory file.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
```

```markdown
2. `counted_while` with counter `t` from 0 to `N` - 1: call `walk_path` with `paths[t].id`. The tool checks the path against the graph: a legal path fits the recipe its bindings form; an illegal one is skipped and still counts as a fit. You never repair a path and never invent one.
```

The tool and the rule it enforces:

`../common/tools.py`:

```python
@tool("walk_path", path_id="string")
def walk_path(run, path_id):
    """Walk one path of graph.json by id: fit the recipe it binds. An illegal path is skipped and counted."""
    g = json.loads(run.files["graph.json"])
    paths = {p["id"]: p for p in json.loads(run.files["paths.json"])}
    if path_id not in paths:
        raise ValueError(f"no path {path_id!r} in paths.json; the loop walks the paths it has, it does not invent one")
    reason = graph.why_illegal(g, paths[path_id])
    if reason:
        return do_fit(run, graph.path_recipe(paths[path_id]) or paths[path_id].get("bindings"), error=f"illegal path: {reason}")
    return do_fit(run, graph.path_recipe(paths[path_id]))
```

`../common/graph.py`:

```python
def why_illegal(graph, path):
    """The first rule this path breaks, or None when it is legal."""
    nodes, edges = graph["nodes"], [tuple(e) for e in graph["edges"]]
    seq = path.get("nodes", [])
    if not seq or any(n not in nodes for n in seq):
        return "names a node that is not in the graph"
    for a, b in zip(seq, seq[1:]):
        if (a, b) not in edges:
            return f"edge {a} -> {b} is not in the graph"
    for n in ONE_OF:
        if seq.count(n) != 1:
            return f"visits {n} {seq.count(n)} times; a path visits it once"
    if any(nodes[n].get("gate") == "freeze_only" for n in seq):
        return "reaches score_test, a sink that opens only after FREEZE"
    if path_recipe(path) is None:
        return "bindings are not a recipe"
    return None
```

Expected output, on this machine (`FAKE_MODEL=1`):

```text
Done. Best val 0.9172 with {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}; test 0.9034; 24 fits.
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
paths walked 24, illegal (skipped and counted) 0; graph.json and paths.json byte-identical after the run: True
```

Files:

```text
step_04_graph_harness/
  skills/adult-income-graph/
    SKILL.md        walk paths[t] for t in 0..N-1; skip and count an illegal path; score_test after FREEZE
    tools.md        Allowed: load_splits, walk_path, score_test, save_model; fit_recipe is Forbidden
    schema.json     the recipe fields, n_fits 24, the test rule, the baseline
    graph.json      nodes, edges, constraints; mutable: false
    paths.json      24 paths (p00 = the baseline) with bindings; mutable through the graph's flag
    loop.json       counted_while over paths; illegal: add or repair a path
  run.py            boot the pack on Adult; count illegal paths; checksum the pack
  test_step.py      the claims below
  README.md         this lesson
```

## Governance considerations

- Who approves what: nobody; nothing is proposed.
- Off switches: the budget, the locked test; `mutable: false` on both
  files, checked by `lint_graph`.
- What the model may not do, and which tool enforces it: fit a recipe that
  is not a path (`fit_recipe` is not in `tools.md`); walk a path that is not
  in `paths.json` (`walk_path` refuses by id); repair or replace an illegal
  path (`walk_path` counts it and moves on); reach `score_test` through the
  graph before FREEZE (`why_illegal` on the sink, and `LockedTest` behind
  it).
- What is and is not self-modified: nothing. `graph.json` and `paths.json`
  are byte-identical after a run. Rung: harness engineering, not RSI.

## How to measure it

| Claim | Test |
|---|---|
| the loop iterates the paths in order and the pack lints | `test_loop_walks_the_paths_in_order_and_the_pack_lints` |
| an illegal path is skipped and counted, never replaced; `paths.json` is not repaired | `test_illegal_path_is_skipped_and_counted_never_replaced` |
| `score_test` is unreachable before FREEZE (the sink's gate, and the locked test behind it) | `test_score_test_is_unreachable_before_freeze` |
| `graph.json` / `paths.json` byte-identical after a run | `test_graph_and_paths_are_byte_identical_after_a_run` |
| `fit_recipe` is not a way around the graph, nor is an invented path id | `test_fit_recipe_is_not_a_way_around_the_graph` |

Scorecard fields reported: all fourteen. Run `python run_tests.py rsi` from
the repo root.

## Next lesson

Next: [05 - a meta skill generates the graph harness](../step_05_meta_generates_graph/README.md).
Previous: [03 - a meta skill generates the loop harness](../step_03_meta_generates_loop/README.md).
