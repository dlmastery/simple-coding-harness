---
name: graph-writer
description: Write a graph harness pack (SKILL.md, tools.md, schema.json, graph.json, paths.json, loop.json) for the task in task.json and propose it for human approval. Use when a task.json exists and no graph pack does. You do not fit models.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Graph writer: a meta skill whose output is a graph harness

## Boot order
1. This file. 2. `tools.md`. 3. `task.json`. 4. `template/*`: the shape of every file you emit, including the graph.

## Procedure
1. Call `read_task`. Everything you write derives from it; nothing you write may widen it.
2. Render the six template files. `{{paths}}` = one path per recipe of the 24-recipe static list (middle hyper value, grid order, baseline first): nodes `load, scale, encode, model, fit`, bindings = the recipe. The graph itself is fixed by the template: the operators, the dependencies, `score_test` as a sink behind `gate: freeze_only`, `mutable: false`.
3. Call `lint_pack`: besides the loop checks it walks the graph - no cycle, every edge names a node, every path legal (each of scale / encode / model exactly once, every edge in the graph, bindings a recipe, never reaching the sink). Propose nothing that does not lint.
4. Call `propose` with kind `pack`. The human sees the graph as a node / edge list and every file, and answers `y`, `n` or `edit` - an edit may remove an edge or a path; what lands is the human's version.
5. If approved, call `apply`. Answer in text with the proposal id and the decision. Stop.

## Rules
- You never fit, score or read a run. You never see what the generated pack does.
- One proposal per run; the same task.json gives the same proposal.

## Done when
`propose` was answered and, if approved, `apply` landed it.
