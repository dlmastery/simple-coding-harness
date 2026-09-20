# Lesson 02 - Loop engineering: the loop is a file

Lesson 01's loop lived in the agent's head: "fit these 24, in order, then
stop". This lesson writes it down. `loop.json` declares the loop's kind
(`counted_while`), its bound (`N: 24`), its counter (`t`), its body, its exit
and - the part that matters most - what is *illegal*: change `N`, reorder
the recipes, open a second loop, score the test before `FREEZE`, write a
memory file, read the log back. The helpers the agent builds honour what the
file declares: the counter is `fits_used` in `state.json`, not a number the
agent keeps; the 25th fit is refused by reading that file. A new helper,
`write_loop_log`, appends one audit line per iteration - and nothing reads
it. That last fact is the lesson: a loop that logs is still not RSI, because
generation n+1 loads the same `loop.json` and makes the same 24 fits. The
log becomes the first RSI file only in lesson 06, when a *different* pack
reads it under a contract.

## Getting started

Prerequisites: lesson 01 (the runtime contract - state, trace, split,
recipe - is unchanged; if you ran lesson 01 the agent will write the same
kind of helpers again, under this pack's `runs/adult-income-loop/helpers/`).
This lesson adds `loop.json` and `recipes.json` to the pack and the
`write_loop_log` contract to `tools.md`. Nothing here is shipped as Python
except `test_step.py`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-loop skill: run the loop harness on ../tasks/01_adult_income and report.
   ```

   The agent reads `SKILL.md`, `tools.md`, `loop.json`, `recipes.json`,
   `schema.json` and the intent, builds the six helpers, and runs the loop
   as declared: four `fit_recipe` calls of six recipes each with a
   `write_loop_log` after each, then the exit in order - `FREEZE`,
   `score_test` once, `save_model`, `scorecard`.

2. No approval. The hook blocks `score_test` until `state.json` says
   `"frozen": true`, which happens on the 24th fit.

3. Headless, as recorded:

   ```bash
   claude -p "Use the adult-income-loop skill: run the loop harness on ../tasks/01_adult_income and report." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: `loop.json` declares the
   counted while (`N` 24 = `n_fits` = the 24 recipes; the counter; the exit
   order; the illegal list), and the log is never read back (asserted from
   the text of the skill and the contract). `RSI_LIVE=1`: the run left
   `t` at 24, 24 loop-log lines `t=1 ..` to `t=24 ..`, one `score_test`
   after `FREEZE`, and the pack byte-identical (both mirrors).

5. To reset: `rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-loop/loop.json` - the loop as data:

```json
{
 "kind": "counted_while",
 "N": 24,
 "counter": "t",
 "error_still_counts": true,
 "body": [
  "recipe = recipes.json[t - 1]",
  "fit_recipe(recipe)  # one fit; fits_used in state.json is t",
  "write_loop_log(t, recipe, val_score)  # audit only"
 ],
 "exit": ["FREEZE", "score_test once, with the best val recipe", "save_model", "scorecard"],
 "illegal": ["change N", "reorder recipes.json", "a second while", "score_test before FREEZE", "write memory.json", "read loop.log back"]
}
```

`.claude/skills/adult-income-loop/SKILL.md` - the procedure runs the file:

```markdown
## Procedure
1. Build the helpers of `tools.md` under `runs/adult-income-loop/helpers/` if they are not there yet.
2. Open the arm: `load_splits P T --arm control --memory off`.
3. Run the loop exactly as `loop.json` declares it: `kind: counted_while`, the counter `t` from 1 to `N`, and for each `t` the body - the recipe is `recipes.json[t - 1]`, `fit_recipe` fits it (an errored fit still counts: `error_still_counts`), `write_loop_log` appends the audit line. You may fit in four calls of six recipes each (`fit_recipe P T --arm control --recipes <recipes 1-6>`, then 7-12, 13-18, 19-24) and log the six after each call; the counter is `fits_used` in `state.json`, not a number you keep in your head.
4. The exit, in the order `loop.json` lists it: the result says `FREEZE`; `score_test P T --arm control --recipe <best val recipe>` once; `save_model`; `scorecard`.
5. Answer in text with `N`, the best val_score, the test score and the number of loop-log lines. Stop.

## Rules
- Everything under `illegal` in `loop.json` is illegal: do not change `N`, reorder the recipes, open a second loop, score the test before FREEZE, write a memory file, or read `loop.log` back.
- The log is an audit trail and nothing else: no step of this procedure and no helper reads it. Generation n+1 loads the same `loop.json` and makes the same 24 fits. That is why this is not RSI yet.
```

`.claude/skills/adult-income-loop/tools.md` - the one new contract:

```markdown
- `write_loop_log(pack, task, arm, t, recipe, val_score)` - append one line `t=<t> recipe=<recipe> val=<val_score>` to `loop.log` in the arm directory. Audit only: no tool and no step of the procedure reads this file back.
```

`test_step.py` - the live assertions:

```python
    log = [l for l in (arm / "loop.log").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(log) == 24 and log[0].startswith("t=1 ") and log[-1].startswith("t=24 ")
    events = [r["event"] for r in rows(arm / "traces.jsonl") if "event" in r]
    assert events.count("score_test") == 1 and events.index("FREEZE") < events.index("score_test")
    assert tree(SKILLS) == before == tree(MIRROR), "a run changed the pack"
```

The recorded run (Claude Code 2.1.278, headless, from this directory; tool
results trimmed):

```text
[Skill adult-income-loop]
[Read tools.md]  [Read loop.json]  [Read recipes.json]  [Read schema.json]  [Read ../tasks/01_adult_income/intent.md]
agent> Now let me check whether helpers already exist and what the data looks like.
$ ls -la runs/ runs/adult-income-loop/ runs/adult-income-loop/helpers/ 2>&1; ls ../tasks/01_adult_income; head -3 ../data/adult_sample.csv; python -c "import sklearn, pandas; print(sklearn.__version__, pandas.__version__)"
ls: cannot access 'runs/adult-income-loop/': No such file or directory
age,workclass,fnlwgt,education,education-num,marital-status,occupation,relationship,race,sex,capital-gain,capital-loss,hours-per-week,native-country,target
28,Local-gov,336951,Assoc-acdm,12,Married-civ-spouse,Protective-serv,Husband,White,Male,0,0,40,United-States,1
1.8.0 2.1.4
agent> No helpers exist yet, so I'll build them per the tools.md contracts: a shared common.py and one script per tool.
[Write runs/adult-income-loop/helpers/common.py (246 lines)]
[Write runs/adult-income-loop/helpers/load_splits.py (45 lines)]   [Write .../fit_recipe.py (63 lines)]
[Write .../write_loop_log.py (27 lines)]   [Write .../score_test.py (34 lines)]   [Write .../save_model.py (30 lines)]   [Write .../scorecard.py (59 lines)]
agent> Helpers built. Now the procedure: open the control arm.
$ python runs/adult-income-loop/helpers/load_splits.py .claude/skills/adult-income-loop ../tasks/01_adult_income --arm control --memory off
{"arm": "control", "seed": 0, "problem": "adult_income", "profile": {"n_rows": 6000, "n_features": 14, "n_classes": 2, "imbalance": 0.239, "has_categorical": 1}, "budget": 24, "memory": "off"}
agent> Arm open; profile matches intent.md (6000 rows, 14 features, imbalance 0.239). Loop body, t = 1..6 (recipes 1-6 from recipes.json):
$ python runs/adult-income-loop/helpers/fit_recipe.py .claude/skills/adult-income-loop ../tasks/01_adult_income --arm control --recipes '[
{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"none"},
{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"balanced"},
... (4 more recipes)
{"results": [{"n": 1, "recipe": {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "val_score": 0.9114, "error": null}, {"n": 2, ... 0.911}, {"n": 3, ... 0.8544}, {"n": 4, ... 0.8577}, {"n": 5, ... 0.9103}, {"n": 6, ... 0.8973}], "fits_left": 18, "FREEZE": false}
$ H=runs/adult-income-loop/helpers/write_loop_log.py; P=.claude/skills/adult-income-loop; T=../tasks/01_adult_income
python $H $P $T --arm control --t 1 --recipe '{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"none"}' --val 0.9114
python $H $P $T --arm control --t 2 --recipe '{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"balanced"}' --val 0.911
... (4 more)
{"appended": "t=1 recipe={\"model\":\"logreg\",\"hyper\":1,\"scale\":\"yes\",\"encode\":\"onehot\",\"class_weight\":\"none\"} val=0.9114"}
{"appended": "t=2 recipe={...} val=0.911"}
... (4 more)
agent> t = 7..12 (recipes 7-12: the last two logreg, the first four rf):
$ python runs/adult-income-loop/helpers/fit_recipe.py ... --recipes '[ ...6 recipes... ]'
{"results": [{"n": 7, ... 0.8277}, {"n": 8, ... 0.8333}, {"n": 9, "recipe": {"model": "rf", ...}, "val_score": 0.9054}, {"n": 10, ... 0.9033}, {"n": 11, ... 0.9048}, {"n": 12, ... 0.9005}], "fits_left": 12, "FREEZE": false}
$ (write_loop_log t=7 .. t=12)
agent> t = 13..18 (last four rf, first two hgb):
$ python runs/adult-income-loop/helpers/fit_recipe.py ... --recipes '[ ...6 recipes... ]'
{"results": [{"n": 13, ... 0.9049}, {"n": 14, ... 0.9034}, {"n": 15, ... 0.9048}, {"n": 16, ... 0.9005}, {"n": 17, "recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "val_score": 0.9177, "error": null}, {"n": 18, ... 0.917}], "fits_left": 6, "FREEZE": false}
agent> The stderr traceback is joblib's physical-core probe failing to spawn wmic under the sandbox - joblib catches it internally and falls back; all six fits scored (error: null). Logging t=13..18:
$ (write_loop_log t=13 .. t=18)
agent> t = 19..24 (the last six hgb) - this call should reach N and FREEZE:
$ python runs/adult-income-loop/helpers/fit_recipe.py ... --recipes '[ ...6 recipes... ]'
{"results": [{"n": 19, ... 0.9108}, {"n": 20, ... 0.9122}, {"n": 21, ... 0.9177}, {"n": 22, ... 0.917}, {"n": 23, ... 0.9108}, {"n": 24, ... 0.9122}], "fits_left": 0, "FREEZE": true}
agent> FREEZE: true, fits_left: 0. Logging t=19..24:
$ (write_loop_log t=19 .. t=24)
$ P=.claude/skills/adult-income-loop; T=../tasks/01_adult_income; R='{"model":"hgb","hyper":0.1,"scale":"yes","encode":"onehot","class_weight":"none"}'
python runs/adult-income-loop/helpers/score_test.py $P $T --arm control --recipe "$R" 2>/dev/null
python runs/adult-income-loop/helpers/save_model.py $P $T --arm control --recipe "$R" 2>/dev/null
python runs/adult-income-loop/helpers/scorecard.py $P $T --arm control
{"test_score": 0.9049, "test_recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "test_scored": 1}
{"saved": "runs/adult-income-loop/adult_income/control/model.pkl", "recipe": {...}, "val_score": 0.9177}
{"problem": "adult_income", "arm": "control", "seed": 0, "n_fits": 24, "fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9177, "best_recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "test_score": 0.9049, "test_scored_once": true, "test_touched_before_freeze": false, "cards_active": 0, "cards_added": 0, "cards_demoted": 0}
agent> Quick verification of the invariants (line count of the log without reading its contents, state, pack unchanged) and a check that the guards refuse a second score_test:
$ D=runs/adult-income-loop/adult_income/control; wc -l < $D/loop.log; grep -c '"t":' $D/traces.jsonl; grep -o '"event": "[A-Za-z_]*"' $D/traces.jsonl | tr '\n' ' '; echo; grep '"frozen"' $D/state.json; echo "--- 2nd score_test:"; python runs/adult-income-loop/helpers/score_test.py ... ; echo "--- 25th fit:"; python runs/adult-income-loop/helpers/fit_recipe.py ... --recipes '[{"model":"logreg","hyper":4,...}]'; git status --short .claude/skills/adult-income-loop .agents/skills/adult-income-loop
24
24
"event": "open" "event": "FREEZE" "event": "score_test" "event": "scorecard"
 "frozen": true,
--- 2nd score_test:
{"error": "scored once already"}
--- 25th fit:
{"error": "budget: 24 fits used"}
agent> Done. Loop harness run on ../tasks/01_adult_income, arm control, seed 0, memory off.
- N = 24 - fits_used reached 24 in state.json, "frozen": true, FREEZE event in the trace.
- Best val_score: 0.9177 - hgb / lr 0.1 / scale yes / onehot / class_weight none (t=17; t=21 ties it with scale no, which is a no-op for trees).
- Test score: 0.9049 - scored once, after FREEZE, with that recipe.
- Loop-log lines: 24 (runs/adult-income-loop/adult_income/control/loop.log, counted with wc -l, never read back).
Guards checked: a second score_test -> {"error": "scored once already"}; a 25th fit -> {"error": "budget: 24 fits used"}; both pack mirrors unchanged by the run.
[30 turns, 386 s]
```

What to notice: the agent built seven small files this time (one per tool
plus `common.py`) where lesson 01's agent built one module - the contract
fixes names and behaviour, not layout. It ran the loop as the file declares
it, four calls of six with the audit log after each, and counted the log's
lines with `wc -l` rather than reading it, because `loop.json` says reading
it back is illegal. Unasked, it then tried the two refusals - a second
`score_test`, a 25th fit - and got the contract's answers from its own
helper. The numbers are lesson 01's (same helper contract, same split): the
loop file changed nothing about the fits, which is the point.

Files:

```text
step_02_loop_harness/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json
│   └── skills/adult-income-loop/
│       ├── SKILL.md                  the procedure runs loop.json
│       ├── tools.md                  the runtime + six contracts (write_loop_log is new)
│       ├── loop.json                 kind, N, counter, body, exit, illegal
│       ├── recipes.json              the 24 recipes the counter walks (= schema.json -> recipes)
│       └── schema.json
├── .agents/skills/adult-income-loop/ the same five files
└── runs/adult-income-loop/           (after a run) helpers/, adult_income/control/{state.json, traces.jsonl, loop.log, scorecard.json, model.pkl}
```

## Governance considerations

- **Who approves what.** Nobody; the pack changes no file. A human wrote
  `loop.json`; the illegal list is the human's, and the only way to change
  `N` is to edit the file by hand.
- **The hook.** As in lesson 01: `score_test` needs `"frozen": true` under
  `runs/`.
- **What the helper refuses.** The 25th fit; a `score_test` before FREEZE or
  a second one; a recipe outside the schema. What no helper can refuse: the
  agent reordering `recipes.json` in its head. The offline test asserts the
  procedure says "in order" and the live test asserts the log lines carry
  `t=1 .. t=24` in the trace's order; the illegal list is the rule, the
  agent is the one who follows it, and the README says so instead of
  pretending a script could.
- **What is and is not self-modified.** Nothing: `loop.json` is
  `mutable: false` in spirit, and the live test compares both mirrors to
  their bytes before the run. The log is written and never read.

## How to measure it

| Claim | Test |
|---|---|
| `loop.json` declares the counted while: `N` 24 = `n_fits` = the recipe count, the counter, `error_still_counts`, the exit order, the illegal moves; `recipes.json` = `schema.json -> recipes` | `test_loop_json_declares_the_counted_while` |
| the log is never read back (the skill and the contract say so) | `test_the_log_is_never_read_back` |
| the pack contract | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: `t` reached `N`, 24 log lines, one `score_test` after `FREEZE`, the pack byte-identical (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields reported: all 14; the card fields are 0.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 03 - a meta skill generates the loop harness](../step_03_meta_generates_loop/README.md):
a writer skill turns the intent into this pack, and a human approves it.
Previous: [lesson 01 - the regular harness](../step_01_regular_harness/README.md).
