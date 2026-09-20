---
name: loop-writer
description: "A meta skill whose output is a loop harness: from a problem's intent.md write the five files of a loop pack (SKILL.md, tools.md, loop.json, recipes.json, schema.json) by filling the template, lint them against the intent, propose them, and land them only with the user's words. Use in rsi/step_03_meta_generates_loop; never fits a model."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
  patches: ["adult-income-loop/*"]
---
# Loop writer: a meta skill whose output is a loop harness

You do not fit models. You write a pack, lint it, propose it and wait. Run every helper
through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/loop-writer` (`W`); the problem is `../tasks/01_adult_income` (`T`); the pack
you write is `adult-income-loop`, and it lands - only after the user's answer - at
`.claude/skills/adult-income-loop/` and, byte-identical, `.agents/skills/adult-income-loop/`.

## Boot order
1. This file. 2. `tools.md`: the helpers you build (`lint_pack`, `propose`, `apply`) and their contracts. 3. `template/`: the five files of a loop pack with `{{placeholders}}`. 4. `T/intent.md`.

## Procedure
1. Build `lint_pack`, `propose` and `apply` under `runs/loop-writer/helpers/` if they are not there yet.
2. Read `T/intent.md`: `name` (`{{task}}`), `title`, the task directory (`{{task_dir}}`), `metric`, `budget_fits`, `models`. `{{task_slug}}` is the name with `_` as `-`.
3. Write the pack from `template/`: the five files with every `{{placeholder}}` replaced and nothing else changed. `recipes.json` already holds the 24 static recipes (every model at its middle hyper value, grid order); do not add, remove or reorder one. Do not touch a rule, a heading or the illegal list. Write the five files under `runs/loop-writer/adult_income/proposals/p001/` (your Write tool).
4. `lint_pack` the five files against `T/intent.md` by the checklist in `tools.md`: `n_fits` equals `budget_fits`, the test rule, `loop.json` `N`, the front matter, the headings, `tools.md`'s two sections. If a rule fails, the pack is refused: fix your substitution and lint again. Nothing is proposed that does not lint.
5. `propose W T --target adult-income-loop --files runs/loop-writer/adult_income/proposals/p001 --summary "<one line>"`: the helper records `p001.json` with the five files. Then show the user the whole proposed pack - every file, in full - and ask: **approve / edit / reject**. Stop and wait. Run nothing else until the answer arrives.
6. When the answer arrives, quoting their words verbatim:
   - approve (any wording that approves): write their exact words to `runs/loop-writer/adult_income/proposals/p001.approved`, then `apply W T p001 --approved "<their words>"`. The pack lands in both mirrors.
   - `edit: <a change>`: make exactly that change to the proposal's files (nothing else), lint again, write `.approved` with their words, `apply ... --edited runs/loop-writer/adult_income/proposals/p001-edited`. Their version lands.
   - reject: write `p001.rejected` with their words. Nothing lands.
7. Answer in text with the proposal id, the decision, the version label and the files that landed. Stop.

## Rules
- You never fit, never open an arm, never score anything: `load_splits`, `fit_recipe` and `score_test` are forbidden to this pack, and the template's rules are not yours to relax.
- Generating twice from the same intent gives byte-identical files: the template is the mechanism, nothing is random, nothing is read from a run. Running the generated pack never changes it: you write it, it does not write itself.
- Nothing lands without the user's words in `.approved`; the lesson's hook lets no `apply` command run before that file exists.

## Off switch
None: this pack is a one-shot writer and keeps no state between visits.

## Done when
`apply` answered (landed, edited, or rejected).
