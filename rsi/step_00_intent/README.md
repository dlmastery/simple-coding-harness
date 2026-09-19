# Lesson 00 - Intent: what to improve, how, and what counts as success

Before any pack exists, a human writes down what should get better
(`task.json`) and what evidence would prove it did (`acceptance.md`). The
framework paper (arXiv:2609.11873) calls this the precondition of every rung
of recursive self-improvement: the designer specifies the objective, the
procedure and the acceptance rule, and autonomy is later measured by which of
those decisions *move* to the system. Nothing in this series may widen the
intent - the budget, the metric, the allowed models and the locked-test rule
are checked by `lint_pack` against this file for every pack a later lesson
writes or generates. This is Stage 1 (Plan) of the playbook: the `intent.md`
that every writer and verifier reads.

## Getting started

Prerequisites: Python 3.10+, `pip install -r requirements.txt` from the repo
root. Nothing is on disk yet from a previous lesson; this one adds the two
intent files, the schema they validate against (`../common/task.schema.json`)
and the curriculum they belong to (`../tasks/`, one `task.json` per problem,
problem 7 the exam).

## How to execute it

1. Validate the intent and watch `lint_pack` refuse a widened pack:

   ```bash
   cd rsi/step_00_intent
   python run.py
   ```

   ```powershell
   cd rsi\step_00_intent
   python run.py
   ```

   There is no approval in this lesson: the human *is* the author.

2. Run the tests: `python run_tests.py rsi` from the repo root, or
   `python -m pytest -q test_step.py` here.

## What it looks like

`task.json` - the intent, validated against `common/task.schema.json`
(`additionalProperties: false`: an extra field is a rejected task):

```json
{
  "name": "adult_income",
  "index": 1,
  "title": "Adult Census Income (> 50k)",
  "source": {
    "kind": "adult"
  },
  "target": "target",
  "metric": "roc_auc",
  "budget": {
    "n_fits": 24,
    "per": "arm"
  },
  "allowed_models": [
    "logreg",
    "rf",
    "hgb"
  ],
  "test_rule": {
    "scores": 1,
    "after": "FREEZE"
  },
  "profile_keys": [
    "n_rows",
    "n_features",
    "n_classes",
    "imbalance",
    "has_categorical"
  ],
  "role": "curriculum",
  "why": "mixed numeric + categorical, class imbalance: the first lessons the pack learns (encoding, class_weight)"
}
```

`acceptance.md` names the fourteen scorecard fields and the pass rule; the
fields are the ones `common/scorecard.py` enforces:

`../common/scorecard.py`:

```python
SCORECARD_FIELDS = (
    "problem", "arm", "seed", "n_fits", "fits_used", "wasted_fits",
    "best_val_score", "best_recipe", "test_score", "test_scored_once",
    "test_touched_before_freeze", "cards_active", "cards_added", "cards_demoted",
)
```

`run.py` reads the bullets back and compares:

`run.py`:

```python
def acceptance_fields(path=HERE / "acceptance.md"):
    """The `- field` bullets under `## The scorecard`: the contract every later scorecard meets."""
    text = path.read_text(encoding="utf-8")
    section = text.split("## The scorecard")[1].split("## ")[0]
    return tuple(FIELD_LINE.findall(section))
```

Expected output, on this machine:

```text
task.json valid: adult_income - Adult Census Income (> 50k); metric roc_auc; budget 24 fits per arm
acceptance.md names 14 scorecard fields; matches common/scorecard.py: True
lint_pack on step 01's pack: ok
lint_pack on a pack with n_fits 48: ['schema.json n_fits 48 != task budget 24']
lint_pack on a pack with two test scores: ["schema.json test_rule differs from the task's"]
```

Files:

```text
step_00_intent/
  task.json         the intent: target, metric, budget, allowed models, test rule, profile keys
  acceptance.md     the scorecard fields and the pass rule, written before any pack exists
  run.py            validates both and shows lint_pack refusing a widened pack
  test_step.py      the claims below
  README.md         this lesson
```

## Governance considerations

- Who approves what: a human writes `task.json` and `acceptance.md`; no
  model is involved in this lesson at all.
- Off switches: none needed; nothing runs.
- What the model may not do, and which tool enforces it: no pack may raise
  `n_fits`, change `test_rule`, `metric` or the allowed `models` -
  `common/packs.py: lint_pack` refuses it, and `common/tasks.py:
  validate_task` refuses a task that does not fit the schema.
- What is and is not self-modified: nothing. This file is the fixed point
  every later lesson is measured against (rung: the L1 precondition).

## How to measure it

| Claim | Test |
|---|---|
| `task.json` validates against the schema | `test_task_json_validates_against_the_schema` |
| a widened task (budget, test rule, extra field) is rejected | `test_a_widened_task_is_rejected` |
| every curriculum task validates, in order, with the same budget and test rule | `test_every_curriculum_task_validates_and_is_in_order` |
| a pack that raises the budget, touches the test rule, the metric or the models is rejected by `lint_pack` | `test_lint_pack_rejects_a_raised_budget_or_a_touched_test_rule` |
| the acceptance fields are exactly the scorecard fields every later step reports | `test_acceptance_fields_are_exactly_the_scorecard_fields` |

Scorecard fields: this lesson defines them; it reports none. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [01 - the regular harness](../step_01_regular_harness/README.md), a
repeatable trainer that is not RSI. Previous: the
[course page](../README.md).
