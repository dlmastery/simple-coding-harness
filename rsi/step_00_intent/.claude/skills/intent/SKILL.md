---
name: intent
description: Validate the intent of the rsi series - task.json (what to improve, how, the budget, the locked-test rule) and acceptance.md (what counts as success) - and show that a pack which widens the intent is refused. Use in rsi/step_00_intent before any pack exists.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Intent: what to improve, how, and what counts as success

You do not fit models, write packs or change any file. You check that the
two intent files are valid and show the reader that the intent cannot be
widened by a later pack. Run every command below through the Bash tool from
this lesson's directory (on Windows that is Git Bash; the PowerShell tool
bypasses the lesson's hook and reads `@file` as a splat).

## Procedure
1. Validate the intent:
   `python ../tools/validate_intent.py --task task.json --acceptance acceptance.md`
   The result lists the budget, the metric, the test rule, the allowed models, the profile keys and the scorecard fields. `ok` must be true.
2. Show that a pack which widens the intent is refused before any human sees it. `widened_pack.json` in this skill's directory is a regular pack whose `schema.json` raises `n_fits` to 48 and scores the test twice:
   `python ../tools/lint_pack.py --files @.claude/skills/intent/widened_pack.json --task task.json`
   `ok` must be false and `problems` must name the budget and the test rule.
3. Lint the curriculum the intent belongs to: `ls ../tasks` (Bash), then for every file there run
   `python ../tools/validate_intent.py --task ../tasks/<file>` and report the seven names, metrics and roles (six `curriculum`, one `exam`).
4. Answer in text: the budget, the metric, the test rule, the 14 scorecard fields, the reasons the widened pack was refused, and the seven problems in order. Stop.

## Rules
- You change nothing. The human is the author of the intent; the scripts are its readers.
- Do not create a pack, a run directory or a card: nothing may be learned before the intent is fixed.

## Done when
Both validations ran and the widened pack was refused.
