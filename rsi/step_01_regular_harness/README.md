# Lesson 01 - The regular harness: a repeatable trainer, and not RSI

A harness is the program around the model. This one is the smallest that
does the job: a skill pack a coding agent boots, a fixed list of 24 recipes
it fits in order, one score on a locked test split after the budget is spent,
one saved model. It does the same thing every run - same text, same fits,
same waste every Monday - which is exactly why it is the control arm of the
whole series and not RSI: nothing it learns survives the run, because nothing
is written that a later run reads. What arrives here and never leaves: the
budget object (`fits_used` in a `state.json` the agent's own helper refuses
to exceed), the locked test (scored once, only after `FREEZE`), and the
append-only trace. And the shape every later lesson keeps: the pack ships no
code. `tools.md` states the contracts of five helpers - what they take, what
they print, which file they append to, what they refuse - and the agent
writes them on first use, under `runs/adult-income-regular/helpers/`, from
that text and the data source named in the intent. The agent *is* the
harness; the skill pack *is* the program.

## Getting started

Prerequisites: lesson 00 (the intent under `../tasks/01_adult_income/`; the
bundled `../data/adult_sample.csv`), scikit-learn and pandas installed for
the helpers the agent will write, and a coding agent. This lesson adds the
first pack, `.claude/skills/adult-income-regular/` (`SKILL.md`, `tools.md`,
`schema.json`), and, once run, the agent's helpers and the run state under
`runs/` (git-ignored). Nothing here is shipped as Python except
`test_step.py`.

Where the skill loads from: `cd rsi/step_01_regular_harness && claude` (the
pack under `.claude/skills/`; the hook from `.claude/settings.json`); this
repo's harness, Antigravity and Codex read the identical
`.agents/skills/adult-income-regular/` as lesson 00 explains.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-regular skill: run the regular harness on ../tasks/01_adult_income and report.
   ```

   The agent reads `SKILL.md`, then `tools.md`, then `schema.json` and the
   intent. Its first act is to write the five helpers the contracts describe
   (the recorded run below wrote one Python module, `helpers/rsi.py`, with a
   sub-command per tool). Then, through its Bash tool from this directory:

   ```bash
   python runs/adult-income-regular/helpers/rsi.py load_splits --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income --arm control --memory off
   python runs/adult-income-regular/helpers/rsi.py fit_recipe  ... --recipes '<the 24 recipes of schema.json>'   # one call, 24 fits, FREEZE
   python runs/adult-income-regular/helpers/rsi.py score_test  ... --recipe '<the best val recipe>'              # once, after FREEZE
   python runs/adult-income-regular/helpers/rsi.py save_model  ... --recipe '<the same recipe>'
   python runs/adult-income-regular/helpers/rsi.py scorecard   ...
   ```

   The exact file name and calling convention are the agent's: the contract
   fixes the tool names, the inputs, the outputs, the files and the refusals,
   not the syntax. Yours may differ; the artifacts under `runs/` may not.

2. There is no approval in this lesson. The hook has one thing to do: it
   blocks any Bash command containing `score_test` until a `state.json`
   under `runs/` says `"frozen": true` - which the helper writes on the
   24th fit.

3. Headless, as recorded (project settings only: the lesson's hook and
   skills, nothing from your user profile):

   ```bash
   claude -p "Use the adult-income-regular skill: run the regular harness on ../tasks/01_adult_income and report." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi` (offline: the pack contract, the schema
   is the intent plus 24 recipes, the procedure is static and scores once,
   the contracts state the refusals). `RSI_LIVE=1` records the run and
   asserts on what it left: 24 fit rows numbered 1..24, `state.json` frozen
   with `test_scored` 1, `FREEZE` before `score_test` in the trace, a
   scorecard with exactly the 14 fields, a `model.pkl`.

5. To reset: `rm -rf runs` (the pack itself never changes in this lesson).

## What it looks like

`.claude/skills/adult-income-regular/SKILL.md` - boot order, procedure,
rules, off switch, done-when. Step 1 is the one that has no equivalent in a
scripted harness: build the helpers.

```markdown
---
name: adult-income-regular
description: "Train a classifier for the Adult income problem by walking a fixed list of 24 recipes, the same way every run, with helpers you build from the contracts in tools.md. Use in rsi/step_01_regular_harness, when the task is adult_income and the pack has no loop, graph or memory file."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# Regular harness: the same trainer, every run

