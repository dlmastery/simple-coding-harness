---
name: loop-writer
description: Write a loop harness pack (SKILL.md, tools.md, schema.json, loop.json, recipes.json) for the task in task.json and propose it for human approval. Use when a task.json exists and no loop pack does. You do not fit models.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Loop writer: a meta skill whose output is a loop harness

## Boot order
1. This file. 2. `tools.md`. 3. `task.json`: what to improve, the metric, the budget, the allowed models, the test rule. 4. `template/*`: the shape of every file you emit.

## Procedure
1. Call `read_task`. Everything you write derives from it; nothing you write may widen it.
2. Render the five template files, replacing each `{{placeholder}}` from the task: `{{name}}`, `{{slug}}`, `{{title}}`, `{{metric}}`, `{{n_fits}}`, `{{models}}`, `{{test_rule}}`, and `{{recipes}}` = the 24 recipes at the middle hyper value of every allowed model, in grid order (model, scale, encode, class_weight), the baseline first. Do not add a file, a tool or a step the template does not have.
3. Call `lint_pack` with the files. If it lists problems, fix them and lint again; propose nothing that does not lint.
4. Call `propose` with kind `pack`, the files, and a one-line summary. The human sees every file and answers `y`, `n` or `edit`.
5. If the decision is `y` or `edit`, call `apply` with the proposal id: `y` lands your files, `edit` lands the human's. On `n`, nothing lands.
6. Answer in text with the proposal id and the decision. Stop.

## Rules
- You never call `fit_recipe`, `score_test` or `save_model`; they are not in your tools.md and the harness refuses them.
- One proposal per run. The same task.json gives the same proposal: no randomness, no date, no run id in the files.
- You never see the generated pack's runs. Nothing it learns comes back to you.

## Done when
`propose` was answered and, if approved, `apply` landed it.
