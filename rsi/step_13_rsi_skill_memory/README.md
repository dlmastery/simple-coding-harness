# Lesson 13 - Recuris: memory as a skill package, with a working memory

Recuris (arXiv:2608.24876) keeps two memories: an experiential one - skill
cards, each for a situation - and a small working memory the actor rewrites
per run ("what I am doing, which cards apply"). Here the cards are markdown
files under `skill-memory/cards/` with front matter (`when` tags, one
`then`, `validated`, `horizon`), listed in `manifest.yaml`; the actor names
its situation with need tags (`small`, `categorical`, `imbalanced`,
`multiclass`) and `skill_memory.py --action need` selects every validated
card whose tags all hold - by the situation, never by recency - and rewrites
`working.md`. The meta pack turns one problem's log into ONE localised,
validated card update (`--action update`): the script refuses a `then` that
did not win its comparisons, snapshots the pack, keeps one file per card
and raises the card's `horizon`. The memory is git-native: files you can
diff. L4: persistent state revised from feedback under a validation rule
the human wrote.

## Getting started

New packs: `.claude/skills/adult-income-skills/` (the actor with
`skill-memory/` and `working.md`; it ships one card,
`onehot-for-categorical`) and `.claude/skills/skill-memory-meta/`; the
curriculum skill from lesson 07 with the meta update in the verifier's
place. One script: `../tools/skill_memory.py` (`tags`, `list`, `need`,
`update`). Reset after a run: restore `skill-memory/` and `working.md` from
git (`git checkout -- .claude/skills/adult-income-skills`), mirror, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the six curriculum problems with the skill-memory meta pack updating one card after each, then the exam, and report the curve, the exam and each card's horizon.
   ```

   Per problem the memory arm starts with the situation, and the meta pack
   ends with one update:

   ```bash
   python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action tags
   python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action need --need categorical,imbalanced
   python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action update --as .claude/skills/skill-memory-meta --card hgb-for-categorical --then model=hgb --when categorical,imbalanced --body "hgb won 6 of 6 comparisons on adult_income" --visit 1
   ```

   No approval prompt: the validation rule decides.

2. By hand: an update whose value lost its comparisons is refused (`not
   validated: encode=ordinal did not win ...; nothing lands`); a second update
   in the same visit is refused; `--action update --as .claude/skills/adult-income-skills`
   (the actor) is refused - `the meta pack updates cards`.

3. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-skills/skill-memory/cards/onehot-for-categorical.md`
- a card is a markdown file:

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

`.claude/skills/skill-memory-meta/SKILL.md` - one update, validated first:

```markdown
## Procedure
3. Take the first field of `model`, `class_weight`, `encode`, `scale` whose winning value the situation's card does not already hold (a card holds one `then`; a card "for the situation" is one whose `when` tags all hold for this need). Update once, with the existing card's name when the situation has one for that field, else a new name (`<value>-for-<tag>`):
   `python ../tools/skill_memory.py --pack P --task T --action update --as M --card <name> --then <field>=<value> --when <tag,tag> --body "<one sentence: what the log showed>" --visit <n>`
   The script refuses an update whose `then` did not win its comparisons on this problem, keeps one file per card, snapshots the pack under `runs/adult-income-skills/versions/` first, raises the card's `horizon` (the number of problems it was updated on), and refuses a second update in the same visit.
```

`../tools/skill_memory.py` - selection by need, and the validation rule:

```python
    if a.action == "need":
        require_tool(run.pack_dir, "skill_memory")
        need = [t.strip() for t in (a.need or "").split(",") if t.strip()] or need_tags(run.profile)
        chosen = [c for c in skill_cards(run.pack_dir) if c.get("validated") and set(c.get("when", [])) <= set(need)]
```

```python
    rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]} for r in run.fit_rows()]
    wins, losses, _ = memory.tally(rows)
    if wins.get((field, value), 0) <= losses.get((field, value), 0):
        raise ValueError(f"not validated: {a.then} did not win its comparisons on {run.problem} "
                         f"({wins.get((field, value), 0)} wins, {losses.get((field, value), 0)} losses); nothing lands")
```

The recorded run (Claude Code 2.1.278, headless, 70 turns, 1460 s; the
arms' fit calls trimmed to the agent's notes and the tables):

