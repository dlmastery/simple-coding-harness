---
name: {{task_slug}}-graph
description: "Train a classifier for the {{title}} problem by walking the 24 paths of paths.json through the DAG of graph.json with the counted loop of loop.json - an illegal path is skipped and counted, never replaced - with helpers you build from the contracts in tools.md. Use in the lesson that landed it, when the pack has graph.json and paths.json."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# Graph harness: the job is a DAG, a recipe is a path, the loop walks paths

Run every helper through the Bash tool from this lesson's directory. This pack's directory
is `.claude/skills/{{task_slug}}-graph` (`P`); the problem is `../tasks/{{task_dir}}` (`T`);
the one arm is `control`.

## Boot order
1. This file. 2. `tools.md`. 3. `graph.json`: the nodes (legal operators), the edges (hard dependencies), the constraints; `score_test` is a sink behind the `FREEZE` gate. 4. `paths.json`: the baseline and the 24 paths with their bindings. 5. `loop.json`: the counted while now iterates over paths. 6. `schema.json`, `T/intent.md`.

## Procedure
1. Build the helpers of `tools.md` under `runs/{{task_slug}}-graph/helpers/` if they are not there yet. `walk_path` is the new one: it checks a path against `graph.json` before it binds and fits it.
2. Open the arm: `load_splits P T --arm control --memory off`.
3. Run `loop.json`: for `t` from 1 to `N`, `walk_path P T --arm control --path <paths.json[t - 1].id>`. A legal path is bound to its recipe (the bindings, the model at its middle hyper value) and fitted through `fit_recipe`; an illegal path - a node the graph lacks, a step that is not an edge, a broken constraint - is skipped and counted: one fit of the budget, a trace row with `error: "illegal path: <why>"`, no fit. Never replace it, never invent a path. You may walk several paths per call if your helper accepts a list.
4. The exit as `loop.json` lists it: `FREEZE`; `score_test P T --arm control --recipe <best val recipe>` once; `save_model`; `scorecard`.
5. Answer in text with the number of legal and illegal paths, the best val_score, the test score and the fits used. Stop.

## Rules
- `graph.json` and `paths.json` are `mutable: false`: a run never changes them (the test compares their bytes).
- Everything under `illegal` in `loop.json` is illegal; an illegal path costs a fit because the budget counts attempts, not successes.
- Never run `score_test` before FREEZE, never twice: `score_test` is a sink the graph puts behind the gate, the hook blocks it and the helper refuses it.

## Off switch
None: no memory. Still not RSI: the next run walks the same paths in the same order.

## Done when
`t` reached `N`, `score_test` answered once, `save_model` once.
