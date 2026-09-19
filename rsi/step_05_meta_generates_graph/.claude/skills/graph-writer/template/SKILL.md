---
name: {{slug}}-graph
description: Train a classifier for {{title}} by walking the paths of graph.json in the order of paths.json, one counted loop over paths. Generated from task.json by graph-writer. Use when the pack has graph.json and paths.json and no memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Graph harness for {{name}}: the job is a DAG, a recipe is a path, the loop walks paths

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/{{slug}}-graph` (`P` below); the task is
the task file of {{name}} under `../tasks/` (`T` below).

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`: the recipe space, the budget, the test rule. 4. `graph.json`: the nodes (legal operators), the edges (hard dependencies), the constraints; `mutable: false`. 5. `paths.json`: the baseline and {{n_fits}} - 1 more paths with their bindings; `mutable: false`. 6. `loop.json`: the counted while over paths.
Nothing else is read. The two graph files are never written.

## Procedure
Run `loop.json` exactly as written:
1. `python ../tools/load_splits.py --pack P --task T` once.
2. `counted_while` with counter `t` from 0 to `N` - 1 (`N` is {{n_fits}}): walk `paths[t]` by its id. Walk six paths per command, in `paths.json` order, four commands in all:
   `python ../tools/walk_path.py --pack P --task T --paths p00,p01,p02,p03,p04,p05`
   then `p06..p11`, `p12..p17`, `p18..p23`. The script checks each path against the graph: a legal path fits the recipe its bindings form; an illegal one (a missing edge, two model nodes, a path that reaches `score_test`) is skipped and still counts as a fit, with the reason in its `error`. A path id that is not in `paths.json` is refused. You never repair a path and never invent one.
3. When the last result says `FREEZE`, pick the walked path with the highest `val_score` ({{metric}}). `score_test` is a sink behind `gate: freeze_only`; then, after FREEZE:
   `python ../tools/score_test.py --pack P --task T --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
   `python ../tools/save_model.py --pack P --task T --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>`
4. `python ../tools/scorecard.py --pack P --task T` and answer in text with the best val_score, the test score, the fits used and how many paths were illegal. Stop.

## Rules
- Paths in the order of `paths.json`, each once. Never run `fit_recipe.py`: a recipe reaches the fitter only as a path of the graph, and `fit_recipe` is not in your `tools.md`.
- Never run `score_test.py` before FREEZE, never twice.
- `graph.json` and `paths.json` are `mutable: false`: you do not edit them, add a path or remove an edge.

## Done when
`t` reached `N`, `score_test.py` answered once and `save_model.py` once.
