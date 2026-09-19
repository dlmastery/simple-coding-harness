---
name: graph-writer
description: Write a graph harness pack (SKILL.md, tools.md, schema.json, graph.json, paths.json, loop.json) for the task in task.json and propose it for human approval; the user sees the graph as nodes and edges and may edit it before it lands. Use in rsi/step_05_meta_generates_graph when a task.json exists and no graph pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Graph writer: a meta skill whose output is a graph harness

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/graph-writer` (`W` below); the pack you
write lands at `.claude/skills/adult-income-graph` (`OUT` below); the task is
`W/task.json` (`T` below).

## Boot order
1. This file. 2. `tools.md`. 3. `W/task.json`. 4. `W/template/*`: the shape of every file you emit, including the graph.

## Procedure
1. Read `W/task.json`. Everything you write derives from it; nothing you write may widen it.
2. Render the six template files into `runs/graph-writer/rendered/` (use your Write tool), replacing each `{{placeholder}}` from the task and nothing else: `{{name}}`, `{{slug}}` (`name` with `_` -> `-`), `{{title}}`, `{{metric}}`, `{{n_fits}}`, `{{models}}` (JSON list), `{{test_rule}}` (JSON), and `{{paths}}` = a JSON list of one path per recipe of the static list (each allowed model at its middle hyper value - `logreg` 1, `rf` 16, `hgb` 0.1 - in grid order: model, then scale yes/no, encode onehot/ordinal, class_weight none/balanced; the baseline first): `{"id": "p00", "nodes": ["load", "scale", "encode", "model", "fit"], "bindings": <the recipe>}`, ids `p00` .. `p23`. The graph itself is fixed by the template: the operators, the dependencies, `score_test` as a sink behind `gate: freeze_only`, `mutable: false`.
3. Lint, and fix until `ok`; besides the loop checks the linter walks the graph - no cycle, every edge names a node, every path legal (each of scale / encode / model exactly once, every edge in the graph, bindings a recipe, never reaching the sink):
   `python ../tools/lint_pack.py --pack runs/graph-writer/rendered --task W/task.json`
4. Propose. The script renders the graph as a node / edge list on top of the diff:
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/graph-writer/rendered --summary "graph pack for <name>: 6 nodes, 5 edges, 24 paths"`
5. Show the user the node / edge list and every file, then ask: **approve / edit / reject**. An edit may remove an edge or a path, or change a binding; what lands is the user's version, linted again. Wait for the answer; run nothing until it arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
   - edit: apply the user's change to a copy of the rendered files under `runs/graph-writer/edited/` (their words say what to change; if a removed edge makes a path illegal, leave the path - the linter will say so and nothing lands until the user resolves it), then `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>" --edited @runs/graph-writer/edited`
   - reject: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>"`
7. Answer in text with the proposal id, the decision and what landed. Stop.

## Rules
- You never fit, score or read a run: `fit_recipe.py`, `walk_path.py` and `score_test.py` are not in your `tools.md` and refuse to act for you. You never see what the generated pack does.
- One proposal per run; the same `task.json` gives the same proposal.
- Never run `apply.py` before the user has answered.

## Done when
`propose.py` answered and, if the user approved or edited, `apply.py` landed it.
