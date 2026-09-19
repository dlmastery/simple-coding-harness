# Lesson 06 - The RSI harness: the first file a later run reads that an earlier run wrote

Two packs. The actor (`adult-income`) trains under the 24-fit budget and
*proposes* its recipes shaped by the memory cards in `memory.json`: a card is
`IF <profile predicate> THEN prefer / forbid <one field value>`, with
`evidence` and `counter` counts, typed by `memory.schema.json` so that a
script can enforce it (`fit_recipe.py` refuses a recipe a forbid card rules
out; there is no free-text field for a diary entry or the word "test"). The
verifier (`adult-income-verifier`) writes the cards, and no one grades their
own homework: its whole input is `{recipe, val_score, error}` rows and the
profile from `read_traces.py` - never the actor's transcript, the test
split or the intent - and the actor cannot write a card at all (`write_card`
is not in its `tools.md`; the script refuses). `MEMORY_OFF` is the off
switch: `--memory off` on an arm or `{"memory": "off"}` in `config.json`
gives lesson 01's numbers exactly. This is L4 in the framework paper's terms:
deployment feedback revises persistent state under an acceptance rule the
human wrote (the verifier contract, the card schema, the demotion rule).

## Getting started

Lesson 05 left the generated graph pack. This lesson adds two packs under
`.claude/skills/` - `adult-income/` (`SKILL.md`, `tools.md`, `schema.json`,
`memory.schema.json`, `memory.json` = `[]`) and `adult-income-verifier/`
(`SKILL.md`, `tools.md`, `memory.schema.json`) - and three scripts:
`read_memory.py`, `write_card.py`, `read_traces.py`. A run **changes the
pack**: `memory.json` fills with cards. Reset with `git checkout --
.claude/skills/adult-income/memory.json .agents/skills/adult-income/memory.json`
(or write `[]` into both) and `rm -rf runs`.

## How to execute it

1. Type the prompt (two problems, so the cards learned on the first can
   act on the second):

   ```text
   Problem 1 is ../tasks/01_adult_income.json, problem 2 is ../tasks/02_breast_cancer.json. On problem 1: use the adult-income skill for the control arm (memory off) and then for the memory arm, then use the adult-income-verifier skill to write the cards. Then on problem 2: the adult-income skill for the control arm and for the memory arm. Report the four scorecards side by side and which cards applied on problem 2.
   ```

   The commands the agent runs, per arm and for the verifier:

   ```bash
   python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --memory off
   python ../tools/fit_recipe.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --recipes @.claude/skills/adult-income/schema.json
   python ../tools/score_test.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/scorecard.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control
   # the memory arm: the same without --arm control / --memory off; with cards, read_memory + batches of fit_recipe --recipes '[...]'
   python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope problem --tally
   python ../tools/write_card.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --as .claude/skills/adult-income-verifier --cards '[{"if": {...}, "then": {...}, "evidence": 1, "counter": 0}, ...]'
   ```

   No approval prompt in this lesson: the acceptance rule is the verifier
   contract plus the card schema, both enforced by `write_card.py`.
   PowerShell: put the cards in a file and pass `--cards '@cards.json'`.

2. Try the refusals by hand: a card with a `note` field, or with `"prefer":
   "test"` (`write_card.py` answers `not a card: ...`); `fit_recipe.py` on a
   recipe a forbid card rules out (`no fit spent`); `write_card.py --as
   .claude/skills/adult-income` (the actor: `not in adult-income's tools.md`).

3. Headless, as recorded: `claude -p "<the prompt>" --allowedTools
   "Bash,Read,Write,Edit,Skill"` (about six minutes). Tests: `python
   run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income/SKILL.md` - the actor's search policy in words,
and the rule it may not break:

