# Lesson 01 - The regular harness: a repeatable trainer, and not RSI

A skill pack that trains a classifier the same way every run: boot
`SKILL.md`, fit the 24 recipes of `schema.json` in order, pick the best
validation score, score the locked test split once, save the model, stop.
Next Monday it boots the same text and wastes the same fits. This is the
control arm of the whole series and, in the framework paper's terms, B0 /
AutoML: a fixed procedure, no persistent change, no decision moved from the
designer to the system. It is also where the machinery arrives - the one
skills harness (`common/harness.py`), the tool table with `execute()`
(`common/tools.py`), the budget object, the locked test and the append-only
trace - so that everything later is a diff against this pack.

## Getting started

Lesson 00 left `task.json` and `acceptance.md`. This lesson adds one pack,
`skills/adult-income-regular/` (three files), and the harness it boots.
The harness copies the pack into `runs/work/` before booting, so the pack
under `skills/` stays what you read here.

## How to execute it

1. Run the pack on Adult with the scripted fake model (no key):

   ```bash
   cd rsi/step_01_regular_harness
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_01_regular_harness
   $env:FAKE_MODEL = "1"; python run.py
   ```

2. Run it with a real model: set `BASE_URL`, `API_KEY` and `MODEL` like the
   rest of the repo and drop `FAKE_MODEL`. There is no approval prompt in
   this lesson: the pack changes nothing.
3. Tests: `python run_tests.py rsi` from the repo root.

## What it looks like

`skills/adult-income-regular/SKILL.md` - the front matter names the pack and
when it triggers; the body is the system prompt:

```markdown
---
name: adult-income-regular
description: Train a classifier for the Adult income problem by walking a fixed list of 24 recipes. Use when the task is adult_income and the pack has no loop, graph or memory file.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Regular harness: the same trainer, every run

## Boot order
1. This file. 2. `tools.md`: the only tools you may call. 3. `schema.json`: the task, the budget and the 24 recipes.
Nothing else is read. Nothing is written except the model file.

## Procedure
1. Call `load_splits` once.
2. The first recipe of `schema.json` -> `recipes` is the baseline. Call `fit_recipe` on every recipe of the list, in order, one call per recipe. That is 24 fits: the budget. A 25th is refused.
3. When a fit result says `FREEZE` (`fits_left` is 0), pick the recipe with the highest `val_score`.
4. Call `score_test` once with that recipe, after FREEZE. Then call `save_model` with it.
5. Answer in text: the best val_score, the test score and the number of fits. Stop.
```

`skills/adult-income-regular/tools.md` - the allowed set is what the harness
offers; everything else is an `Error:` result:

```markdown
## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- fit_recipe - one fit on train scored on val; counted against the budget of 24
- score_test - the locked test split, once, after FREEZE
- save_model - pickle the chosen recipe's fitted pipeline
```

The harness reads those files and runs the stage-15 loop:

`../common/harness.py`:

```python
def run(session, model, max_calls=MAX_CALLS, user="Begin. Follow the procedure in your instructions."):
    """The loop. `model(messages, tool_schemas) -> {content, tool_calls}`; every call goes through execute()."""
    session.messages = [{"role": "system", "content": session.system}]
    resume(session, model, user, max_calls)
```

```python
    session.messages.append({"role": "user", "content": user})
    schemas = schemas_for(session.allowed)
    for _ in range(max_calls):
        reply = model(session.messages, schemas)
        session.calls += 1
        session.messages.append(entry(reply))
        if not reply.get("tool_calls"):
            break
        for call in reply["tool_calls"]:
            result = execute(session, call)
            session.messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
```

`execute()` is the one place every call goes through - unknown, disallowed
or malformed becomes a result the model reads, never a crash:

`../common/tools.py`:

