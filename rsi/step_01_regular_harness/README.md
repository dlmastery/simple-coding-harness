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
   (the recorded run below wrote one Python module, `helpers/harness.py`,
   with a sub-command per tool). Then, through its Bash tool from this
   directory:

   ```bash
   python runs/adult-income-regular/helpers/harness.py load_splits .claude/skills/adult-income-regular ../tasks/01_adult_income --arm control --memory off
   python runs/adult-income-regular/helpers/harness.py fit_recipe  ... --arm control --recipes @runs/adult-income-regular/helpers/recipes_24.json   # one call, 24 fits, FREEZE
   python runs/adult-income-regular/helpers/harness.py score_test  ... --arm control --recipe '<the best val recipe>'                           # once, after FREEZE
   python runs/adult-income-regular/helpers/harness.py save_model  ... --arm control --recipe '<the same recipe>'
   python runs/adult-income-regular/helpers/harness.py scorecard   ... --arm control
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

```text
[Skill adult-income-regular]
[Read .claude/skills/adult-income-regular/tools.md]  [Read .claude/skills/adult-income-regular/schema.json]
[Read ../tasks/01_adult_income/intent.md]
agent> Let me check whether helpers or an open arm already exist.
$ ls -R runs 2>/dev/null | head -50; ls ../tasks/01_adult_income; ls ../data 2>/dev/null | head; python -c "import sklearn, pandas, numpy; print(sklearn.__version__, pandas.__version__, numpy.__version__)"
intent.md
README.md
adult_sample.csv
1.8.0 2.1.4 1.26.4
agent> No helpers exist yet. I'll build one module implementing the four allowed tools per the contracts in tools.md.
[Write runs/adult-income-regular/helpers/harness.py (359 lines)]
agent> Step 2: open the control arm.
$ python runs/adult-income-regular/helpers/harness.py load_splits .claude/skills/adult-income-regular ../tasks/01_adult_income --arm control --memory off
{"profile": {"n_rows": 6000, "n_features": 14, "n_classes": 2, "imbalance": 0.239, "has_categorical": 1}, "budget": {"n_fits": 24, "fits_used": 0}, "arm": "control", "seed": 0, "memory": "off"}
agent> Profile matches intent.md (6000 rows, 14 features, 2 classes, imbalance 0.239, categorical). Step 3: fit the 24 recipes in schema order, one call.
$ python -c "import json; json.dump(json.load(open('.claude/skills/adult-income-regular/schema.json'))['recipes'], open('runs/adult-income-regular/helpers/recipes_24.json','w'))" && python runs/adult-income-regular/helpers/harness.py fit_recipe .claude/skills/adult-income-regular ../tasks/01_adult_income --arm control --recipes @runs/adult-income-regular/helpers/recipes_24.json
{"results": [{"n": 1, "recipe": {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "val_score": 0.9114, "error": null},
 {"n": 2, ... "val_score": 0.911}, {"n": 3, ... "encode": "ordinal" ... "val_score": 0.8544}, {"n": 4, ... 0.8577}, {"n": 5, ... 0.9103}, {"n": 6, ... 0.8973}, {"n": 7, ... 0.8277}, {"n": 8, ... 0.8333},
 {"n": 9, "recipe": {"model": "rf", ...}, "val_score": 0.9054}, {"n": 10, ... 0.9033}, {"n": 11, ... 0.9048}, {"n": 12, ... 0.9005}, {"n": 13, ... 0.9049}, {"n": 14, ... 0.9034}, {"n": 15, ... 0.9048}, {"n": 16, ... 0.9005},
 {"n": 17, "recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "val_score": 0.9177, "error": null}, {"n": 18, ... 0.917}, {"n": 19, ... 0.9108}, {"n": 20, ... 0.9122}, {"n": 21, ... 0.9177}, {"n": 22, ... 0.917}, {"n": 23, ... 0.9108}, {"n": 24, ... 0.9122}],
 "fits_left": 0, "FREEZE": true}
$ python runs/adult-income-regular/helpers/harness.py score_test .claude/skills/adult-income-regular ../tasks/01_adult_income --arm control --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}' 2>/dev/null
{"test_score": 0.9049, "test_recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "test_scored": 1}
$ python runs/adult-income-regular/helpers/harness.py save_model ... --recipe '{"model": "hgb", ...}' 2>/dev/null && python runs/adult-income-regular/helpers/harness.py scorecard .claude/skills/adult-income-regular ../tasks/01_adult_income --arm control 2>/dev/null
{"saved": "runs/adult-income-regular/adult_income/control/model.pkl", "recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}}
{"problem": "adult_income", "arm": "control", "seed": 0, "n_fits": 24, "fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9177, "best_recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "test_score": 0.9049, "test_scored_once": true, "test_touched_before_freeze": false, "cards_active": 0, "cards_added": 0, "cards_demoted": 0}
agent> Done. Regular harness run on ../tasks/01_adult_income, control arm, seed 0:
| Best val_score | 0.9177 (ROC-AUC) |
| Test score     | 0.9049 (scored once, after FREEZE) |
| Fits           | 24 / 24 |
| Best recipe    | hgb, learning_rate 0.1, scale yes, onehot, no class weight (fit #17; #21 tied with scale=no) |
| Wasted fits    | 16 (the first recipe within 0.005 of the best was #17) |
Trajectory in the fixed order: logreg+onehot ~ 0.911, logreg+ordinal drops to 0.83-0.86, rf ~ 0.900-0.905,
hgb+onehot 0.917-0.918. No fit errored; test_touched_before_freeze is false.
Artifacts under runs/adult-income-regular/: helpers/harness.py (the five tools, built fresh - none existed)
and adult_income/control/ with state.json ("frozen": true), traces.jsonl, model.pkl, scorecard.json.
[12 turns, 216 s]
```

The helper the agent wrote, `runs/adult-income-regular/helpers/harness.py`
(359 lines, one function per tool and a CLI; the pipeline, as the
contract states it - quoted from the run, not shipped):

```text
def _build_pipeline(recipe, df, target):
    feats = [c for c in df.columns if c != target]
    num = [c for c in feats if pd.api.types.is_numeric_dtype(df[c])]
    cat = [c for c in feats if c not in num]
    num_tf = StandardScaler() if recipe["scale"] == "yes" else "passthrough"
    cat_tf = (OneHotEncoder(handle_unknown="ignore") if recipe["encode"] == "onehot"
              else OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))
    pre = ColumnTransformer([("num", num_tf, num), ("cat", cat_tf, cat)], sparse_threshold=0)
    cw = "balanced" if recipe["class_weight"] == "balanced" else None
    h = recipe["hyper"]
    if recipe["model"] == "logreg":
        clf = LogisticRegression(C=h, max_iter=2000, class_weight=cw)
    elif recipe["model"] == "rf":
        clf = RandomForestClassifier(n_estimators=40, max_depth=h, random_state=0, class_weight=cw)
    else:
        clf = HistGradientBoostingClassifier(learning_rate=h, max_iter=40, max_bins=64,
                                             random_state=0, class_weight=cw)
    return Pipeline([("pre", pre), ("clf", clf)])
```

What to notice: the first thing the agent did was look for helpers and,
finding none, write them - 359 lines from a page of contracts, before any
fit. The 24 fits came in one call and the 24th froze the arm; `score_test`
came after, once. `wasted_fits` is 16: the static order visits every
`logreg` and `rf` recipe before the first `hgb`, which is the waste every
Monday that lesson 06's cards are meant to remove. The numbers are this
machine's (this agent's helper, sklearn 1.8): yours may differ, the
artifacts may not.

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
