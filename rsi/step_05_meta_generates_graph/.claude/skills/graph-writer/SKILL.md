---
name: graph-writer
description: "A meta skill whose output is a graph harness: from a problem's intent.md write the six files of a graph pack (SKILL.md, tools.md, graph.json, paths.json, loop.json, schema.json) by filling the template, lint the DAG and every path against the intent, propose them as a node / edge list, and land them - or the user's edited version - only with the user's words. Use in rsi/step_05_meta_generates_graph; never fits a model."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
  patches: ["adult-income-graph/*"]
---
# Graph writer: a meta skill whose output is a graph harness

You do not fit models. Run every helper through the Bash tool from this lesson's directory.
This pack's directory is `.claude/skills/graph-writer` (`W`); the problem is
`../tasks/01_adult_income` (`T`); the pack you write is `adult-income-graph`, landing - only
after the user's answer - at `.claude/skills/adult-income-graph/` and `.agents/skills/adult-income-graph/`.

## Boot order
1. This file. 2. `tools.md`. 3. `template/`: the six files with `{{placeholders}}`. 4. `bad_paths.json`: a paths file that must be refused. 5. `T/intent.md`.

## Procedure
1. Build `lint_pack`, `propose` and `apply` under `runs/graph-writer/helpers/` if they are not there yet. `lint_pack` now checks the graph: no cycle in `graph.json` (plus any `edges_added`), and every path of `paths.json` uses only nodes the graph has, walks only its edges, has exactly one `scale`, one `encode`, one `model`, and never steps through the test sink.
2. Read `T/intent.md` (`{{task}}`, `{{title}}`, `{{task_dir}}`, `{{metric}}`, `{{budget_fits}}`; `{{task_slug}}` is the name with `_` as `-`) and write the six files from `template/` with every placeholder replaced and nothing else changed, under `runs/graph-writer/adult_income/proposals/p001/`.
3. Self-check the lint before you trust it: `lint_pack` the same pack with `paths.json` replaced by `bad_paths.json` (a cycle `fit -> load` under `edges_added`, a path with two `scale` nodes, a path that steps through the test sink). It must be refused with those three problems named. Show the refusal. Then `lint_pack` the real pack against `T/intent.md`: it must pass.
4. `propose W T --target adult-income-graph --files runs/graph-writer/adult_income/proposals/p001 --summary "<one line>"`. Show the user the graph as a node / edge list, the 24 paths as `id: bindings` lines, and the other four files in full, and ask: **approve / edit / reject**. Stop and wait.
5. When the answer arrives, quoting their words verbatim:
   - approve: write their words to `runs/graph-writer/adult_income/proposals/p001.approved`, then `apply W T p001 --approved "<their words>"`.
   - `edit: <a change>` (for example `edit: remove path p24`, or a changed binding): make exactly that change to a copy of the proposal's files under `runs/graph-writer/adult_income/proposals/p001-edited/`, lint the edited pack (an edit that breaks the DAG or a constraint is refused: tell the user and ask again), write `.approved` with their words, `apply ... --edited runs/graph-writer/adult_income/proposals/p001-edited`. Their version lands.
   - reject: write `p001.rejected`; nothing lands.
6. Answer in text with the proposal id, the lint results (the refused check and the passing one), the decision and the files that landed. Stop.

## Rules
- You never fit, never open an arm, never score anything.
- Nothing is proposed that does not lint; a cycle or an illegal path is refused before the human sees it.
- `edit` is the interesting answer: what lands is the human's version, and you never see a run result - there is no feedback loop here.

## Off switch
None: a one-shot writer.

## Done when
`apply` answered (landed, edited, or rejected).
