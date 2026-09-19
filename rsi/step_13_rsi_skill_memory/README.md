# Lesson 13 - Recuris: memory as a skill package, with a working memory

Recuris (arXiv:2608.24876) keeps two memories: an experiential one - skill
cards, each for a situation - and a working one that the agent rewrites per
task to say what it is doing and which cards apply. Here the experiential
memory is `skill-memory/manifest.yaml` plus one markdown card per
situation (front matter: `when` tags, `then`, `validated`, `horizon`), and
the working memory is `working.md`. The actor names its situation with
need tags (`small`, `categorical`, `imbalanced`, `multiclass`) and the one
new tool, `skill_memory`, selects every validated card whose tags all hold
- by the situation, never by which card is newest - then rewrites
`working.md`. After each problem the meta agent turns the log into ONE
localised, validated card update: the tool refuses a `then` that did not
win its comparisons, touches one card file, snapshots first, and raises the
card's `horizon`. The memory is files you can diff, and the gain is reported
by how many problems the package has seen.

## Getting started

Lesson 12 left the modular actors. This lesson adds
`skills/adult-income-skills/` (the actor with `skill-memory/` and
`working.md`), `skills/skill-memory-meta/`, and the tool `skill_memory`
(`need` for the actor, `update` for the meta). The package ships one card
(`onehot-for-categorical`); everything else it learns.

## How to execute it

1. The curriculum with a card update after every problem:

   ```bash
   cd rsi/step_13_rsi_skill_memory
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_13_rsi_skill_memory
   $env:FAKE_MODEL = "1"; python run.py
   ```

   No prompt: the validation rule (the value must have won its comparisons
   on this problem) is the acceptance rule, and the human wrote it.
2. Read `runs/work/adult-income-skills/skill-memory/` after the run and
   `git diff` it against `skills/`: that is the memory.
3. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-skills/SKILL.md`:

```markdown
2. Name the situation: the need tags are `small` (fewer than 1000 rows), `categorical` (any categorical column), `imbalanced` (rarest class under 0.35), `multiclass` (more than two classes). Call `skill_memory` with action `need` and `{need: [tags]}`. The tool selects every validated card whose `when` tags all hold for this need - by the situation, never by which card is newest - rewrites `working.md` with the need and the cards, and returns the cards' `then` values as preferences.
```

`skills/adult-income-skills/skill-memory/cards/onehot-for-categorical.md` -
a card is a markdown file with typed front matter:

```markdown
---
name: onehot-for-categorical
when: [categorical]
then: encode=onehot
validated: true
horizon: 1
---
```

`skills/skill-memory-meta/SKILL.md`:

```markdown
3. Take the first field of `model`, `class_weight`, `encode`, `scale` whose winning value the situation's card does not already hold (a card holds one `then`). Call `skill_memory` with action `update` once: `{card, then, when, body}` - the existing card's name when the situation has one for that field, else a new name. The tool refuses an update whose `then` did not win its comparisons on this problem, keeps one file per card, snapshots the pack under `versions/` first, and raises the card's `horizon` (the number of problems it was updated on).
```

The tool's two halves:

`../common/tools.py`:

```python
        # selection by need, not by recency: every card whose situation tags all hold, in manifest order
        chosen = [c for c in skill_cards(run.target) if c.get("validated") and set(c.get("when", [])) <= set(need)]
```

```python
        wins, losses, _ = memory.tally(rows)
        if wins.get((field, value), 0) <= losses.get((field, value), 0):
            raise ValueError(f"not validated: {then} did not win its comparisons on {run.problem} "
                             f"({wins.get((field, value), 0)} wins, {losses.get((field, value), 0)} losses); nothing lands")
        if run.visits.get("skill_update", 0) >= 1:
            raise ValueError("one card update per visit")
