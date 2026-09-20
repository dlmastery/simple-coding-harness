---
name: skill-memory-meta
description: "Recuris's meta agent - turn one problem's execution evidence into ONE localised, validated update of the actor's skill memory, a card for the situation the problem was in. Use in rsi/step_13_rsi_skill_memory after the actor's memory arm on a problem is frozen and scored."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# Recuris's meta agent: evidence becomes a card, one at a time

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/skill-memory-meta` (`M`); the actor pack is `.claude/skills/adult-income-skills`
(`P`); the problem is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `M/config.md`. The actor's cards, its `working.md` and the log come through helpers.

## Procedure
1. Build `read_traces` and `skill_memory` under `runs/skill-memory-meta/helpers/` if they are not there yet (they may import the actor's runtime helpers). Read the evidence and the memory: `read_traces P T --scope problem --tally`, `skill_memory P T --action list`, `skill_memory P T --action tags`.
2. Name the situation of this problem with the same need tags the actor used. From the tally, per field, take the value with the most wins net of losses.
3. Take the first field of `model`, `class_weight`, `encode`, `scale` whose winning value the situation's card does not already hold (a card holds one `then`; a card "for the situation" is one whose `when` tags all hold for this need). Update once, with the existing card's name when the situation has one for that field, else a new name (`<value>-for-<tag>`): `skill_memory P T --action update --as M --card <name> --then <field>=<value> --when <tag,tag> --body "<one sentence: what the log showed>" --visit <n>`. The helper refuses an update whose `then` did not win its comparisons on this problem, keeps one file per card, snapshots the pack under `runs/adult-income-skills/versions/` first, raises the card's `horizon` (the number of problems it was updated on), and refuses a second update in the same visit.
4. Answer in text with the helper's result (card, file, horizon, version). Stop.

## Rules
- One update per visit; the helper refuses a second.
- An update is localised to one card file (plus a manifest line for a new card) and validated before it lands.
- You never fit and never score the test split: `fit_recipe` and `score_test` are forbidden to this pack.

## Off switch
META_OFF: `meta: off` in `M/config.md`; no card changes and the pack stays byte-identical between problems.

## Done when
`skill_memory --action update` has answered once, or there was nothing to update.
