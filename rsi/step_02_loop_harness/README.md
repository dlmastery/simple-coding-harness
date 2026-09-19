# Lesson 02 - Loop engineering: the loop is a file

Lesson 01's procedure lived in prose. Here the loop becomes `loop.json`: a
`counted_while` with a named counter, a budget `N`, a body, an `exit`
sequence (`FREEZE` -> `score_test` -> `save_model`) and an `illegal` list.
The tools enforce what the file declares - the 25th fit and a pre-FREEZE
`score_test` are refused whatever the model writes - and the pack gains one
tool, `write_loop_log`, an audit line per iteration that no tool ever reads
back. That last fact is the lesson: a log that is written and never read is
not memory, and a loop file that generation n+1 loads unchanged is not
recursion. Still harness engineering, still not RSI.

## Getting started

Lesson 01 left the harness and the pack `adult-income-regular`. This lesson
adds `skills/adult-income-loop/` with two new files (`loop.json`,
`recipes.json`) and one new tool (`write_loop_log`); `schema.json` loses its
recipe list to `recipes.json`, and `lint_pack` learns to check a loop
(`common/packs.py: lint_loop`).

## How to execute it

1. Run the loop pack on Adult:

   ```bash
   cd rsi/step_02_loop_harness
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_02_loop_harness
   $env:FAKE_MODEL = "1"; python run.py
   ```

2. Look at `runs/adult-income-loop/loop_log.jsonl`: 24 lines, one per
   iteration. Then grep the tool table for a reader: there is none.
3. No approval prompt: the pack changes nothing. Tests:
   `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-loop/loop.json` - the loop, the gate and the illegal moves,
in one file:

```json
{
 "kind": "counted_while",
 "N": 24,
 "counter": "t",
 "error_still_counts": true,
 "body": [
  "recipe = recipes[t]",
  "fit_recipe(recipe)",
  "write_loop_log({t, recipe, val_score})"
 ],
 "exit": ["FREEZE", "score_test", "save_model"],
 "illegal": [
  "change N",
  "reorder recipes",
  "a second while",
  "score_test before FREEZE",
  "write memory.json"
 ]
}
```

`skills/adult-income-loop/SKILL.md` - the front matter, then a procedure that
is now one sentence: run the file.

```markdown
---
name: adult-income-loop
description: Train a classifier for the Adult income problem by running the counted loop in loop.json over recipes.json. Use when the pack has loop.json and no memory file.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
```

The audit tool, and the sentence that matters in its docstring:

`../common/tools.py`:

```python
@tool("write_loop_log", entry="object")
def write_loop_log(run, entry):
    """Append one audit line to loop_log.jsonl. Nothing reads it back: there is no tool that does."""
    with open(run.run_dir / "loop_log.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"problem": run.problem, "arm": run.arm, **entry}) + "\n")
    return "logged"
```

What `lint_pack` checks a loop for, so a later writer cannot hand a human a
loop that quietly raises `N`:

`../common/packs.py`:

```python
def lint_loop(loop, task, files):
    problems = []
    if loop.get("kind") != "counted_while":
        problems.append("loop.json kind must be counted_while")
    if loop.get("N") != task["budget"]["n_fits"]:
        problems.append(f"loop.json N {loop.get('N')} != task budget {task['budget']['n_fits']}")
    if not loop.get("error_still_counts", False):
        problems.append("loop.json must count errors")
    exit_steps = loop.get("exit", [])
    if exit_steps[:2] != ["FREEZE", "score_test"]:
        problems.append("loop.json exit must be FREEZE then score_test")
```

Expected output, on this machine (`FAKE_MODEL=1`):

```text
Done. Best val 0.9172 with {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}; test 0.9034; 24 fits.
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
loop_log.jsonl: 24 lines, read back by: nobody; pack byte-identical after the run: True
```

The same numbers as lesson 01, by construction: same recipes, same order,
same budget. What changed is who enforces the order.

Files:

```text
step_02_loop_harness/
  skills/adult-income-loop/
    SKILL.md        run loop.json as written; the illegal list is binding
    tools.md        Allowed: load_splits, fit_recipe, write_loop_log, score_test, save_model
    schema.json     the recipe fields, n_fits 24, the test rule, the baseline
    loop.json       counted_while, N 24, counter t, body, exit, illegal
    recipes.json    the 24 recipes the loop iterates over (middle hyper value, grid order)
  run.py            boot the pack on Adult; count the audit lines; checksum the pack
  test_step.py      the claims below
  README.md         this lesson
```

## Governance considerations

- Who approves what: nobody; the pack proposes nothing.
- Off switches: the budget object and the locked test, as in lesson 01.
- What the model may not do, and which tool enforces it: change `N`
  (`Budget.spend` refuses fit 25 whatever the model believes `N` is);
  `score_test` before FREEZE (`LockedTest.score_once`); write
  `memory.json` (no tool in `tools.md` writes a file; `execute` refuses
  `write_card`). "Reorder recipes" and "a second while" are stated in the
  file and checked by the test, not by a tool: an advisory rule, and the
  lesson says so.
- What is and is not self-modified: nothing. The audit log is written and
  never read; generation n+1 loads the same `loop.json`. Rung: harness
  engineering, not RSI.

## How to measure it

| Claim | Test |
|---|---|
| `loop.json` is honoured by the tools: N fits in `recipes.json` order, the 25th fit and a pre-FREEZE `score_test` refused, the pack lints | `test_loop_json_is_honoured_by_the_tools` |
| the audit log is written (24 lines) and never read back (the only tool that touches it writes) | `test_the_audit_log_is_written_and_never_read_back` |
| the pack is byte-identical after a run and no `memory.json` appeared | `test_pack_is_byte_identical_after_a_run` |
| generation n+1 loads the same loop: two runs, one log | `test_generation_n_plus_1_loads_the_same_loop` |

Scorecard fields reported: all fourteen; the card fields are 0. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [03 - a meta skill generates the loop harness](../step_03_meta_generates_loop/README.md),
under human approval. Previous: [01 - the regular harness](../step_01_regular_harness/README.md).