## Boot order
1. This file. 2. `tools.md`: the helpers you build and their contracts. 3. `schema.json`: the task, the budget (`n_fits: 24`), the recipe space (`fields`) and the 24 recipes, in order. 4. `T/intent.md`: the data source and the metric.

## Procedure
1. Build the helpers named under `## Allowed` in `tools.md` under `runs/adult-income-regular/helpers/` if they are not there yet (one file per tool, or one module with one function per tool: the names and the contracts are what matters, and the runtime section of `tools.md` says exactly how to read the table, split it and fit a recipe). Reuse them if they exist.
2. Open the arm and keep the profile it prints: `load_splits P T --arm control --memory off`.
3. Fit the 24 recipes of `schema.json -> recipes`, in order, in one call: `fit_recipe P T --arm control --recipes <the list>`. The first is the baseline. That is the whole budget: the helper counts each fit in `state.json` and refuses a 25th.
4. The result says `FREEZE` (`fits_left` is 0). Pick the recipe with the highest `val_score` from `results`.
5. Score it on the locked test split once, after FREEZE, then save it: `score_test P T --arm control --recipe <that recipe>`, then `save_model P T --arm control --recipe <that recipe>`.
6. Write the scorecard - `scorecard P T --arm control` - and answer in text with the best val_score, the test score and the number of fits. Stop.

## Rules
- Fit only the recipes that appear in `schema.json`, in their order. Never invent a field or a value; `fit_recipe` refuses a recipe outside `fields`.
- Never run `score_test` before FREEZE, and never twice: the lesson's hook blocks the command until a `state.json` says `"frozen": true`, and the helper refuses it by reading the state.
```

`.claude/skills/adult-income-regular/tools.md` - the runtime the helpers
share (paths, `state.json`, the trace, the data, the profile, the split, the
recipe as a scikit-learn pipeline) and then one contract per tool. The two
that carry the lesson:

```markdown
- `fit_recipe(pack, task, arm, recipes)` - for each recipe of the list, in order: refuse (no fit, `"refused": "..."` on that item) a recipe outside `schema.json -> fields`, one an active `forbid` card rules out (memory arms only), or one this arm already fitted; refuse every item once `fits_used` is `n_fits` (`"error": "budget: 24 fits used"`); otherwise fit on train, score on val, append the fit row and add one to `fits_used` (an errored fit counts). The moment `fits_used` reaches `n_fits`, write `"frozen": true` and append `{"event": "FREEZE"}`. Print `results` (each with `n`, `recipe`, `val_score`, `error`), `fits_left` and `FREEZE` (true / false). Refuses the 25th call by reading `state.json`, not by counting in memory.
- `score_test(pack, task, arm, recipe)` - refuse unless `state.json` says `"frozen": true` (`"error": "the test split is locked until FREEZE"`); refuse when `test_scored` is already 1 (`"error": "scored once already"`); refuse a recipe this arm never fitted. Otherwise fit it again on train (deterministic), score the test part, write `test_score`, `test_recipe`, `test_scored: 1`, append `{"event": "score_test", "recipe", "test_score"}`, print them.
```

and the split, fixed so that every arm of every lesson sees the same rows:

```markdown
- **Split.** `order = numpy.random.default_rng(seed).permutation(n_rows)`; train = the first
  55 %, val = the next 15 %, private = the next 10 %, test = the last 20 % (cuts at
  `int(n * 0.55)`, `int(n * 0.70)`, `int(n * 0.80)`). The same seed gives the same rows on
  every machine. Only `score_test` may read the test part; only `private_score` the private part.