```markdown
---
name: adult-income
description: Train a classifier for a curriculum problem under a 24-fit budget, proposing recipes shaped by the memory cards in memory.json (the memory arm), or walking the static list with the memory off (the control arm). Use in rsi/step_06_rsi_harness and later, when the pack has memory.json and a verifier pack writes to it.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# RSI harness: the inner pack (the actor)

## Procedure
2. Search policy: obey-memory.
   - No applicable card (every control arm; a memory arm with an empty memory): walk `schema.json` -> `recipes` in order, in one call:
     `python ../tools/fit_recipe.py --pack P --task T [--arm control] --recipes @P/schema.json`
   - Otherwise take, per field, the applicable `prefer` card with the most `evidence` minus `counter` as the preferred value (`python ../tools/read_memory.py --pack P --task T` lists them under `preferred`; a tie is no preference). Then, in calls of up to eight recipes each, in this order until a result says `FREEZE`:
     a. Probe: one recipe per model of `schema.json` -> `models`, the preferred model first, each with the preferred `scale` / `encode` / `class_weight` (defaults `yes` / `onehot` / `none`) at its middle hyper value (`logreg` 1, `rf` 16, `hgb` 0.1). The probe winner is the model belief.
     b. The believed model's family: its recipes from `recipes` (middle hyper value) first, then its hyper variants; inside each group the recipes carrying the most preferred values first (`class_weight` and `encode` count 2, `scale` and `hyper` 1), then grid order.
     c. The rest of the grid of `fields`, grid order (model, hyper, scale, encode, class_weight).

## Rules
- Never write a card: that is the verifier's job, and `write_card` is not in your `tools.md`. Only a meta pack may patch this pack.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`. No card is read or written; you run the static order. Same 24 fits, so the numbers can be compared.
```

`.claude/skills/adult-income-verifier/SKILL.md` - the contract, verbatim
(`lint_pack` refuses a verifier pack without it), and the rule that turns a
log into cards:

```markdown
---
name: adult-income-verifier
description: Turn the fit log of one problem into memory cards for the actor pack adult-income. Use after the actor's memory arm on a problem is frozen and scored; input is the log and the profile, nothing else.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

## Procedure
1. Read the fits of this problem's memory arm, with the pairwise tally:
   `python ../tools/read_traces.py --pack P --task T --scope problem --tally`
2. Tally every pair of rows whose recipes differ in exactly one field (two models at their default hyper value count as differing in `model` only): the higher `val_score` is a win for its value of that field and a loss for the other; a pair where one side errored marks the erroring value. The script's `tally` is the same count; check yours against it.
3. Per field, write ONE `prefer` card for the value with the most wins net of losses (`evidence` 1) - if it has any net wins at all - and a `counter` 1 card (same `if`/`then`, `evidence` 0) for every value that lost more than it won. Write a `forbid` card (`evidence` 1) for a value that errored.
```

`../tools/_lib/memory.py` - a card is typed; the words "test" and "intent"
cannot get in; a counterexample demotes:

```python
FORBIDDEN_WORDS = ("test", "intent")


def validate_card(card, schema=CARD_SCHEMA):
    """A card is typed. Anything outside the type - a reason, an intent, the word test - is refused."""
    jsonschema.validate(card, schema)
    text = json.dumps(card).lower()
    for word in FORBIDDEN_WORDS:
        if word in text:
            raise ValueError(f"a card may not mention {word!r}")
    return card
```

```python
def active(card):
    """Some evidence, and at most half as many counterexamples: one counter demotes a one-evidence card."""
    return card["evidence"] >= MIN_EVIDENCE and card["evidence"] >= 2 * card["counter"]
```

`../tools/fit_recipe.py` - a forbid card is a gate, not advice:

```python
    cards = [] if run.memory_off else memory.load(run.memory_path)
    card = memory.forbidden(rec, cards, run.profile)
    if card is not None:
        raise ValueError(f"a forbid card rules this recipe out: {json.dumps(card['then'])} (no fit spent)")
```

`../tools/read_traces.py` - the verifier's whole input, and the shape that
*is* the contract:

```python
    if a.scope == "problem":
        raw = run.fit_rows(arm=a.of)
        rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]} for r in raw]
```

The recorded run (Claude Code 2.1.278, headless, 28 turns, 347 s; the
agent piped the fit results through a one-line `python -c` formatter of its
own, trimmed here):

```text
[Skill adult-income]
agent> Memory is empty. Problem 1, control arm: open the arm.
$ python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --memory off
agent> No applicable cards -> walk the static list in one call.
$ python ../tools/fit_recipe.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --recipes @.claude/skills/adult-income/schema.json
agent> FREEZE. Best val_score is 0.9172, first reached at fit 18: hgb, 0.1, yes, onehot, balanced.
$ python ../tools/score_test.py ... --arm control --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced && python ../tools/save_model.py ... && python ../tools/scorecard.py ... --arm control
agent> Problem 1 control done: best val 0.9172, test 0.9034, 24 fits, 16 wasted. Now problem 1 memory
arm (memory is empty, so the same static walk applies).
$ python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
$ python ../tools/fit_recipe.py ... --recipes @.claude/skills/adult-income/schema.json
agent> Same numbers (same seed, same order). Best is fit 18 again.
[Skill adult-income-verifier]
$ python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope problem --tally
{"scope": "problem", "rows": [{"recipe": {...}, "val_score": 0.9114, "error": null}, ... 24 rows], "profile": {...},
 "tally": {"wins": [...], "losses": [...], "errored": []}, "cards_by_rule": [ ... 9 cards ... ]}
