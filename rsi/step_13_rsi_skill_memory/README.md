# Lesson 13 - Recuris: memory as a skill package, with a working memory

Recuris (arXiv:2608.24876) keeps two memories: an experiential one, as
skills grounded in what worked, and a working one that says what the agent
is doing now and which skills apply. Here the experiential memory is a
*skill package* - `skill-memory/manifest.yaml` and one markdown card per
situation, each with `when` tags, one `then`, a `validated` flag and a
`horizon` (the number of problems it was updated on) - and the working
memory is `working.md`, rewritten at the start of every run with the need
tags of the problem (`small`, `categorical`, `imbalanced`, `multiclass`) and
the cards selected *by that need*, never by which card is newest. The meta
pack turns one problem's tally into ONE localised card update, validated
against the log before it lands, snapshotted first, and the horizon rises.
The memory is git-native: files you can diff. L4, with the validation rule
human.

## Getting started

Prerequisites: lesson 07 (the curriculum). This lesson replaces
`memory.json` by `skill-memory/` (shipped with one card,
`onehot-for-categorical`) and `working.md`, the verifier by
`skill-memory-meta`, and adds the `skill_memory` contract (`tags`, `list`,
`need`, `update`).

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill with the skill-memory-meta meta pack: run the curriculum (problems 1 to 6: control arm, memory arm with the cards selected by need, then one validated card update), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report, and list every card with its horizon.
   ```

2. No approval: the update is validated against the tally, one per visit.

3. Headless, as recorded:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the manifest and the shipped
   card have the skill-package shape; cards are selected by need, not
   recency; one localised, validated update per visit. `RSI_LIVE=1`: every
   arm frozen and scored once; `working.md` rewritten with a need and cards;
   every card validated with a horizon; at most six updates, one version
   each; the exam unchanged.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-skills/skill-memory/cards/onehot-for-categorical.md`:

```markdown
---
name: onehot-for-categorical
when: [categorical]
then: encode=onehot
validated: true
horizon: 1
---
The pack arrived with one card: on tables with a categorical column, one-hot encoding beat ordinal on every comparison of the first curriculum problem.
```

`.claude/skills/adult-income-skills/SKILL.md` - the need, and the selection:

```markdown
3. Name the situation. The need tags are `small` (fewer than 1000 rows), `categorical` (any categorical column), `imbalanced` (rarest class under 0.35), `multiclass` (more than two classes); `skill_memory P T --action tags` prints them from the profile. Then select the cards by need: `skill_memory P T --action need --need <tag,tag,...>`. The helper selects every validated card whose `when` tags all hold for this need - by the situation, never by which card is newest - rewrites `working.md` with the need and the cards, and prints the cards' `then` values as `prefer`.
```

`.claude/skills/skill-memory-meta/SKILL.md` - the one update:

```markdown
3. Take the first field of `model`, `class_weight`, `encode`, `scale` whose winning value the situation's card does not already hold (a card holds one `then`; a card "for the situation" is one whose `when` tags all hold for this need). Update once, with the existing card's name when the situation has one for that field, else a new name (`<value>-for-<tag>`): `skill_memory P T --action update --as M --card <name> --then <field>=<value> --when <tag,tag> --body "<one sentence: what the log showed>" --visit <n>`. The helper refuses an update whose `then` did not win its comparisons on this problem, keeps one file per card, snapshots the pack under `runs/adult-income-skills/versions/` first, raises the card's `horizon` (the number of problems it was updated on), and refuses a second update in the same visit.
```

`test_step.py`:

```python
    cards = [front_matter((PACK / "skill-memory" / c["file"]).read_text(encoding="utf-8"))[0] for c in manifest["cards"]]
    assert all(c["validated"] is True and c["horizon"] >= 1 for c in cards)
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, the
working memory and the updates in full):

<!-- transcript -->

Files:

```text
step_13_rsi_skill_memory/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income-skills/          SKILL.md, tools.md (skill_memory ...), schema.json, eval.md, config.md, working.md, skill-memory/{manifest.yaml, cards/*.md}
│   ├── skill-memory-meta/            SKILL.md, tools.md (read_traces, skill_memory), config.md
│   └── adult-income-curriculum/
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income-skills/{helpers/, <task>/, versions/, curve.json, exam.json}, skill-memory-meta/
```

## Governance considerations

- **Who approves what.** The validation rule (a `then` must have won its
  comparisons on this problem), one update per visit, and a snapshot before
  each - all human-written; no per-card approval.
- **The hook.** As always.
- **What the helper refuses.** An update from anyone but the meta pack; an
  unvalidated `then`; a second update per visit; any write on the exam.
- **What is and is not self-modified.** One card file (and a manifest line
  for a new card) per problem, and `working.md` every run. The tag
  vocabulary and the validation rule do not change.

## How to measure it

| Claim | Test |
|---|---|
| the memory is a skill package: manifest + a validated card with `when` / `then` / `horizon`; a working memory file | `test_memory_is_a_skill_package` |
| cards are selected by the situation's need, never by recency | `test_cards_are_selected_by_need_not_recency` |
| one localised, validated update per visit | `test_one_localised_validated_update_per_visit` |
| the pack contract for three packs | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: `working.md` rewritten, cards validated with horizons, one version per update, the exam unchanged (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 14 - the Darwin Gödel Machine lineage](../step_14_rsi_self_modifying/README.md):
the agent's own source, behind an archive and a gate. Previous:
[lesson 12 - ModularRSI](../step_12_rsi_modular/README.md).
