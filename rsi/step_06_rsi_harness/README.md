# Lesson 06 - The RSI harness: the first file that changes because of what happened

Two packs. The actor (`adult-income`) boots `memory.json` and proposes one
recipe at a time under a search policy the cards shape; the verifier
(`adult-income-verifier`) boots after the actor's run is frozen, sees only
`{recipe, val_score, error, profile}` rows, and writes typed cards - IF a
profile condition THEN prefer or forbid one field value, with evidence and
counter counts. A card is a constraint on the *next* proposal, enforced by
a tool (`fit_recipe` refuses a forbidden recipe), and no one grades their
own homework: the verifier never sees the actor's transcript, and the actor
has no `write_card`. `MEMORY_OFF` is the off switch: same pack, same 24
fits, no cards, and the numbers must fall back to lesson 01's exactly. In
the framework paper's terms this is L4: deployment feedback revises
persistent state under an acceptance rule we wrote (the verifier contract).

## Getting started

Lesson 05 left the writers and the approval cycle. This lesson adds the two
packs, `memory.schema.json` (the JSON Schema of a card), `memory.json`
(starts as `[]`), the tools `read_memory`, `write_card` and `read_traces`,
and `common/memory.py` (cards, the verifier's rule, the preference a search
obeys). `common/curriculum.py: run_problem` runs actor then verifier on one
problem and returns the scorecard.

## How to execute it

1. Run the pack over four small curriculum problems in a row, memory arm
   and `MEMORY_OFF` arm each, the pack carried forward:

   ```bash
   cd rsi/step_06_rsi_harness
   FAKE_MODEL=1 python run.py
   FAKE_MODEL=1 python run.py adult_income breast_cancer      # any problems by name, in order
   MEMORY_OFF=1 FAKE_MODEL=1 python run.py                    # the off switch
   ```

   ```powershell
   cd rsi\step_06_rsi_harness
   $env:FAKE_MODEL = "1"; python run.py
   $env:MEMORY_OFF = "1"; python run.py
   ```

   No approval prompt: the verifier writes cards under the contract, the
   contract is the acceptance rule, and the human wrote it.
2. Read `runs/work/adult-income/memory.json` after the run: that file is
   the whole difference between the two arms.
3. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/adult-income/SKILL.md` - the actor:

```markdown
---
name: adult-income
description: Train a classifier for a curriculum problem under a 24-fit budget, proposing one recipe at a time shaped by the memory cards. Use when the pack has memory.json and a verifier pack writes to it.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
```

```markdown
2. For t in 1..24: read the cards that apply (an `if` the profile satisfies, `evidence` >= 1, `counter` at most half the `evidence`), propose ONE recipe from `schema.json` -> `fields`, and call `fit_recipe`. A recipe a forbid card rules out is refused by the tool and costs no fit; do not propose it again.
   Search policy: obey-memory
```

```markdown
## Off switch
MEMORY_OFF: the harness does not load `memory.json`; you run the static order. Same 24 fits, so the numbers can be compared.
```

`skills/adult-income-verifier/SKILL.md` - the contract line is checked
verbatim by `lint_pack`, and the procedure is the rule the fake model and a
real one both apply:

```markdown
---
name: adult-income-verifier
description: Turn the fit log of one problem into memory cards for the actor pack. Use after the actor's run on a problem is frozen; input is the log and the profile, nothing else.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.
```

```markdown
3. Per field, write ONE prefer card for the value with the most wins net of losses (`evidence` 1) - if it has any net wins at all - and a `counter` 1 card for every value that lost more than it won. Write a `forbid` card (`evidence` 1) for a value that errored. A card's `if` is the side of the field's threshold this profile is on (`class_weight` -> `imbalance` 0.35; `encode` -> `has_categorical`; `scale` -> `n_features` 10; `model` -> `n_rows` 1000; `hyper` -> `n_classes` 3). Call `write_card` once per card; the tool merges the counts into `memory.json`. One problem is one piece of evidence: a card is active from its first, and it is demoted as soon as its counters reach half its evidence.
```

A card, as `memory.json` holds it after the run below:

```json
{"if": {"key": "has_categorical", "op": "==", "value": 1}, "then": {"field": "encode", "prefer": "onehot"}, "evidence": 2, "counter": 0}
```

The tools that make the rules enforceable:

`../common/tools.py`:

```python
    card = memory.forbidden(rec, cards_for(run), run.profile)
    if card is not None:
        raise ValueError(f"a forbid card rules this recipe out: {json.dumps(card['then'])} (no fit spent)")
```

```python
@tool("write_card", card="object")
def write_card(run, card):
    """Merge one card into memory.json: validated against memory.schema.json; refused if it names the test or the intent."""
    if run.memory_off:
        raise ValueError("MEMORY_OFF: no card is written this run")
    if run.memory_frozen:
        raise ValueError("the memory is frozen; no card lands until the next problem")
    schema = json.loads(run.files.get("memory.schema.json") or json.dumps(memory.CARD_SCHEMA))
    try:
        memory.validate_card(card, schema)
    except Exception as e:
        raise ValueError(f"not a card: {str(e).splitlines()[0]}")
```

`../common/memory.py`:

```python
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

