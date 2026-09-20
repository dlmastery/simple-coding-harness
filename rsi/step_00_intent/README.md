# Lesson 00 - Intent: what to improve, how, and what counts as success

Before any pack exists, a human writes down what should get better
(`intent.md`) and what evidence would prove it did (`acceptance.md`). The
framework paper (arXiv:2609.11873) calls this the precondition of every rung
of recursive self-improvement: the designer specifies the objective, the
procedure and the acceptance rule, and autonomy is later measured by which of
those decisions *move* to the system. Nothing in this series may widen the
intent - the budget, the metric, the allowed models and the locked-test rule
are checked against this file, by the `lint_pack` checklist every later pack
implements, for every pack a later lesson writes or generates. This is Stage 1
(Plan) of the playbook: the `intent.md` every writer and verifier reads. It is
also the first lesson that runs *inside a coding agent*, and the first thing
to notice about this series: there is no Python here at all. The skill under
`.claude/skills/intent/` states two checklists, and the agent performs them by
reading. In every later lesson the same pattern holds - the pack states a
contract, the agent builds the helper that implements it - which is why the
only `.py` file a lesson ships is its test.

## Getting started

Prerequisites: Python 3.10+ and `pip install -r requirements.txt` from the
repo root (scikit-learn, pandas, numpy, pyyaml - the agent's helpers use
them from lesson 01 on; the tests use pyyaml); a coding agent - Claude Code
2.1 or later on your PATH for the recorded transcript below, or any agent
that reads `SKILL.md` files. Nothing is on disk yet from a previous lesson;
this one adds the two intent files, the curriculum they belong to
(`../tasks/NN_<name>/intent.md`, one per problem, problem 7 the exam), the
bundled data (`../data/`) and the skill that checks them
(`.claude/skills/intent/`, mirrored byte-for-byte to `.agents/skills/intent/`
for this repo's harness).

Where the skill loads from, per agent:

- **Claude Code**: `cd rsi/step_00_intent && claude` - the pack under
  `.claude/skills/intent/` is discovered by name; `.claude/settings.json`
  installs the lesson's hook (a shell one-liner, below).
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

   The agent reads `.claude/skills/intent/SKILL.md`, then performs the two
   checklists of `tools.md` by reading `intent.md`, `acceptance.md`,
   `.claude/skills/intent/widened_pack.json` and the seven
   `../tasks/*/intent.md` files (its Read tool, or `cat` through Bash). It
   runs no helper and writes nothing: the test asserts the directory is
   byte-identical afterwards.

2. There is no approval in this lesson: the human *is* the author, and the
   skill changes nothing.

3. Headless, the way the transcript below was recorded (project settings
   only, so the lesson's own hook and skills are the whole session; your
   user-level MCP servers and plugins stay out of the transcript):

   ```bash
   claude -p "Use the intent skill in .claude/skills/intent: validate this lesson's intent and report." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi` from the repo root, or
   `python -m pytest -q test_step.py` here. `RSI_LIVE=1` adds the recorded
   run: the test runs the line above, keeps the stream under
   `runs/_recording/`, and asserts the directory did not change and the
   report names the budget, the freeze, the 14 fields and the seven problems.

## What it looks like

`intent.md` - the playbook's Stage 1 artifact: YAML front matter with the
machine-checkable facts, then prose. This file is byte-identical to
`../tasks/01_adult_income/intent.md`; every later pack reads that copy.

```markdown
---
name: adult_income
index: 1
title: "Adult Census Income (> 50k)"
role: curriculum
target: target
metric: roc_auc
budget_fits: 24
models: [logreg, rf, hgb]
data:
  kind: csv
  path: data/adult_sample.csv
test: locked, scored once after FREEZE
profile_keys: [n_rows, n_features, n_classes, imbalance, has_categorical]
---

# Intent: Adult Census Income (> 50k)

## What to improve
ROC-AUC of a classifier that predicts whether income is above 50K on the bundled 6,000-row Adult sample, under a budget of 24 fits per arm, searching the shared recipe space (model in logreg / rf / hgb, one hyper-parameter, scale, encode, class weight).

## Why
Mixed numeric and categorical columns and a class imbalance: the first lessons a pack can learn are encoding and class weight, and they are the first cards the verifier writes.

## What counts as success
A higher best validation score, or the same score reached with fewer wasted fits, than the control arm (`memory: off`) at the same budget of 24 fits and the same seed - and the locked test split scored exactly once, after FREEZE. A run that peeks at the test split proves nothing.

## What is off limits
The budget (24 fits per arm), the metric, the three models, the test rule and these profile keys: no pack, writer or meta pack may widen them, and `lint_pack` refuses one that tries. The private part of the split is the gate's; no actor arm reads it.

## The profile the verifier may condition on
`n_rows`, `n_features`, `n_classes`, `imbalance` (the share of the rarest class) and
`has_categorical` - five numbers about the table, nothing about the signal.
```

`acceptance.md` - the scorecard fields (the 14 every later arm reports) and
the pass rule, stated relatively: memory arm against `MEMORY_OFF` arm, same
helper, same seed, same budget. It says why the numbers are relative: the
agent that runs a lesson writes its own fit helper from the contract, so two
machines need not print the same validation score.

`.claude/skills/intent/SKILL.md` - the front matter names the skill and when
it triggers; the body is the procedure, each step a checklist to perform:

```markdown
---
name: intent
description: "Validate the intent of the rsi series - intent.md (what to improve, how, the budget, the locked-test rule; YAML front matter and prose) and acceptance.md (what counts as success) - by the checklists in tools.md, and show that a pack which widens the intent is refused. Use in rsi/step_00_intent before any pack exists."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# Intent: what to improve, how, and what counts as success

## Procedure
1. `validate_intent` on `intent.md` and `acceptance.md`: read both and go through every rule of the checklist in `tools.md`, noting each rule as it passes or fails. ...
2. `lint_pack` on `widened_pack.json` in this skill's directory - a regular pack, given as `{"<file>": "<text>"}`, whose schema raises `n_fits` to 48, scores the test twice and adds a model the intent does not allow. Name every rule of the checklist it breaks. It is refused before any human sees it.
3. The curriculum the intent belongs to: read `../tasks/*/intent.md` (seven directories) and `validate_intent` each one; ...

## Rules
- You change nothing and create nothing: no helper, no run directory, no card, no pack. The human is the author of the intent; you are its reader.
```

`.claude/skills/intent/tools.md` - the two checklists as contracts. In every
later lesson this file is "the helpers you build and their contracts"; here
the contracts are performed by reading:

```markdown
## Allowed

- `validate_intent(intent.md[, acceptance.md])` - a checklist you perform by reading, not a script: the front matter has `name`, `index`, `title`, `role` (`curriculum` | `exam` | `pool`), `target`, `metric` (`roc_auc` | `roc_auc_ovr_macro`), `budget_fits` equal to 24, `models` a subset of `[logreg, rf, hgb]`, `data.kind` in `csv` | `sklearn` | `synthetic`, the line `test: locked, scored once after FREEZE`, and the five `profile_keys`; ...
- `lint_pack(files, intent.md)` - every reason a pack may not run for a task, as a list of problems (empty = ok): `schema.json -> n_fits` differs from `budget_fits`; `test_rule` is not `locked, scored once after FREEZE`; `metric` or `models` differ from the intent's; ...

## Forbidden

- load_splits, fit_recipe, score_test, save_model - nothing is trained in this lesson
- write_card, propose, apply, gate, rollback - nothing is written or changed
```

`.claude/settings.json` - the lesson's hook, a shell one-liner (no script
file). Every Bash call the agent makes goes through it first; it blocks a
command containing `score_test` unless some `runs/**/state.json` says
`"frozen": true`, and a command containing `apply` unless a
`proposals/*.approved` file exists. In this lesson it has nothing to block,
but the shape is the same in every lesson. It needs a POSIX shell (Git Bash
on Windows, which Claude Code uses for its Bash tool); agents without hooks
get the helper-level refusal the contracts state.

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "IN=$(cat); if printf %s \"$IN\" | grep -q score_test && ! grep -rqs '\"frozen\": true' runs; then echo 'gate: the test split is locked until FREEZE - no runs/**/state.json says \"frozen\": true' >&2; exit 2; fi; if printf %s \"$IN\" | grep -Eq 'apply([^a-z_]|$)' && [ -z \"$(find runs -name '*.approved' 2>/dev/null)\" ]; then echo 'gate: apply needs proposals/<id>.approved holding the user'\"'\"'s exact words - show the proposal and ask first' >&2; exit 2; fi; exit 0"}]}
    ]
  }
}
```

`test_step.py` - the only Python in the lesson. Offline it checks the pack
contract and this lesson's claims; the widened pack's three broken rules are
computed the way the checklist says:

```python
def test_widened_pack_breaks_the_checklist():
    """The planted pack raises n_fits to 48, scores the test twice and adds xgb: three rules the lint checklist names."""
    files = json.loads((SKILLS / "intent" / "widened_pack.json").read_text(encoding="utf-8"))
    schema = json.loads(files["schema.json"])
    intent = front_matter((HERE / "intent.md").read_text(encoding="utf-8"))[0]
    problems = []
    if schema["n_fits"] != intent["budget_fits"]:
        problems.append(f"n_fits {schema['n_fits']} != budget_fits {intent['budget_fits']}")
    if schema["test_rule"] != "locked, scored once after FREEZE":
        problems.append("test_rule")
    if not set(schema["models"]) <= set(intent["models"]):
        problems.append("models")
    assert problems == ["n_fits 48 != budget_fits 24", "test_rule", "models"]
