# Lesson 06 - The RSI harness: the first file a later run reads that an earlier run wrote

Everything before this page ran the same way every time. This page adds one
file, `memory.json`, and one contract about who may write it. The actor pack
(`adult-income`) searches the recipe space under the cards it finds there:
a card is a typed constraint on the *next* proposal - `IF` a profile
predicate `THEN` prefer or forbid one field value, with `evidence` and
`counter` counts - and `fit_recipe` refuses a forbidden recipe outright.
The verifier pack (`adult-income-verifier`) is the only writer, and it boots
blind: its input is `{recipe, val_score, error}` rows and the profile, from
one helper, never the actor's transcript, the test split or the intent;
`write_card` refuses a card that mentions either. No one grades their own
homework. The off switch is one line in `config.md`: `memory: off` is
`MEMORY_OFF`, the memory arm runs the static order, and its numbers must be
the control arm's exactly. The recorded run makes the recursion visible in
one lesson: the control arm and the memory arm (empty memory: the same 24
fits, the same numbers), the verifier writing the first cards from the log,
then a second memory arm that boots them. This is the framework paper's L4:
deployment feedback revises persistent state under an acceptance rule the
human wrote (the verifier contract, the schema, the demotion rule).

## Getting started

Prerequisites: lesson 01 (the runtime; the control arm here *is* lesson
01's walk) and lesson 02 (the log). This lesson adds two packs: the actor
(`SKILL.md`, `tools.md`, `schema.json`, `memory.json` = `[]`,
`memory.schema.json`, `config.md`) and the verifier (`SKILL.md`, `tools.md`,
`memory.schema.json`), and three contracts - `read_memory`, `read_traces`,
`write_card`. After a run, `memory.json` holds cards in both mirrors.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income skill on ../tasks/01_adult_income: run the control arm, then the memory arm. Then use the adult-income-verifier skill to write the cards from the memory arm's log. Then run the adult-income memory arm again as arm memory-r2 with the cards, and report what changed.
   ```

   The agent builds the actor's helpers, runs the control arm (static list,
   one call), the memory arm (no applicable card: the same static list),
   scores each once; builds the verifier's two helpers, tallies the memory
   arm's log pairwise, writes the cards; then opens `memory-r2`, whose
   `read_memory --order obey-memory` now returns a probe shaped by the
   cards, fits in batches of eight until `FREEZE`, scores once.

2. No human approval in this lesson: the acceptance rule is the verifier
   contract and the schema, both written by the human beforehand. The hook
   blocks `score_test` until `"frozen": true`.

3. Headless, as recorded:

   ```bash
   claude -p "Use the adult-income skill on ../tasks/01_adult_income: run the control arm, then the memory arm. Then use the adult-income-verifier skill to write the cards from the memory arm's log. Then run the adult-income memory arm again as arm memory-r2 with the cards, and report what changed." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the memory starts empty and
   the schema types a card; `config.md` carries both switches; the verifier
   is blind by contract and refuses `test` / `intent` in a card; the actor
   never writes a card and states the obey-memory policy; the pairwise rule
   is stated with its thresholds. `RSI_LIVE=1`: three arms each with 24
   fits, frozen, one test score after `FREEZE`; the memory arm's best val
   equals the control arm's (an empty memory changes nothing); `memory.json`
   holds cards with exactly the four keys, no `test`, no `intent`, no
   duplicate; `memory-r2` ran with `cards_active` ≥ 1; the `write_card`
   event names the verifier; both mirrors equal.

5. To reset: restore the two packs (`git checkout -- .claude .agents`, or
   copy them from `../step_06_rsi_harness` in a fresh clone) and `rm -rf runs`.
   The live test keeps a pristine copy under the system temp directory and
   restores from it before every run.

## What it looks like

`.claude/skills/adult-income/memory.schema.json` - a card is exactly this:

```json
{
 "title": "memory card: IF profile THEN prefer or forbid one field value",
 "type": "object",
 "additionalProperties": false,
 "required": ["if", "then", "evidence", "counter"],
 "properties": {
  "if": {"required": ["key", "op", "value"], "properties": {"key": {"enum": ["n_rows", "n_features", "n_classes", "imbalance", "has_categorical"]}, "op": {"enum": [">", "<", ">=", "<=", "=="]}, "value": {"type": "number"}}},
  "then": {"required": ["field"], "properties": {"field": {"enum": ["model", "hyper", "scale", "encode", "class_weight"]}, "prefer": {}, "forbid": {}}, "oneOf": [{"required": ["prefer"]}, {"required": ["forbid"]}]},
  "evidence": {"type": "integer", "minimum": 0},
  "counter": {"type": "integer", "minimum": 0}
 }
}
```

`.claude/skills/adult-income/config.md` - the off switches, one line each:

```markdown
---
memory: "on"
meta: "on"
---
# Off switches

`memory: off` is MEMORY_OFF: no card is read or written on any arm of this pack; the memory
arm runs the static order and must reproduce the control arm's numbers exactly (the
delete-the-file check). `memory: frozen` reads the cards but refuses every `write_card` (the
exam). `meta: off` is META_OFF: a meta pack proposes nothing and the actor pack stays
byte-identical between problems. Flip a line, rerun, compare.
```

`.claude/skills/adult-income/SKILL.md` - the search policy the actor runs
under the cards (the same text `read_memory --order obey-memory` implements):

```markdown
   - Search policy: obey-memory. No applicable card (every control arm; a memory arm with an empty memory): walk `schema.json -> recipes` in order, in one call. Otherwise take, per field, the `preferred` value `read_memory` prints (the applicable `prefer` card with the most `evidence - counter`; a tie is no preference) and, in calls of up to eight recipes, in this order until a result says `FREEZE`:
     a. Probe: one recipe per model of `schema.json -> models`, the preferred model first, each with the preferred `scale` / `encode` / `class_weight` (defaults `yes` / `onehot` / `none`) at its middle hyper value. The probe winner is the model belief.
     b. The believed model's family: its static recipes (middle hyper value) first, then its hyper variants; inside each group the recipes carrying the most preferred values first (`class_weight` and `encode` count 2, `scale` and `hyper` 1), then grid order.
     c. The rest of the grid of `fields`, grid order (model, hyper, scale, encode, class_weight).
```

`.claude/skills/adult-income-verifier/SKILL.md` - the contract line and the
rule that turns a log into cards:

```markdown
Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

4. The rule, per field: ONE `prefer` card for the value with the most wins net of losses (`evidence` 1, `counter` 0) if that net is positive; a counter card (`evidence` 0, `counter` 1, the same `if` and `then`) for every value that lost more than it won; a `forbid` card (`evidence` 1) for a value that errored. A card's `if` is the side of the field's threshold this profile is on - `class_weight` -> `imbalance` 0.35; `encode` -> `has_categorical` == 0 / 1; `scale` -> `n_features` 10; `model` -> `n_rows` 1000; `hyper` -> `n_classes` 3 - written `{"key": ..., "op": ">=" or "<" (== for has_categorical), "value": <the threshold>}`. The helper's `cards_by_rule` is this list; write it in one call:
   `write_card P T --as V --cards <the list>`
```

`.claude/skills/adult-income-verifier/tools.md` - what `write_card` refuses:

```markdown
- `write_card(pack, task, as, cards)` - refuse unless `as` is the verifier pack (`"error": "only the verifier writes cards"`); refuse when the task's `role` is `exam` or the memory arm's state says memory `frozen` (`"error": "memory frozen"`); refuse a card with any key beyond `if`, `then`, `evidence`, `counter`, an `if.key` outside the five profile keys, an `if.op` outside `> < >= <= ==`, a `then.field` outside the five recipe fields, `then` without exactly one of `prefer` / `forbid`, or whose serialised text contains `test` or `intent`. Merge into `<pack>/memory.json` (both mirrors): a card with the same `if` and `then` adds its `evidence` and `counter` to the one on disk, any other is appended; a merged card whose `counter * 2 >= evidence` is `demoted`. Append `{"event": "write_card", "as", "n", "new", "demoted"}` to the memory arm's trace and print those counts.
```

`test_step.py` - the live assertions that carry the lesson:

```python
    assert cards["control"]["best_val_score"] == cards["memory"]["best_val_score"], "an empty memory must give the control arm's numbers"
    assert cards["control"]["cards_active"] == 0 and cards["memory-r2"]["cards_active"] >= 1
    memory = json.loads((ACTOR / "memory.json").read_text(encoding="utf-8"))
    assert memory and all(set(c) == {"if", "then", "evidence", "counter"} for c in memory)
    assert "test" not in json.dumps(memory) and "intent" not in json.dumps(memory)
```

The recorded run (Claude Code 2.1.278, headless; tool results trimmed):

```text
[Skill adult-income]
[Read tools.md]  [Read schema.json]  [Read memory.schema.json]  [Read config.md]  [Read memory.json]  [Read ../tasks/01_adult_income/intent.md]
[Write runs/adult-income/helpers/tools.py (one module: load_splits, read_memory, fit_recipe, score_test, save_model, scorecard)]
agent> Now the control arm: open it, then walk the static list in one call.
$ python runs/adult-income/helpers/tools.py load_splits .claude/skills/adult-income ../tasks/01_adult_income --arm control --memory off
{"arm": "control", "seed": 0, "problem": "adult_income", "profile": {"n_rows": 6000, "n_features": 14, "n_classes": 2, "imbalance": 0.239, "has_categorical": 1}, "split": {"train": 3300, "val": 900, "private": 600, "test": 1200}, ...}
$ python -c "import json; json.dump(json.load(open('.claude/skills/adult-income/schema.json'))['recipes'], open('runs/adult-income/helpers/static.json','w'))" && python runs/adult-income/helpers/tools.py fit_recipe ... --arm control --recipes @runs/adult-income/helpers/static.json | ...
1 0.9114  {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
2 0.911   ...
... (17 0.9177 hgb onehot none; 24 rows)
fits_left 0 FREEZE True
$ R='{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}' && python runs/adult-income/helpers/tools.py score_test ... --arm control --recipe "$R" && ... save_model ... && ... scorecard ... --arm control
{"arm": "control", "recipe": {...}, "test_score": 0.9049, "error": null, "test_scored": 1}
{"problem": "adult_income", "arm": "control", "seed": 0, "n_fits": 24, "fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9177, ..., "test_score": 0.9049, "test_scored_once": true, "test_touched_before_freeze": false, "cards_active": 0, "cards_added": 0, "cards_demoted": 0}
$ python runs/adult-income/helpers/tools.py load_splits ... --arm memory && python runs/adult-income/helpers/tools.py read_memory ... --arm memory --order obey-memory | ...
{'memory': 'on', 'cards': 0, 'applicable': 0, 'preferred': {}, 'policy': 'static (no applicable card)', 'remaining': 72}
$ python runs/adult-income/helpers/tools.py fit_recipe ... --arm memory --recipes @runs/adult-income/helpers/static.json | ...
1 0.9114  {"model": "logreg", ...}
... (the same 24 numbers as the control arm)
fits_left 0 FREEZE True
agent> Identical to the control arm, as the empty-memory check requires. Score, save, scorecard:
$ ... score_test ... --arm memory --recipe "$R" ... && ... scorecard ... --arm memory
test_score 0.9049 None
{"problem": "adult_income", "arm": "memory", "seed": 0, "n_fits": 24, "fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9177, ...}
agent> Memory arm (round 1, empty memory) done: best val 0.9177, test 0.9049, 24 fits, 16 wasted - byte-for-byte equal to control, as expected with no cards. Now the verifier.
[Skill adult-income-verifier]
[Write runs/adult-income-verifier/helpers/verify.py (231 lines: read_traces, write_card)]
$ python runs/adult-income-verifier/helpers/verify.py read_traces .claude/skills/adult-income ../tasks/01_adult_income --scope problem --tally > runs/adult-income-verifier/tally.json && python -c "... print the profile, the pair count, wins, losses, sample pairs, cards_by_rule ..."
profile {'n_rows': 6000, 'n_features': 14, 'n_classes': 2, 'imbalance': 0.239, 'has_categorical': 1} rows 24 pairs 60
wins {"class_weight": {"none": 8, "balanced": 4}, "encode": {"onehot": 12}, "scale": {"yes": 5, "no": 1}, "model": {"logreg": 3, "hgb": 16, "rf": 5}}
losses {"class_weight": {"balanced": 8, "none": 4}, "encode": {"ordinal": 12}, "scale": {"no": 5, "yes": 1}, "model": {"rf": 11, "logreg": 13}}
errored {}
sample pairs:
  {'field': 'class_weight', 'a': 'none', 'b': 'balanced', 'a_score': 0.9114, 'b_score': 0.911, 'result': 'win:"none"'}
  {'field': 'encode', 'a': 'onehot', 'b': 'ordinal', 'a_score': 0.9114, 'b_score': 0.8544, 'result': 'win:"onehot"'}
  {'field': 'model', 'a': 'logreg', 'b': 'hgb', 'a_score': 0.9114, 'b_score': 0.9177, 'result': 'win:"hgb"'}
cards_by_rule:
  {"if": {"key": "n_rows", "op": ">=", "value": 1000}, "then": {"field": "model", "prefer": "hgb"}, "evidence": 1, "counter": 0}
  {"if": {"key": "n_rows", "op": ">=", "value": 1000}, "then": {"field": "model", "prefer": "logreg"}, "evidence": 0, "counter": 1}
  {"if": {"key": "n_rows", "op": ">=", "value": 1000}, "then": {"field": "model", "prefer": "rf"}, "evidence": 0, "counter": 1}
  {"if": {"key": "n_features", "op": ">=", "value": 10}, "then": {"field": "scale", "prefer": "yes"}, "evidence": 1, "counter": 0}
  ... (5 more: has_categorical == 1 -> onehot; imbalance < 0.35 -> class_weight none; and the counter cards for scale no, ordinal, balanced)
$ python runs/adult-income-verifier/helpers/verify.py write_card .claude/skills/adult-income ../tasks/01_adult_income --as .claude/skills/adult-income-verifier --cards @runs/adult-income-verifier/cards.json && diff .claude/skills/adult-income/memory.json .agents/skills/adult-income/memory.json && echo MIRRORS_EQUAL && tail -1 runs/adult-income/adult_income/memory/traces.jsonl
{"n": 9, "new": 9, "demoted": 5, "total_on_disk": 9, "active": 4}
MIRRORS_EQUAL
{"event": "write_card", "as": "adult-income-verifier", "n": 9, "new": 9, "demoted": 5}
$ python runs/adult-income/helpers/tools.py load_splits ... --arm memory-r2 | ... && python runs/adult-income/helpers/tools.py read_memory ... --arm memory-r2 --order obey-memory | ...
memory on cards 9 applicable 4
preferred {'model': 'hgb', 'hyper': None, 'scale': 'yes', 'encode': 'onehot', 'class_weight': 'none'}
forbidden {'model': [], 'hyper': [], 'scale': [], 'encode': [], 'class_weight': []}
policy obey-memory remaining 3
  {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
  {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
  {"model": "rf", "hyper": 16, "scale": "yes", "encode": "onehot", "class_weight": "none"}
agent> The probe: hgb first (the preferred model), then logreg and rf, each with the preferred scale/encode/class_weight at the middle hyper.
$ ... fit_recipe ... --arm memory-r2 --recipes @$H/next.json ... && ... read_memory ... --arm memory-r2 --order obey-memory ...
1 0.9177  {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
2 0.9114  {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
3 0.9054  {"model": "rf", "hyper": 16, "scale": "yes", "encode": "onehot", "class_weight": "none"}
fits_left 21 FREEZE False
next (remaining 69 ):
  {"model": "hgb", "hyper": 0.1, "scale": "no", "encode": "onehot", "class_weight": "none"}
  {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
  ... (the hgb family: static variants by preferred-value count, then hyper 0.05 and 0.3)
$ for i in 1 2 3; do ... fit_recipe ... --arm memory-r2 --recipes @$H/next.json ...; ... read_memory ... --order obey-memory ...; done
4 0.9177  {"model": "hgb", "hyper": 0.1, "scale": "no", "encode": "onehot", "class_weight": "none"}
5 0.917   ...
11 0.9173 {"model": "hgb", "hyper": 0.05, "scale": "yes", "encode": "onehot", "class_weight": "none"}
12 0.9095 {"model": "hgb", "hyper": 0.3, ...}
... (24 fits; the three surplus items of the last batch refused on budget)
agent> FREEZE at 24 fits; the three surplus items were refused on budget without fitting. Best val is 0.9177 at fit 1. Score, save, scorecard:
$ ... score_test ... --arm memory-r2 --recipe "$R" ... && ... scorecard ... --arm memory-r2 && python -c "... print the three scorecards side by side ..."; git status --short . | head
{"problem": "adult_income", "arm": "memory-r2", "seed": 0, "n_fits": 24, "fits_used": 24, "wasted_fits": 0, "best_val_score": 0.9177, "best_recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "test_score": 0.9049, ..., "cards_active": 4, "cards_added": 9, "cards_demoted": 5}
agent> All three arms ran on ../tasks/01_adult_income (seed 0, 24 fits each, one shared helper/split).
| arm                        | best val | test   | fits | wasted | cards active / added / demoted |
| control (--memory off)     | 0.9177   | 0.9049 | 24   | 16     | 0 / 0 / 0 |
| memory (empty memory.json) | 0.9177   | 0.9049 | 24   | 16     | 0 / 0 / 0 |
| memory-r2 (9 cards)        | 0.9177   | 0.9049 | 24   | 0      | 4 / 9 / 5 |
Every arm: test_scored_once true, test_touched_before_freeze false; score_test was run exactly once, after FREEZE.
1. Control arm - walked the 24 static recipes in one call. Best appeared at fit 17 (the first hgb recipe), so 16 fits were wasted.
2. Memory arm - memory.json was empty, so obey-memory degraded to static; the 24 val scores are identical to control's, number for number (the delete-the-file check).
3. Verifier - read_traces --tally on the memory arm's log found 60 pairs one field apart; I hand-checked the first few. Net tallies: model hgb +16, logreg -10, rf -6; encode onehot +12; scale yes +4; class_weight none +4; no hyper pairs exist in the static list. Rule -> 9 cards written, 9 new, 5 demoted: 4 active prefer cards (n_rows>=1000 -> hgb, n_features>=10 -> scale yes, has_categorical==1 -> onehot, imbalance<0.35 -> class_weight none) plus 5 born-demoted counter cards (evidence 0 / counter 1) for logreg, rf, scale no, ordinal, balanced. Both mirrors are identical.
4. memory-r2 - all 4 cards applied. The probe put hgb first with the preferred scale/encode/class_weight, and it scored the run's best (0.9177) on fit 1; then the search stayed in the hgb family. Nothing forbidden, nothing refused except the three surplus items after the 24th fit.
What changed: wasted fits 16 -> 0. Memory moved the best recipe from fit 17 to fit 1; that's the whole effect, and it is exactly what the pass rule's "same score with fewer wasted fits" clause asks for. Best val and test score unchanged (0.9177 / 0.9049): the static list already contained the best recipe, and the extra family exploration memory-r2 bought found nothing better - so on this problem the gain is efficiency, not accuracy.
[23 turns, 632 s]
```

What to notice: the memory arm with an empty memory reproduced the control
arm number for number - the delete-the-file check, passed before anything
was learned. The verifier's own `read_traces` found 60 pairs one field apart
and turned them into nine typed cards by the rule; five of them are counter
cards born demoted, which is how a value that lost gets remembered without
ever being obeyed. Then `memory-r2` booted the four active cards and its
probe put `hgb` first: the best recipe on fit 1 instead of fit 17, wasted
fits 16 to 0, the same test score. On this problem the memory bought
efficiency, not accuracy; the page says so, and the pass rule counts it.

Files:

```text
step_06_rsi_harness/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json
│   └── skills/
│       ├── adult-income/                 the actor (inner pack)
│       │   ├── SKILL.md                  boot order incl. memory.json unless MEMORY_OFF; obey-memory; never write a card
│       │   ├── tools.md                  the runtime + load_splits, read_memory (with the policies), fit_recipe, score_test, save_model, scorecard
│       │   ├── schema.json
│       │   ├── memory.json               [] when shipped; the cards after a run (both mirrors)
│       │   ├── memory.schema.json        IF profile THEN prefer / forbid, evidence, counter
│       │   └── config.md                 memory: on | off | frozen; meta: on | off
│       └── adult-income-verifier/        the writer of memory.json
│           ├── SKILL.md                  the contract line, the tally, the rule with its thresholds
│           ├── tools.md                  read_traces, write_card; fit_recipe / score_test forbidden
│           └── memory.schema.json        the same schema
├── .agents/skills/                       the same two packs
└── runs/                                 (after a run) adult-income/{helpers/, adult_income/{control,memory,memory-r2}/}, adult-income-verifier/helpers/
```

## Governance considerations

- **Who approves what.** The human wrote the acceptance rule before the
  run: the verifier contract (rows and a profile in, typed cards out), the
  schema (what a card may say), the demotion rule (counters at half the
  evidence), and the off switch. No card is approved one by one; that is
  the point of L4 - the rule is human, the revisions are the system's.
- **The hook.** `score_test` after `"frozen": true` only.
- **What the helper refuses.** `write_card`: a caller that is not the
  verifier, a card outside the schema, a card whose text says `test` or
  `intent`, any write on an exam problem or a frozen memory. `fit_recipe`:
  a recipe a `forbid` card rules out (it costs no fit). `read_memory`: reads
  nothing when the arm's state says memory `off`.
- **What is and is not self-modified.** `memory.json` is (both mirrors);
  nothing else in either pack. The verifier is a separate skill that boots
  with the trace only - the live test asserts the `write_card` event names
  it, and the offline test that its procedure never names `score_test`.
- **The evidence standard.** The memory arm and the control arm share the
  helper, the split and the budget; the memory arm with an empty memory
  reproduces the control arm exactly, and `memory-r2` is the same arm with
  the cards. Any difference is the cards. Numbers vary between machines
  because the agent writes the fit helper; the comparison does not.

## How to measure it

| Claim | Test |
|---|---|
| `memory.json` ships empty; the schema types a card with exactly `if` / `then` / `evidence` / `counter`, the five profile keys; both packs carry the same schema | `test_memory_starts_empty_and_the_schema_types_a_card` |
| `config.md` carries `memory` and `meta` and explains MEMORY_OFF / META_OFF | `test_config_has_the_off_switches` |
| the verifier is blind by contract, writes cards and never scores; `write_card` refuses `test` / `intent`, a non-verifier caller, an exam problem | `test_verifier_is_blind_by_contract` |
| the actor never names `write_card` in its procedure; states the obey-memory policy; MEMORY_OFF must equal the control arm | `test_actor_never_writes_a_card_and_scores_once` |
| the pairwise rule is stated with its five thresholds | `test_the_pairwise_rule_is_stated_with_its_thresholds` |
| the pack contract for both packs | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: three arms frozen and scored once; empty memory = control; cards typed, clean, merged; `memory-r2` booted them; the verifier's event; mirrors equal (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields: all 14; `cards_active`, `cards_added`, `cards_demoted`
are real numbers from here on.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 07 - the proof](../step_07_proof/README.md): a locked test per
problem, the learning curve over problems 1-6, and an exam the pack never
wrote to. Previous:
[lesson 05 - a meta skill generates the graph harness](../step_05_meta_generates_graph/README.md).