```

`.claude/skills/adult-income-regular/schema.json` - the intent's facts
(`n_fits`, `test_rule`, `metric`, `models`), the recipe space (`fields`: 3
models x 3 hyper values x 2 x 2 x 2 = 72 recipes) and the 24 static recipes
(every model at its middle hyper value, grid order), the first of which is
the baseline. The offline test checks the schema against the intent and
that the 24 recipes are distinct and all sit at the middle hyper value.

`test_step.py` - the live assertions are the contract the run must leave:

```python
    s = state("adult-income-regular", "adult_income", "control")
    assert s["fits_used"] == s["n_fits"] == 24 and s["frozen"] is True and s["test_scored"] == 1
    fits = [r for r in rows(arm / "traces.jsonl") if "t" in r]
    assert len(fits) == 24 and [r["t"] for r in fits] == list(range(1, 25))
    events = [r["event"] for r in rows(arm / "traces.jsonl") if "event" in r]
    assert events.index("FREEZE") < events.index("score_test") and events.count("score_test") == 1
```

The recorded run (Claude Code 2.1.278, headless, from this directory; the
helper the agent wrote is quoted in part, tool results trimmed):

<!-- transcript -->

Files:

```text
step_01_regular_harness/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json                     the hook: score_test needs "frozen": true somewhere under runs/
│   └── skills/adult-income-regular/
│       ├── SKILL.md                      boot order, the static procedure, the rules
│       ├── tools.md                      the runtime + five contracts: load_splits, fit_recipe, score_test, save_model, scorecard
│       └── schema.json                   the intent's facts, the 72-recipe space, the 24 static recipes
├── .agents/skills/adult-income-regular/  the same three files
└── runs/                                 (after a run, git-ignored)
    └── adult-income-regular/
        ├── helpers/                      what the agent wrote from the contracts
        └── adult_income/control/         state.json, traces.jsonl, scorecard.json, model.pkl
```

## Governance considerations

- **Who approves what.** Nobody: the pack changes no file, so there is
  nothing to approve. The human wrote the intent (lesson 00) and the pack.
- **The hook.** Blocks `score_test` until a `state.json` says
  `"frozen": true`. In the recorded run the agent never tried early; the
  offline test only asserts the hook line is there, the live test that
  `FREEZE` precedes `score_test` in the trace.
- **What the helper refuses** - because the contract says so and the agent
  implemented it: the 25th fit (read from `state.json`, not counted in the
  agent's head), a recipe outside the schema, a second `score_test`, a
  `score_test` before FREEZE, a `save_model` of a recipe never fitted.
  Agents without hooks (this repo's harness, Antigravity, Codex) get exactly
  these refusals. What is *not* enforced by anything but the text: that the
  agent builds the helper honestly. That is the teaching line of the series -
  the pack states rules, the agent follows them, the hook enforces two - and
  every later lesson keeps the split visible.
- **What is and is not self-modified.** Nothing in the pack. The helpers are
  the agent's, written once; `runs/` holds state, not learning.
- **Numbers.** Two machines need not print the same `val_score`: the agent
  writes its own fit helper. On one machine the numbers are reproducible
  (the split is a constant, the models are seeded), and every later
  comparison is arm against arm on that machine.

## How to measure it

| Claim | Test |
|---|---|
| `schema.json` is the intent (`n_fits`, `test_rule`, `metric`, `models`) plus 24 distinct static recipes at the middle hyper value, baseline first | `test_schema_is_the_intent_plus_24_recipes` |
| the procedure walks the list in order in one call and names `score_test` once | `test_procedure_is_static_and_scores_once` |
| the contracts state the refusals the helpers must implement (the 25th fit, `score_test` before FREEZE, a second `score_test`) and where the helpers live | `test_contracts_state_the_refusals` |
| the pack contract (front matter, named files exist, forbidden tools absent, mirror identical, hook line, no Python but the test) | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: 24 fit rows 1..24, frozen, `test_scored` 1, FREEZE before `score_test`, a 14-field scorecard, `model.pkl`, the mirror untouched (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields reported: all 14 of lesson 00; `cards_active`,
`cards_added` and `cards_demoted` are 0 because there is no memory file.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 02 - loop engineering](../step_02_loop_harness/README.md): the same
24 fits, but the loop becomes a file (`loop.json`) and the helpers honour
what it declares. Previous: [lesson 00 - intent](../step_00_intent/README.md).
