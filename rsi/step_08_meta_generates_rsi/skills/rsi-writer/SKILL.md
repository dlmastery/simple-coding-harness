---
name: rsi-writer
description: Write the RSI harness for the task in task.json - an actor pack with memory.json, memory.schema.json and eval.md, and a verifier pack with the contract - and propose both for human approval. Use when a task.json exists and no RSI pack does. You do not fit models.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# RSI writer: a meta skill whose output is a mechanism that will change itself

## Boot order
1. This file. 2. `tools.md`. 3. `task.json`. 4. `template/actor/*` and `template/verifier/*`: the shape of the two packs you emit.

## Procedure
1. Call `read_task`. Everything you write derives from it; nothing you write may widen it.
2. Render both template directories: `{{name}}`, `{{slug}}`, `{{title}}`, `{{n_fits}}`, `{{models}}`, `{{test_rule}}`, `{{recipes}}` (the static list of the allowed models), `{{card_schema}}` (the JSON Schema of a card, identical in both packs). The verifier's SKILL.md keeps its contract line word for word: it is the acceptance rule of the mechanism, and `lint_pack` refuses a verifier without it.
3. Call `lint_pack` with every file of both packs (paths `actor/...` and `verifier/...`). Propose nothing that does not lint.
4. Call `propose` with kind `pack`. The human sees the verifier contract first, then every file, and answers `y`, `n` or `edit`. Say in your summary that this pack will change its own memory.json on every problem it runs.
5. If approved, call `apply`. Answer in text with the proposal id and the decision. Stop.

## Rules
- You never fit, score, read a trace or write a card. You never see what the generated packs learn.
- One proposal per run; the same task.json gives the same proposal.

## Done when
`propose` was answered and, if approved, `apply` landed both packs.
