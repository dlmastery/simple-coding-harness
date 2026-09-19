# Lesson 02 - Loop engineering: the loop is a file

The same trainer as lesson 01, with its loop written down: `loop.json` names
the kind (`counted_while`), the counter (`t`), the bound (`N: 24`), the
body (fit `recipes[t]`, write one audit line), the exit (FREEZE, then
`score_test` once, then `save_model`) and the illegal moves (change `N`,
reorder, a second loop, `score_test` before FREEZE, write `memory.json`).
The agent executes the file; the scripts enforce what the file declares -
the 25th fit and the early or second test score are refused whatever the
agent intends. Still not RSI: `loop_log.jsonl` is written and never read
back (no script reads it), and the next generation loads the same
`loop.json`. Harness engineering is the craft of making the loop explicit
and enforceable; RSI (lesson 06) is what happens when a later run reads what
an earlier run wrote.

## Getting started

Lesson 01 left the regular pack and the tool scripts. This lesson adds
`.claude/skills/adult-income-loop/` (five files: `SKILL.md`, `tools.md`,
`schema.json`, `loop.json`, `recipes.json`), mirrored to `.agents/skills/`,
and one script the loop's body names: `../tools/write_loop_log.py`. Open your
agent in this directory (`cd rsi/step_02_loop_harness && claude`). A run
writes only under `runs/`; the pack is byte-identical afterwards (asserted).

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-loop skill: run the loop in loop.json on the Adult income problem and report the scorecard.
   ```

   The agent executes `loop.json`: four slices of six iterations, each a
   fit call and a log call, then the exit:

   ```bash
   python ../tools/load_splits.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
   python ../tools/fit_recipe.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-loop/recipes.json --range 0:6
   python ../tools/write_loop_log.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --entries '[{"t": 0, "recipe": {...}, "val_score": 0.9114}, ...]'
   # ... --range 6:12, 12:18, 18:24, each followed by its log call ...
   python ../tools/score_test.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/save_model.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/scorecard.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
   ```

   PowerShell note: the `--entries '[...]'` JSON survives single quotes in
   PowerShell 7; in 5.1 write it to a file and pass `--entries '@entries.json'`.
   No approval prompt: the pack changes nothing.

2. Try an illegal move by hand: `python ../tools/score_test.py ...` after
   the first slice answers `the test split is locked until FREEZE: 18 fits
   remain` (and the hook blocks it first in Claude Code). Edit `N` to 48 in a
   copy of `loop.json` and lint it: `python ../tools/lint_pack.py --pack <copy>
   --task ../tasks/01_adult_income.json` answers `loop.json N 48 != task budget 24`.

3. Reset with `rm -rf runs`. Headless: `claude -p "<the prompt>" --allowedTools
   "Bash,Read,Write,Edit,Skill"`. Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-loop/loop.json` - the loop as data. Everything
in `illegal` that a script can see, a script refuses; the rest the agent
refuses itself, and the test checks the pack after a run:

```json
{
 "kind": "counted_while",
 "N": 24,
 "counter": "t",
 "error_still_counts": true,
 "body": [
  "recipe = recipes[t]",
  "fit_recipe.py --recipe recipe  (or --recipes @recipes.json --range t:t+6)",
  "write_loop_log.py {t, recipe, val_score}"
 ],
 "exit": ["FREEZE", "score_test", "save_model", "scorecard"],
 "illegal": ["change N", "reorder recipes", "a second while", "score_test before FREEZE", "write memory.json"]
}
```

`.claude/skills/adult-income-loop/SKILL.md` - the procedure says "run
`loop.json` exactly as written" and names the commands:

