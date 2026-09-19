---
name: intent
description: Validate the intent of the rsi series - intent.md (what to improve, how, the budget, the locked-test rule; YAML front matter and prose) and acceptance.md (what counts as success) - by the checklists in tools.md, and show that a pack which widens the intent is refused. Use in rsi/step_00_intent before any pack exists.
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# Intent: what to improve, how, and what counts as success

You do not fit models, write helpers, write packs or change any file. You read, check and
report, with your Read tool or `cat` through Bash, from this lesson's directory.

## Boot order
1. This file. 2. `tools.md`: the two checklists you perform. 3. `intent.md` and `acceptance.md`: the intent.

## Procedure
1. `validate_intent` on `intent.md` and `acceptance.md`: read both and go through every rule of the checklist in `tools.md`, noting each rule as it passes or fails. List the budget, the metric, the test rule, the models, the data source, the five profile keys and the 14 scorecard fields.
2. `lint_pack` on `widened_pack.json` in this skill's directory - a regular pack, given as `{"<file>": "<text>"}`, whose `schema.json` raises `n_fits` to 48, scores the test twice and adds a model the intent does not allow. Name every rule of the checklist it breaks. It is refused before any human sees it.
3. The curriculum the intent belongs to: read `../tasks/*/intent.md` (seven directories) and `validate_intent` each one; report the seven names in index order with metric and role (six `curriculum`, one `exam`).
4. Answer in text: the budget, the metric, the test rule, the 14 scorecard fields, the reasons the widened pack was refused, and the seven problems in order. Stop.

## Rules
- You change nothing and create nothing: no helper, no run directory, no card, no pack. The human is the author of the intent; you are its reader.
- Report a rule that fails as a failure; do not repair the file.

## Off switch
None: nothing runs here, so nothing is switched off. The off switches arrive with the first memory file, in lesson 06.

## Done when
Both checklists ran on the intent and the widened pack was refused.