```python
def execute(run, call):
    """Turn one tool call into a result string. Never raises; unknown / disallowed / malformed -> `Error:`."""
    name = call.get("name")
    try:
        args = json.loads(call.get("arguments") or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:
        return f"Error: the arguments of {name} are not a JSON object: {e}"
    if name not in run.allowed:
        return f"Error: {name} is not in this pack's tools.md; it is not available"
    if name not in TOOLS:
        return f"Error: no tool named {name!r}"
```

The budget is an object, and FREEZE is the moment it is spent:

`../common/budget.py`:

```python
    @property
    def frozen(self):
        """FREEZE: every fit is spent. The test split may be scored once, the memory may not change."""
        return self.used >= self.n

    def spend(self):
        """Count one fit before it happens. An error still counts: a wasted fit is a fit."""
        if self.frozen:
            raise BudgetExhausted(f"budget of {self.n} fits used; fit {self.used + 1} refused")
        self.used += 1
        return self.used
```

Expected output, on this machine (`FAKE_MODEL=1`, the bundled 6,000-row
Adult sample, 28 model calls, about 15 s):

```text
Done. Best val 0.9172 with {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}; test 0.9034; 24 fits.
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
model calls 28; trace C:\Users\evija\simple-coding-harness\rsi\step_01_regular_harness\runs\adult-income-regular\traces.jsonl
```

`wasted 16`: sixteen fits went by before the first recipe within 0.005 of
the arm's best - the eight logistic regressions and the eight random forests
of the static list. Run it again tomorrow and it wastes the same sixteen.

Files:

```text
step_01_regular_harness/
  skills/adult-income-regular/
    SKILL.md        the procedure: 24 fits in order, best val, score_test once, save_model
    tools.md        Allowed: load_splits, fit_recipe, score_test, save_model; Forbidden: the rest
    schema.json     the task, n_fits 24, the test rule, the recipe fields, the baseline and the 24 recipes
  run.py            boot the pack on Adult (FAKE_MODEL=1 or a real model)
  test_step.py      the claims below
  README.md         this lesson
  runs/             (created by run.py, ignored by git) the working copy, the trace, the model pickle
```

## Governance considerations

- Who approves what: nobody needs to; the pack proposes nothing and writes
  no file but a model pickle in `runs/`.
- Off switches: the budget (`common/budget.py`) refuses the 25th fit; the
  loop's call cap (`MAX_CALLS`) stops a pack that never answers in text.
- What the model may not do, and which tool enforces it: fit a recipe
  outside the schema (`fit_recipe` validates); fit a 25th time
  (`Budget.spend`); score the test split before FREEZE or twice
  (`common/gate.py: LockedTest`); call a tool not in `tools.md`
  (`execute`).
- What is and is not self-modified: nothing is. `SKILL.md` is identical
  before and after the run and the next run boots the same text. Rung: not
  RSI - B0 / AutoML.

## How to measure it

| Claim | Test |
|---|---|
| the fake model follows `SKILL.md`: 24 fits in schema order, best-val pick, one `score_test` | `test_fake_follows_skill_md_24_fits_in_schema_order_best_val_one_test` |
| the 25th `fit_recipe` and the second `score_test` are `Error:` results | `test_25th_fit_and_second_score_test_are_error_results` |
| `score_test` before FREEZE is refused | `test_score_test_before_freeze_is_refused` |
| an unknown / disallowed / malformed tool call is an `Error:` result and the loop continues | `test_unknown_disallowed_malformed_calls_are_errors_and_the_loop_continues` |
| the trace is append-only | `test_trace_is_append_only` |
| the same pack twice gives the same log | `test_same_pack_twice_gives_the_same_log` |
| the pack is byte-identical after a run | `test_pack_is_byte_identical_after_a_run` |

Scorecard fields reported: all fourteen of `acceptance.md`, with
`cards_active` / `cards_added` / `cards_demoted` at 0 (no memory). Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [02 - loop engineering](../step_02_loop_harness/README.md): the loop
becomes a file the tools enforce. Previous:
[00 - intent](../step_00_intent/README.md).