```markdown
---
name: adult-income-loop
description: Train a classifier for the Adult income problem by running the counted loop in loop.json over recipes.json. Use in rsi/step_02_loop_harness, when the pack has loop.json and no memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Loop harness: the loop is a file

## Procedure
Run `loop.json` exactly as written:
1. `python ../tools/load_splits.py --pack P --task T` once.
2. `counted_while` with counter `t` from 0 to `N` - 1 (`N` is 24): the body fits `recipes[t]` and writes one audit line with `t`, the recipe and the `val_score`. Execute the body for six consecutive values of `t` per pair of commands, four pairs in all:
   `python ../tools/fit_recipe.py --pack P --task T --recipes @P/recipes.json --range 0:6`
   `python ../tools/write_loop_log.py --pack P --task T --entries '[{"t": 0, "recipe": {...}, "val_score": ...}, ...]'`
   then `--range 6:12`, `--range 12:18`, `--range 18:24`, each followed by its log call. An error still counts: `t` advances.

## Rules
The `illegal` list of `loop.json` is binding: do not change `N`, do not reorder the recipes, do not open a second loop, never run `score_test.py` before FREEZE, never write `memory.json`. The scripts refuse the ones they can see (the 25th fit, the early or second test score, a recipe outside the schema); the rest you refuse yourself.
```

`../tools/write_loop_log.py` - the whole script. Note what is absent: a read
path. No tool in `../tools/` opens `loop_log.jsonl` (the test greps for it):

```python
def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "write_loop_log")
    entries = [cli.value(a.entry)] if a.entry else cli.value(a.entries) if a.entries else None
    if not entries or not all(isinstance(e, dict) for e in entries):
        raise ValueError("an entry is a JSON object (--entry), or --entries a JSON list of them")
    path = run.root / "loop_log.jsonl"
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for entry in entries:
            f.write(json.dumps({"problem": run.problem, "arm": run.arm, **entry}) + "\n")
    return {"logged": len(entries), "path": str(path)}
```

`../tools/_lib/packs.py` - what `lint_pack` holds a loop file to, so a
writer (lesson 03) cannot hand a human a loop that changes the budget:

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

The recorded run (Claude Code 2.1.278, headless, from this directory; the
agent read the five pack files first, then ran the loop; results trimmed):

```text
[Skill adult-income-loop]
agent> Boot complete. Step 1: load the splits.
$ python ../tools/load_splits.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
{"pack": "adult-income-loop", "problem": "adult_income", "arm": "memory", "n_fits": 24, "fits_left": 24, ...}
agent> Step 2, first slice: t = 0..5.
$ python ../tools/fit_recipe.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-loop/recipes.json --range 0:6
{"results": [{"t": 0, "n": 1, "recipe": {"model": "logreg", ... "class_weight": "none"}, "val_score": 0.9114, ...},
             {"t": 1, "n": 2, ... "val_score": 0.911}, {"t": 2, ... "val_score": 0.8544}, {"t": 3, ... 0.8577},
             {"t": 4, ... 0.91}, {"t": 5, ... 0.9074}], "fits_used": 6, "n_fits": 24, "fits_left": 18}
$ python ../tools/write_loop_log.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --entries '[{"t":0,"recipe":{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"none"},"val_score":0.9114}, ... {"t":5, ...}]'
{"logged": 6, "path": "...\\runs\\adult-income-loop\\adult_income\\loop_log.jsonl"}
agent> Second slice: t = 6..11.
$ python ../tools/fit_recipe.py ... --range 6:12
{"results": [{"t": 6, ... "val_score": 0.8278}, ... {"t": 11, ... 0.9026}], "fits_used": 12, "fits_left": 12}
$ python ../tools/write_loop_log.py ... --entries '[{"t":6, ...}, ... {"t":11, ...}]'
{"logged": 6, ...}
agent> Third slice: t = 12..17.
$ python ../tools/fit_recipe.py ... --range 12:18
{"results": [... {"t": 16, ... "val_score": 0.915}, {"t": 17, ... "val_score": 0.9172}], "fits_used": 18, "fits_left": 6}
$ python ../tools/write_loop_log.py ... --entries '[...]'
agent> Last slice: t = 18..23.
$ python ../tools/fit_recipe.py ... --range 18:24
{"results": [... {"t": 23, ... "val_score": 0.91, "fits_left": 0}], "fits_used": 24, "fits_left": 0, "FREEZE": true}
$ python ../tools/write_loop_log.py ... --entries '[...]'
$ python ../tools/score_test.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
{"test_score": 0.9034, ...}
$ python ../tools/save_model.py ... && python ../tools/scorecard.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
{"problem": "adult_income", "arm": "memory", "fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9172,
 "test_score": 0.9034, "test_scored_once": true, "test_touched_before_freeze": false, "cards_active": 0, ...}
agent> Loop done: t reached 24, score_test.py answered once after FREEZE, save_model.py ran once.
Best val_score 0.9172 (hgb, hyper=0.1, scale=yes, onehot, balanced, t=17); test score 0.9034;
24 / 24 fits (wasted_fits: 16). Val scores by block: logreg 0.83-0.91 (onehot >> ordinal),
rf 0.90-0.91 (flat), hgb 0.91-0.92. t=21 tied at 0.9172; I took the earlier one.
```

