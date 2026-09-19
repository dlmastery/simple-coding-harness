# Lesson 05 - A meta skill generates the graph harness, under human approval

Lesson 03's writer, extended: `graph-writer` renders lesson 04's six files
from `task.json`, `lint_pack` now walks the graph before any human sees it
(no cycle, every edge names a node, every path legal, the sink gated), and
the proposal shows the graph as a node / edge list. The interesting answer
this time is `edit`: the human removes an edge, and what lands is the
human's graph - the writer never learns that it happened, and never sees
how the generated pack runs. Still L1, still no feedback loop, still not
RSI; but the acceptance now covers a whole search space at once, which is
what a human will be asked to accept in lessons 08 and 09.

## Getting started

Lesson 04 left the graph pack and `common/graph.py`. This lesson adds
`skills/graph-writer/` whose `template/` holds lesson 04's files with
placeholders (`{{paths}}` is rendered from the task's allowed models), and
one line in `common/approve.py: show` that prints a `graph.json` as nodes and
edges. `run.py` reuses lesson 03's runner with this writer.

## How to execute it

1. Generate, read the graph, decide:

   ```bash
   cd rsi/step_05_meta_generates_graph
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_05_meta_generates_graph
   $env:FAKE_MODEL = "1"; python run.py
   ```

   At `approve p1 (pack)? [y/n/edit]`: `y` lands the graph as proposed;
   `edit` lets you paste the files with, say, an edge removed; `n` lands
   nothing. Scripted: `HUMAN=script:y`.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/graph-writer/SKILL.md`:

```markdown
---
name: graph-writer
description: Write a graph harness pack (SKILL.md, tools.md, schema.json, graph.json, paths.json, loop.json) for the task in task.json and propose it for human approval. Use when a task.json exists and no graph pack does. You do not fit models.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
```

```markdown
3. Call `lint_pack`: besides the loop checks it walks the graph - no cycle, every edge names a node, every path legal (each of scale / encode / model exactly once, every edge in the graph, bindings a recipe, never reaching the sink). Propose nothing that does not lint.
4. Call `propose` with kind `pack`. The human sees the graph as a node / edge list and every file, and answers `y`, `n` or `edit` - an edit may remove an edge or a path; what lands is the human's version.
```

The lint that runs before the human is asked:

`../common/graph.py`:

```python
def lint_graph(graph, paths, task):
    problems = []
    nodes = graph.get("nodes", {})
    edges = [tuple(e) for e in graph.get("edges", [])]
    for a, b in edges:
        if a not in nodes or b not in nodes:
            problems.append(f"edge {a} -> {b} names an unknown node")
    if has_cycle(nodes, edges):
        problems.append("graph.json has a cycle")
    if graph.get("mutable", True):
        problems.append("graph.json must be mutable: false")
```

And the `propose` tool refuses a pack that does not lint, so the human only
ever sees legal graphs:

`../common/tools.py`:

```python
    if kind == "pack":
        problems = lint_pack(run, payload)
        if problems != "ok":
            raise ValueError(f"lint_pack refuses this pack before the human sees it: {problems['problems']}")
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y`; the
files of the proposal are elided):

```text
### graph.json as a graph
nodes: load, scale, encode, model, fit, score_test
edges: load -> scale; scale -> encode; encode -> model; model -> fit; fit -> score_test
### graph.json
...
Proposal p1 decided y: applied p1 (y) to adult-income-graph.
lint of the landed pack: ok
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
generated pack byte-identical after its run: True
```

Files:

```text
step_05_meta_generates_graph/
  skills/graph-writer/
    SKILL.md              read the task, render six files, lint (loop + graph), propose, apply if approved
    tools.md              Allowed: read_task, lint_pack, propose, apply
    task.json             the intent of lesson 00
    template/SKILL.md     lesson 04's SKILL.md with placeholders
    template/tools.md     lesson 04's tools.md
    template/schema.json  lesson 03's schema template
    template/graph.json   lesson 04's graph, verbatim: the operators are not the writer's to choose
    template/paths.json   {{paths}}
    template/loop.json    lesson 04's loop with N = {{n_fits}}
  run.py                  lesson 03's generate -> approve -> run, pointed at graph-writer
  test_step.py            the claims below
  README.md               this lesson
```

## Governance considerations

- Who approves what: the human approves the graph (as nodes and edges) and
  every file; an `edit` is the human's graph.
- Off switches: `n`; the lint gate before the prompt.
- What the model may not do, and which tool enforces it: fit (`execute`
  refuses `fit_recipe`); propose a cyclic graph or an illegal path
  (`propose` -> `lint_pack` -> `lint_graph` refuses before the human is
  asked); land without approval (`apply`).
- What is and is not self-modified: nothing. The writer never sees the run
  results of what it wrote, so the edit the human made never feeds back.
  Rung: L1.

## How to measure it

| Claim | Test |
|---|---|
| `lint_pack` rejects a proposal with a cycle before the human ever sees it | `test_lint_rejects_a_cycle_before_the_human_sees_it` |
| `lint_pack` rejects a path that violates a constraint (a node twice, the sink reached) | `test_lint_rejects_a_path_that_violates_a_constraint` |
| the human sees the graph as a node / edge list | `test_the_human_sees_the_graph_as_nodes_and_edges` |
| an `edit` that removes an edge lands and the pack still boots and runs | `test_an_edit_that_removes_an_edge_lands_and_the_pack_still_boots` |
| `y` lands a graph pack that passes lesson 04's checks | `test_y_lands_a_graph_pack_that_passes_step_04_checks` |

Scorecard fields reported by the generated pack's run: all fourteen. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [06 - the RSI harness](../step_06_rsi_harness/README.md): the first
file that changes because of what happened. Previous:
[04 - graph engineering](../step_04_graph_harness/README.md).
