---
name: loop-writer
description: Write a loop harness pack (SKILL.md, tools.md, schema.json, loop.json, recipes.json) for the task in task.json and propose it for human approval; nothing lands until the user answers. Use in rsi/step_03_meta_generates_loop when a task.json exists and no loop pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Loop writer: a meta skill whose output is a loop harness

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/loop-writer` (`W` below); the pack you
write lands at `.claude/skills/adult-income-loop` (`OUT` below); the task is
`W/task.json` (`T` below).

## Boot order
1. This file. 2. `tools.md`. 3. `W/task.json`: what to improve, the metric, the budget, the allowed models, the test rule. 4. `W/template/*`: the shape of every file you emit.

## Procedure
1. Read `W/task.json`. Everything you write derives from it; nothing you write may widen it.
2. Render the five template files into a scratch directory, `runs/loop-writer/rendered/` (create it; use your Write tool), replacing each `{{placeholder}}` from the task and nothing else:
   `{{name}}` = `name`; `{{slug}}` = `name` with `_` replaced by `-`; `{{title}}` = `title`; `{{metric}}` = `metric`; `{{n_fits}}` = `budget.n_fits`; `{{models}}` = `allowed_models` as a JSON list; `{{test_rule}}` = `test_rule` as JSON; `{{recipes}}` = the JSON list of the `n_fits` recipes at each allowed model's middle hyper value (`logreg` 1, `rf` 16, `hgb` 0.1) in grid order - model in `allowed_models` order, then `scale` yes/no, `encode` onehot/ordinal, `class_weight` none/balanced - so the baseline (`logreg`, 1, yes, onehot, none) is first. Do not add a file, a tool, a step or a recipe the template does not have.
3. Lint what you rendered, and fix it until `ok` is true; propose nothing that does not lint:
   `python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task W/task.json`
4. Propose it. The script lints again, writes the proposal under `runs/loop-writer/<task>/proposals/` and returns its id and the text the user must see:
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for <name>: 24 static recipes, counted loop"`
5. Show the user every file of the proposal (the `diff` field), then ask, in your own words but with these three options: **approve / edit / reject**. Wait for the answer. Do not run anything until it arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
   - edit: write the user's version into `runs/loop-writer/edited/` and run `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>" --edited @runs/loop-writer/edited`
   - reject: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>"` (the script records the rejection; nothing lands)
7. Answer in text with the proposal id, the decision and what landed (the `files` list, or nothing). Stop.

## Rules
- You never run `fit_recipe.py`, `score_test.py` or `save_model.py`: they are not in your `tools.md`, and the scripts refuse to act for a pack whose `tools.md` does not allow them.
- One proposal per run. The same `task.json` gives the same proposal: no randomness, no date, no run id in the files.
- You never see the generated pack's runs. Nothing it learns comes back to you.
- Never run `apply.py` before the user has answered; the hook blocks it without `--approved` and the script refuses it.

## Done when
`propose.py` answered and, if the user approved or edited, `apply.py` landed it.
