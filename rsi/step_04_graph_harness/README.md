# Lesson 04 - Graph engineering with loops: the job is a DAG, a recipe is a path

The trainer's job written as a graph: `graph.json` names the legal
operators as nodes (`load`, `scale`, `encode`, `model`, `fit`, `score_test`),
the hard dependencies as edges, and the constraints (one `scale`, one
`encode`, one `model` per path; no cycles; `score_test` a sink behind
`gate: freeze_only`). A recipe is a path with bindings; `paths.json` lists
the baseline and 23 more; the counted loop of lesson 02 now iterates over
paths and `walk_path.py` fits what a path binds. An illegal path - a missing
edge, a second model, a path that reaches the sink - is skipped and still
counts as a fit; a path id that is not in the file is refused. Both graph
files are `mutable: false`. Still not RSI: the graph is the human's, the walk
is fixed, and nothing about the walk changes the next one. What this lesson
adds is a *structure a later writer can generate and a human can read as
nodes and edges* (lesson 05).

## Getting started

Lesson 03 left the generated loop pack. This lesson adds
`.claude/skills/adult-income-graph/` (`SKILL.md`, `tools.md`, `schema.json`,
`graph.json`, `paths.json`, `loop.json`), mirrored to `.agents/skills/`, and
one script: `../tools/walk_path.py`. Open your agent in this directory. A run
writes only under `runs/`.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-graph skill: walk the graph's paths on the Adult income problem and report the scorecard.
   ```

   The agent runs the counted loop as four walks of six paths, then the exit:

   ```bash
   python ../tools/load_splits.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
   python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p00,p01,p02,p03,p04,p05
   python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p06,p07,p08,p09,p10,p11
   python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p12,p13,p14,p15,p16,p17
   python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p18,p19,p20,p21,p22,p23
   python ../tools/score_test.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/save_model.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/scorecard.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
   ```

   No approval prompt; no quoting issues in any shell (ids and `k=v` pairs).

2. Plant an illegal path by hand, in a copy: give `p03` the nodes
   `["load", "encode", "scale", "model", "fit"]` (the graph has no edge
   `load -> encode`) and walk it. The result has `val_score: null`,
   `"error": "illegal path: edge load -> encode is not in the graph"` and
   `n: 4` - counted, not repaired. Ask for `p99`: refused, "the loop walks the
   paths it has, it does not invent one".

3. Reset with `rm -rf runs`. Headless: `claude -p "<the prompt>" --allowedTools
   "Bash,Read,Write,Edit,Skill"`. Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-graph/graph.json` - nodes, edges, constraints,
immutable:

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
 "edges": [["load", "scale"], ["scale", "encode"], ["encode", "model"], ["model", "fit"], ["fit", "score_test"]],
 "constraints": {"one_of": ["scale", "encode", "model"], "no_cycles": true, "sink_after_freeze": "score_test"}
}
```

`.claude/skills/adult-income-graph/SKILL.md` - the loop over paths:

```markdown
---
name: adult-income-graph
description: Train a classifier for the Adult income problem by walking the paths of graph.json in the order of paths.json, one counted loop over paths. Use in rsi/step_04_graph_harness, when the pack has graph.json and paths.json and no memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Graph harness: the job is a DAG, a recipe is a path, the loop walks paths

## Procedure
Run `loop.json` exactly as written:
1. `python ../tools/load_splits.py --pack P --task T` once.
2. `counted_while` with counter `t` from 0 to `N` - 1 (`N` is 24): walk `paths[t]` by its id. Walk six paths per command, in `paths.json` order, four commands in all:
   `python ../tools/walk_path.py --pack P --task T --paths p00,p01,p02,p03,p04,p05`
   then `p06..p11`, `p12..p17`, `p18..p23`. The script checks each path against the graph: a legal path fits the recipe its bindings form; an illegal one (a missing edge, two model nodes, a path that reaches `score_test`) is skipped and still counts as a fit, with the reason in its `error`. A path id that is not in `paths.json` is refused. You never repair a path and never invent one.

## Rules
- Paths in the order of `paths.json`, each once. Never run `fit_recipe.py`: a recipe reaches the fitter only as a path of the graph, and `fit_recipe` is not in your `tools.md`.
- `graph.json` and `paths.json` are `mutable: false`: you do not edit them, add a path or remove an edge.
```

`../tools/_lib/graph.py` - what makes a path illegal, in the order the
script checks:

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

`../tools/walk_path.py` - skip and count, never invent:

```python
    for pid in ids:
        if pid not in paths:
            results.append({"path": pid, "error": f"no path {pid!r} in paths.json; the loop walks the paths it has, it does not invent one", "refused": True})
            continue
        reason = graph.why_illegal(g, paths[pid])
        try:
            if reason:
                results.append({"path": pid, **fit_one(run, graph.path_recipe(paths[pid]) or paths[pid].get("bindings"), error=f"illegal path: {reason}")})
            else:
                results.append({"path": pid, **fit_one(run, graph.path_recipe(paths[pid]))})
