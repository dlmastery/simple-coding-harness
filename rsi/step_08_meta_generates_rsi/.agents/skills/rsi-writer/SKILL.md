---
name: rsi-writer
description: Write the RSI harness for the task in task.json - an actor pack with memory.json, memory.schema.json and eval.md, and a verifier pack with the contract - and propose both for human approval; the user approves a mechanism that will change itself later. Use in rsi/step_08_meta_generates_rsi when a task.json exists and no RSI pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# RSI writer: a meta skill whose output is a mechanism that will change itself

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/rsi-writer` (`W` below); the two packs
you write land under `.claude/skills/` as `adult-income` and
`adult-income-verifier` (`OUT` = `.claude/skills`); the task is `W/task.json`
(`T` below).

## Boot order
1. This file. 2. `tools.md`. 3. `W/task.json`. 4. `W/template/actor/*` and `W/template/verifier/*`: the shape of the two packs you emit.

## Procedure
1. Read `W/task.json`. Everything you write derives from it; nothing you write may widen it.
2. Render both packs into `runs/rsi-writer/rendered/<slug>/` (from `template/actor/`) and `runs/rsi-writer/rendered/<slug>-verifier/` (from `template/verifier/`) - the directory names are the packs' names, so the agent finds them once they land (use your Write tool), replacing each `{{placeholder}}` and nothing else: `{{name}}`, `{{slug}}` (`name` with `_` -> `-`), `{{title}}`, `{{metric}}`, `{{n_fits}}`, `{{models}}` (JSON list), `{{test_rule}}` (JSON), `{{recipes}}` (the static list: each allowed model at its middle hyper value - `logreg` 1, `rf` 16, `hgb` 0.1 - in grid order model, scale yes/no, encode onehot/ordinal, class_weight none/balanced, the baseline first, as a JSON list of `n_fits` recipes). Files without a placeholder are copied as they are: `memory.json` is `[]`, `memory.schema.json` is the card type, and the verifier's `SKILL.md` carries the contract line word for word - `lint_pack` refuses a verifier pack without it.
3. Lint the directory of packs and fix until `ok`:
   `python ../tools/lint_pack.py --pack runs/rsi-writer/rendered --task W/task.json`
4. Propose both packs at once. The script prints the verifier contract on top of the diff: it is the acceptance rule the user is approving.
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for <name>: actor + verifier, empty memory, the contract"`
5. Show the user the contract first, then every file of both packs, and say plainly what they are approving: not a one-off pack but a mechanism - the verifier will write cards into the actor's `memory.json` after every problem, and the actor's next run will obey them. Ask: **approve / edit / reject**. Wait; run nothing until the answer arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
   - edit: write the user's version under `runs/rsi-writer/edited/` (same two subdirectories) and `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>" --edited @runs/rsi-writer/edited`
   - reject: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>"`
7. Answer in text with the proposal id, the decision, what landed, and the contract line. Stop.

## Rules
- You never fit, score or write a card: `fit_recipe.py`, `score_test.py` and `write_card.py` are not in your `tools.md` and refuse to act for you.
- You never see the generated packs' runs; nothing they learn comes back to you.
- One proposal per run; the same `task.json` gives the same proposal.
- Never run `apply.py` before the user has answered.

## Done when
`propose.py` answered and, if the user approved or edited, `apply.py` landed both packs.