```text
[Skill adult-income-curriculum]
agent> Problem 01, memory arm: need tags small? no (6000 rows); categorical, imbalanced.
$ python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action need --need categorical,imbalanced
{"need": ["categorical", "imbalanced"], "cards": [{"name": "onehot-for-categorical", "when": ["categorical"], "then": "encode=onehot", "horizon": 1}], "prefer": {"encode": "onehot"}, "working": ".../working.md"}
... (the probe, then the hgb family; FREEZE; score once; scorecard) ...
$ python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action update --as .claude/skills/skill-memory-meta --card hgb-for-categorical-imbalanced --then model=hgb --when categorical,imbalanced --body "hgb won every model comparison on adult_income" --visit 1
{"card": "hgb-for-categorical-imbalanced", "file": "skill-memory/cards/hgb-for-categorical-imbalanced.md", "horizon": 1, "version": "gen_001", "new": true, "wins": 16, "losses": 0}
agent> Meta updates, one per visit (card -> horizon):
| 1 | adult_income | new hgb-for-categorical-imbalanced (model=hgb), gen_001 |
| 2 | breast_cancer | new hgb-for-small (model=hgb), gen_002 |
| 3 | wine | nothing - all 24 fits tied at 1.0, tally had 0 wins / 0 losses |
| 4 | digits | new hgb-for-imbalanced-multiclass (model=hgb), gen_003 |
| 5 | synth_shift_a | hgb-for-small updated -> model=logreg, when small,categorical, gen_004 |
| 6 | synth_shift_b | new none-for-small-categorical-imbalanced (class_weight=none), gen_005 |
$ python ../tools/curve.py --pack .claude/skills/adult-income-skills --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      0/0/0
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       0/0/0
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/0
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       0/0/0
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       0/0/0
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      0/0/0
agent> never_negative: true; wasted fits total 6 (memory) vs 33 (control).
Final horizons (skill_memory.py --action list): onehot-for-categorical [categorical] encode=onehot - 1;
hgb-for-categorical-imbalanced [categorical, imbalanced] model=hgb - 1; hgb-for-small [small, categorical]
model=logreg - 2; hgb-for-imbalanced-multiclass [imbalanced, multiclass] model=hgb - 1;
none-for-small-categorical-imbalanced [small, categorical, imbalanced] class_weight=none - 1.
$ python ../tools/exam.py --pack .claude/skills/adult-income-skills --task ../tasks/07_exam.json --seeds 0,1,2,3,4
exam: memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap 0.0306; pack unchanged: False; no card written: True
agent> pack_unchanged did not hold as printed (False). The per-boot checksums show the only differing file is
working.md, rewritten by skill_memory.py --action need on the seed-0 memory arm (step 2 of the actor's
procedure). All cards, the manifest and every other pack file are identical across all 10 exam boots; no
card changed. The check flags the actor's own working-memory rewrite, not a change to the memory.
agent> Report names every applicable card that did not transfer - the script reported cards_applicable: []
and did_not_transfer: [] (its card-transfer check reads memory.json cards, not the skill-memory cards), so it
named none. By my reading of the log, two selected cards did not transfer: hgb-for-small (model=logreg -
logreg lost every probe on all 5 seeds; hgb won) and onehot-for-categorical (ordinal beat onehot on seed 0,
where the memory arm lost).
[70 turns, 1460 s]
```

What to notice, honestly: the memory arm reaches the static grid's answer
in 6 wasted fits over the curriculum where the grid needs 33 - the best
figure in the series - because a selected card's `then` goes straight into
the probe; the val gaps are lesson 07's except breast cancer (0 here: the
skill memory had one card, `encode=onehot`, which is a no-op on a table
without categoricals, so the probe ran the default order). The agent
caught two things the scripts got wrong at recording time, and both are
fixed on this page's account: `exam.py` flagged `working.md` - the actor's
own scratch, rewritten by design - as a pack change (it now ignores it,
like lesson 11's `plan.json`), and its "did not transfer" check reads
`memory.json` cards only, so for a skill package it names none; the agent
read the exam log and named `hgb-for-small` (updated to `model=logreg` on
problem 5 and wrong on every exam seed) and `onehot-for-categorical` (wrong
on seed 0). `curve.py`'s cards columns read `memory.json` too and show 0
for this pack; the horizon list above is the card report. The updated
card is the honest one: `hgb-for-small` flipped to `logreg` on the linear
synthetic table and misled the exam - a horizon of 2 is two problems, not
two agreeing problems.

Files:

```text
step_13_rsi_skill_memory/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-skills/
│   ├── SKILL.md, tools.md, schema.json, eval.md
│   ├── skill-memory/manifest.yaml, cards/onehot-for-categorical.md    the experiential memory
│   └── working.md                                                    the working memory, rewritten per run
├── .claude/skills/skill-memory-meta/         SKILL.md, tools.md
├── .claude/skills/adult-income-curriculum/
└── .agents/skills/...
```

## Governance considerations

- **Who approves what.** The validation rule (the value won its pairwise
  comparisons on this problem's log), written by the human; one update per
  visit; the actor may select cards and may not update them.
- **The hook.** The locked test.
- **What the script refuses.** An unvalidated `then`; a second update per
  visit; an update by the actor; a fit for the meta pack.
- **What is and is not self-modified.** One card file (and a manifest line
  for a new card) per problem, with a snapshot under `versions/`;
  `working.md` per run. `SKILL.md`, `schema.json` and the policy are not.

## How to measure it

| Claim | Test |
|---|---|
| a card is selected by the working-memory need, not by recency (a newer card for another situation is not selected) | `test_card_selected_by_need_not_recency` |
| an update is localised to one card file (+ manifest), validated before it lands, once per visit; the actor cannot update, the meta pack cannot fit | `test_update_is_localised_validated_and_once_per_visit` |
| over the curriculum the horizons grow, the gain per problem is never negative, and the curve is complete | `test_horizon_report_over_the_curriculum` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 14 - the Darwin Goedel Machine lineage](../step_14_rsi_self_modifying/README.md).
Previous: [Lesson 12 - ModularRSI](../step_12_rsi_modular/README.md).
