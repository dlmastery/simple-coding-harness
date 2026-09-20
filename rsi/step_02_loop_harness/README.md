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

<!-- transcript -->

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
