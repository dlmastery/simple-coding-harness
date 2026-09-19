---
name: adult-income-graph
description: Train a classifier for the Adult income problem by walking the paths of graph.json in the order of paths.json, one per loop iteration. Use when the pack has graph.json and no memory file.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Graph harness: the job is a DAG, a recipe is a path, the loop walks paths

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the budget and the test rule. 4. `graph.json`: the nodes (legal operators), the edges (hard dependencies) and the constraints. 5. `paths.json`: the paths the loop walks, each with its bindings. 6. `loop.json`: the counted loop over paths.
`graph.json` and `paths.json` are `mutable: false`. You do not add a node, an edge or a path.

## Procedure
1. Call `load_splits` once.
2. `counted_while` with counter `t` from 0 to `N` - 1: call `walk_path` with `paths[t].id`. The tool checks the path against the graph: a legal path fits the recipe its bindings form; an illegal one is skipped and still counts as a fit. You never repair a path and never invent one.
3. When a result says `FREEZE`, pick the walked path with the highest `val_score`. Call `score_test` once with its recipe, after FREEZE - `score_test` is a sink behind `gate: freeze_only` - then `save_model`.
4. Answer in text with the best val_score, the test score, the fits used and how many paths were illegal. Stop.

## Rules
- One `walk_path` per iteration, in the order of `paths.json`.
- Never call `score_test` before FREEZE, never twice.
- No file is written: the graph and the paths are the same on the next run.

## Done when
`t` reached `N`, `score_test` was called once and `save_model` once.
