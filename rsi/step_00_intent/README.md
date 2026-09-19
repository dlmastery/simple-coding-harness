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
that every writer and verifier reads. It is also the first lesson that runs
*inside a coding agent*: you open Claude Code (or this repo's harness,
Antigravity, Codex) in this directory, the agent finds the skill under
`.claude/skills/`, and the only Python it touches are the tool scripts under
`../tools/` that it runs through its shell.

## Getting started

Prerequisites: Python 3.10+ and `pip install -r requirements.txt` from the
repo root (scikit-learn, pandas, jsonschema, pyyaml); a coding agent - Claude
Code 2.1 or later on your PATH for the recorded transcript below, or any agent
that reads `SKILL.md` files. Nothing is on disk yet from a previous lesson;
this one adds the two intent files, the schema they validate against
(`../tools/_lib/task.schema.json`), the curriculum they belong to
(`../tasks/`, one `task.json` per problem, problem 7 the exam), and the
skill that checks them (`.claude/skills/intent/`, mirrored to
`.agents/skills/intent/` for this repo's harness).

Where the skill loads from, per agent:

- **Claude Code**: `cd rsi/step_00_intent && claude` - the pack under
  `.claude/skills/intent/` is discovered by name; `.claude/settings.json`
  installs the lesson's hook (`../hooks/gate.py`).
- **This repo's harness** (root codelab stage 4+): the same files under
  `.agents/skills/intent/`; run the harness with this directory as cwd.
- **Antigravity** (root step 18): `skills_paths=[".agents/skills"]` with this
  directory as cwd.
- **Codex**: copy or symlink `.agents/skills/intent` into `~/.codex/skills/`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the intent skill in .claude/skills/intent: validate this lesson's intent and report.
   ```

   The agent reads `.claude/skills/intent/SKILL.md` and runs, through its
   Bash tool:

   ```bash
   python ../tools/validate_intent.py --task task.json --acceptance acceptance.md
   python ../tools/lint_pack.py --files @.claude/skills/intent/widened_pack.json --task task.json
   ls ../tasks && for f in ../tasks/*; do python ../tools/validate_intent.py --task "$f"; done
   ```

   In PowerShell (if you run the scripts by hand) `@file` is the splat
   operator, so quote it: `--files '@.claude/skills/intent/widened_pack.json'`.

2. There is no approval in this lesson: the human *is* the author, and the
   skill changes nothing (the test asserts the directory is byte-identical
   after both commands).

3. Headless, the way the transcript below was recorded:

   ```bash
   claude -p "Use the intent skill in .claude/skills/intent: validate this lesson's intent and report." --allowedTools "Bash,Read,Write,Edit,Skill"
   ```

4. Tests: `python run_tests.py rsi` from the repo root, or
   `python -m pytest -q test_step.py` here. `RSI_LIVE=1` adds the `claude -p`
   smoke test.

## What it looks like

`.claude/skills/intent/SKILL.md` - the front matter names the skill and when
it triggers; the body is the procedure the agent follows, each step an exact
command:

```markdown
---
name: intent
description: Validate the intent of the rsi series - task.json (what to improve, how, the budget, the locked-test rule) and acceptance.md (what counts as success) - and show that a pack which widens the intent is refused. Use in rsi/step_00_intent before any pack exists.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Intent: what to improve, how, and what counts as success

## Procedure
1. Validate the intent:
   `python ../tools/validate_intent.py --task task.json --acceptance acceptance.md`
2. Show that a pack which widens the intent is refused before any human sees it. `widened_pack.json` in this skill's directory is a regular pack whose `schema.json` raises `n_fits` to 48 and scores the test twice:
   `python ../tools/lint_pack.py --files @.claude/skills/intent/widened_pack.json --task task.json`
```

`.claude/skills/intent/tools.md` - what the skill may and may not run. The
scripts enforce it too: a script whose name is not under `## Allowed` in the
acting pack's `tools.md` refuses to run for it.

```markdown
## Allowed
- validate_intent - task.json against the task schema, acceptance.md against the scorecard fields
- lint_pack - every reason a pack may not run for a task; refuses a pack that widens the intent

## Forbidden
- load_splits, fit_recipe, score_test, save_model - nothing is trained in this lesson
- write_card, propose, apply, patch_pack - nothing is written or changed
```

`.claude/settings.json` - the lesson's hook. Every Bash call the agent makes
goes through `../hooks/gate.py` first; in this lesson it has nothing to block,
but the shape is the same in every lesson:

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/../hooks/gate.py\""}]}
    ]
  }
}
```

`../tools/validate_intent.py` - the script behind step 1. Like every tool
script it prints one JSON object and exits 0 even when the answer is no:

```python
def main(argv=None):
    a = PARSER.parse_args(argv)
    problems = []
    try:
        task = tasks.load_task(a.task)
    except Exception as e:
        return {"ok": False, "problems": [f"task.json: {str(e).splitlines()[0]}"]}
    missing = []
    if a.acceptance:
        text = Path(a.acceptance).read_text(encoding="utf-8")
        missing = [f for f in SCORECARD_FIELDS if f"`{f}`" not in text and not re.search(rf"^- {f}$", text, re.M)]
        if missing:
            problems.append(f"acceptance.md lacks the scorecard fields {missing}")
        if "once" not in text or "FREEZE" not in text:
            problems.append("acceptance.md must state the locked-test rule: scored once, after FREEZE")
```

`../tools/_lib/packs.py` - the part of `lint_pack` that refuses a pack that
widens the intent, used by step 2 and by every later writer:

```python
    if "schema.json" in files:
        schema = json.loads(files["schema.json"])
        n_fits = schema.get("n_fits")
        if n_fits != task["budget"]["n_fits"]:
            problems.append(f"schema.json n_fits {n_fits} != task budget {task['budget']['n_fits']}")
        if schema.get("test_rule") != task["test_rule"]:
            problems.append("schema.json test_rule differs from the task's")
```

The recorded run (Claude Code 2.1.278, headless, from this directory; tool
results trimmed to their first lines):

```text
agent> Using the `intent` skill to validate this lesson's intent.
[Skill intent]
agent> Step 1: validate the intent files.
$ python ../tools/validate_intent.py --task task.json --acceptance acceptance.md
{
 "ok": true,
 "problems": [],
 "task": "adult_income",
 "budget": {"n_fits": 24, "per": "arm"},
 "metric": "roc_auc",
 "test_rule": {"scores": 1, "after": "FREEZE"},
 "allowed_models": ["logreg", "rf", "hgb"],
 "profile_keys": ["n_rows", "n_features", "n_classes", "imbalance", "has_categorical"],
 "scorecard_fields": ["problem", ...
agent> Step 2: show the widened pack is refused.
$ python ../tools/lint_pack.py --files @.claude/skills/intent/widened_pack.json --task task.json
{
 "ok": false,
 "problems": [
  "schema.json n_fits 48 != task budget 24",
  "schema.json test_rule differs from the task's"
 ],
 "pack": "proposal",
 "task": "adult_income"
}
agent> Step 3: lint every task in the curriculum.
$ ls ../tasks && for f in ../tasks/*; do echo "== $f"; python ../tools/validate_intent.py --task "$f"; done
01_adult_income.json
02_breast_cancer.json
03_wine.json
04_digits.json
05_synth_shift_a.json
06_synth_shift_b.json
07_exam.json
== ../tasks/01_adult_income.json
{"ok": true, "problems": [], "task": "adult_income", ...
agent> Both validations ran and the widened pack was refused. Nothing was changed,
no pack, run directory or card was created.

## Intent report - rsi/step_00_intent
1. Intent is valid: task adult_income; budget 24 fits per arm; metric roc_auc;
   test rule: score the locked test split once, only after FREEZE; models logreg,
   rf, hgb; profile keys n_rows, n_features, n_classes, imbalance, has_categorical;
   14 scorecard fields: problem, arm, seed, n_fits, fits_used, wasted_fits,
   best_val_score, best_recipe, test_score, test_scored_once,
   test_touched_before_freeze, cards_active, cards_added, cards_demoted.
2. Widened pack refused: n_fits 48 != task budget 24; test_rule differs (scores: 2).
3. Curriculum: 01 adult_income roc_auc curriculum; 02 breast_cancer roc_auc
   curriculum; 03 wine roc_auc_ovr_macro curriculum; 04 digits roc_auc_ovr_macro
   curriculum; 05 synth_shift_a roc_auc curriculum; 06 synth_shift_b roc_auc
   curriculum; 07 exam roc_auc exam. Six curriculum, one exam.
[8 turns, 90 s]
```

What to notice: the agent read the roles from the task files itself because
the validator's output had no `role` field at recording time (it does now);
the report is the scripts' JSON, not the agent's opinion; and the one time
the agent reached for a non-Bash tool (`Grep` on `../tasks`) the sandbox
refused it - the lesson directory is the agent's world, and everything
outside it comes through the scripts.

Files:

```text
step_00_intent/
├── README.md
├── task.json                       what to improve, how, the budget, the test rule
├── acceptance.md                   the scorecard fields and the pass rule
├── test_step.py
├── .claude/
│   ├── settings.json               the PreToolUse hook -> ../hooks/gate.py
│   └── skills/intent/
│       ├── SKILL.md                the procedure, one command per step
│       ├── tools.md                allowed / forbidden scripts
│       └── widened_pack.json       a pack that raises the budget: refused
└── .agents/skills/intent/          the same three files, for this repo's harness
```

## Governance considerations

- **Who approves what.** The human writes `task.json` and `acceptance.md`;
  no agent proposes them and no agent may change them. Every later
  proposal (a generated pack in 03/05/08, a patch in 09-16) is linted
  against this task before a human sees it.
- **The hook.** `.claude/settings.json` runs `../hooks/gate.py` before every
  Bash call. It blocks `score_test.py` before FREEZE and `apply.py` /
  `patch_pack.py --proposal` without `--approved "<the user's words>"`.
  In this lesson neither can occur; the hook is installed so that the shape
  is the same from the first page.
- **What the script refuses.** `lint_pack.py` refuses a `schema.json` whose
  `n_fits`, `test_rule`, `metric` or `models` differ from the task's; the
  agent cannot talk it into a wider budget. `validate_intent.py` refuses a
  `task.json` outside the schema (budget above 24, a second test score, an
  unknown model) and an `acceptance.md` missing a scorecard field.
- **What is and is not self-modified.** Nothing. This lesson has no
  persistent state that changes; the test asserts the directory is
  byte-identical after the skill's commands.

## How to measure it

| Claim | Test |
|---|---|
| `task.json` and `acceptance.md` validate against the schema | `test_intent_validates` |
| the acceptance fields are exactly the 14 scorecard fields every later lesson reports | `test_acceptance_fields_are_exactly_the_scorecard_fields` |
| a pack that raises the budget or touches the test rule is refused by `lint_pack` | `test_widened_pack_is_refused` |
| a bad task is a JSON result, not a crash | `test_a_bad_task_is_a_result_not_a_crash` |
| the seven curriculum problems validate, in order, six curriculum + one exam | `test_curriculum_validates_in_order` |
| the CLI contract: JSON on stdout, exit 0 | `test_cli_contract_json_out_exit_zero` |
| the pack contract: front matter, every named script exists, forbidden tools absent from the procedure, `.claude/skills == .agents/skills`, the hook installed | `test_pack_contract` |
| the skill changes nothing on disk | `test_skill_changes_nothing` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields this lesson defines (reported from lesson 01 on): `problem`,
`arm`, `seed`, `n_fits`, `fits_used`, `wasted_fits`, `best_val_score`,
`best_recipe`, `test_score`, `test_scored_once`, `test_touched_before_freeze`,
`cards_active`, `cards_added`, `cards_demoted`.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 01 - the regular harness](../step_01_regular_harness/README.md): a
skill that trains the same way every run, and is not RSI. (This is the first
lesson; the [course page](../README.md) lists them all.)