Expected output, on this machine (`FAKE_MODEL=1`, the four small problems;
`mem` is the memory arm, `ctl` the `MEMORY_OFF` arm at the same budget and
seed; `wasted` counts fits before the arm reached the `MEMORY_OFF` arm's
best val score; `cards +/-/act` is cards activated / demoted / active):

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       1/0/1
 2 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/1
 3 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/0/6
 4 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      2/0/8
memory.json after 4 problems: 8 cards, 8 active
  {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "hgb"}, "evidence": 2, "counter": 0}
  {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "logreg"}, "evidence": 1, "counter": 0}
  {"if": {"key": "n_classes", "op": "<", "value": 3}, "then": {"field": "hyper", "prefer": 1}, "evidence": 1, "counter": 0}
  {"if": {"key": "n_features", "op": "<", "value": 10}, "then": {"field": "scale", "prefer": "no"}, "evidence": 1, "counter": 0}
  {"if": {"key": "has_categorical", "op": "==", "value": 1}, "then": {"field": "encode", "prefer": "onehot"}, "evidence": 2, "counter": 0}
  {"if": {"key": "imbalance", "op": ">=", "value": 0.35}, "then": {"field": "class_weight", "prefer": "none"}, "evidence": 1, "counter": 0}
  {"if": {"key": "n_classes", "op": "<", "value": 3}, "then": {"field": "hyper", "prefer": 0.3}, "evidence": 1, "counter": 0}
  {"if": {"key": "imbalance", "op": "<", "value": 0.35}, "then": {"field": "class_weight", "prefer": "none"}, "evidence": 1, "counter": 0}
```

Read it top to bottom: on problem 1 the arms are identical (no card yet);
by problem 4 the memory arm reaches the static grid's best within 3 fits
instead of 17, and its own best is 0.065 higher on validation and 0.076
higher on the locked test, because the cards sent it to the `hgb` family
first and the freed budget explored that family's learning rates. Wine sits
at 1.0 for every recipe: ties teach nothing, and the verifier wrote nothing.

Files:

```text
step_06_rsi_harness/
  skills/adult-income/
    SKILL.md            the actor: boot order, the search policy line, the off switch
    tools.md            Allowed: load_splits, fit_recipe, read_memory, score_test, save_model; write_card Forbidden
    schema.json         the recipe fields, n_fits 24, the test rule, the static list, a (still empty) forbid list
    memory.schema.json  the JSON Schema of a card: if / then / evidence / counter, nothing else
    memory.json         [] - the first RSI file
  skills/adult-income-verifier/
    SKILL.md            the contract line, the comparison rule, the card thresholds
    tools.md            Allowed: read_traces, write_card; fit_recipe and score_test Forbidden
    memory.schema.json  the same schema; write_card validates against this copy
  run.py                actor -> verifier per problem, both arms, the pack carried forward
  test_step.py          the claims below
  README.md             this lesson
```

## Governance considerations

- Who approves what: the human approved the verifier contract by writing
  it; every card lands under it without a prompt. That is the acceptance
  rule of this rung, and the reason lesson 08 makes a human approve the
  contract explicitly when a writer generates it.
- Off switches: `MEMORY_OFF` (no cards loaded, no card written); the budget
  and the locked test as before; `memory_frozen` (lesson 07's exam) closes
  `write_card`.
- What the model may not do, and which tool enforces it: the actor may not
  write a card (`write_card` is not in its `tools.md`); the verifier may not
  fit or score (`lint_pack` refuses a verifier with those tools, `execute`
  refuses the calls); a card may not carry a reason, an intent or the word
  test (`memory.schema.json` has `additionalProperties: false`,
  `validate_card` scans the text); a forbidden recipe is not fitted
  (`fit_recipe`); the verifier is booted with the actor's log, never its
  messages (`read_traces` returns five keys).
- What is and is not self-modified: `memory.json` is. `SKILL.md`,
  `tools.md`, `schema.json` and `memory.schema.json` are not - only a meta
  pack may patch them (lesson 09). The model's weights are what they were.
  Rung: L4; what stays human is the contract and the off switch.

## How to measure it

| Claim | Test |
|---|---|
| the verifier pack's transcript contains no actor text; its rows have the contract's keys only | `test_verifier_transcript_contains_no_actor_text` |
| `write_card` refuses a card mentioning `test` or `intent`, or carrying any extra field | `test_write_card_refuses_a_card_that_names_the_test_or_the_intent` |
| a planted wrong card is demoted after two counterexamples | `test_a_planted_wrong_card_is_demoted_after_two_counterexamples` |
| `fit_recipe` refuses a forbidden recipe, at no cost to the budget | `test_fit_recipe_refuses_a_forbidden_recipe` |
| same seeds and budget: the memory arm >= the `MEMORY_OFF` arm and wastes fewer fits | `test_memory_arm_beats_memory_off_at_the_same_budget` |
| `MEMORY_OFF` reproduces lesson 01's numbers exactly | `test_memory_off_reproduces_step_01_exactly` |

Scorecard fields reported: all fourteen, per arm and per problem;
`cards_added` / `cards_demoted` / `cards_active` are live from here on. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [07 - proof](../step_07_proof/README.md): the locked test, the
learning curve across the curriculum, the exam. Previous:
[05 - a meta skill generates the graph harness](../step_05_meta_generates_graph/README.md).