What to notice: the numbers are lesson 01's to the fourth decimal - the
same 24 fits in the same order give the same log, which is the point of
a control arm. In the first recording of this lesson `write_loop_log.py`
had a bug (`--entries` was declared but not read); the agent noticed,
logged the 24 lines one `--entry` at a time, and flagged the bug in its
final answer without touching the tool - which is what the rules asked of
it. The script was fixed and the lesson re-recorded.

Files:

```text
step_02_loop_harness/
├── README.md
├── test_step.py
├── .claude/settings.json                 the hook
├── .claude/skills/adult-income-loop/
│   ├── SKILL.md                          run loop.json exactly as written
│   ├── tools.md                          + write_loop_log
│   ├── schema.json                       the recipe space, the budget, the test rule
│   ├── loop.json                         the loop as data
│   └── recipes.json                      what the loop iterates over
├── .agents/skills/adult-income-loop/     the same five files
└── runs/adult-income-loop/adult_income/  (after a run)
    ├── state.json, traces.jsonl, scorecard_memory_0.json, model_memory_0.pkl
    └── loop_log.jsonl                    24 audit lines; nothing reads them
```

## Governance considerations

- **Who approves what.** Nobody; the loop was written by the human and
  executes as written.
- **The hook.** Blocks `score_test.py` before FREEZE and a second time, as
  in lesson 01.
- **What the script refuses.** Everything in `illegal` it can see: the 25th
  fit (`N`), `score_test` before FREEZE, a recipe outside `schema.json`. What
  it cannot see - a reordered walk, a second loop - the pack forbids in
  text and the test checks from the trace (the fit order equals
  `recipes.json`).
- **What is and is not self-modified.** Nothing. The audit log is
  write-only by construction: the generation that comes next cannot read it,
  so nothing it says can change the next run. Lesson 06 changes exactly that.

## How to measure it

| Claim | Test |
|---|---|
| `loop.json` is honoured: 24 fits in `recipes.json` order, `t` 0..23, one test score; the 25th fit and the second score refused | `test_loop_json_is_honoured` |
| `score_test` before FREEZE is refused with the fits remaining | `test_score_test_before_freeze_refused` |
| the audit log holds 24 lines and no script reads it back | `test_audit_log_written_never_read` |
| the pack is byte-identical after a run | `test_pack_is_byte_identical_after_a_run` |
| `lint_pack` refuses a loop with `N` 48 or an exit that scores before FREEZE | `test_lint_refuses_a_changed_loop` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard (seed 0): identical to lesson 01's - `fits_used 24`, `wasted_fits
16`, `best_val_score 0.9172`, `test_score 0.9034`.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 03 - a meta skill generates the loop harness](../step_03_meta_generates_loop/README.md),
under human approval. Previous: [Lesson 01 - the regular harness](../step_01_regular_harness/README.md).