```

The recorded run (Claude Code 2.1.278, headless; the agent read the six pack
files first; results trimmed):

```text
[Skill adult-income-graph]
agent> Boot complete. Now step 1: load the splits.
$ python ../tools/load_splits.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
{"pack": "adult-income-graph", "problem": "adult_income", "n_fits": 24, "fits_used": 0, ...}
agent> Splits loaded (24 fits budget, 0 used). Now the counted while: four commands of six
paths each, in paths.json order.
$ python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p00,p01,p02,p03,p04,p05
{"results": [{"path": "p00", "n": 1, "recipe": {"model": "logreg", ...}, "val_score": 0.9114, "error": null, "fits_left": 23}, ...
             {"path": "p05", "n": 6, ... "val_score": 0.9074, "error": null, "fits_left": 18}], "fits_used": 6, "n_fits": 24, "fits_left": 18}
$ python ../tools/walk_path.py ... --paths p06,p07,p08,p09,p10,p11
$ python ../tools/walk_path.py ... --paths p12,p13,p14,p15,p16,p17
$ python ../tools/walk_path.py ... --paths p18,p19,p20,p21,p22,p23
{"results": [... {"path": "p23", "n": 24, ... "fits_left": 0}], "fits_used": 24, "fits_left": 0, "FREEZE": true}
$ python ../tools/score_test.py ... --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
{"test_score": 0.9034, ...}
$ python ../tools/save_model.py ... && python ../tools/scorecard.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
{"fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9172, "test_score": 0.9034, "test_scored_once": true, ...}
agent> Done. The loop ran to completion exactly as loop.json specifies: t reached N = 24,
score_test answered once after FREEZE, save_model once.
Best val_score 0.9172 (p17: hgb, lr 0.1, scale yes, onehot, balanced); test 0.9034; fits 24/24;
illegal paths 0 - all 24 paths fit the graph (every error was null).
p17 and p21 tied at 0.9172 (identical except scale, a no-op for hgb); I took p17, the earlier
one in paths.json order. Everything ran as the pack prescribes: no fit_recipe, no edits to
graph.json / paths.json, test scored exactly once.
[16 turns, 124 s]
```

What to notice: same numbers as lessons 01-03 (the 24 paths bind the 24
static recipes in the same order), and zero illegal paths in the shipped
file - the illegal-path behaviour is exercised by the test on a copy, and by
you in step 2 above.

Files:

```text
step_04_graph_harness/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-graph/
│   ├── SKILL.md, tools.md, schema.json
│   ├── graph.json                 nodes, edges, constraints; mutable: false
│   ├── paths.json                 p00 (baseline) .. p23 with bindings; mutable: false
│   └── loop.json                  counted while over paths
├── .agents/skills/adult-income-graph/
└── runs/adult-income-graph/adult_income/   (after a run)
```

## Governance considerations

- **Who approves what.** Nobody; the graph and the paths are the human's
  and immutable during a run.
- **The hook.** As before: `score_test.py` before FREEZE or twice.
- **What the script refuses.** A path id not in `paths.json`; `fit_recipe.py`
  for this pack (not in its `tools.md`: a recipe reaches the fitter only as a
  path); `score_test` before FREEZE or twice. An illegal path is not refused
  but *counted* with its reason - a bad plan costs budget, which is what
  makes "the loop never invents a path" checkable.
- **What is and is not self-modified.** Nothing; `graph.json` and `paths.json`
  checksums are equal before and after a run (asserted).

## How to measure it

| Claim | Test |
|---|---|
| the loop walks `paths.json` in order, binds the 24 static recipes, scores the test once | `test_loop_walks_paths_in_order_and_scores_once` |
| an illegal path is skipped and counted with its reason, never replaced; an unknown id is refused | `test_illegal_path_is_skipped_and_counted_never_replaced` |
| `score_test` is unreachable before FREEZE; `fit_recipe` is not a tool of this pack | `test_score_test_unreachable_before_freeze_and_fit_recipe_not_a_tool` |
| `graph.json` / `paths.json` are byte-identical after a run | `test_graph_files_byte_identical_after_a_run` |
| `lint_pack` refuses a cyclic graph and a path that breaks a constraint | `test_lint_refuses_a_cycle_and_a_bad_path` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard (seed 0): `fits_used 24`, `wasted_fits 16`, `best_val_score 0.9172`,
`test_score 0.9034`, illegal paths 0.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 05 - a meta skill generates the graph harness](../step_05_meta_generates_graph/README.md),
where `edit` is the interesting answer. Previous:
[Lesson 03 - a meta skill generates the loop harness](../step_03_meta_generates_loop/README.md).
