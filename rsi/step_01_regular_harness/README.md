# Lesson 01 - The regular harness: a repeatable trainer, and not RSI

A skill that trains a classifier the same way every run: the agent opens
the arm, fits the 24 recipes of `schema.json` in order with one command,
picks the best validation score, scores the locked test split once, saves
the model, writes the scorecard, stops. Next Monday it boots the same text
and wastes the same fits. This is the control arm of the whole series and,
in the framework paper's terms, B0 / AutoML: a fixed procedure, no
persistent change, no decision moved from the designer to the system. It is
also where the machinery arrives - the tool scripts under `../tools/` (the
budget object, the locked test and the append-only trace as files under
`runs/`), and the hook under `../hooks/` - so that everything later is a
diff against this pack.

## Getting started

Lesson 00 left `task.json` and `acceptance.md`, and the curriculum under
`../tasks/`. This lesson adds one pack, `.claude/skills/adult-income-regular/`
(three files: `SKILL.md`, `tools.md`, `schema.json`), mirrored to
`.agents/skills/`, and the lesson's `.claude/settings.json` with the hook.
Open your agent in this directory (`cd rsi/step_01_regular_harness && claude`;
this repo's harness, Antigravity with `skills_paths=[".agents/skills"]`, or
Codex with the pack under `~/.codex/skills/` - see lesson 00). Running the
skill writes only under `runs/` (git-ignored): the pack itself does not change,
and the test asserts it.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-regular skill: train the Adult income classifier and report the scorecard.
   ```

   The agent runs, through its Bash tool, exactly the five commands of the
   procedure:

   ```bash
   python ../tools/load_splits.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json
   python ../tools/fit_recipe.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-regular/schema.json
   python ../tools/score_test.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/save_model.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
   python ../tools/scorecard.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json
   ```

   Recipes are written as `k=v` pairs so no shell has to quote JSON; a
   recipe may also be JSON on the line (bash) or `@file` (any shell; in
   PowerShell quote it, `'@file'`). No approval prompt: this pack changes
   nothing.

2. Try to break the rule, by hand: run `score_test.py` again. The hook blocks
   it before it runs (`gate: the test split was scored once already`), and
   without the hook the script answers `{"error": "the test split was scored
   once already; there is no second look"}`. Run `fit_recipe.py` once more:
   `fit 25 refused (FREEZE)`. Nothing is spent.

3. Reset with `rm -rf runs` (the pack under `.claude/skills/` was never
   written to).

4. Headless, as recorded below:
   `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi` from the repo root.

## What it looks like

`.claude/skills/adult-income-regular/SKILL.md` - the front matter names the
pack and when it triggers; the body is the procedure, each step an exact
command:

```markdown
---
name: adult-income-regular
description: Train a classifier for the Adult income problem by walking a fixed list of 24 recipes, the same way every run. Use in rsi/step_01_regular_harness, when the task is adult_income and the pack has no loop, graph or memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Regular harness: the same trainer, every run

## Procedure
1. Open the arm and read the profile:
   `python ../tools/load_splits.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json`
2. Fit the 24 recipes of `schema.json` -> `recipes`, in order, in one call; the first is the baseline. That is the whole budget: the script counts each fit and refuses a 25th.
   `python ../tools/fit_recipe.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-regular/schema.json`
3. The result's last line says `FREEZE` (`fits_left` is 0). Pick the recipe with the highest `val_score` from `results`.

## Rules
- Fit only the recipes that appear in `schema.json`, in their order. Never invent a field or a value; the script refuses a recipe outside the schema.
- Never run `score_test.py` before FREEZE, and never twice: the hook blocks it and the script refuses it.
- Do not read or write any other file. The next run boots this same text and makes the same 24 fits.
```

`.claude/skills/adult-income-regular/schema.json` - the task, the budget and
the 24 recipes (the 3 x 2 x 2 x 2 grid at each model's middle hyper value):

```json
{
 "task": "adult_income",
 "target": "target",
 "metric": "roc_auc",
 "n_fits": 24,
 "test_rule": {"scores": 1, "after": "FREEZE"},
 "models": ["logreg", "rf", "hgb"],
 "baseline": {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"},
 "recipes": [ ...24 recipes... ]
}
```

`../tools/_lib/state.py` - the budget, FREEZE and the locked test are
numbers in `runs/<pack>/<task>/state.json`, and every script starts from the
file:

```python
    def spend(self):
        """Count one fit before it happens; the 25th raises. An error still counts: a wasted fit is a fit."""
        s = self.arm_state
        if s["frozen"] or s["fits_used"] >= s["n_fits"]:
            raise ValueError(f"budget of {s['n_fits']} fits used; fit {s['fits_used'] + 1} refused (FREEZE)")
        s["fits_used"] += 1
        if s["fits_used"] >= s["n_fits"]:
            s["frozen"] = True
        return s["fits_used"]
```

```python
    def score_test_once(self, rec):
        s = self.arm_state
        if not s["frozen"]:
            raise ValueError(f"the test split is locked until FREEZE: {self.left} fits remain (or run freeze.py to forfeit them)")
        if s["test_scored"]:
            raise ValueError("the test split was scored once already; there is no second look")
        score = tasks.score_on(self.task, self.seed, rec, "test")
        s["test_scored"], s["test_score"], s["test_recipe"] = True, score, rec
```

`../tools/fit_recipe.py` - a recipe outside the schema, a model the task
does not allow, or (from lesson 06) a recipe a forbid card rules out is
refused before any budget is spent:

```python
def check(run, rec, schema):
    """Every reason this recipe may not be fitted, before any budget is spent."""
    rec = recipe.validate(rec)
    if rec["model"] not in run.task["allowed_models"]:
        raise ValueError(f"model {rec['model']} is not allowed by the task")
    if rec["model"] not in schema.get("models", recipe.SCHEMA["model"]):
        raise ValueError(f"model {rec['model']} is not in schema.json -> models")
```

`../hooks/gate.py` - the same rule, enforced before the script runs, for an
agent that honours hooks (Claude Code does; the others get the script's
refusal):

```python
        if name == "score_test.py":
            try:
                s = state_for(args, cwd)
            except Exception as e:      # an unreadable state is the script's problem, not the hook's
                return False, f"gate: could not read the state ({e}); the script decides"
            if s is None:
                return True, "gate: score_test.py needs --pack and --task, and an arm opened by load_splits.py"
            if not s["frozen"]:
                return True, f"gate: the test split is locked until FREEZE - {s['n_fits'] - s['fits_used']} fits remain on arm {s['arm']}"
            if s["test_scored"]:
                return True, "gate: the test split was scored once already; there is no second look"
```

The recorded run (Claude Code 2.1.278, headless, from this directory; the
fit results trimmed after the third recipe):

```text
[Skill adult-income-regular]
agent> Using the adult-income-regular skill: load splits, fit the 24 schema recipes,
score the best once on test, save, scorecard.
$ python ../tools/load_splits.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json
{"pack": "adult-income-regular", "problem": "adult_income", "arm": "memory", "seed": 0,
 "profile": {"n_rows": 6000, "n_features": 14, "n_classes": 2, "imbalance": 0.239, "has_categorical": 1},
 "metric": "roc_auc", "n_fits": 24, "fits_used": 0, "fits_left": 24, "frozen": false, ...}
$ python ../tools/fit_recipe.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-regular/schema.json
{"results": [
  {"n": 1, "recipe": {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "val_score": 0.9114, "error": null, "fits_left": 23},
  {"n": 2, "recipe": {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}, "val_score": 0.911, "error": null, "fits_left": 22},
  {"n": 3, "recipe": {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "ordinal", "class_weight": "none"}, "val_score": 0.8544, "error": null, "fits_left": 21},
  ...
  {"n": 24, ... "fits_left": 0}], "fits_used": 24, "n_fits": 24, "fits_left": 0, "FREEZE": true}
agent> FREEZE reached. Best val_score is 0.9172, tied between recipes 18 and 22; taking the
first one (n=18: hgb, hyper=0.1, scale=yes, onehot, balanced).
$ python ../tools/score_test.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
{"test_score": 0.9034, "recipe": {...}, "fits_used": 24, "metric": "roc_auc"}
$ python ../tools/save_model.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
{"saved": "...\\runs\\adult-income-regular\\adult_income\\model_memory_0.pkl", ...}
$ python ../tools/scorecard.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json
{"problem": "adult_income", "arm": "memory", "seed": 0, "n_fits": 24, "fits_used": 24, "wasted_fits": 16,
 "best_val_score": 0.9172, "best_recipe": {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"},
 "test_score": 0.9034, "test_scored_once": true, "test_touched_before_freeze": false,
 "cards_active": 0, "cards_added": 0, "cards_demoted": 0}
agent> Done. Best val_score 0.9172, test score 0.9034, 24 / 24 fits (FREEZE reached).
HGB dominated (0.910-0.917); logreg with onehot was close behind; RF sat at ~0.903-0.905.
Ordinal encoding hurt logreg badly (0.83-0.86) but was neutral for the tree models.
`scale` made no difference for the tree models, so recipes 9-16 and 21-24 duplicated
results - the scorecard counts 16 wasted fits.
[9 turns, 89 s]
```

What to notice: the agent's commentary at the end ("ordinal hurt logreg",
"scale made no difference for trees") is exactly the knowledge the static
walk throws away every Monday - `wasted_fits: 16` is the price. Lesson 06
puts it in a file. Also: the agent prefixed every command with `cd
"<this directory>"` on its own; the paths in `SKILL.md` are relative to the
lesson directory and that is where the agent was opened.

Files:

```text
step_01_regular_harness/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json                     the hook
│   └── skills/adult-income-regular/
│       ├── SKILL.md                      boot order, procedure, rules
│       ├── tools.md                      allowed / forbidden scripts
│       └── schema.json                   task, budget, the 24 recipes
├── .agents/skills/adult-income-regular/  the same three files
└── runs/adult-income-regular/adult_income/   (after a run; git-ignored)
    ├── state.json                        fits used, frozen, test scored
    ├── traces.jsonl                      boot, 24 fits, score_test, save_model
    ├── scorecard_memory_0.json
    └── model_memory_0.pkl
```

## Governance considerations

- **Who approves what.** Nobody: the pack changes nothing, so there is
  nothing to approve. The human wrote the pack; the agent executes it.
- **The hook.** `../hooks/gate.py` blocks `score_test.py` while
  `state.json` says fits remain, and again once it says `test_scored`.
- **What the script refuses.** The 25th `fit_recipe.py`; a recipe outside
  `schema.json`; `score_test.py` before FREEZE or twice; `save_model.py` for
  a recipe this arm never fitted; any script whose name is not under
  `## Allowed` in the pack's `tools.md` (`write_card.py` answers `not in
  adult-income-regular's tools.md`).
- **What is and is not self-modified.** Nothing is. `runs/` is written; the
  pack is not; the trace is append-only (there is no script that rewrites or
  deletes a line). This is the B0 boundary the framework paper draws: a
  better answer this run, no persistent change.

## How to measure it

| Claim | Test |
|---|---|
| the static walk makes 24 fits in schema order, the baseline first, and one test score, and the scorecard has exactly lesson 00's fields | `test_static_walk_24_fits_in_schema_order_one_test_score` |
| the 25th fit and the second score are refusals (JSON results), and `state.json` says so | `test_25th_fit_and_second_score_are_refusals` |
| `score_test` before FREEZE is refused by the script and blocked by the hook (exit 2) | `test_score_test_before_freeze_is_refused_by_script_and_hook` |
| an unknown value, malformed JSON, an extra field or a disallowed script is a result, and no fit is spent | `test_bad_calls_are_results_not_crashes` |
| the trace is append-only and the same pack twice gives the same log | `test_trace_is_append_only_and_deterministic` |
| the CLI contract (subprocess, JSON out, exit 0) | `test_cli_contract` |
| the pack contract (front matter, scripts exist, forbidden absent, mirror identical, hook installed) | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard on this machine (seed 0): `fits_used 24`, `wasted_fits 16`,
`best_val_score 0.9172`, `test_score 0.9034`, `test_scored_once true`,
`test_touched_before_freeze false`, cards 0 / 0 / 0.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 02 - loop engineering](../step_02_loop_harness/README.md): the same
trainer with its loop, counter and gate named in a file the scripts enforce.
Previous: [Lesson 00 - intent](../step_00_intent/README.md).