$ python ../tools/write_card.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --as .claude/skills/adult-income-verifier --cards '[
{"if":{"key":"n_rows","op":">=","value":1000},"then":{"field":"model","prefer":"hgb"},"evidence":1,"counter":0},
{"if":{"key":"n_rows","op":">=","value":1000},"then":{"field":"model","prefer":"logreg"},"evidence":0,"counter":1},
{"if":{"key":"n_rows","op":">=","value":1000},"then":{"field":"model","prefer":"rf"},"evidence":0,"counter":1},
{"if":{"key":"n_features","op":">=","value":10},"then":{"field":"scale","prefer":"yes"},"evidence":1,"counter":0},
{"if":{"key":"n_features","op":">=","value":10},"then":{"field":"scale","prefer":"no"},"evidence":0,"counter":1},
{"if":{"key":"has_categorical","op":"==","value":1},"then":{"field":"encode","prefer":"onehot"},"evidence":1,"counter":0},
{"if":{"key":"has_categorical","op":"==","value":1},"then":{"field":"encode","prefer":"ordinal"},"evidence":0,"counter":1},
{"if":{"key":"imbalance","op":"<","value":0.35},"then":{"field":"class_weight","prefer":"none"},"evidence":1,"counter":0},
{"if":{"key":"imbalance","op":"<","value":0.35},"then":{"field":"class_weight","prefer":"balanced"},"evidence":0,"counter":1}]'
{"cards": 9, "written": 9, "added": 9, "demoted": 0, "refused": 0, "by": "adult-income-verifier", ...}
$ python ../tools/load_splits.py ... --task ../tasks/02_breast_cancer.json --arm control --memory off
$ python ../tools/fit_recipe.py ... --task ../tasks/02_breast_cancer.json --arm control --recipes @.claude/skills/adult-income/schema.json
agent> Best val 0.9954, first at fit 18: hgb, 0.1, yes, onehot, balanced.
agent> Problem 2 control done. Now the memory arm - open it and read which cards apply.
$ python ../tools/load_splits.py ... --task ../tasks/02_breast_cancer.json && python ../tools/read_memory.py ... --task ../tasks/02_breast_cancer.json
agent> One applicable card: scale: yes (n_features 30 >= 10). No preferred model / encode /
class_weight, so probe uses defaults onehot / none in grid model order.
$ python ../tools/fit_recipe.py ... --recipes '[{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"none"}, {"model":"rf","hyper":16,...}, {"model":"hgb","hyper":0.1,...}]'
agent> Probe winner: hgb (0.9949 vs logreg 0.9937, rf 0.9917). Model belief = hgb. Step b: the hgb
family from recipes (scale=yes ones first), then hyper variants.
$ python ../tools/fit_recipe.py ... --recipes '[ 8 hgb recipes ]'
$ python ../tools/fit_recipe.py ... --recipes '[ 8 more: hgb at 0.05 and 0.3 ]'
agent> New best: hgb 0.3 yes onehot none at 0.9966. Five fits left - the remaining hyper variants.
$ python ../tools/fit_recipe.py ... --recipes '[ 5 hgb recipes ]'
FREEZE True fits_left 0
$ python ../tools/score_test.py ... --recipe model=hgb,hyper=0.3,scale=yes,encode=onehot,class_weight=none && ... scorecard.py ...
agent> ## Scorecards
| | P1 adult_income control | P1 memory | P2 breast_cancer control | P2 memory |
| best val_score | 0.9172 | 0.9172 | 0.9954 | 0.9966 |
| test_score     | 0.9034 | 0.9034 | 0.9844 | 0.9883 |
| best recipe    | hgb 0.1 yes onehot balanced | same | hgb 0.1 yes onehot balanced | hgb 0.3 yes onehot none |
| fits used / wasted | 24 / 16 | 24 / 16 | 24 / 0 | 24 / 0 |
| cards active   | 0 | 0 | 0 | 4 |
Problem 1's two arms are identical by construction: memory was empty, so the memory arm walked the
same static list as the control arm.
Which cards applied on problem 2 (profile: n_rows 569, n_features 30, n_classes 2, imbalance 0.373,
has_categorical 0): 1 of 4 - n_features >= 10 -> prefer scale: yes. Did not apply: n_rows >= 1000 ->
hgb (569 rows), has_categorical == 1 -> onehot (no categoricals), imbalance < 0.35 -> class_weight
none (0.373). So the memory arm had only a scale preference and no model belief; it ran the probe,
committed to hgb, and spent the remaining 21 fits on the hgb family - which is where the gain came
from: the static list never leaves hyper 0.1, while the family search found hgb at learning rate 0.3
(0.9966 val / 0.9883 test vs 0.9954 / 0.9844).
One observation for the series: the model card is keyed on n_rows >= 1000, so hgb's dominance on
problem 1 couldn't transfer to a 569-row problem even though it won here too.
[28 turns, 347 s]
```

What to notice: the memory arm's recipes are the agent's own choices,
following the policy text - and they land on the same 0.9966 / 0.9883 the
test's scripted policy finds. The agent's closing observation is exactly
the superstition problem lesson 07's curriculum is built around (a card
conditioned on `n_rows` cannot know whether the signal is linear), and it
was made from the profile and the numbers, not from the data. The verifier
never saw the actor's messages; it saw 24 rows and a profile.

Files:

```text
step_06_rsi_harness/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/          the actor
│   ├── SKILL.md, tools.md, schema.json
│   ├── memory.schema.json                IF profile THEN prefer / forbid one field value
│   └── memory.json                       [] shipped; the cards land here
├── .claude/skills/adult-income-verifier/ SKILL.md (the contract), tools.md, memory.schema.json
├── .agents/skills/...                    the same
└── runs/adult-income/{adult_income,breast_cancer}/   state.json (both arms), traces.jsonl, scorecards
```

## Governance considerations

- **Who approves what.** The human wrote the acceptance rule - the
  verifier contract, `memory.schema.json`, the demotion rule - and the
  system applies it without asking: this is the first lesson where a run
  changes a file a later run reads. No human sits in the loop per card;
  the human's decision is the rule and the off switch.
- **The hook.** As before (locked test). No approval call exists in this
  lesson.
- **What the script refuses.** `write_card.py`: a card outside the schema
  (an extra field, an unknown profile key, both `prefer` and `forbid`), a
  card mentioning `test` or `intent`, any card under `MEMORY_OFF`, any card
  from a pack whose `tools.md` lacks `write_card` (the actor).
  `fit_recipe.py`: a recipe a forbid card rules out (no fit spent).
  `read_traces.py` cannot return anything but rows and the profile.
  `fit_recipe.py` / `score_test.py`: refused for the verifier.
- **What is and is not self-modified.** `memory.json` is - by the verifier,
  under the contract. `SKILL.md`, `schema.json`, the policy line and
  `tools.md` are not: "only a meta pack may patch this pack" (lesson 09).
  Autonomy attribution: the system decides *which cards*, from evidence;
  the human decided what a card may be, who may write one, and how one
  dies.

## How to measure it

| Claim | Test |
|---|---|
| `MEMORY_OFF` (`config.json`) reproduces lesson 01's numbers exactly and refuses every card | `test_memory_off_reproduces_lesson_01_exactly` |
| the verifier's input is rows `{recipe, val_score, error}` and the profile, nothing else; it writes typed cards (`encode: onehot` among them) | `test_verifier_sees_only_rows_and_profile_and_writes_typed_cards` |
| a card with a note, the word `test` or `intent`, both prefer and forbid, or an unknown key is refused; the actor cannot write a card, the verifier cannot fit | `test_write_card_refuses_test_intent_and_extra_fields` |
| a planted wrong card is demoted by one counterexample; a forbid card refuses a fit and no budget is spent | `test_planted_wrong_card_is_demoted_and_forbid_card_refuses_a_fit` |
| after problem 1, the memory arm on problem 2 beats the control arm (val and test) at the same budget, wastes no more fits, and reaches a hyper variant the static list never visits | `test_memory_arm_beats_control_on_problem_2_after_problem_1` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecards on this machine (seed 0): problem 1 memory = control (val 0.9172,
test 0.9034, wasted 16); problem 2 control val 0.9954 / test 0.9844, memory
val 0.9966 / test 0.9883, wasted 0 / 0, cards active 4. Breast cancer is
nearly saturated for this recipe space; the gain is small and real.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 07 - the proof](../step_07_proof/README.md): the learning curve over
six problems and the exam. Previous:
[Lesson 05 - the graph writer](../step_05_meta_generates_graph/README.md).