```

Expected output, on this machine (`FAKE_MODEL=1`):

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      0/0/0
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       0/0/0
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/0
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       0/0/0
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       0/0/0
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      0/0/0
gain by horizon (problems seen so far -> val gap, cards in the package, highest card horizon, working memory):
  horizon 1: gap +0.0000, cards 2, max horizon 1, need ['categorical', 'imbalanced'], applied ['onehot-for-categorical'], updated this problem: True
  horizon 2: gap +0.0000, cards 3, max horizon 1, need ['small'], applied [], updated this problem: True
  horizon 3: gap +0.0000, cards 3, max horizon 1, need ['small', 'imbalanced', 'multiclass'], applied ['model-when-small'], updated this problem: False
  horizon 4: gap +0.0000, cards 4, max horizon 1, need ['imbalanced', 'multiclass'], applied [], updated this problem: True
  horizon 5: gap +0.0024, cards 4, max horizon 2, need ['small', 'categorical'], applied ['onehot-for-categorical', 'model-when-small'], updated this problem: True
  horizon 6: gap +0.0646, cards 4, max horizon 3, need ['small', 'categorical', 'imbalanced'], applied ['onehot-for-categorical', 'model-when-categorical-imbalanced', 'model-when-small'], updated this problem: True
```

The `cards +/-/act` columns read 0 because this pack keeps no
`memory.json`; the package's own counts are on the horizon lines: one card
shipped, four by the end, the `model-when-small` card updated on three
problems (horizon 3). The shipped card already put Adult's memory arm at
the grid's best in 2 fits instead of 16; the cards learned on problems 1-5
give problem 6 the same +0.065 as lesson 09, with the reasons now readable
in each card's body.

Files:

```text
step_13_rsi_skill_memory/
  skills/adult-income-skills/
    SKILL.md                      name the situation, get the cards, obey them, score_test once after FREEZE
    tools.md                      Allowed: load_splits, skill_memory (need), fit_recipe, score_test, save_model
    working.md                    rewritten every run: Need and Cards
    skill-memory/manifest.yaml    the package index: name and file per card
    skill-memory/cards/*.md       one card per situation: when, then, validated, horizon, and the reason in prose
    schema.json, eval.md          lesson 07's
  skills/skill-memory-meta/
    SKILL.md                      tally the problem's pairs; one validated update of one card
    tools.md                      Allowed: read_traces, read_memory, read_pack, skill_memory (update)
  run.py                          the curriculum with a meta visit per problem; the gain-by-horizon report
  test_step.py                    the claims below
  README.md                       this lesson
```

## Governance considerations

- Who approves what: the validation rule (won its comparisons on this
  problem) approves a card update; the human wrote the rule, the need tags
  and the shipped card.
- Off switches: `MEMORY_OFF` (the actor skips the working memory and walks
  the static list); `versions/gen_NNN` before every update.
- What the model may not do, and which tool enforces it: pick a card by
  recency (the tool selects by tags, in manifest order); land an update the
  log contradicts (`skill_memory` refuses); update two cards in one visit
  (refused); fit from the meta pack (`tools.md`).
- What is and is not self-modified: the card files and the manifest.
  `SKILL.md`, the need tags and the validation rule are not. Rung: L4
  (memory consolidation under a human acceptance rule).

## How to measure it

| Claim | Test |
|---|---|
| a skill card is selected by the working-memory need, not by recency; `working.md` says which; the probes obey it | `test_a_card_is_selected_by_need_not_by_recency` |
| an update is localised to one card (plus its manifest line) and validated before it lands; a contradicted one is refused; one per visit | `test_an_update_is_localised_to_one_card_and_validated_first` |
| the horizon report shows the gain per sequence length: cards and horizons grow, the gap does not fall, the versions are files | `test_the_horizon_report_shows_the_gain_per_sequence_length` |

Scorecard fields reported: all fourteen (the card fields at 0 - the memory
is the package), plus `skill_cards`, `horizon` and `update` per problem.
Run `python run_tests.py rsi` from the repo root.

## Next lesson

Next: [14 - the Darwin Gödel Machine lineage](../step_14_rsi_self_modifying/README.md):
the agent's own source, behind an archive and a gate. Previous:
[12 - ModularRSI](../step_12_rsi_modular/README.md).