```

The recorded run (Claude Code 2.1.278, headless, from this directory; tool
results trimmed to their first lines):

```text
[Skill intent]
[Read .claude/skills/intent/tools.md]  [Read intent.md]  [Read acceptance.md]
[Read .claude/skills/intent/widened_pack.json]
agent> Now the seven curriculum intents.
$ for d in ../tasks/*/; do echo "=== $d"; cat "$d/intent.md"; echo; done
=== ../tasks/01_adult_income/
---
name: adult_income
index: 1
... (255 more lines)
agent> # Intent validation report - rsi/step_00_intent

Nothing was built, run or changed. Both checklists from tools.md were performed by reading.

## 1. validate_intent(intent.md, acceptance.md) - ok: true
| Rule | Value | Result |
| name | adult_income | pass |
| budget_fits = 24 | 24 | pass |
| models subset of [logreg, rf, hgb] | [logreg, rf, hgb] | pass |
| data.kind in csv/sklearn/synthetic | csv (data/adult_sample.csv) | pass |
| test: locked, scored once after FREEZE | exact | pass |
| five profile_keys | n_rows, n_features, n_classes, imbalance, has_categorical | pass |
Body headings: all five present, in order. Pass.
acceptance.md: ## The scorecard lists exactly 14 `- field` lines. Pass. The pass rule says
"once" and "FREEZE" - pass.

## 2. lint_pack(widened_pack.json, intent.md) - refused
1. schema.json -> n_fits is 48; budget_fits is 24.
2. schema.json -> test_rule is "scored twice: once after FREEZE and once more with the
   runner-up", not `locked, scored once after FREEZE`.
3. schema.json -> models is [logreg, rf, hgb, xgb] - xgb is not in the intent's models.
Rules that pass (so the refusal is precisely about widening): metric = roc_auc matches;
SKILL.md has the front matter and the four headings; tools.md has ## Allowed and
## Forbidden. Three hard failures -> the pack is refused before any human sees it.

## 3. The curriculum - ../tasks/*/intent.md, all seven ok: true
| 1 | adult_income  | roc_auc           | curriculum | csv       |
| 2 | breast_cancer | roc_auc           | curriculum | sklearn   |
| 3 | wine          | roc_auc_ovr_macro | curriculum | sklearn   |
| 4 | digits        | roc_auc_ovr_macro | curriculum | sklearn   |
| 5 | synth_shift_a | roc_auc           | curriculum | synthetic |
| 6 | synth_shift_b | roc_auc           | curriculum | synthetic |
| 7 | exam          | roc_auc           | exam       | synthetic |
Six curriculum, one exam. ../tasks/01_adult_income/intent.md is identical to this lesson's
intent.md.

## 4. Answers
- Budget: 24 fits per arm. Metric: ROC-AUC (roc_auc_ovr_macro on the two multiclass problems).
- Test rule: locked, scored once after FREEZE.
- 14 scorecard fields: problem, arm, seed, n_fits, fits_used, wasted_fits, best_val_score,
  best_recipe, test_score, test_scored_once, test_touched_before_freeze, cards_active,
  cards_added, cards_demoted.
- Widened pack refused because: n_fits 48 != 24; test_rule scores the test twice; models adds xgb.
- Seven problems in order: adult_income, breast_cancer, wine, digits, synth_shift_a,
  synth_shift_b, exam.
Done: both checklists ran on the intent and the widened pack was refused.
[8 turns, 51 s]
```

What to notice: no helper was built and no command but one `cat` loop was
run - the two "tools" are checklists, and the agent performed them by
reading; the widened pack was refused on the three rules the offline test
computes the same way; and the report is the checklist's verdicts, rule by
rule, not the agent's opinion of the intent. The live test asserts the
directory was byte-identical afterwards, and it was.

Files:

```text
step_00_intent/
├── README.md
├── intent.md                       what to improve, how, the budget, the test rule (= ../tasks/01_adult_income/intent.md)
├── acceptance.md                   the scorecard fields and the pass rule
├── test_step.py                    the only Python: the pack contract offline, the recorded run under RSI_LIVE=1
├── .claude/
│   ├── settings.json               the PreToolUse hook: one shell line
│   └── skills/intent/
│       ├── SKILL.md                the procedure, each step a checklist
│       ├── tools.md                the two checklists as contracts; the forbidden tools
│       └── widened_pack.json       a pack that raises the budget: refused
└── .agents/skills/intent/          the same three files, for this repo's harness
../tasks/NN_<name>/intent.md        the curriculum: seven intents, problem 7 the exam
../data/adult_sample.csv            the bundled table (and data/README.md: how it was made, no script)
```

## Governance considerations

- **Who approves what.** The human writes `intent.md` and `acceptance.md`;
  no agent proposes them and no agent may change them. Every later proposal
  (a generated pack in 03/05/08, a patch in 09-16) is linted against the
  intent - by the agent's own `lint_pack`, built from this contract - before
  a human sees it.
- **The hook.** `.claude/settings.json` runs the one-liner before every Bash
  call: no `score_test` command before a `state.json` says `"frozen": true`,
  no `apply` command without a `proposals/*.approved` file holding the user's
  words. In this lesson neither can occur; the hook is installed so that the
  shape is the same from the first page.
- **What the checklist refuses.** `lint_pack` refuses a `schema.json` whose
  `n_fits`, `test_rule`, `metric` or `models` differ from the intent's; the
  agent cannot talk itself into a wider budget without breaking a rule it
  wrote down. `validate_intent` refuses an intent outside the rules (a budget
  other than 24, a second test score, an unknown model) and an
  `acceptance.md` missing a scorecard field.
- **What is and is not self-modified.** Nothing. This lesson has no
  persistent state that changes; the live test asserts the directory is
  byte-identical after the skill ran.
- **Honesty of the numbers.** No helper exists yet, so no number is produced
  here; `acceptance.md` already states that every later number is compared
  arm against arm on one machine, never against a number printed elsewhere.

## How to measure it

| Claim | Test |
|---|---|
| the lesson's `intent.md` is the first curriculum problem, byte for byte | `test_intent_is_the_first_curriculum_problem` |
| the acceptance fields are exactly the 14 scorecard fields every later lesson reports, and the pass rule says once / FREEZE | `test_acceptance_fields_are_exactly_the_scorecard_fields` |
| a pack that raises the budget, scores twice or adds a model breaks three rules of the checklist | `test_widened_pack_breaks_the_checklist` |
| the seven curriculum problems are in index order, six curriculum + one exam, all at 24 fits with the locked test | `test_curriculum_in_order` |
| the procedure has no write step and names no helper | `test_skill_changes_nothing` |
| every intent file has the front matter fields and the five body headings | `test_intent_contract` |
| the pack contract: front matter, every named file exists, forbidden tools absent from the procedure, `.claude/skills == .agents/skills`, the hook line, no Python but the test | `test_front_matter`, `test_procedure_names_existing_files`, `test_forbidden_tools_absent_from_procedure`, `test_mirror_identical`, `test_hook_installed`, `test_no_python_shipped` |
| the recorded run reproduces: nothing changed, the report names 24, FREEZE, 48, the 14 fields and the seven problems (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields this lesson defines (reported from lesson 01 on): `problem`,
`arm`, `seed`, `n_fits`, `fits_used`, `wasted_fits`, `best_val_score`,
`best_recipe`, `test_score`, `test_scored_once`, `test_touched_before_freeze`,
`cards_active`, `cards_added`, `cards_demoted`.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 01 - the regular harness](../step_01_regular_harness/README.md): a
skill that trains the same way every run, with helpers the agent builds from
the contracts, and is not RSI. (This is the first lesson; the
[course page](../README.md) lists them all.)
