# Zero to Hero: Recursive Self-Improvement

## A hello world, skills only: make the agent's own files get better across runs, and prove it

**Status: complete, rebuilt to run inside a coding agent.** Eighteen lessons
(00-17), every one a skill pack you run by opening Claude Code (or this
repo's harness, Antigravity, Codex) in the lesson directory and typing the
prompt its README gives. There is no Python driver: the agent is the loop,
and Python survives only as the tool scripts under [`tools/`](tools/) that a
skill tells the agent to run through its shell, and as the pytest tests of
those scripts and of the pack contracts (`python run_tests.py rsi`, offline,
no key). Every lesson page carries a transcript recorded with `claude -p`
from that directory. The plan of record is [`OUTLINE.md`](OUTLINE.md) (v10,
19 Sep 2026). Layout and lesson format follow the Claude Academy *AI-native
SDLC playbook*: six stages, one lesson per step, the same seven headings on
every page.

The job is real software: a sequence of simple ML problems (Adult income,
breast cancer, wine, digits, two synthetic tables, and a held-out exam),
each under a 24-fit budget, solved in order so that what the harness learned
on problem 1 makes it better at problem 2, then 3 - until the pack is the
expert. The agent is configured only by skill files. The thing that improves
is the skill pack - memory cards, a search-policy line, a schema patch, the
harness text itself - behind a verifier that cannot see the actor's story, a
locked test that can be scored once, a human approval cycle, a private gate
and a rollback. Definitions and evidence standards are those of *The Last AI
Built by Humans: Toward Genuine Recursive Self-Improvement*
(arXiv:2609.11873). The model's weights are never touched.

**The headline, on this machine** (Claude Code 2.1.278 headless, seed 0;
lesson 07, 61 turns, 27 minutes): over the six curriculum problems the
memory arm's best validation score minus the control arm's at the same
budget was 0 / +0.0012 / 0 / 0 / +0.0024 / +0.0646, with the memory arm
reaching the static grid's answer in 20 fits over the curriculum where the
grid needed 33; on the exam problem the frozen pack beat the control arm on
4 of 5 seeds (mean test gap +0.0308), and the report named three cards that
did not transfer. Wine and digits are saturated for this recipe space and
teach nothing; the pages say so.

## What you'll learn

By the end of this course, you'll be able to:

- Say, in the framework paper's terms, what is and is not recursive
  self-improvement - B0 self-refinement, AutoML, a harness you engineered by
  hand, a harness a meta skill generated - and name the rung (L1-L5) each one
  stands on.
- Engineer a harness as files a coding agent runs: a loop with a counted
  budget and a freeze gate, a graph whose paths are recipes, and a meta
  skill that writes such a harness from an intent file under a human
  approval cycle.
- Add the first RSI file (memory cards behind a verifier contract) and prove
  it with a matched budget, one locked test score and a transfer table.
- Run an RSI meta harness that patches the harness one change per
  generation, under human approval and then under a private gate, with
  version history and rollback.
- Show the learning curve: experience from problem n helping on n+1 at a
  matched budget, and a held-out exam the pack never wrote to.
- Reproduce, on the same curriculum, what Dream-RSI, RSIAgent, ModularRSI,
  Recuris, the Darwin Gödel Machine, AIDE² and MetaSkill-Evolve each change -
  and point at the file.
- Put every rule a skill states behind a script that refuses and a hook
  that blocks: the playbook's "advisory skill + deterministic gate" split.

## Who this course is for

Engineers who build agents with skills and want to know what "the agent
improves itself" means in files, tests and approvals, not slogans. It is a
hello world on purpose: no OSWorld, no GPUs, no weight updates.

## Prerequisites

Python 3.10+, `pip install -r requirements.txt` from the repo root
(scikit-learn, pandas, numpy, pyyaml, jsonschema); a coding agent - Claude
Code 2.1+ for the recorded transcripts, or any agent that reads `SKILL.md`
files and has a shell. The root codelab's stages 4 (skills), 15 (`execute()`
as the one door), 27 (hooks), 30 (evals) and 35 (approval prompts) are the
ideas reused here. Tests need no key and no agent.

Estimated time: about an hour of reading; a lesson's run takes from two
minutes (00-05) to half an hour (a whole curriculum, 07 and 09-16) in
Claude Code.

## How to navigate

**Which agent, where the skills load from.** Every lesson directory holds
`.claude/skills/<pack>/` (Claude Code discovers them when opened there) and
the byte-identical `.agents/skills/<pack>/` (this repo's harness, root
codelab stage 4; a test asserts the two are equal), plus
`.claude/settings.json` with the lesson's PreToolUse hook.

- **Claude Code**: `cd rsi/step_NN_... && claude`, then type the prompt from
  the lesson's "How to execute it". Headless, as every transcript was
  recorded: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`;
  a lesson with an approval is two turns, `claude -p --continue "<your answer>"`.
- **This repo's harness**: run it with the lesson directory as cwd; it
  loads `.agents/skills/`; approvals arrive through `ask_user`.
- **Antigravity** (root step 18): `skills_paths=[".agents/skills"]` with the
  lesson directory as cwd.
- **Codex**: copy or symlink the lesson's `.agents/skills/*` into
  `~/.codex/skills/`.

Skills tell the agent to run every command through its Bash tool, from the
lesson directory (on Windows that is Git Bash; the PowerShell tool bypasses
the hook and reads `@file` as a splat operator - if you run the scripts by
hand in PowerShell, quote it: `'@file'`).

**Two orders.** The steps are numbered in build order: each one copies the
packs of the one before and changes one idea, so `diff -r` between two step
directories is the lesson. The course page groups the same steps by SDLC
stage, which is the reading order: Plan (00), Design (01, 02, 04), Build
(03, 05, 06, 08), Test (07), Deploy (09), Maintain (10-17).

**Where the runtime lives.** Nothing in a step directory is a loop. A step
is packs under `.claude/skills/`, a `test_step.py` and a README. The
mechanics are built once:

```text
tools/                       one script per tool; JSON in (on the line, k=v pairs, or @file), one JSON object out, exit 0 even on a refusal
  load_splits.py             open an arm: the profile, the budget, the applicable cards; runs/<pack>/<task>/state.json
  fit_recipe.py              fits, counted; refuses the 25th, a recipe outside the schema, a forbid card's recipe; flags a suspicious score
  score_test.py              the locked test: once, after FREEZE            save_model.py, freeze.py, write_loop_log.py, walk_path.py
  read_memory.py             the cards, which apply, the preferred values; --order <policy> = the next eight recipes of a named policy
  write_card.py              the verifier's pen: typed cards, merged, demoted   read_traces.py: rows {recipe, val_score, error} + profile, --tally
  lint_pack.py               every reason a pack may not run for a task      propose.py / apply.py: the human approval cycle on disk
  read_pack.py, patch_pack.py, private_score.py, rollback.py     the meta harness: one patch per visit; human, gate, both, metered
  rank_policies.py (10)  write_plan.py (11)  contrast.py (12)  skill_memory.py (13)  archive.py (14)  meter.py (15)
  scorecard.py, curve.py, exam.py, validate_intent.py, map.py
  _lib/                      shared code: data, synth, tasks, recipe, memory, packs, graph, policies, scorecard, trace, state, proposals, render, testing
hooks/gate.py                the Claude Code PreToolUse hook every lesson installs: blocks score_test.py before FREEZE or twice, and apply.py / patch_pack.py --proposal without --approved "<the user's words>"
tasks/                       the curriculum: one task.json per problem, in order, plus the exam
data/                        the bundled Adult sample (6k rows) and how it was made
```

State lives on disk: `<lesson>/runs/<pack>/<task>/state.json` (one entry per
arm and seed: fits used, frozen, test scored) and `traces.jsonl` (append-only)
next to it; `runs/<pack>/versions/gen_NNN/` for snapshots; the pack itself
for what learned (`memory.json`, `roles/`, `operators.md`). `runs/` is
git-ignored; a lesson that changes its pack says how to reset it.

**Running things.** From the repo root:

```bash
python run_tests.py rsi                     # every lesson's tests (offline, the scripts as gates, the tests as the agent)
python run_tests.py rsi/step_06             # one lesson
python check_snippets.py rsi                # every python snippet on every lesson page exists in the code
RSI_LIVE=1 python run_tests.py rsi/step_01  # adds the claude -p smoke test of that lesson
```

## Lessons

```text
rsi/
  OUTLINE.md                          the plan: definitions, format, steps, tests, tutorial validation
  tools/, hooks/, tasks/, data/       the runtime (above)
  Stage 1: Plan
  step_00_intent/                     task.json + acceptance.md; the intent skill validates them and shows a widened pack refused
  Stage 2: Design
  step_01_regular_harness/            a repeatable trainer: same SKILL.md every run, 24 fits, one test score - not RSI
  step_02_loop_harness/               loop engineering: loop.json, a counted while with a freeze; an audit log nothing reads
  step_04_graph_harness/              graph engineering with loops: graph.json + paths.json; an illegal path is skipped and counted
  Stage 3: Build
  step_03_meta_generates_loop/        a meta skill writes the loop pack; the human approves, edits or rejects; twice gives the same
  step_05_meta_generates_graph/       a meta skill writes the graph pack; lint kills cycles first; an edit changes a binding
  step_06_rsi_harness/                memory cards behind a verifier contract; MEMORY_OFF reproduces lesson 01 exactly
  step_08_meta_generates_rsi/         a meta skill writes actor + verifier; the human approves the contract first
  Stage 4: Test
  step_07_proof/                      one test score per problem, the learning curve over problems 1-6, the exam over 5 seeds
  Stage 5: Deploy
  step_09_rsi_meta_harness/           actor -> verifier -> meta across the curriculum; approval: human | gate; versions + rollback
  Stage 6: Maintain
  step_10_rsi_dream/                  Dream-RSI: rank search policies on the trace log at zero fits; the log is silent elsewhere
  step_11_rsi_agent/                  RSIAgent: planner / actor / verifier, broad then deep, memory frozen before the test
  step_12_rsi_modular/                ModularRSI: five module files, contrast on a benchmark-disjoint pool, one module patched
  step_13_rsi_skill_memory/           Recuris: memory as a skill package + working memory; one validated card update per problem
  step_14_rsi_self_modifying/         DGM lineage: rewrites of SKILL.md / loop.json from an archive of variants scored held-out
  step_15_rsi_aide2/                  AIDE2: a tree-search inner agent; the outer loop keeps a rewrite only if better on the set
  step_16_rsi_meta_skills/            MetaSkill-Evolve: task skills every problem, the meta pack's own role files every k, with a human
  step_17_map/                        the ladder, every recorded curve side by side, who approved what, the terms, the reported numbers
```

## The numbers, side by side

From [lesson 17](step_17_map/README.md), read from each lesson's recorded
run on the real curriculum (memory arm minus control arm, best validation
score, per problem; `wasted m/c` is the fits the memory / control arm spent
before reaching the static grid's answer, summed over the curriculum):

```text
  lesson               adult_income  breast_cancer           wine         digits  synth_shift_a  synth_shift_b  wasted m/c
  07 proof                  +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
  09 meta (gate)            +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
  10 Dream-RSI              +0.0000        +0.0012        +0.0000        +0.0005        +0.0024        +0.0646       34/33
  11 RSIAgent               +0.0000        +0.0000        +0.0000        +0.0000        +0.0000        -0.0270       27/33
  13 Recuris                +0.0000        +0.0000        +0.0000        +0.0000        +0.0024        +0.0646        6/33
  16 MetaSkill              +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
```

Three methods are reported on their own pages instead: ModularRSI patched
one module and the loser's pool score went 0.8847 -> the winner's 0.8945
path (gate 0.8737 -> 0.879); the DGM lineage's first generation scored
0.0 held-out by construction and its rewrite was kept on a tie; AIDE²'s
operator rewrite was kept on a total gain of +0.0005 from one problem.
Exam wins, memory vs control over five seeds: 07 4/5 (+0.0308), 09 4/5
(+0.0308), 10 4/5 (+0.0282), 11 4/5 (+0.0006), 13 4/5 (+0.0306).

Every number quoted from a paper anywhere in the series is marked
*reported*.

## How the series is built

- A lesson is a skill pack the agent runs; the scripts under `tools/` are
  the gates (the budget, the freeze, the forbid cards, the schema, the
  verifier contract, the approval word, the size cap, the `patches:` globs,
  `tools.md`'s Allowed list), and `hooks/gate.py` blocks the two calls a
  skill may never make before they run.
- Every "generate" and every "improve" goes through the approval cycle:
  `propose.py` (or `patch_pack.py`) writes the proposal and its diff, the
  agent shows it and asks, and only `apply.py --approved "<the user's exact
  words>"` lands it; the trace records who approved. `approval: gate`
  replaces the human by the private split; `both` puts the human after the
  gate; `metered` (lesson 15) decides after a whole curriculum ran.
- The tests play the agent with the same commands the skill names; where
  the agent's choice matters, they follow the policy text of the skill
  (`_lib/policies.py`). The `RSI_LIVE=1` test runs the lesson's prompt
  through `claude -p`.

## How to read a lesson

Every lesson section below has the same shape; every lesson README has the
seven playbook headings (concept, Getting started, How to execute it, What
it looks like, Governance considerations, How to measure it, Next lesson)
and says more than this page does.

- **The idea.** One sentence.
- **Rung.** Where the lesson stands on the paper's ladder, and what stays
  human.
- **Files.** The tree of what this lesson adds, one line per file.
- **Build.** The pack files and the scripts, quoted verbatim with the file
  named above each and the explanation under it.
- **Run.** The prompt to type, the commands the agent then runs, and what
  you will be asked at an approval.
- **See.** The transcript recorded with `claude -p` on this machine, and
  what to notice in it - including where the method did not pay.
- **What the test proves.** One line per claim, with the test's name.
- **Governance.** Who approves what, the hook, what the script refuses, what
  is and is not self-modified.
- **Diff from the previous lesson.**

---

## Lesson 00: Intent: what to improve, how, and what counts as success

**The idea.** Before any pack exists, a human writes down what should get better
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

**Rung.** The L1 precondition. Everything is human.

**Files.**

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

**Build.**

`step_00_intent/.claude/skills/intent/SKILL.md` - the front matter names the skill and when
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

`step_00_intent/.claude/skills/intent/tools.md` - what the skill may and may not run. The
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

`step_00_intent/.claude/settings.json` - the lesson's hook. Every Bash call the agent makes
goes through `hooks/gate.py` first; in this lesson it has nothing to block,
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

`tools/validate_intent.py` - the script behind step 1. Like every tool
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

`tools/_lib/packs.py` - the part of `lint_pack` that refuses a pack that
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

**Run.** Open your agent in `step_00_intent/` and type:

```text
Use the intent skill in .claude/skills/intent: validate this lesson's intent and report.
```

The commands the agent runs:

```bash
python ../tools/validate_intent.py --task task.json --acceptance acceptance.md
python ../tools/lint_pack.py --files @.claude/skills/intent/widened_pack.json --task task.json
ls ../tasks && for f in ../tasks/*; do python ../tools/validate_intent.py --task "$f"; done
```

**See.** The recorded run (Claude Code 2.1.278, headless, from this directory; tool
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

**What the test proves.**

- `task.json` and `acceptance.md` validate against the schema (`test_intent_validates`).
- the acceptance fields are exactly the 14 scorecard fields every later lesson reports (`test_acceptance_fields_are_exactly_the_scorecard_fields`).
- a pack that raises the budget or touches the test rule is refused by `lint_pack` (`test_widened_pack_is_refused`).
- a bad task is a JSON result, not a crash (`test_a_bad_task_is_a_result_not_a_crash`).
- the seven curriculum problems validate, in order, six curriculum + one exam (`test_curriculum_validates_in_order`).
- the CLI contract: JSON on stdout, exit 0 (`test_cli_contract_json_out_exit_zero`).
- the pack contract: front matter, every named script exists, forbidden tools absent from the procedure, `.claude/skills == .agents/skills`, the hook installed (`test_pack_contract`).
- the skill changes nothing on disk (`test_skill_changes_nothing`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The human writes `task.json` and `acceptance.md`;
  no agent proposes them and no agent may change them. Every later
  proposal (a generated pack in 03/05/08, a patch in 09-16) is linted
  against this task before a human sees it.
- **The hook.** `step_00_intent/.claude/settings.json` runs `hooks/gate.py` before every
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

**Diff from the previous lesson.** The first one.

---

## Lesson 01: The regular harness: a repeatable trainer, and not RSI

**The idea.** A skill that trains a classifier the same way every run: the agent opens
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

**Rung.** Not RSI (B0 / AutoML). Everything is human.

**Files.**

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

**Build.**

`step_01_regular_harness/.claude/skills/adult-income-regular/SKILL.md` - the front matter names the
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

`step_01_regular_harness/.claude/skills/adult-income-regular/schema.json` - the task, the budget and
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

`tools/_lib/state.py` - the budget, FREEZE and the locked test are
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

`tools/fit_recipe.py` - a recipe outside the schema, a model the task
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

`hooks/gate.py` - the same rule, enforced before the script runs, for an
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

**Run.** Open your agent in `step_01_regular_harness/` and type:

```text
Use the adult-income-regular skill: train the Adult income classifier and report the scorecard.
```

The commands the agent runs:

```bash
python ../tools/load_splits.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json
python ../tools/fit_recipe.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-regular/schema.json
python ../tools/score_test.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/save_model.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/scorecard.py --pack .claude/skills/adult-income-regular --task ../tasks/01_adult_income.json
```

**See.** The recorded run (Claude Code 2.1.278, headless, from this directory; the
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

**What the test proves.**

- the static walk makes 24 fits in schema order, the baseline first, and one test score, and the scorecard has exactly lesson 00's fields (`test_static_walk_24_fits_in_schema_order_one_test_score`).
- the 25th fit and the second score are refusals (JSON results), and `state.json` says so (`test_25th_fit_and_second_score_are_refusals`).
- `score_test` before FREEZE is refused by the script and blocked by the hook (exit 2) (`test_score_test_before_freeze_is_refused_by_script_and_hook`).
- an unknown value, malformed JSON, an extra field or a disallowed script is a result, and no fit is spent (`test_bad_calls_are_results_not_crashes`).
- the trace is append-only and the same pack twice gives the same log (`test_trace_is_append_only_and_deterministic`).
- the CLI contract (subprocess, JSON out, exit 0) (`test_cli_contract`).
- the pack contract (front matter, scripts exist, forbidden absent, mirror identical, hook installed) (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** Nobody: the pack changes nothing, so there is
  nothing to approve. The human wrote the pack; the agent executes it.
- **The hook.** `hooks/gate.py` blocks `score_test.py` while
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

**Diff from 00.** A pack that fits; the budget, the locked test and the
trace as files under `runs/`.

---

## Lesson 02: Loop engineering: the loop is a file

**The idea.** The same trainer as lesson 01, with its loop written down: `loop.json` names
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

**Rung.** Harness engineering, not RSI.

**Files.**

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

**Build.**

`step_02_loop_harness/.claude/skills/adult-income-loop/loop.json` - the loop as data. Everything
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

`step_02_loop_harness/.claude/skills/adult-income-loop/SKILL.md` - the procedure says "run
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

`tools/write_loop_log.py` - the whole script. Note what is absent: a read
path. No tool in `tools/` opens `loop_log.jsonl` (the test greps for it):

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

`tools/_lib/packs.py` - what `lint_pack` holds a loop file to, so a
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

**Run.** Open your agent in `step_02_loop_harness/` and type:

```text
Use the adult-income-loop skill: run the loop in loop.json on the Adult income problem and report the scorecard.
```

The commands the agent runs:

```bash
python ../tools/load_splits.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
python ../tools/fit_recipe.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-loop/recipes.json --range 0:6
python ../tools/write_loop_log.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --entries '[{"t": 0, "recipe": {...}, "val_score": 0.9114}, ...]'
# ... --range 6:12, 12:18, 18:24, each followed by its log call ...
python ../tools/score_test.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/save_model.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/scorecard.py --pack .claude/skills/adult-income-loop --task ../tasks/01_adult_income.json
```

**See.** The recorded run (Claude Code 2.1.278, headless, from this directory; the
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

**What the test proves.**

- `loop.json` is honoured: 24 fits in `recipes.json` order, `t` 0..23, one test score; the 25th fit and the second score refused (`test_loop_json_is_honoured`).
- `score_test` before FREEZE is refused with the fits remaining (`test_score_test_before_freeze_refused`).
- the audit log holds 24 lines and no script reads it back (`test_audit_log_written_never_read`).
- the pack is byte-identical after a run (`test_pack_is_byte_identical_after_a_run`).
- `lint_pack` refuses a loop with `N` 48 or an exit that scores before FREEZE (`test_lint_refuses_a_changed_loop`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

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

**Diff from 01.** `loop.json`, `recipes.json`, one write-only script.

---

## Lesson 03: A meta skill generates the loop harness, under human approval

**The idea.** The first "agent builds agent": a writer skill that never fits a model
reads `task.json`, renders lesson 02's pack from a template (five files), lints
it against the task, and proposes it. The human sees every file and answers
approve / edit / reject; `n` means nothing lands, `edit` means the human's
version lands, and the trace records who approved and with which words. It
is one shot from a spec - the same `task.json` gives the same proposal, and
running the generated pack never changes it - so this is where most "agent
builds agent" demos stop: L1 in the framework paper's terms (humans specify
what, how and success; the system executes a generation procedure; the human
accepts). Not RSI yet: nothing the generated pack learns comes back to the
writer.

**Rung.** L1. The spec and the acceptance are human.

**Files.**

```text
step_03_meta_generates_loop/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/loop-writer/
│   ├── SKILL.md, tools.md
│   ├── task.json                   the spec (a copy of ../tasks/01_adult_income.json)
│   └── template/                   SKILL.md, tools.md, schema.json, loop.json, recipes.json with {{placeholders}}
├── .agents/skills/loop-writer/     the same files
├── .claude/skills/adult-income-loop/   (after approval: the generated pack)
└── runs/loop-writer/
    ├── rendered/                   the agent's rendering (scratch)
    └── adult_income/
        ├── proposals/p1.json, p1.diff
        └── traces.jsonl            propose, then apply {by: human, words: "approve"}
```

**Build.**

`step_03_meta_generates_loop/.claude/skills/loop-writer/SKILL.md` - the writer's procedure. Step 5 is the
approval question; step 6 lands "exactly what was decided":

```markdown
---
name: loop-writer
description: Write a loop harness pack (SKILL.md, tools.md, schema.json, loop.json, recipes.json) for the task in task.json and propose it for human approval; nothing lands until the user answers. Use in rsi/step_03_meta_generates_loop when a task.json exists and no loop pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Loop writer: a meta skill whose output is a loop harness

## Procedure
1. Read `W/task.json`. Everything you write derives from it; nothing you write may widen it.
2. Render the five template files into a scratch directory, `runs/loop-writer/rendered/` (create it; use your Write tool), replacing each `{{placeholder}}` from the task and nothing else:
3. Lint what you rendered, and fix it until `ok` is true; propose nothing that does not lint:
   `python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task W/task.json`
4. Propose it. The script lints again, writes the proposal under `runs/loop-writer/<task>/proposals/` and returns its id and the text the user must see:
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for <name>: 24 static recipes, counted loop"`
5. Show the user every file of the proposal (the `diff` field), then ask, in your own words but with these three options: **approve / edit / reject**. Wait for the answer. Do not run anything until it arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
```

`step_03_meta_generates_loop/.claude/skills/loop-writer/template/loop.json` - a template is the target
file with `{{placeholders}}`; the writer may fill them and nothing else:

```json
{
 "kind": "counted_while",
 "N": {{n_fits}},
 "counter": "t",
 "error_still_counts": true,
 "body": [
  "recipe = recipes[t]",
  "fit_recipe.py --recipe recipe  (or --recipes @recipes.json --range t:t+6)",
  "write_loop_log.py {t, recipe, val_score}"
 ],
 "exit": ["FREEZE", "score_test", "save_model", "scorecard"]
}
```

`tools/_lib/proposals.py` - the user's words decide, by their first word,
and anything unclear is a no:

```python
YES = ("y", "yes", "approve", "approved", "ok", "okay", "lgtm", "go", "ship", "accept", "accepted", "apply", "land", "sure")
NO = ("n", "no", "reject", "rejected", "nope", "deny", "denied", "stop", "cancel", "decline")
EDIT = ("edit", "edited", "change", "modify")


def classify(words):
    """The user's words -> y / n / edit, by the first word. Anything unclear is a no: nothing lands by default."""
    first = re.sub(r"[^a-z]", "", (words or "").strip().lower().split(" ")[0]) if words and words.strip() else ""
    if first in EDIT:
        return "edit"
    if first in YES:
        return "y"
    if first in NO:
        return "n"
    return "n"
```

`tools/apply.py` - refuses without the words, records a rejection, lints
an edited pack before it lands, applies at most once:

```python
    if a.approved is None or not a.approved.strip():
        raise ValueError('apply needs --approved "<the user\'s exact words>": ask them first; nothing lands without an answer')
    path, record = proposals.load(run.root, a.proposal)
    if record["applied"]:
        raise ValueError(f"proposal {a.proposal} was applied already")
    if record["decision"] == "n":
        raise ValueError(f"proposal {a.proposal} was rejected already; propose again if you have something new")
    decision = proposals.classify(a.approved)
    record["decision"], record["words"], record["approved_by"] = decision, a.approved, "human"
```

`tools/propose.py` - a pack that does not lint is refused before the user
ever sees it:

```python
    if a.kind == "pack":
        if not isinstance(payload, dict) or not all(isinstance(v, str) for v in payload.values()):
            raise ValueError("a pack payload is {path: text}")
        problems = lint_payload(payload, run.task)
        if problems:
            raise ValueError(f"lint_pack refuses this pack before the user sees it: {problems}")
```

**Run.** Open your agent in `step_03_meta_generates_loop/` and type:

```text
Use the loop-writer skill: generate the loop pack for the task in .claude/skills/loop-writer/task.json and propose it to me.
```

The commands the agent runs:

```bash
python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task .claude/skills/loop-writer/task.json
python ../tools/propose.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --target .claude/skills/adult-income-loop --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for adult_income: 24 static recipes, counted loop"
```

**See.** The recorded run (Claude Code 2.1.278, headless, two turns; the agent's
rendering of the five files omitted - it is lesson 02's pack with
`adult_income` filled in):

```text
[Skill loop-writer]
agent> Using the loop-writer skill. Boot order: tools.md, task.json, templates.
[Read .claude/skills/loop-writer/task.json]  [Read template/SKILL.md] [Read template/loop.json] ...
agent> Now rendering the five files. The 24 recipes: models in allowed_models order at their
middle hyper, then scale yes/no, encode onehot/ordinal, class_weight none/balanced.
[Write runs/loop-writer/rendered/SKILL.md] [Write runs/loop-writer/rendered/loop.json]
[Write runs/loop-writer/rendered/recipes.json] [Write runs/loop-writer/rendered/schema.json]
[Write runs/loop-writer/rendered/tools.md]
$ python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task .claude/skills/loop-writer/task.json
{"ok": true, "problems": [], "pack": "runs/loop-writer/rendered", "task": "adult_income"}
agent> Lint is clean. Proposing.
$ python ../tools/propose.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --target .claude/skills/adult-income-loop --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for adult_income: 24 static recipes, counted loop"
{"id": "p1", "kind": "pack", "target": ".claude/skills/adult-income-loop", "diff": "### SKILL.md\n---\nname: adult-income-loop ...",
 "next": "Show the diff to the user. Ask: approve / edit / reject. Then: python ../tools/apply.py ... --approved \"<the user's exact words>\""}
agent> Proposal p1 is written (lint: ok: true, 0 problems) - loop pack for adult_income: 24 static
recipes, counted loop - targeting .claude/skills/adult-income-loop. Nothing has landed yet.
Here are all five files of the proposal:
### SKILL.md  (name: adult-income-loop ... `t` reached `N` (24) ...)
### loop.json ("N": 24 ...)   ### recipes.json (24 recipes)   ### schema.json   ### tools.md
Every value comes from task.json (name, title, metric roc_auc, budget 24, models logreg/rf/hgb,
test rule 1 score after FREEZE); the templates were filled and nothing was added.
How do you want to proceed with proposal p1?
- approve - I land it as-is at .claude/skills/adult-income-loop
- edit - tell me what to change; I write your version and land that
- reject - nothing lands, the rejection is recorded
I'll wait for your answer before running anything.
[20 turns, 124 s]
=== user> approve
$ python ../tools/apply.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --proposal p1 --approved "approve"
{"id": "p1", "decision": "y", "landed": true, "target": ".claude/skills/adult-income-loop", "version": null,
 "files": ["SKILL.md", "loop.json", "recipes.json", "schema.json", "tools.md"], "approved_by": "human", "words": "approve"}
agent> Proposal p1 - decision: approved (your words: "approve") - landed.
What landed at .claude/skills/adult-income-loop/: SKILL.md, loop.json, recipes.json, schema.json, tools.md.
```

What to notice: the agent stopped and waited - in headless mode the answer
came as a second `claude -p --continue "approve"` turn, and `apply.py`
carries those words into the trace (`"by": "human", "words": "approve"`).
The landed pack equals the reference rendering file for file except that
the agent's `recipes.json` is formatted one recipe per line where the
reference indents it - same 24 recipes, same order; `lint_pack` checks the
content, and the test's "same task twice, byte-identical" claim is about
the script's determinism given the same payload.

**What the test proves.**

- the writer cannot fit or score (its `tools.md` does not allow it; the scripts refuse) (`test_writer_cannot_fit`).
- the rendered pack lints; the proposal shows every file before anything lands (`test_rendered_pack_lints_and_the_proposal_is_shown_before_anything_lands`).
- "no" leaves the disk untouched, and the proposal cannot be revived (`test_no_leaves_the_disk_untouched`).
- "yes" lands exactly the proposal, once, with the human's words in the trace (`test_yes_lands_exactly_the_proposal`).
- "edit" lands the human's text; an edit that widens the budget does not lint and does not land (`test_edit_lands_the_humans_text`).
- the same task twice gives byte-identical proposals (`test_same_task_twice_gives_byte_identical_proposals`).
- the generated pack passes lesson 02's checks and is unchanged by its run; nothing comes back to the writer (`test_generated_pack_runs_like_lesson_02_and_is_unchanged_by_its_run`).
- `apply` without the words is refused by the script and blocked by the hook (`test_apply_without_words_is_refused_and_blocked`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The human approves the whole pack, file by file,
  before it exists on disk; `edit` lands the human's text, not the model's.
  The writer decides nothing about the task: every value in the pack comes
  from `task.json`, and `lint_pack` refuses a pack that widens it.
- **The hook.** Blocks `apply.py` without `--approved "<words>"` (exit 2,
  "show the proposal and ask first").
- **What the script refuses.** `fit_recipe.py` / `score_test.py` for the
  writer (`not in loop-writer's tools.md`); a proposal that does not lint;
  `apply.py` without words, twice, or after a rejection; an edited pack that
  does not lint.
- **What is and is not self-modified.** Nothing modifies itself. The writer
  writes a *different* pack, once, and never sees its runs; the generated
  pack changes no file when it runs (asserted). Autonomy attribution: the
  system executed a generation procedure the human specified; the human
  accepted. That is L1.

**Diff from 02.** A pack that writes a pack; the approval cycle.

---

## Lesson 04: Graph engineering with loops: the job is a DAG, a recipe is a path

**The idea.** The trainer's job written as a graph: `graph.json` names the legal
operators as nodes (`load`, `scale`, `encode`, `model`, `fit`, `score_test`),
the hard dependencies as edges, and the constraints (one `scale`, one
`encode`, one `model` per path; no cycles; `score_test` a sink behind
`gate: freeze_only`). A recipe is a path with bindings; `paths.json` lists
the baseline and 23 more; the counted loop of lesson 02 now iterates over
paths and `walk_path.py` fits what a path binds. An illegal path - a missing
edge, a second model, a path that reaches the sink - is skipped and still
counts as a fit; a path id that is not in the file is refused. Both graph
files are `mutable: false`. Still not RSI: the graph is the human's, the walk
is fixed, and nothing about the walk changes the next one. What this lesson
adds is a *structure a later writer can generate and a human can read as
nodes and edges* (lesson 05).

**Rung.** Harness engineering, not RSI.

**Files.**

```text
step_04_graph_harness/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-graph/
│   ├── SKILL.md, tools.md, schema.json
│   ├── graph.json                 nodes, edges, constraints; mutable: false
│   ├── paths.json                 p00 (baseline) .. p23 with bindings; mutable: false
│   └── loop.json                  counted while over paths
├── .agents/skills/adult-income-graph/
└── runs/adult-income-graph/adult_income/   (after a run)
```

**Build.**

`step_04_graph_harness/.claude/skills/adult-income-graph/graph.json` - nodes, edges, constraints,
immutable:

```json
{
 "mutable": false,
 "nodes": {
  "load": {"op": "load_splits"},
  "scale": {"op": "scale", "values": ["yes", "no"]},
  "encode": {"op": "encode", "values": ["onehot", "ordinal"]},
  "model": {"op": "model", "values": ["logreg", "rf", "hgb"], "binds": ["hyper", "class_weight"]},
  "fit": {"op": "fit_recipe"},
  "score_test": {"op": "score_test", "gate": "freeze_only", "sink": true}
 },
 "edges": [["load", "scale"], ["scale", "encode"], ["encode", "model"], ["model", "fit"], ["fit", "score_test"]],
 "constraints": {"one_of": ["scale", "encode", "model"], "no_cycles": true, "sink_after_freeze": "score_test"}
}
```

`step_04_graph_harness/.claude/skills/adult-income-graph/SKILL.md` - the loop over paths:

```markdown
---
name: adult-income-graph
description: Train a classifier for the Adult income problem by walking the paths of graph.json in the order of paths.json, one counted loop over paths. Use in rsi/step_04_graph_harness, when the pack has graph.json and paths.json and no memory file.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Graph harness: the job is a DAG, a recipe is a path, the loop walks paths

## Procedure
Run `loop.json` exactly as written:
1. `python ../tools/load_splits.py --pack P --task T` once.
2. `counted_while` with counter `t` from 0 to `N` - 1 (`N` is 24): walk `paths[t]` by its id. Walk six paths per command, in `paths.json` order, four commands in all:
   `python ../tools/walk_path.py --pack P --task T --paths p00,p01,p02,p03,p04,p05`
   then `p06..p11`, `p12..p17`, `p18..p23`. The script checks each path against the graph: a legal path fits the recipe its bindings form; an illegal one (a missing edge, two model nodes, a path that reaches `score_test`) is skipped and still counts as a fit, with the reason in its `error`. A path id that is not in `paths.json` is refused. You never repair a path and never invent one.

## Rules
- Paths in the order of `paths.json`, each once. Never run `fit_recipe.py`: a recipe reaches the fitter only as a path of the graph, and `fit_recipe` is not in your `tools.md`.
- `graph.json` and `paths.json` are `mutable: false`: you do not edit them, add a path or remove an edge.
```

`tools/_lib/graph.py` - what makes a path illegal, in the order the
script checks:

```python
def why_illegal(graph, path):
    """The first rule this path breaks, or None when it is legal."""
    nodes, edges = graph["nodes"], [tuple(e) for e in graph["edges"]]
    seq = path.get("nodes", [])
    if not seq or any(n not in nodes for n in seq):
        return "names a node that is not in the graph"
    for a, b in zip(seq, seq[1:]):
        if (a, b) not in edges:
            return f"edge {a} -> {b} is not in the graph"
    for n in ONE_OF:
        if seq.count(n) != 1:
            return f"visits {n} {seq.count(n)} times; a path visits it once"
    if any(nodes[n].get("gate") == "freeze_only" for n in seq):
        return "reaches score_test, a sink that opens only after FREEZE"
    if path_recipe(path) is None:
        return "bindings are not a recipe"
    return None
```

`tools/walk_path.py` - skip and count, never invent:

```python
    for pid in ids:
        if pid not in paths:
            results.append({"path": pid, "error": f"no path {pid!r} in paths.json; the loop walks the paths it has, it does not invent one", "refused": True})
            continue
        reason = graph.why_illegal(g, paths[pid])
        try:
            if reason:
                results.append({"path": pid, **fit_one(run, graph.path_recipe(paths[pid]) or paths[pid].get("bindings"), error=f"illegal path: {reason}")})
            else:
                results.append({"path": pid, **fit_one(run, graph.path_recipe(paths[pid]))})
```

**Run.** Open your agent in `step_04_graph_harness/` and type:

```text
Use the adult-income-graph skill: walk the graph's paths on the Adult income problem and report the scorecard.
```

The commands the agent runs:

```bash
python ../tools/load_splits.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p00,p01,p02,p03,p04,p05
python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p06,p07,p08,p09,p10,p11
python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p12,p13,p14,p15,p16,p17
python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p18,p19,p20,p21,p22,p23
python ../tools/score_test.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/save_model.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/scorecard.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
```

**See.** The recorded run (Claude Code 2.1.278, headless; the agent read the six pack
files first; results trimmed):

```text
[Skill adult-income-graph]
agent> Boot complete. Now step 1: load the splits.
$ python ../tools/load_splits.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
{"pack": "adult-income-graph", "problem": "adult_income", "n_fits": 24, "fits_used": 0, ...}
agent> Splits loaded (24 fits budget, 0 used). Now the counted while: four commands of six
paths each, in paths.json order.
$ python ../tools/walk_path.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json --paths p00,p01,p02,p03,p04,p05
{"results": [{"path": "p00", "n": 1, "recipe": {"model": "logreg", ...}, "val_score": 0.9114, "error": null, "fits_left": 23}, ...
             {"path": "p05", "n": 6, ... "val_score": 0.9074, "error": null, "fits_left": 18}], "fits_used": 6, "n_fits": 24, "fits_left": 18}
$ python ../tools/walk_path.py ... --paths p06,p07,p08,p09,p10,p11
$ python ../tools/walk_path.py ... --paths p12,p13,p14,p15,p16,p17
$ python ../tools/walk_path.py ... --paths p18,p19,p20,p21,p22,p23
{"results": [... {"path": "p23", "n": 24, ... "fits_left": 0}], "fits_used": 24, "fits_left": 0, "FREEZE": true}
$ python ../tools/score_test.py ... --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
{"test_score": 0.9034, ...}
$ python ../tools/save_model.py ... && python ../tools/scorecard.py --pack .claude/skills/adult-income-graph --task ../tasks/01_adult_income.json
{"fits_used": 24, "wasted_fits": 16, "best_val_score": 0.9172, "test_score": 0.9034, "test_scored_once": true, ...}
agent> Done. The loop ran to completion exactly as loop.json specifies: t reached N = 24,
score_test answered once after FREEZE, save_model once.
Best val_score 0.9172 (p17: hgb, lr 0.1, scale yes, onehot, balanced); test 0.9034; fits 24/24;
illegal paths 0 - all 24 paths fit the graph (every error was null).
p17 and p21 tied at 0.9172 (identical except scale, a no-op for hgb); I took p17, the earlier
one in paths.json order. Everything ran as the pack prescribes: no fit_recipe, no edits to
graph.json / paths.json, test scored exactly once.
[16 turns, 124 s]
```

What to notice: same numbers as lessons 01-03 (the 24 paths bind the 24
static recipes in the same order), and zero illegal paths in the shipped
file - the illegal-path behaviour is exercised by the test on a copy, and by
you in step 2 above.

**What the test proves.**

- the loop walks `paths.json` in order, binds the 24 static recipes, scores the test once (`test_loop_walks_paths_in_order_and_scores_once`).
- an illegal path is skipped and counted with its reason, never replaced; an unknown id is refused (`test_illegal_path_is_skipped_and_counted_never_replaced`).
- `score_test` is unreachable before FREEZE; `fit_recipe` is not a tool of this pack (`test_score_test_unreachable_before_freeze_and_fit_recipe_not_a_tool`).
- `graph.json` / `paths.json` are byte-identical after a run (`test_graph_files_byte_identical_after_a_run`).
- `lint_pack` refuses a cyclic graph and a path that breaks a constraint (`test_lint_refuses_a_cycle_and_a_bad_path`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** Nobody; the graph and the paths are the human's
  and immutable during a run.
- **The hook.** As before: `score_test.py` before FREEZE or twice.
- **What the script refuses.** A path id not in `paths.json`; `fit_recipe.py`
  for this pack (not in its `tools.md`: a recipe reaches the fitter only as a
  path); `score_test` before FREEZE or twice. An illegal path is not refused
  but *counted* with its reason - a bad plan costs budget, which is what
  makes "the loop never invents a path" checkable.
- **What is and is not self-modified.** Nothing; `graph.json` and `paths.json`
  checksums are equal before and after a run (asserted).

**Diff from 02.** The loop iterates paths; two immutable files.

---

## Lesson 05: A meta skill generates the graph harness, under human approval

**The idea.** Lesson 03's writer, extended to emit `graph.json`, `paths.json` and the loop
over paths; `lint_pack` now walks the graph (no cycle, every edge names a
node, every path legal, `score_test` a sink behind FREEZE), and the proposal
shows the graph to the human as a node / edge list. `edit` is the
interesting answer: the human's change is what lands - a removed edge, a
changed binding - re-linted first, so a human cannot land an illegal graph
either. The writer never sees the run results: still no feedback loop, still
not RSI, still L1 in the framework's terms. What the lesson buys is the
shape every later "improve" reuses: a structured artefact, a linter that
refuses before a human looks, and an approval whose `edit` branch is real.

**Rung.** L1.

**Files.**

```text
step_05_meta_generates_graph/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/graph-writer/
│   ├── SKILL.md, tools.md, task.json
│   └── template/                  SKILL.md, tools.md, schema.json, graph.json, paths.json ({{paths}}), loop.json
├── .agents/skills/graph-writer/
├── .claude/skills/adult-income-graph/   (after approval / edit)
└── runs/graph-writer/{rendered/, edited/, adult_income/proposals/p1.json, adult_income/traces.jsonl}
```

**Build.**

`step_05_meta_generates_graph/.claude/skills/graph-writer/SKILL.md` - step 6's `edit` branch:

```markdown
---
name: graph-writer
description: Write a graph harness pack (SKILL.md, tools.md, schema.json, graph.json, paths.json, loop.json) for the task in task.json and propose it for human approval; the user sees the graph as nodes and edges and may edit it before it lands. Use in rsi/step_05_meta_generates_graph when a task.json exists and no graph pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Graph writer: a meta skill whose output is a graph harness

## Procedure
5. Show the user the node / edge list and every file, then ask: **approve / edit / reject**. An edit may remove an edge or a path, or change a binding; what lands is the user's version, linted again. Wait for the answer; run nothing until it arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
   - edit: apply the user's change to a copy of the rendered files under `runs/graph-writer/edited/` (their words say what to change; if a removed edge makes a path illegal, leave the path - the linter will say so and nothing lands until the user resolves it), then `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>" --edited @runs/graph-writer/edited`
```

`tools/_lib/graph.py` - what the linter walks before a human sees a
proposal, and again before an edit lands:

```python
def lint_graph(graph, paths, task):
    problems = []
    nodes = graph.get("nodes", {})
    edges = [tuple(e) for e in graph.get("edges", [])]
    for a, b in edges:
        if a not in nodes or b not in nodes:
            problems.append(f"edge {a} -> {b} names an unknown node")
    if has_cycle(nodes, edges):
        problems.append("graph.json has a cycle")
    if graph.get("mutable", True):
        problems.append("graph.json must be mutable: false")
    sinks = [n for n, spec in nodes.items() if spec.get("gate") == "freeze_only"]
    if "score_test" in nodes and "score_test" not in sinks:
        problems.append("score_test must be a sink with gate: freeze_only")
```

`tools/_lib/proposals.py` - the graph rendered for the human, on top of
the files:

```python
        for name, text in payload.items():
            if name.endswith("graph.json"):
                g = json.loads(text)
                out.append(f"### {name} as a graph\nnodes: {', '.join(g['nodes'])}\nedges: " + "; ".join(f"{a} -> {b}" for a, b in g["edges"]))
```

`tools/apply.py` - an edited pack is linted again; the human's version is
what lands:

```python
    if decision == "edit":
        if a.edited is None:
            raise ValueError("--approved edit needs --edited <the user's version>; nothing lands")
        payload = cli.value(a.edited)
        if record["kind"] == "pack":
            problems = lint_payload(payload, run.task)
            if problems:
                raise ValueError(f"the edited pack does not lint: {problems}; nothing lands")
```

**Run.** Open your agent in `step_05_meta_generates_graph/` and type:

```text
Use the graph-writer skill: generate the graph pack for the task in .claude/skills/graph-writer/task.json and propose it to me.
```

The commands the agent runs:

```bash
python ../tools/lint_pack.py --pack runs/graph-writer/rendered --task .claude/skills/graph-writer/task.json
python ../tools/propose.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --target .claude/skills/adult-income-graph --kind pack --payload @runs/graph-writer/rendered --summary "graph pack for adult_income: 6 nodes, 5 edges, 24 paths"
```

**You will be asked**: approve / edit / reject, with the graph shown as
nodes and edges and the 24 paths as a table. Try `edit`: say what to
change (in the recording: "edit: change the binding of p07 to hyper 0.25
(logreg C=0.25); keep everything else"). The agent applies your change to
a copy under `runs/graph-writer/edited/`, lints it, and runs:

**See.** The recorded run (Claude Code 2.1.278, headless, two turns; the agent's
rendering and the 24-row path table it showed are trimmed):

```text
[Skill graph-writer]
agent> Using the graph-writer skill. Boot order: tools.md, task.json, then the templates.
[Read task.json] [Read template/*]  [Write runs/graph-writer/rendered/{SKILL.md,graph.json,loop.json,paths.json,schema.json,tools.md}]
$ python ../tools/lint_pack.py --pack runs/graph-writer/rendered --task .claude/skills/graph-writer/task.json
{"ok": true, "problems": [], ...}
agent> Lint is ok. Proposing:
$ python ../tools/propose.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --target .claude/skills/adult-income-graph --kind pack --payload @runs/graph-writer/rendered --summary "graph pack for adult_income: 6 nodes, 5 edges, 24 paths"
{"id": "p1", "diff": "### graph.json as a graph\nnodes: load, scale, encode, model, fit, score_test\nedges: load -> scale; scale -> encode; encode -> model; model -> fit; fit -> score_test\n### SKILL.md ...", ...}
agent> ## Proposal p1 - graph pack for adult_income
Target: .claude/skills/adult-income-graph - lint: ok (0 problems) - nothing has landed yet.
The graph: nodes load, scale, encode, model, fit, score_test; edges load -> scale -> encode -> model -> fit -> score_test.
score_test: sink, gate: freeze_only. Constraints: one_of [scale, encode, model], no_cycles. mutable: false.
The paths: 24, every one load -> scale -> encode -> model -> fit; p00 logreg 1 yes onehot none (baseline) ...
p07 logreg 1 no ordinal balanced ... p23 hgb 0.1 no ordinal balanced.
approve / edit / reject? An edit may remove an edge or a path, or change a binding - tell me what
to change and I'll re-lint your version before it lands. I'll run nothing until you answer.
[20 turns, 117 s]
=== user> edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else
agent> Applying your edit to a copy under runs/graph-writer/edited/, then linting it before it lands.
$ mkdir -p runs/graph-writer/edited && cp runs/graph-writer/rendered/* runs/graph-writer/edited/
[Edit runs/graph-writer/edited/paths.json]
$ python ../tools/lint_pack.py --pack runs/graph-writer/edited --task .claude/skills/graph-writer/task.json
{"ok": true, "problems": [], ...}
agent> Edited version lints ok. Landing it with your words:
$ python ../tools/apply.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --proposal p1 --approved "edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else" --edited @runs/graph-writer/edited
{"id": "p1", "decision": "edit", "landed": true, "target": ".claude/skills/adult-income-graph", "files": ["SKILL.md", "graph.json", "loop.json", "paths.json", "schema.json", "tools.md"], "approved_by": "human", "words": "edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else"}
agent> Proposal p1 - decision: edit - landed. The only difference from the proposed pack is
paths.json's p07: hyper 1 -> 0.25. The edited pack was re-linted before landing: ok, 0 problems
(0.25 is in logreg's hyper list [0.25, 1, 4], so the path is still a valid recipe).
I did not fit, score, or run the generated pack; that's for the adult-income-graph skill itself.
[6 turns, 51 s]
```

What to notice: what landed is the human's version (`p07` at `C=0.25`,
checked after the recording), the human's words are in the trace, and the
agent re-linted before landing without being told twice - the rule is in
its procedure and in the script.

**What the test proves.**

- the writer cannot walk or fit (`test_writer_cannot_walk_or_fit`).
- a cycle or an illegal path is refused before the human sees the proposal (no proposal file is written) (`test_cycle_and_bad_path_refused_before_the_human_sees_them`).
- the proposal shows the graph as nodes and edges (`test_proposal_shows_the_graph_as_nodes_and_edges`).
- an edit that changes a binding lands and the pack still runs; one that lowers `N` does not lint (`test_edit_removing_a_path_lands_and_the_pack_still_runs`).
- an edit that removes an edge every path needs does not land (`test_edit_removing_a_needed_edge_does_not_land`).
- the generated pack equals lesson 04's graph and paths and passes its checks (`test_generated_pack_passes_lesson_04_checks`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The human approves the graph and the paths, and
  may edit them; the writer decides nothing about the task. The linter
  stands between both of them and the disk: neither the writer's nor the
  human's version lands unless it lints against `task.json`.
- **The hook.** Blocks `apply.py` without the user's words.
- **What the script refuses.** A cyclic graph, an unknown node, a path that
  visits `scale` / `encode` / `model` other than once, a path that reaches
  the sink, a binding that is not a recipe, a changed budget - before the
  human sees the proposal and again on an edit; `walk_path.py` /
  `fit_recipe.py` for the writer.
- **What is and is not self-modified.** Nothing. The generated pack is
  immutable while it runs (lesson 04's checksums), and the writer never
  reads a run.

**Diff from 03.** Six templates; the linter walks a DAG.

---

## Lesson 06: The RSI harness: the first file a later run reads that an earlier run wrote

**The idea.** Two packs. The actor (`adult-income`) trains under the 24-fit budget and
*proposes* its recipes shaped by the memory cards in `memory.json`: a card is
`IF <profile predicate> THEN prefer / forbid <one field value>`, with
`evidence` and `counter` counts, typed by `memory.schema.json` so that a
script can enforce it (`fit_recipe.py` refuses a recipe a forbid card rules
out; there is no free-text field for a diary entry or the word "test"). The
verifier (`adult-income-verifier`) writes the cards, and no one grades their
own homework: its whole input is `{recipe, val_score, error}` rows and the
profile from `read_traces.py` - never the actor's transcript, the test
split or the intent - and the actor cannot write a card at all (`write_card`
is not in its `tools.md`; the script refuses). `MEMORY_OFF` is the off
switch: `--memory off` on an arm or `{"memory": "off"}` in `config.json`
gives lesson 01's numbers exactly. This is L4 in the framework paper's terms:
deployment feedback revises persistent state under an acceptance rule the
human wrote (the verifier contract, the card schema, the demotion rule).

**Rung.** L4. The verifier contract, the card schema and the demotion rule
are human.

**Files.**

```text
step_06_rsi_harness/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/          the actor
│   ├── SKILL.md, tools.md, schema.json
│   ├── memory.schema.json                IF profile THEN prefer / forbid one field value
│   └── memory.json                       [] shipped; the cards land here
├── .claude/skills/adult-income-verifier/ SKILL.md (the contract), tools.md, memory.schema.json
├── .agents/skills/...                    the same
└── runs/adult-income/{adult_income,breast_cancer}/   state.json (both arms), traces.jsonl, scorecards
```

**Build.**

`step_06_rsi_harness/.claude/skills/adult-income/SKILL.md` - the actor's search policy in words,
and the rule it may not break:

```markdown
---
name: adult-income
description: Train a classifier for a curriculum problem under a 24-fit budget, proposing recipes shaped by the memory cards in memory.json (the memory arm), or walking the static list with the memory off (the control arm). Use in rsi/step_06_rsi_harness and later, when the pack has memory.json and a verifier pack writes to it.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# RSI harness: the inner pack (the actor)

## Procedure
2. Search policy: obey-memory.
   - No applicable card (every control arm; a memory arm with an empty memory): walk `schema.json` -> `recipes` in order, in one call:
     `python ../tools/fit_recipe.py --pack P --task T [--arm control] --recipes @P/schema.json`
   - Otherwise take, per field, the applicable `prefer` card with the most `evidence` minus `counter` as the preferred value (`python ../tools/read_memory.py --pack P --task T` lists them under `preferred`; a tie is no preference). Then, in calls of up to eight recipes each, in this order until a result says `FREEZE`:
     a. Probe: one recipe per model of `schema.json` -> `models`, the preferred model first, each with the preferred `scale` / `encode` / `class_weight` (defaults `yes` / `onehot` / `none`) at its middle hyper value (`logreg` 1, `rf` 16, `hgb` 0.1). The probe winner is the model belief.
     b. The believed model's family: its recipes from `recipes` (middle hyper value) first, then its hyper variants; inside each group the recipes carrying the most preferred values first (`class_weight` and `encode` count 2, `scale` and `hyper` 1), then grid order.
     c. The rest of the grid of `fields`, grid order (model, hyper, scale, encode, class_weight).

## Rules
- Never write a card: that is the verifier's job, and `write_card` is not in your `tools.md`. Only a meta pack may patch this pack.

## Off switch
MEMORY_OFF: `--memory off` on the arm, or `{"memory": "off"}` in `config.json`. No card is read or written; you run the static order. Same 24 fits, so the numbers can be compared.
```

`step_06_rsi_harness/.claude/skills/adult-income-verifier/SKILL.md` - the contract, verbatim
(`lint_pack` refuses a verifier pack without it), and the rule that turns a
log into cards:

```markdown
---
name: adult-income-verifier
description: Turn the fit log of one problem into memory cards for the actor pack adult-income. Use after the actor's memory arm on a problem is frozen and scored; input is the log and the profile, nothing else.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

## Procedure
1. Read the fits of this problem's memory arm, with the pairwise tally:
   `python ../tools/read_traces.py --pack P --task T --scope problem --tally`
2. Tally every pair of rows whose recipes differ in exactly one field (two models at their default hyper value count as differing in `model` only): the higher `val_score` is a win for its value of that field and a loss for the other; a pair where one side errored marks the erroring value. The script's `tally` is the same count; check yours against it.
3. Per field, write ONE `prefer` card for the value with the most wins net of losses (`evidence` 1) - if it has any net wins at all - and a `counter` 1 card (same `if`/`then`, `evidence` 0) for every value that lost more than it won. Write a `forbid` card (`evidence` 1) for a value that errored.
```

`tools/_lib/memory.py` - a card is typed; the words "test" and "intent"
cannot get in; a counterexample demotes:

```python
FORBIDDEN_WORDS = ("test", "intent")


def validate_card(card, schema=CARD_SCHEMA):
    """A card is typed. Anything outside the type - a reason, an intent, the word test - is refused."""
    jsonschema.validate(card, schema)
    text = json.dumps(card).lower()
    for word in FORBIDDEN_WORDS:
        if word in text:
            raise ValueError(f"a card may not mention {word!r}")
    return card
```

```python
def active(card):
    """Some evidence, and at most half as many counterexamples: one counter demotes a one-evidence card."""
    return card["evidence"] >= MIN_EVIDENCE and card["evidence"] >= 2 * card["counter"]
```

`tools/fit_recipe.py` - a forbid card is a gate, not advice:

```python
    cards = [] if run.memory_off else memory.load(run.memory_path)
    card = memory.forbidden(rec, cards, run.profile)
    if card is not None:
        raise ValueError(f"a forbid card rules this recipe out: {json.dumps(card['then'])} (no fit spent)")
```

`tools/read_traces.py` - the verifier's whole input, and the shape that
*is* the contract:

```python
    if a.scope == "problem":
        raw = run.fit_rows(arm=a.of)
        rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]} for r in raw]
```

**Run.** Open your agent in `step_06_rsi_harness/` and type:

```text
Problem 1 is ../tasks/01_adult_income.json, problem 2 is ../tasks/02_breast_cancer.json. On problem 1: use the adult-income skill for the control arm (memory off) and then for the memory arm, then use the adult-income-verifier skill to write the cards. Then on problem 2: the adult-income skill for the control arm and for the memory arm. Report the four scorecards side by side and which cards applied on problem 2.
```

The commands the agent runs:

```bash
python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --memory off
python ../tools/fit_recipe.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --recipes @.claude/skills/adult-income/schema.json
python ../tools/score_test.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced
python ../tools/scorecard.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control
# the memory arm: the same without --arm control / --memory off; with cards, read_memory + batches of fit_recipe --recipes '[...]'
python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope problem --tally
python ../tools/write_card.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --as .claude/skills/adult-income-verifier --cards '[{"if": {...}, "then": {...}, "evidence": 1, "counter": 0}, ...]'
```

**See.** The recorded run (Claude Code 2.1.278, headless, 28 turns, 347 s; the
agent piped the fit results through a one-line `python -c` formatter of its
own, trimmed here):

```text
[Skill adult-income]
agent> Memory is empty. Problem 1, control arm: open the arm.
$ python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --memory off
agent> No applicable cards -> walk the static list in one call.
$ python ../tools/fit_recipe.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --arm control --recipes @.claude/skills/adult-income/schema.json
agent> FREEZE. Best val_score is 0.9172, first reached at fit 18: hgb, 0.1, yes, onehot, balanced.
$ python ../tools/score_test.py ... --arm control --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced && python ../tools/save_model.py ... && python ../tools/scorecard.py ... --arm control
agent> Problem 1 control done: best val 0.9172, test 0.9034, 24 fits, 16 wasted. Now problem 1 memory
arm (memory is empty, so the same static walk applies).
$ python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
$ python ../tools/fit_recipe.py ... --recipes @.claude/skills/adult-income/schema.json
agent> Same numbers (same seed, same order). Best is fit 18 again.
[Skill adult-income-verifier]
$ python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope problem --tally
{"scope": "problem", "rows": [{"recipe": {...}, "val_score": 0.9114, "error": null}, ... 24 rows], "profile": {...},
 "tally": {"wins": [...], "losses": [...], "errored": []}, "cards_by_rule": [ ... 9 cards ... ]}
$ python ../tools/write_card.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --as .claude/skills/adult-income-verifier --cards '[
{"if":{"key":"n_rows","op":">=","value":1000},"then":{"field":"model","prefer":"hgb"},"evidence":1,"counter":0},
{"if":{"key":"n_rows","op":">=","value":1000},"then":{"field":"model","prefer":"logreg"},"evidence":0,"counter":1},
{"if":{"key":"n_rows","op":">=","value":1000},"then":{"field":"model","prefer":"rf"},"evidence":0,"counter":1},
{"if":{"key":"n_features","op":">=","value":10},"then":{"field":"scale","prefer":"yes"},"evidence":1,"counter":0},
{"if":{"key":"n_features","op":">=","value":10},"then":{"field":"scale","prefer":"no"},"evidence":0,"counter":1},
{"if":{"key":"has_categorical","op":"==","value":1},"then":{"field":"encode","prefer":"onehot"},"evidence":1,"counter":0},
{"if":{"key":"has_categorical","op":"==","value":1},"then":{"field":"encode","prefer":"ordinal"},"evidence":0,"counter":1},
{"if":{"key":"imbalance","op":"<","value":0.35},"then":{"field":"class_weight","prefer":"none"},"evidence":1,"counter":0},
{"if":{"key":"imbalance","op":"<","value":0.35},"then":{"field":"class_weight","prefer":"balanced"},"evidence":0,"counter":1}]'
{"cards": 9, "written": 9, "added": 9, "demoted": 0, "refused": 0, "by": "adult-income-verifier", ...}
$ python ../tools/load_splits.py ... --task ../tasks/02_breast_cancer.json --arm control --memory off
$ python ../tools/fit_recipe.py ... --task ../tasks/02_breast_cancer.json --arm control --recipes @.claude/skills/adult-income/schema.json
agent> Best val 0.9954, first at fit 18: hgb, 0.1, yes, onehot, balanced.
agent> Problem 2 control done. Now the memory arm - open it and read which cards apply.
$ python ../tools/load_splits.py ... --task ../tasks/02_breast_cancer.json && python ../tools/read_memory.py ... --task ../tasks/02_breast_cancer.json
agent> One applicable card: scale: yes (n_features 30 >= 10). No preferred model / encode /
class_weight, so probe uses defaults onehot / none in grid model order.
$ python ../tools/fit_recipe.py ... --recipes '[{"model":"logreg","hyper":1,"scale":"yes","encode":"onehot","class_weight":"none"}, {"model":"rf","hyper":16,...}, {"model":"hgb","hyper":0.1,...}]'
agent> Probe winner: hgb (0.9949 vs logreg 0.9937, rf 0.9917). Model belief = hgb. Step b: the hgb
family from recipes (scale=yes ones first), then hyper variants.
$ python ../tools/fit_recipe.py ... --recipes '[ 8 hgb recipes ]'
$ python ../tools/fit_recipe.py ... --recipes '[ 8 more: hgb at 0.05 and 0.3 ]'
agent> New best: hgb 0.3 yes onehot none at 0.9966. Five fits left - the remaining hyper variants.
$ python ../tools/fit_recipe.py ... --recipes '[ 5 hgb recipes ]'
FREEZE True fits_left 0
$ python ../tools/score_test.py ... --recipe model=hgb,hyper=0.3,scale=yes,encode=onehot,class_weight=none && ... scorecard.py ...
agent> ## Scorecards
| | P1 adult_income control | P1 memory | P2 breast_cancer control | P2 memory |
| best val_score | 0.9172 | 0.9172 | 0.9954 | 0.9966 |
| test_score     | 0.9034 | 0.9034 | 0.9844 | 0.9883 |
| best recipe    | hgb 0.1 yes onehot balanced | same | hgb 0.1 yes onehot balanced | hgb 0.3 yes onehot none |
| fits used / wasted | 24 / 16 | 24 / 16 | 24 / 0 | 24 / 0 |
| cards active   | 0 | 0 | 0 | 4 |
Problem 1's two arms are identical by construction: memory was empty, so the memory arm walked the
same static list as the control arm.
Which cards applied on problem 2 (profile: n_rows 569, n_features 30, n_classes 2, imbalance 0.373,
has_categorical 0): 1 of 4 - n_features >= 10 -> prefer scale: yes. Did not apply: n_rows >= 1000 ->
hgb (569 rows), has_categorical == 1 -> onehot (no categoricals), imbalance < 0.35 -> class_weight
none (0.373). So the memory arm had only a scale preference and no model belief; it ran the probe,
committed to hgb, and spent the remaining 21 fits on the hgb family - which is where the gain came
from: the static list never leaves hyper 0.1, while the family search found hgb at learning rate 0.3
(0.9966 val / 0.9883 test vs 0.9954 / 0.9844).
One observation for the series: the model card is keyed on n_rows >= 1000, so hgb's dominance on
problem 1 couldn't transfer to a 569-row problem even though it won here too.
[28 turns, 347 s]
```

What to notice: the memory arm's recipes are the agent's own choices,
following the policy text - and they land on the same 0.9966 / 0.9883 the
test's scripted policy finds. The agent's closing observation is exactly
the superstition problem lesson 07's curriculum is built around (a card
conditioned on `n_rows` cannot know whether the signal is linear), and it
was made from the profile and the numbers, not from the data. The verifier
never saw the actor's messages; it saw 24 rows and a profile.

**What the test proves.**

- `MEMORY_OFF` (`config.json`) reproduces lesson 01's numbers exactly and refuses every card (`test_memory_off_reproduces_lesson_01_exactly`).
- the verifier's input is rows `{recipe, val_score, error}` and the profile, nothing else; it writes typed cards (`encode: onehot` among them) (`test_verifier_sees_only_rows_and_profile_and_writes_typed_cards`).
- a card with a note, the word `test` or `intent`, both prefer and forbid, or an unknown key is refused; the actor cannot write a card, the verifier cannot fit (`test_write_card_refuses_test_intent_and_extra_fields`).
- a planted wrong card is demoted by one counterexample; a forbid card refuses a fit and no budget is spent (`test_planted_wrong_card_is_demoted_and_forbid_card_refuses_a_fit`).
- after problem 1, the memory arm on problem 2 beats the control arm (val and test) at the same budget, wastes no more fits, and reaches a hyper variant the static list never visits (`test_memory_arm_beats_control_on_problem_2_after_problem_1`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The human wrote the acceptance rule - the
  verifier contract, `memory.schema.json`, the demotion rule - and the
  system applies it without asking: this is the first lesson where a run
  changes a file a later run reads. No human sits in the loop per card;
  the human's decision is the rule and the off switch.
- **The hook.** As before (locked test). No approval call exists in this
  lesson.
- **What the script refuses.** `write_card.py`: a card outside the schema
  (an extra field, an unknown profile key, both `prefer` and `forbid`), a
  card mentioning `test` or `intent`, any card under `MEMORY_OFF`, any card
  from a pack whose `tools.md` lacks `write_card` (the actor).
  `fit_recipe.py`: a recipe a forbid card rules out (no fit spent).
  `read_traces.py` cannot return anything but rows and the profile.
  `fit_recipe.py` / `score_test.py`: refused for the verifier.
- **What is and is not self-modified.** `memory.json` is - by the verifier,
  under the contract. `SKILL.md`, `schema.json`, the policy line and
  `tools.md` are not: "only a meta pack may patch this pack" (lesson 09).
  Autonomy attribution: the system decides *which cards*, from evidence;
  the human decided what a card may be, who may write one, and how one
  dies.

**Diff from 04.** Two packs; `memory.json` is the first file that changes
because of what happened.

---

## Lesson 07: The proof: a locked test, a learning curve, an exam

**The idea.** Lesson 06 showed a card helping on one problem. This lesson is the evidence
standard the framework paper sets: **structural** recursion (a revised
mechanism governs a later round) is not enough; **effective** recursion
needs stronger successors under comparable budgets and independent
evaluation. So: the curriculum skill runs the six problems in order with
the memory arm and the control arm at the same 24-fit budget on every
problem, the verifier writing after each memory arm, and `curve.py` prints
the learning curve - memory best val minus control best val, wasted fits,
cards added / demoted / active. Then the frozen pack meets the exam problem
it never wrote to, over five seeds, and `exam.py` counts the wins and names
every applicable card that did not transfer. `eval.md` in the actor pack
states the claims before the run; the scorecard fields are lesson 00's; the
test split is scored once per arm, after FREEZE, and the scripts refuse
anything else. The agent orchestrates; the scripts measure.

**Rung.** The evidence standard: structural recursion you can see, effective
recursion under a matched budget and an independent evaluation.

**Files.**

```text
step_07_proof/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/              the actor + eval.md (memory.json shipped as [])
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/   SKILL.md, tools.md: the orchestrator
├── .agents/skills/...
└── runs/adult-income/                        (after a run)
    ├── <problem>/state.json, traces.jsonl, scorecard_{memory,control}_0.json   x 6
    ├── exam/state.json (10 arms), traces.jsonl, scorecards
    ├── curve.json
    └── exam.json
```

**Build.**

`step_07_proof/.claude/skills/adult-income/eval.md` - the claims, written before the run:

```markdown
## The learning curve
Problems 1 to 6 in order, the pack carried forward, the verifier writing after each memory arm. Per problem: `gap_val` = memory best val - control best val; `wasted` = fits before reaching the control arm's best (within 0.005), plus every fit that errored; cards added / demoted / active. The claim: the gap is never negative, and larger on the last problem than on the second.

## The exam
Problem 7 is never written to: both arms open with `--freeze-memory` (`write_card.py` refuses), and the exam is run over five seeds. The claim: the memory arm beats the control arm on at least 3 of 5 seeds (a higher test score, or the same score reached with fewer wasted fits), and the report names every applicable card that did not transfer.
```

`step_07_proof/.claude/skills/adult-income-curriculum/SKILL.md` - the orchestrator:

```markdown
---
name: adult-income-curriculum
description: Run the actor pack adult-income over the six curriculum problems in order with the verifier writing after each, print the learning curve, then run the frozen pack on the exam problem over five seeds and print the exam report. Use in rsi/step_07_proof and later, to produce the proof of a lesson.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

## Procedure
1. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open the arm, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open, `read_memory.py --order obey-memory` for the next recipes, fit them, repeat until FREEZE, score once, scorecard).
   c. Verifier: follow `V/SKILL.md` on `T` (the tally, then the cards, written with `--as V`).
2. The learning curve:
   `python ../tools/curve.py --pack P --tasks ../tasks`
3. The exam, on `tasks/07_exam.json`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off --freeze-memory`, then the memory arm with `--seed s --freeze-memory` (both as in step 1, with `--seed s` on every command). No verifier: the memory is frozen and `write_card.py` refuses.
4. The exam report:
   `python ../tools/exam.py --pack P --task ../tasks/07_exam.json --seeds 0,1,2,3,4`
```

`tools/_lib/scorecard.py` - wasted fits, the second number of the curve:

```python
def wasted_fits(rows, bar=None):
    """Fits spent before the first recipe that reaches the bar (within 0.005), plus every fit that errored.
    The bar is the MEMORY_OFF arm's best val score on the same problem and seed - the static grid's answer -
    or, for that arm itself and for a run with no control, the arm's own best. Experience is measured by
    how many fits it saved on the way to the same answer."""
    scored = [r for r in rows if r["val_score"] is not None]
    if not scored:
        return len(rows)
    target = (max(r["val_score"] for r in scored) if bar is None else bar) - GOOD
    first_good = next((i for i, r in enumerate(rows) if r["val_score"] is not None and r["val_score"] >= target), len(rows))
    return first_good + sum(1 for r in rows[first_good:] if r["val_score"] is None)
```

`tools/exam.py` - a win, and the cards that did not transfer:

```python
        gap = None if m["test_score"] is None or c["test_score"] is None else round(m["test_score"] - c["test_score"], 4)
        win = gap is not None and (gap > 0 or (gap == 0 and m["wasted_fits"] < c["wasted_fits"]))
```

```python
    did_not_transfer = [c for c in applicable if "prefer" in c["then"]
                        and sum(1 for b in best if b and b[c["then"]["field"]] == c["then"]["prefer"]) <= len(best) // 2]
```

**Run.** Open your agent in `step_07_proof/` and type:

```text
Use the adult-income-curriculum skill: run the six curriculum problems and the exam, and report the learning curve and the exam tables.
```

The commands the agent runs:

```bash
python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
# the exam: for s in 0 1 2 3 4, both arms with --seed s --freeze-memory (the control arm also --arm control --memory off)
python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
```

**See.** The recorded run (Claude Code 2.1.278, headless, 61 turns, 1627 s; 55
script calls, trimmed to the agent's own notes and the two tables):

```text
[Skill adult-income-curriculum]
agent> Pack state is clean (empty memory, no runs). Starting problem 01, control arm.
agent> Problem 01 done: both arms 0.9172 val / 0.9034 test, 16 wasted each; verifier wrote 9 cards
(9 new, 0 demoted, 4 active). On to problem 02, control arm.
agent> One applicable card (scale: yes); no model preference, so the probe is the three models in grid
order with scale=yes. Probe winner: hgb. Now its family ... The order matches the rule (hgb family,
scale=yes recipes first, then hyper variants). I'll take the script's `next` in calls of eight until FREEZE.
agent> Memory arm: val 0.9966 vs control 0.9954, test 0.9883 vs 0.9844. Verifier on problem 02.
agent> Problem 02 verified: 6 cards (6 new, 0 demoted). Problem 03, control arm.
agent> Every recipe hits 1.0 on wine's val split; the first one is the best by tie order.
agent> Wine is saturated: every pair ties, so cards_by_rule is empty. Nothing to write for problem 03.
agent> Problem 04 verified: 6 cards written, 2 new, 1 demoted (class_weight: none for imbalance < 0.35).
agent> Problem 05 verified: 10 written, 5 new, 1 demoted (class_weight: balanced for imbalance >= 0.35).
agent> Model is tied (hgb vs logreg, 1 each) so no model preference; class_weight has no active card
(both demoted). Running the memory arm. ... Eight cards.
agent> Curriculum done. The learning curve:
$ python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/11
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/11
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/11
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/1/11
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/11
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      1/0/11
{"summary": {"gaps_val": [0.0, 0.0012, 0.0, 0.0, 0.0024, 0.0646], "wasted_memory_total": 20, "wasted_control_total": 33, "never_negative": true}}
agent> Curve claim holds: gap_val never negative (min 0.0), and problem 6 (+0.0646) > problem 2 (+0.0012).
Now the exam, seed 0, control arm first. ... Seeds 1-4, same procedure; one call per arm per seed.
agent> All five seeds done. The exam report:
$ python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
exam exam: memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap 0.0308; pack unchanged: True; no card written: True
  seed 0: memory test 0.865 val 0.8985 wasted 8 | control test 0.8661 val 0.8858 wasted 19 | gap -0.0011 loss
  seed 1: memory test 0.9057 val 0.9318 wasted 16 | control test 0.8077 val 0.9167 wasted 10 | gap 0.098 win
  seed 2: memory test 0.9208 val 0.9131 wasted 4 | control test 0.9208 val 0.9131 wasted 17 | gap 0.0 win
  seed 3: memory test 0.9314 val 0.887 wasted 5 | control test 0.9215 val 0.8766 wasted 18 | gap 0.0099 win
  seed 4: memory test 0.9352 val 0.9389 wasted 0 | control test 0.8881 val 0.9117 wasted 16 | gap 0.0471 win
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 0.1} (evidence 1, counter 0)
  did not transfer: {"key": "n_rows", "op": "<", "value": 1000} -> {"field": "model", "prefer": "logreg"} (evidence 1, counter 0)
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 1} (evidence 1, counter 0)
agent> The claims of eval.md:
- Test split locked - held: test_touched_before_freeze is false and test_scored_once is true on all 22 scorecards.
- Learning curve, gap never negative - held: min gap_val is 0.0.
- Learning curve, gap larger on problem 6 than problem 2 - held: +0.0646 vs +0.0012.
- Exam, memory beats control on >= 3 of 5 seeds - held: 4 of 5 (seed 0 lost on test by 0.0011 despite a higher val score).
- Exam names every applicable card that did not transfer - held: three listed above.
- Exam never written to - held: pack_unchanged: true, no_card_written: true.
Not run, per the skill: save_model.py and the delete-the-file check, which eval.md describes but this
lesson's procedure does not call for.
[61 turns, 1627 s]
```

What to notice, honestly: wine and digits are saturated for this recipe
space (every recipe scores 1.0 / 0.999 on val) and teach nothing - the gap
is 0 and the verifier writes no card on wine. The curve is carried by the
two synthetic tables, where the model belief (`hgb` for tables under 1000
rows, learned on problems 2 and 5) and the demotion of `class_weight:
balanced` are what save 14 wasted fits on problem 6 and add +0.0646 val /
+0.0764 test. Problem 5's test gap is -0.0003 with a +0.0024 val gap: the
claim is on val, and the README does not pretend otherwise. On the exam
seed 0 is a loss by 0.0011 on test with a higher val score - noise of a
700-row table - and the three cards that did not transfer are exactly the
kind the profile cannot justify (a hyper value or a model conditioned on
`n_rows`). After the run the actor's `memory.json` holds 23 cards, 11
active; the shipped file is `[]`.

**What the test proves.**

- on the offline curriculum the gap is never negative, larger on problem 6 than on 2, the memory arm wastes fewer fits in total, cards are added and a superstition is demoted (`test_curve_gap_never_negative_and_growing`).
- the test is scored exactly once per problem and arm; every scorecard has exactly the acceptance fields (`test_test_scored_once_per_problem_and_arm_with_every_field`).
- on the exam the frozen pack beats the control arm on >= 3 of 5 seeds; no card is written; the pack is unchanged; the report names the cards that did not transfer (`test_exam_frozen_pack_beats_control_on_most_seeds`).
- `{"memory": "off"}` in `config.json` gives the control arm's numbers exactly (`test_memory_off_config_gives_control_numbers`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`, about 25 minutes) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** Nobody per card (lesson 06's rule); the human
  wrote the claims (`eval.md`) and the acceptance fields (lesson 00) before
  the run, and reads the two tables after it. The exam problem is the
  human's independent evaluation: no pack ever writes on it.
- **The hook.** The locked test, as always - and it is now exercised 22
  times per run.
- **What the script refuses.** `write_card.py` under `--freeze-memory`;
  `score_test.py` before FREEZE or twice, per arm and seed; `curve.py` and
  `exam.py` never invent a missing arm (they list it as missing).
- **What is and is not self-modified.** `memory.json`, by the verifier,
  between problems - and not on the exam. Everything else is byte-identical
  (`pack_unchanged: true` compares the checksums at the first exam boot with
  the pack after the last seed).

**Diff from 06.** `eval.md`, the orchestrator, two measuring scripts.

---

## Lesson 08: A meta skill generates the RSI harness, under human approval

**The idea.** Lesson 05's writer, extended to emit the inner pack **and** the verifier
pack - `memory.json` (empty), `memory.schema.json` (the card type),
`eval.md` (how the pack is judged) and the verifier's `SKILL.md` with the
contract line - from `task.json`. The proposal shows the verifier contract
first, and `lint_pack` refuses a verifier pack without it: the human is
approving the acceptance rule. That is the difference from lessons 03 and
05: the human is not approving a one-off pack but *a mechanism that will
change itself later* - after every problem the verifier will write cards
into the actor's memory, and the actor's next run will obey them. The
README says so, the skill says so to the user, and the recorded transcript
shows the diff the human saw. L1 for the generation; what it generates
runs at L4 (lesson 06); nothing the generated packs learn comes back to the
writer.

**Rung.** L1 for the generation; what it generates runs at L4.

**Files.**

```text
step_08_meta_generates_rsi/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/rsi-writer/
│   ├── SKILL.md, tools.md, task.json
│   └── template/
│       ├── actor/      SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, eval.md
│       └── verifier/   SKILL.md (with the contract), tools.md, memory.schema.json
├── .agents/skills/rsi-writer/
├── .claude/skills/adult-income/, adult-income-verifier/   (after approval)
└── runs/rsi-writer/{rendered/, adult_income/proposals/p1.json}
```

**Build.**

`step_08_meta_generates_rsi/.claude/skills/rsi-writer/SKILL.md` - step 5 is what makes this lesson
different from lesson 03:

```markdown
---
name: rsi-writer
description: Write the RSI harness for the task in task.json - an actor pack with memory.json, memory.schema.json and eval.md, and a verifier pack with the contract - and propose both for human approval; the user approves a mechanism that will change itself later. Use in rsi/step_08_meta_generates_rsi when a task.json exists and no RSI pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# RSI writer: a meta skill whose output is a mechanism that will change itself

## Procedure
4. Propose both packs at once. The script prints the verifier contract on top of the diff: it is the acceptance rule the user is approving.
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for <name>: actor + verifier, empty memory, the contract"`
5. Show the user the contract first, then every file of both packs, and say plainly what they are approving: not a one-off pack but a mechanism - the verifier will write cards into the actor's `memory.json` after every problem, and the actor's next run will obey them. Ask: **approve / edit / reject**. Wait; run nothing until the answer arrives.
```

`tools/_lib/packs.py` - the contract as a constant, and the lint rules a
verifier pack must meet before a human sees it:

```python
VERIFIER_CONTRACT = ("Contract: the verifier sees only {recipe, val_score, error, profile}; "
                     "it never sees the actor's transcript, the test split or the intent.")
```

```python
    if "write_card" in allowed and "memory.schema.json" not in files:
        problems.append("a verifier pack needs memory.schema.json")
    if "write_card" in allowed and VERIFIER_CONTRACT not in body:
        problems.append("a verifier pack must state the verifier contract verbatim")
    if "write_card" in allowed and any(t in allowed for t in ("fit_recipe", "score_test", "walk_path")):
        problems.append("a verifier pack may not fit or score: no one grades their own homework")
```

`tools/_lib/proposals.py` - a directory of packs lands pack by pack; the
writer next to them is not touched:

```python
def land_pack(target, files):
    """Write the payload under target. One pack replaces target; a directory of packs replaces each sub-pack
    directory and nothing else under target (the writer's own pack lives next to them)."""
    import shutil

    target = Path(target)
    subs = sub_packs(files)
    if subs:
        for sub in subs:
            if (target / sub).exists():
                shutil.rmtree(target / sub)
        packs.write_pack(target, files)
        return {sub: packs.checksums(target / sub) for sub in subs}
```

**Run.** Open your agent in `step_08_meta_generates_rsi/` and type:

```text
Use the rsi-writer skill: generate the RSI harness (actor and verifier) for the task in .claude/skills/rsi-writer/task.json and propose it to me.
```

The commands the agent runs:

```bash
python ../tools/lint_pack.py --pack runs/rsi-writer/rendered --task .claude/skills/rsi-writer/task.json
python ../tools/propose.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --target .claude/skills --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for adult_income: actor + verifier, empty memory, the contract"
```

**You will be asked**, with the contract quoted first and a plain
sentence about what you are approving. Answer approve / edit / reject;
the agent then runs
`python ../tools/apply.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --proposal p1 --approved "<your words>"`.
Strip the contract line from the verifier's `SKILL.md` in an edit and
the edit is refused: `a verifier pack must state the verifier contract verbatim`.

**See.** The recorded run (Claude Code 2.1.278, headless, two turns; the agent's
nine Write calls and its rendering of every file are trimmed):

```text
[Skill rsi-writer]
agent> Following the boot order: tools.md, task.json, then the templates.
$ find .claude/skills/rsi-writer -type f | sort && ls ../tools
[Write runs/rsi-writer/rendered/adult-income/{SKILL.md,tools.md,schema.json,memory.json,memory.schema.json,eval.md}]
[Write runs/rsi-writer/rendered/adult-income-verifier/{SKILL.md,tools.md,memory.schema.json}]
agent> Now the lint.
$ python ../tools/lint_pack.py --pack runs/rsi-writer/rendered --task .claude/skills/rsi-writer/task.json
{"ok": true, "problems": [], ...}
agent> Lint is ok. Now the proposal.
$ python ../tools/propose.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --target .claude/skills --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for adult_income: actor + verifier, empty memory, the contract"
{"id": "p1", "diff": "### verifier contract (the acceptance rule you are approving)\nContract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.\n\n### adult-income-verifier/SKILL.md ...", ...}
agent> Proposal p1 is written; nothing has landed. Lint: ok, 0 problems. Both packs target
.claude/skills/ as adult-income and adult-income-verifier.
## The contract (the acceptance rule you are approving)
> Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's
> transcript, the test split or the intent.
## What you are approving
Not a one-off pack but a mechanism that changes itself: after every problem's memory arm, the
verifier (adult-income-verifier) reads the fit log, tallies pairs of recipes one field apart, and
writes prefer / forbid / counter cards into the actor's memory.json. The actor's (adult-income) next
run obeys those cards (obey-memory search policy ...). The control arm (--arm control --memory off)
ignores the file and walks the static list, so the two can always be compared under the same 24 fits.
Everything derives from task.json (...); nothing widens it. Memory starts empty ([]).
## The files
### adult-income/ (the actor): SKILL.md ... tools.md ... schema.json (24 recipes ...) memory.json []
memory.schema.json - the card type ... eval.md - how the pack is judged, with 24 fits rendered in
### adult-income-verifier/: SKILL.md (the contract line, the procedure) ... tools.md ... memory.schema.json
approve / edit / reject?
=== user> approve
$ python ../tools/apply.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --proposal p1 --approved "approve"
{"id": "p1", "decision": "y", "landed": true, "target": ".claude/skills", "files": ["adult-income-verifier/SKILL.md", "adult-income-verifier/memory.schema.json", "adult-income-verifier/tools.md", "adult-income/SKILL.md", "adult-income/eval.md", "adult-income/memory.json", "adult-income/memory.schema.json", "adult-income/schema.json", "adult-income/tools.md"], "approved_by": "human", "words": "approve"}
agent> Proposal p1 - approved ("approve") - landed. Both packs are now in .claude/skills/:
adult-income/ (SKILL.md, tools.md, schema.json (24 static recipes), memory.json ([]), memory.schema.json,
eval.md) and adult-income-verifier/ (SKILL.md, tools.md, memory.schema.json). apply.py reported
landed: true, 9 files, approved_by: human. The contract in force: (the line above)
[2 turns, 29 s]
```

What to notice: the first thing the user reads is the contract, and the
agent's own summary of what is being approved is the point of the lesson in
one paragraph. The one place the agent tried a shell shortcut (`mkdir` +
`cp` of the template files) was refused by the permission system in
headless mode, and it fell back to its Write tool - the same nine files,
just written by hand.

**What the test proves.**

- the proposal carries the verifier contract verbatim, first; a proposal without it is refused (`test_proposal_carries_the_contract_and_is_refused_without_it`).
- "no" lands nothing; the writer cannot fit or write a card (`test_no_lands_nothing_and_the_writer_cannot_fit_or_write_a_card`).
- the two packs land side by side without touching the writer, and pass lesson 06's checks (cards written, memory arm >= control on problem 2, forbid cards enforced); nothing comes back to the writer (`test_generated_packs_land_side_by_side_and_pass_lesson_06_checks`).
- the same task twice gives the same proposal (`test_same_task_twice_gives_the_same_proposal`).
- the generated actor's schema and card type equal lesson 07's (`test_generated_actor_equals_lesson_07_actor`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The human approves the verifier contract and the
  card schema - the acceptance rule under which the actor's memory will
  change from then on - before either exists. `edit` may change the actor's
  procedure or the schema (re-linted); it may not remove the contract.
- **The hook.** Blocks `apply.py` without the user's words.
- **What the script refuses.** A verifier pack without the contract, with a
  fitting tool, or without `memory.schema.json`; a widened budget; the writer
  fitting, scoring or writing a card; `apply.py` without words.
- **What is and is not self-modified.** The writer is not. The packs it
  writes will be (their `memory.json`, by the verifier) - and that is what
  the human is told they are approving. Autonomy attribution (the paper's
  challenge 2): the human approved an improver, not a result.

**Diff from 05.** Two sub-packs in one proposal; the contract as the
acceptance rule.

---

## Lesson 09: The RSI meta harness: a pack that patches the pack, problem by problem

**The idea.** Lesson 06's verifier changes one file, `memory.json`, under a contract.
This lesson adds a pack that may change the actor pack itself - its
`Search policy:` line, its `schema.json` `forbid` list, its cards - one
proposal per visit, between two curriculum problems. `patch_pack.py`
snapshots the actor under `runs/adult-income/versions/gen_NNN/` before
anything lands, refuses a second proposal per visit, a patch outside the
meta pack's `patches:` globs, one that changes more than 20 % of the pack's
text or removes the test rule; then who decides is one line of the meta
pack's front matter. `approval: human` (`adult-income-meta`): the agent shows
the diff, asks, and lands only with the user's exact words. `approval:
gate` (`adult-income-meta-gate`): the evidence recipe is scored against the
incumbent on the private split - rows no actor arm ever sees - and a loss
rolls the pack back; the human reads the log and may `rollback.py`. The
actor ships with `Search policy: static` so that the first patch is
visible: generation 2 boots what generation 1 wrote (its boot row carries
the patched checksums), and that reboot is the recursion. L4 under the
human; L5 flavour under the gate. The gate itself, the archive rule and the
off switch (`{"meta": "off"}`) stay human, and this page says so.

**Rung.** L4 under the human; L5 flavour under the gate. The gate, the
archive rule and the off switch stay human.

**Files.**

```text
step_09_rsi_meta_harness/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/              the actor, Search policy: static, schema.json forbid: []
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/   + the meta visit
├── .claude/skills/adult-income-meta/         approval: human
├── .claude/skills/adult-income-meta-gate/    approval: gate
├── .agents/skills/...
└── runs/adult-income/versions/gen_001/       (after a run: the snapshot before the first patch)
```

**Build.**

`step_09_rsi_meta_harness/.claude/skills/adult-income-meta/SKILL.md` - one change, the first that
applies; who decides is the front matter:

```markdown
---
name: adult-income-meta
description: Improve the actor pack adult-income between two curriculum problems - one patch per visit to its search-policy line, its schema.json forbid list or its memory cards - and put it through the human approval cycle. Use in rsi/step_09_rsi_meta_harness after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: human
  patches: ["SKILL.md", "schema.json", "memory.json"]
---
# The RSI meta harness: a pack that patches the pack

## Procedure
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change that line to `Search policy: obey-memory` (the whole `SKILL.md`, with that one line changed).
   b. A field value lost every comparison one field apart it was in, at least three times across the whole log, and never won: add `{"field": ..., "value": ...}` to `schema.json` -> `forbid` (`hyper` values are excluded: they belong to one model each).
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet (`read_traces.py --scope problem --tally` lists `cards_by_rule`); merge at most three of them into `memory.json`.
   If none applies, say so and stop: nothing is proposed this visit.
```

`tools/patch_pack.py` - the rules every patch meets before anyone
decides, and the private gate:

```python
    if changed > SIZE_CAP * total:
        raise ValueError(f"the patch changes {changed} of {total} characters, more than {int(SIZE_CAP * 100)} % of the pack; one small change per generation")
    if "SKILL.md" in changes and changes["SKILL.md"]["after"] and "after FREEZE" not in changes["SKILL.md"]["after"]:
        raise ValueError("a patch may not remove the test rule from SKILL.md")
```

```python
def private_gate(run, target_run, candidate):
    """Keep-or-rollback on the private split: the candidate must not score below the incumbent."""
    before = tasks.score_on(run.task, run.seed, incumbent_recipe(target_run), "private")
    after = tasks.score_on(run.task, run.seed, candidate, "private")
    keep = after is not None and (before is None or after >= before)
```

```python
        if not verdict["keep"]:
            packs.rollback(target, versions, label)
            record.update(decision="n", approved_by="gate", applied=False)
```

`tools/_lib/proposals.py` - the snapshot every patch takes first:

```python
def land_patch(target, versions_dir, patch):
    """Snapshot the target under versions/gen_NNN, then write the patched files. Returns the snapshot label."""
    versions_dir = Path(versions_dir)
    label = f"gen_{len(list(versions_dir.glob('gen_*'))) + 1:03d}" if versions_dir.exists() else "gen_001"
    packs.snapshot(target, versions_dir, label)
```

**Run.** Open your agent in `step_09_rsi_meta_harness/` and type:

```text
Use the adult-income-curriculum skill with the meta pack adult-income-meta-gate: run the six curriculum problems with a gate visit after each, then the exam, and report the curve, the exam and the meta decisions.
```

```text
On ../tasks/01_adult_income.json: use the adult-income skill for the control arm and the memory arm, then the adult-income-verifier skill, then the adult-income-meta skill (approval: human) for meta visit 1 and propose its patch to me.
```

The commands the agent runs:

```bash
python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope all
python ../tools/read_memory.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
python ../tools/read_pack.py --pack .claude/skills/adult-income
python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-gate --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --visit 1 --files @runs/adult-income-meta-gate/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "Search policy static -> obey-memory: 4 cards active after problem 01 (rule a)"
```

**You will be asked**: the diff of the one-line change, approve / edit /
reject. The agent then runs
`python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --proposal g1 --approved "<your words>"`.
Without your words the hook blocks the call and the script refuses it;
"no" records a rejection and lands nothing; "edit" lands your version.

**See.** The recorded run under the gate (Claude Code 2.1.278, headless, 76 turns,
1650 s; the arms' fit calls trimmed to the agent's notes):

```text
[Skill adult-income-curriculum]
agent> The pack's policy line is static and there are no cards, so the memory arm walks the static list.
agent> Verifier: 9 cards written, 9 new, 0 demoted (4 active prefer cards, 5 counter-only). Now meta visit 1 -
read everything the meta pack may see.
$ python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope all
$ python ../tools/read_memory.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
$ python ../tools/read_pack.py --pack .claude/skills/adult-income
agent> Rule (a) applies: the policy line is static and 4 cards are active. I write the whole SKILL.md with
that one line changed to the patch scratch dir.
[Write runs/adult-income-meta-gate/patch/SKILL.md]
$ diff .claude/skills/adult-income/SKILL.md runs/adult-income-meta-gate/patch/SKILL.md; python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-gate --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --visit 1 --files @runs/adult-income-meta-gate/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "Search policy static -> obey-memory: 4 cards active after problem 01 (rule a)"
26c26
<    Search policy: static
---
>    Search policy: obey-memory
{"id": "g1", "decision": "y", "approved_by": "gate", "gate": {"before": 0.8951, "after": 0.8951, "keep": true}, "landed": true, "version": "gen_001", "files": ["SKILL.md"], ...}
agent> Meta visit 1: proposal g1, gate before 0.8951 / after 0.8951, keep -> landed as gen_001. The actor's
policy is now obey-memory.
agent> Problem 02 control: best val 0.9954, test 0.9844, wasted 0. Re-reading the actor's policy line before
the memory arm, then opening it.
...
agent> Meta visit 4: (a) no; (b) no non-hyper value has zero wins; (c) all six problem-04 cards_by_rule are
already held in memory (2 added, 4 merged). Nothing proposed.
agent> Meta visit 5: ... Nothing proposed.   agent> ... Meta visit 6.
agent> Curve written; never_negative: true, gap on problem 6 (+0.0646) > problem 2 (+0.0012). Now the exam
over five seeds ...
agent> Done. curve.json and exam.json exist under runs/adult-income/, and both tables were produced. No pack
file was edited by hand; cards went through write_card.py, the one patch through patch_pack.py.
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/11
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/11
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/11
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/1/11
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/11
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      1/0/11
exam: memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score won by fewer wasted fits), mean test gap 0.0308; pack unchanged: True; no card written: True
Meta decisions (adult-income-meta-gate, approval: gate):
| 1 | adult_income | g1: rule (a) - Search policy: static -> obey-memory (4 cards active) | gate 0.8951 / 0.8951, keep -> landed | gen_001 |
| 2 | breast_cancer | none - (a) already obey-memory; (b) only hyper 0.05 never won, and hyper is excluded; (c) all 6 cards_by_rule already in memory | nothing proposed |
| 3-6 | ... | none - every card already held (wine: every pair tied) | nothing proposed |
read_pack.py --checksums: versions = ['gen_001'] - one generation, one landed patch.
[76 turns, 1650 s]
```

The recorded human visit (two turns; the arms trimmed):

```text
[Skill adult-income] ... [Skill adult-income-verifier] ... [Skill adult-income-meta]
agent> Everything ran; here is where things stand and the patch waiting on you.
Problem 01 (adult_income, seed 0) - both arms: control 0.9172 / test 0.9034 / 24 fits / 16 wasted; memory
the same. Identical, as expected: memory.json was empty, so the memory arm ran the same static walk (gap_val
= 0; the delete-the-file check holds). Test scored once per arm, after FREEZE.
Verifier: tally checked by hand against the script's (model hgb 16-0, encode onehot 10-2, class_weight none
8-4, scale yes 6-1, no errors). Wrote 9 cards, 9 new, 0 demoted. Four are active prefer cards for this
profile: model=hgb, scale=yes, encode=onehot, class_weight=none.
$ python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --files @runs/adult-income-meta/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "Search policy static -> obey-memory: 4 cards active after problem 01 (model=hgb, scale=yes, encode=onehot, class_weight=none), rule (a)"
{"id": "g1", "decision": null, "landed": false, "diff": "--- a/SKILL.md
+++ b/SKILL.md
@@ -25,3 +25,3 @@ ...
-   Search policy: static
+   Search policy: obey-memory ...", "next": "Show the diff to the user. Ask: approve / edit / reject. Then: python ../tools/patch_pack.py ... --proposal g1 --approved \"<the user's exact words>\""}
agent> Meta visit 1 - proposal g1 (snapshot taken, nothing landed). Rule (a) applied first: the actor's
search policy is static and 4 cards are active. One change to .claude/skills/adult-income/SKILL.md:
-   Search policy: static
+   Search policy: obey-memory
One thing worth knowing before you decide: the cards say class_weight=none (8-4 across all pairs), but the
single best recipe used balanced - it won only within hgb+onehot. Under obey-memory the actor will probe
hgb/yes/onehot/none first and reach the hgb family by fit ~3 instead of fit 17, so the expected gain is in
wasted fits, not in best val.
approve / edit / reject? I'll run nothing until you answer, then pass your exact words to patch_pack.py --proposal g1.
[24 turns, 218 s]
=== user> approve
$ python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --proposal g1 --approved "approve"
{"id": "g1", "decision": "y", "landed": true, "version": "gen_001", "files": ["SKILL.md"], "approved_by": "human", "words": "approve"}
agent> Landed. Proposal g1 - approved (your words: "approve"), approved_by human. Version gen_001 - the
pre-patch actor pack is snapshotted under runs/adult-income/versions/gen_001/; rollback can restore it.
Files changed: .claude/skills/adult-income/SKILL.md - Search policy: static -> Search policy: obey-memory.
```

What to notice: the whole curriculum under the gate reproduces lesson 07's
numbers to the fourth decimal - because the one patch that fires (the
policy flip after problem 1) turns the actor into lesson 07's actor before
problem 2, and rules (b) and (c) never fire on this curriculum (no
non-hyper value loses every comparison; the verifier already holds every
card the rule would merge). The gate kept the flip on a tie (0.8951 =
0.8951: the evidence recipe *is* the incumbent), which is honest and thin;
lesson 14 shows the same gate rolling a bad rewrite back. One `versions/`
entry after six problems is the right number, and the page does not dress
it up.

**What the test proves.**

- under `approval: human` "no" lands nothing, "yes" lands the patch as `gen_001`, and generation 2 boots the patched checksums (`test_human_no_lands_nothing_yes_lands_and_the_next_generation_boots_it`).
- "edit" lands the user's version (`test_human_edit_lands_the_users_version`).
- the gate keeps a good patch; a patch whose evidence recipe scores lower on the private split is rejected and `versions/` restores the pack byte for byte (`test_gate_keeps_a_good_patch_and_rolls_back_a_bad_one`).
- `META_OFF` leaves the pack byte-identical; one proposal per visit; the 20 % cap; the test rule cannot be removed; the meta pack cannot score or fit (`test_meta_off_one_per_visit_size_cap_and_no_score_test`).
- the offline curriculum under the gate flips the policy line on problem 1 and keeps the curve non-negative (`test_curriculum_under_the_gate_improves_the_policy_line`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** Under `approval: human`, the human, per patch, with
  their words in the trace; under `approval: gate`, the private split, per
  patch, with the numbers in the trace and `rollback.py` in the human's
  hand. The rule that picks the change (a / b / c), the size cap, the
  `patches:` list and `META_OFF` are the human's.
- **The hook.** Blocks `patch_pack.py --proposal` without the user's words;
  the locked test.
- **What the script refuses.** A second proposal per visit; a file outside
  `patches:`; more than 20 % of the pack; removing the test rule; a pack
  patching itself; `score_test.py` / `fit_recipe.py` for the meta pack; a
  gate loss (rolled back).
- **What is and is not self-modified.** The actor's policy line, forbid
  list and cards - through a snapshot. The verifier, `eval.md`, the gate and
  the meta pack's own procedure are not (lesson 16 changes that last one).

**Diff from 07.** The meta packs; `versions/` under `runs/`; the policy line
starts `static` so the first patch is visible.

---

## Lesson 10: Dream-RSI: rank the search policies on the log, at zero fits

**The idea.** Dream-RSI (arXiv:2609.14858) replays experience as a simulator: instead of
spending fits to compare search strategies, the meta pack replays the fit
log and asks, for each policy in `policies.md`, what its first 24 picks
would have scored. A pick the log holds is answered for free; a pick the
log does not hold is `unknown` - the gym is exact where you have been and
silent everywhere else. `rank_policies.py` makes zero fits (the target's
budget counter is read before and after), ranks by the best logged val and
breaks ties towards the policy that would visit more new places, and the
winner is proposed as the actor's `Search policy:` line through the private
gate. The honest half of the lesson: a saturated log (`saturated: true`,
every policy's `unknown` is 0) means the next lap would learn nothing, and
the script says so instead of promising a gain. L2 in the framework's
terms: the system chooses *how* to improve; the policy library stays human.

**Rung.** L2. The policy library is human.

**Files.**

```text
step_10_rsi_dream/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/              the actor: policy line `static`, five policies described
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/   names the dream meta pack
├── .claude/skills/adult-income-meta-dream/   SKILL.md, tools.md, policies.md
├── .agents/skills/...
└── runs/{adult-income, adult-income-meta-dream}/   (after a run)
```

**Build.**

`step_10_rsi_dream/.claude/skills/adult-income-meta-dream/SKILL.md`:

```markdown
---
name: adult-income-meta-dream
description: Choose the actor pack's search policy by replaying the fit log as a simulator (Dream-RSI) with zero fits, and propose the winner as the actor's Search policy line through the private gate. Use in rsi/step_10_rsi_dream after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: gate
  patches: ["SKILL.md"]
---
# Dream-RSI: the log is an exact gym for the recipes you visited, and silent elsewhere

## Procedure
2. Rank every policy named in `policies.md` on the log of the problem just finished:
   `python ../tools/rank_policies.py --pack M --task T --target P --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family`
   The script replays the log: for each policy it walks the policy's first 24 picks, answers a pick from the log when the log has it, and counts a pick the log does not have as `unknown`. No fit is spent (`fits_spent: 0`, and the actor's budget counter is unchanged). A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher, because a lap that only revisits the log learns nothing.
3. If `winner` equals the current policy line, say so and stop.

## Rules
- Zero fits: `fit_recipe` is not in your `tools.md`; `rank_policies.py` reports `fits_spent: 0` and the budget counter proves it.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new, and recursion pays only if it does.
```

`tools/rank_policies.py` - the replay:

```python
    for name in [p.strip() for p in a.policies.split(",") if p.strip()]:
        fits, tried, unknown = [], [], 0
        try:
            for n in range(1, schema["n_fits"] + 1):
                pick = next((r for r in policies.policy_order(name, static, cards, profile, fits, seed=a.seed, forbid=forbid) if r not in tried), None)
                if pick is None:
                    break
                tried.append(pick)
                if recipe.key(pick) in logged:
                    fits.append(({"recipe": pick}, {"n": n, "val_score": logged[recipe.key(pick)]}))
                else:
                    unknown += 1
```

```python
    ranked.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
```

**Run.** Open your agent in `step_10_rsi_dream/` and type:

```text
Use the adult-income-curriculum skill with the meta pack adult-income-meta-dream: run the six curriculum problems with a Dream-RSI visit after each, then the exam, and report the curve, the exam and the policy rankings.
```

The commands the agent runs:

```bash
python ../tools/rank_policies.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family
python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --files @runs/adult-income-meta-dream/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "policy -> obey-memory: best logged val 0.9172, unknown 0" --visit 1
```

**See.** The recorded run (Claude Code 2.1.278, headless, 70 turns, 1495 s; the
arms' fit calls trimmed to the visits and the tables):

```text
[Skill adult-income-curriculum]
agent> Verifier: 9 cards written, 9 new, 0 demoted. Now the Dream-RSI visit 1 on problem 01.
$ python ../tools/rank_policies.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family
{"ranking": [{"policy": "obey-memory", "best_logged_val": 0.9172, "visited": 10, "unknown": 14, ...}, {"policy": "neighbours-of-top-3", "best_logged_val": 0.9172, "unknown": 6, ...}, {"policy": "static", "best_logged_val": 0.9172, "visited": 24, "unknown": 0, ...}, ...],
 "winner": "obey-memory", "fits_spent": 0, "log_size": 24, "saturated": false, "current_policy": "static"}
agent> Winner obey-memory != current static, so I write the patched SKILL.md (only the policy line changed)
and propose it through the gate.
$ python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --files @runs/adult-income-meta-dream/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "policy -> obey-memory: best logged val 0.9172, unknown 14" --visit 1
{"id": "g1", "decision": "y", "approved_by": "gate", "gate": {"before": 0.8951, "after": 0.8951, "keep": true}, "landed": true, "version": "gen_001", "files": ["SKILL.md"], ...}
agent> Visit 1: gate kept (private 0.8951 -> 0.8951), landed as gen_001, policy now obey-memory.
agent> Visit 2: gate kept (1.0 -> 1.0), gen_002, policy now random.
agent> Visit 3: kept, gen_003, policy neighbours-of-top-3.
agent> Visit 4: kept (private 0.9985 -> 0.9994), gen_004, policy obey-memory.
agent> Visit 5: kept (0.9323 -> 0.9395), gen_005, policy neighbours-of-top-3.
agent> Visit 6: kept (0.5806 -> 0.8817), gen_006, policy random. All six problems done - the learning curve.
$ python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/10
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/10
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/10
 4 digits                   0.9995    0.999 +0.0005     0.999    0.9984    0/0       4/0/10
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/10
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834   17/17      2/1/10
$ python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score won by fewer wasted fits), mean test gap 0.0282; pack unchanged: True; no card written: True
agent> Dream-RSI visits (all zero fits, fits_spent: 0 every time):
| visit | problem | ranking (policy: best logged val / unknown) | proposal | gate | version |
| 1 | adult_income | obey-memory 0.9172/14, neighbours 0.9172/6, static 0.9172/0, prefer-untried 0.9172/0, random 0.915/17 | static -> obey-memory | keep 0.8951 -> 0.8951 | gen_001 |
| 2 | breast_cancer | random 0.9966/17, prefer-untried 0.9954/20, static 0.9954/14, neighbours 0.9954/14, obey-memory 0.9954/2 (stopped early) | obey-memory -> random | keep 1.0 -> 1.0 | gen_002 |
| 3 | wine | neighbours 1.0/18, static 1.0/17, prefer-untried 1.0/17, random 1.0/0, obey-memory none/3 (stopped early) | random -> neighbours-of-top-3 | keep 1.0 -> 1.0 | gen_003 |
| 4 | digits | obey-memory 0.999/16, random 0.999/16, neighbours 0.999/9, prefer-untried 0.999/9, static 0.999/8 | neighbours -> obey-memory | keep 0.9985 -> 0.9994 | gen_004 |
| 5 | synth_shift_a | neighbours 0.9531/6, random 0.9528/18, prefer-untried 0.9507/20, static 0.9507/14, obey-memory 0.9507/2 (stopped early) | obey-memory -> neighbours-of-top-3 | keep 0.9323 -> 0.9395 | gen_005 |
| 6 | synth_shift_b | random 0.8571/17, obey-memory 0.8571/12, neighbours 0.8571/7, prefer-untried 0.7925/16, static 0.7925/8 | neighbours -> random | keep 0.5806 -> 0.8817 | gen_006 |
The log was never saturated (some policy always had unknown picks), and every one of the six proposals was
kept - the gate never rolled one back. Note that the winner flipped on every visit; the ranking rewards
the policy that would revisit the fewest logged recipes, so it tends to pick whatever the previous policy wasn't.
[70 turns, 1495 s]
```

What to notice, honestly: the curve's gaps are lesson 07's except digits
(+0.0005) and the wasted fits on problem 6 (17 under `neighbours-of-top-3`
where `obey-memory` wasted 3), and the exam's mean test gap is +0.0282
against lesson 07's +0.0308. Dream-RSI's ranking is exact where the log
has been and rewards leaving it; on a log that one policy wrote, the
policy that *did not* write it ranks first at every tie, so the line
flipped six times in six visits - `static -> obey-memory -> random ->
neighbours-of-top-3 -> obey-memory -> neighbours-of-top-3 -> random` - and
the gate kept each flip because the evidence recipe is the log's best
recipe under either policy. The replay is a gym for the recipes you
visited and silent elsewhere; it does not know which policy *found*
them. That is the paper's point about "reliable verification", and this
page reports it rather than smoothing it over.

**What the test proves.**

- `rank_policies` spends zero fits (the state is byte-identical), `static` replays the log fully, `random` and `neighbours-of-top-3` leave it (`unknown` > 0), the meta pack cannot fit (`test_rank_policies_spends_zero_fits_and_marks_unknown`).
- the winner becomes the policy line through the gate; the next lap visits recipes the log did not hold; any other file is refused (`test_winner_becomes_the_policy_line_and_the_next_lap_visits_new_recipes`).
- a saturated log is reported as such (`test_saturated_log_is_reported`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The private gate, per visit; the policy library
  (`policies.md`) is the human's and the meta pack may not add to it.
- **The hook.** The locked test; no human call in this lesson.
- **What the script refuses.** A fit for the meta pack; a patch to any file
  but `SKILL.md`; a second proposal per visit; a patch the private split
  scores lower.
- **What is and is not self-modified.** The actor's `Search policy:` line
  (one line of its `SKILL.md`), through a snapshot and the gate. The five
  policies' definitions, the cards' rule and the verifier are not.

**Diff from 09.** One script and one meta pack; the actor's policy menu.

---

## Lesson 11: RSIAgent: the next experiment, chosen on purpose; the memory, frozen at test

**The idea.** RSIAgent (arXiv:2609.15364) splits the loop into a curriculum module that
picks the next experiment by uncertainty, an actor that runs it, and a
verifier that sees only the world's result. Here the planner
(`adult-income-planner`) scores every model family by
`u = (1 - success) + c / (n + 1)` and writes twelve experiments into the
actor's `plan.json`: a broad phase (`c = 2.0`) that touches every family
before repeating one, then a deep phase (`c = 0.25`) that goes where the
faults are. The actor (`adult-income-actor`) proposes nothing of its own -
every memory-arm fit is an experiment from the plan, and it cannot read the
memory or write a plan (`tools.md`, enforced). The memory is frozen while the
actor runs: the verifier writes after `score_test`, and on the transfer
table (the exam) no card lands at all. L3 in the framework's terms - the
system chooses which experience to acquire; the uncertainty rule and the
phase lengths stay human.

**Rung.** L3. The uncertainty rule and the phase lengths are human.

**Files.**

```text
step_11_rsi_agent/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-actor/        SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, eval.md, plan.json (scratch)
├── .claude/skills/adult-income-planner/      SKILL.md, tools.md
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/
└── .agents/skills/...
```

**Build.**

`step_11_rsi_agent/.claude/skills/adult-income-planner/SKILL.md` - the rule and its numbers:

```markdown
---
name: adult-income-planner
description: RSIAgent's curriculum module - choose the actor's next experiments by uncertainty (a broad phase that touches every model family, then a deep phase that goes where the faults are) and write them to the actor's plan.json. Use in rsi/step_11_rsi_agent before the actor's first fit on a problem and again when its plan runs dry.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# RSIAgent's curriculum: the next experiment, chosen on purpose

## Procedure
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far and `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline). The script prints these per family; check them.
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
   In the broad phase every family starts equal and the large `c` makes the plan round-robin: every family is touched before any is repeated. In the deep phase the small `c` lets `1 - success` dominate: the family with the most faults (fits below the baseline, or errors) comes first.
3. Build the plan greedily: 12 times, take the family with the highest `u` (ties: the family the cards prefer, then schema order), give it its next untried recipe (static recipes of `schema.json` -> `recipes` before hyper variants; inside those, the recipes carrying the most card-preferred values first), and count that experiment as one more fit for the family (recompute `u` with `n + 1` and the same success).
```

`tools/write_plan.py` - the numbers, and the plan as the only thing the
actor fits:

```python
def uncertainty(rows, c, models):
    """Per family: n, wins, success, u - the numbers the planner ranks families by."""
    baseline = next((r["val_score"] for r in rows if r["val_score"] is not None), None)
    out = {}
    for m in models:
        mine = [r for r in rows if r["recipe"]["model"] == m]
        n = len(mine)
        wins = sum(1 for r in mine if r["val_score"] is not None and baseline is not None and r["val_score"] >= baseline)
        faults = sum(1 for r in mine if r["val_score"] is None or (baseline is not None and r["val_score"] < baseline))
        success = (wins + 1) / (n + 2)
        out[m] = {"n": n, "wins": wins, "faults": faults, "success": round(success, 4), "u": round((1 - success) + c / (n + 1), 4)}
    return out
```

`step_11_rsi_agent/.claude/skills/adult-income-actor/tools.md` - the actor's world:

```markdown
## Forbidden
- write_plan - the planner writes the plan, run for the planner pack
- read_memory - the cards are the planner's input, not yours: you run experiments
- write_card, read_traces - the verifier's tools
```

**Run.** Open your agent in `step_11_rsi_agent/` and type:

```text
Use the adult-income-curriculum skill: run the six curriculum problems with the planner choosing the actor's experiments, then the exam, and report the curve and the exam.
```

The commands the agent runs:

```bash
python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-actor --uncertainty --c 2.0
python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-actor --plan '{"phase": "broad", "c": 2.0, "experiments": [ ...12 recipes... ]}'
python ../tools/fit_recipe.py --pack .claude/skills/adult-income-actor --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-actor/plan.json
```

**See.** The recorded run (Claude Code 2.1.278, headless, 48 turns, 1368 s; fit
calls trimmed to the agent's notes and the tables):

```text
[Skill adult-income-curriculum]
agent> Now the memory arm: open, then the planner's broad phase.
$ python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-actor --uncertainty --c 2.0
{"phase": "broad", "c": 2.0, "fits_so_far": 0, "families": {"logreg": {"n": 0, "wins": 0, "faults": 0, "success": 0.5, "u": 2.5}, "rf": {...same...}, "hgb": {...same...}}, "tried": []}
$ python ../tools/write_plan.py ... --plan '{"phase": "broad", "c": 2.0, "experiments": [ ...12 recipes... ]}'
{"written": ".../adult-income-actor/plan.json", "phase": "broad", "c": 2.0, "experiments": 12, "families": ["logreg", "rf", "hgb", "logreg", "rf", "hgb", "logreg", "rf", "hgb", "logreg", "rf", "hgb"]}
agent> Broad phase: round-robin logreg/rf/hgb x4, as the rule predicts. Actor fits it.
$ python ../tools/fit_recipe.py --pack .claude/skills/adult-income-actor --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-actor/plan.json
agent> Plan ran dry, 12 fits remain. Planner's deep phase (c = 0.25).
$ python ../tools/write_plan.py ... --uncertainty --c 0.25
{"phase": "deep", "c": 0.25, "fits_so_far": 12, "families": {"logreg": {"n": 4, "wins": 1, "faults": 3, "success": 0.3333, "u": 0.7167}, "rf": {"n": 4, "wins": 0, "faults": 4, "success": 0.1667, "u": 0.8833}, "hgb": {"n": 4, "wins": 4, "faults": 0, "success": 0.8333, "u": 0.2167}}, ...}
agent> Deep phase: rf has the most faults (4/4 below baseline), so all 12 go to rf. Actor fits it.
agent> FREEZE. Best memory-arm val: 0.9172 (hgb 0.1 yes onehot balanced). Score test, scorecard, then the verifier.
agent> Tally checks out against my own count. Writing the 9 cards as V.
agent> Problem 02: gap 0 (0.9954 both), wasted 0 vs 0; 5 cards written, 4 active cards applied. On to 03.
...
$ python ../tools/curve.py --pack .claude/skills/adult-income-actor --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      9/0/9
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       5/0/9
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/9
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       4/0/9
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    1/0       0/1/9
 6 synth_shift_b            0.7655   0.7925 -0.0270    0.8603     0.834   24/17      2/0/9
$ python ../tools/exam.py --pack .claude/skills/adult-income-actor --task ../tasks/07_exam.json --seeds 0,1,2,3,4
exam: memory arm beats control on 4 of 5 seeds (1 on test score, 4 same score; a tie won by fewer wasted fits), mean test gap 0.0006; pack unchanged: True; no card written: True
  did not transfer: n_classes < 3 -> hyper 8; has_categorical == 1 -> encode onehot (evidence 2, counter 1); n_classes < 3 -> hyper 1
agent> The claims of eval.md:
- Curve, gap never negative: did not hold - problem 6 has gap_val = -0.027 (memory best val 0.7655 vs
control 0.7925). The class_weight: none card (evidence from problems 1 and 4) pushed every none recipe
ahead in the broad phase, and the deep phase went to the two faultiest families (logreg, rf), so
hgb/onehot/balanced - the control's best - was never fitted; the memory arm wasted all 24 fits by the
curve's definition, though its test score was higher (0.8603 vs 0.834).
- Curve, gap larger on problem 6 than on problem 2: did not hold - -0.027 vs 0.000.
- Exam, memory beats control on >= 3 of 5 seeds: held - 4 of 5 (one on test score, three ties won on
fewer wasted fits; seed 1 lost by one wasted fit).
The planner's greedy rule was applied through a scratch helper (runs/_planner_scratch/build_plan.py,
gitignored under runs/) that reproduces SKILL.md step 3 from the numbers write_plan.py --uncertainty and
read_memory.py printed; the deep phase consistently sent all 12 experiments to the faultiest family,
which is what the small c in the rule produces.
[48 turns, 1368 s]
```

What to notice, honestly: RSIAgent's uncertainty rule is the one method
in this series that *loses* the curve on problem 6 (-0.027 val, all 24
fits wasted by the curve's definition, though the test score is higher),
because the deep phase spends its twelve experiments on the faultiest
family instead of the best one - it goes where the faults are, as the
paper says, and on a trees-shaped table with a linear-looking profile that
is the wrong place. The wasted-fits column is where it pays: 2 vs 16 on
problem 1, 27 vs 33 over the curriculum, and 0 / 6 / 9 vs 16 / 17 / 18 on
three exam seeds; the exam is won 4 of 5 on ties broken by fewer wasted
fits, with a mean test gap of +0.0006. The agent wrote itself a helper
script for the greedy plan (under `runs/`, scratch) rather than
hand-ranking twelve recipes per phase; the numbers it ranked by were the
script's.

**What the test proves.**

- the broad phase touches every family before the deep phase repeats one, and stays round-robin under `c = 2.0` (`test_broad_touches_every_family_before_deep_repeats_one`).
- the deep phase's first experiment goes to the family with the most faults (`test_deep_phase_prefers_the_family_with_the_most_faults`).
- the actor fits only what the plan says; it cannot read memory or write a plan; the planner cannot fit (`test_actor_fits_only_the_plan_and_cannot_read_memory_or_write_a_plan`).
- no card lands before `score_test`; on the transfer table the memory is frozen and unchanged (`test_memory_frozen_before_score_and_unchanged_on_the_transfer_table`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** Nobody per experiment: the human wrote the
  uncertainty rule, `c` for each phase and the phase length, and the
  planner applies them. The verifier writes after the score, never before.
- **The hook.** The locked test.
- **What the script refuses.** `write_plan.py` for the actor; `fit_recipe.py`
  for the planner; a plan that is not `{phase, c, experiments}` or holds a
  recipe outside the schema; `write_card.py` on the exam (frozen memory).
- **What is and is not self-modified.** `plan.json` is rewritten every phase
  (scratch, excluded from the pack's checksums); `memory.json` changes after
  the score, by the verifier; nothing else.

**Diff from 09.** The choice of the next experiment moves to a pack.

---

## Lesson 12: ModularRSI: a harness module, evolved off the benchmark

**The idea.** ModularRSI (arXiv:2609.14857) treats the agent harness as modules - agent
loop, tool use, observation management, context management, task completion
detection - and evolves them one at a time on data the benchmark never
sees. Here two actor packs share everything except `modules/context.md`:
actor A's search policy is `static`, actor B's `obey-memory`. Both run the
pool (two synthetic tables no curriculum or exam problem uses), the
verifier writes the same cards into both after each pool task, and
`contrast.py` pairs the success and the failure per task and names the one
module file whose text differs. The meta pack patches the loser's module
with the winner's text (`patches: ["modules/*.md"]`: any other file is
refused) and the pool task's private split decides keep-or-rollback. The
eval table is never used for validation. L2 -> L5 flavour: the system
localises the bug and patches a harness module; the module boundaries and
the pool stay human.

**Rung.** L2 -> L5 flavour. The module boundaries and the pool are human.

**Files.**

```text
step_12_rsi_modular/
├── README.md, test_step.py, .claude/settings.json
├── pool/01_pool_trees_1.json, 02_pool_trees_2.json     benchmark-disjoint (1500 rows each)
├── .claude/skills/actor-a/    SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, eval.md, modules/{agent_loop,tool_use,observation,context,completion}.md
├── .claude/skills/actor-b/    the same, context.md says obey-memory
├── .claude/skills/adult-income-verifier/
├── .claude/skills/modular-meta/   SKILL.md (approval: gate, patches: modules/*.md), tools.md
└── .agents/skills/...
```

**Build.**

`step_12_rsi_modular/.claude/skills/actor-a/modules/context.md` - the one module the two actors
differ in (actor B's says `obey-memory`):

```markdown
# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: static
  (static: walk `schema.json` -> `recipes` in order, cards or no cards: `--recipes @P/schema.json`.)
- MEMORY_OFF (`--memory off` on the arm, or `config.json`): no card is read; you run the static order.
```

`step_12_rsi_modular/.claude/skills/modular-meta/SKILL.md`:

```markdown
---
name: modular-meta
description: ModularRSI's meta pack - localise a harness bug to one module by contrasting two actor packs on a benchmark-disjoint pool, patch that one module of the losing pack with the winning text, and validate on the pool's private split before it lands. Use in rsi/step_12_rsi_modular after both actors have run every pool task.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: gate
  patches: ["modules/*.md"]
---
# ModularRSI's meta pack: a module, evolved off the benchmark

## Procedure
2. Contrast the two actors over the pool:
   `python ../tools/contrast.py --pack M --task T --a A --b B --tasks pool`
   The script pairs, per pool task both actors ran, the success (higher best val) with the failure, names the one `modules/*.md` file whose text differs between the two packs (`module`), returns both texts, and the `winner`.
3. If `winner` is null, or `module` is null (no single module differs, or several do), say so and stop: the bug is not localised.
```

`tools/contrast.py`:

```python
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
```

```python
    winner = max((na, nb), key=lambda n: wins[n]) if decided and wins[na] != wins[nb] else None
    module = differing[0] if len(differing) == 1 else None
```

**Run.** Open your agent in `step_12_rsi_modular/` and type:

```text
Use the modular-meta skill: run both actors on the pool, contrast them, and patch the losing actor's module if the bug is localised.
```

The commands the agent runs:

```bash
python ../tools/contrast.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json --a .claude/skills/actor-a --b .claude/skills/actor-b --tasks pool
python ../tools/patch_pack.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json --target .claude/skills/actor-a --files @runs/modular-meta/patch --recipe model=hgb,hyper=0.3,scale=yes,encode=onehot,class_weight=balanced --summary "modules/context.md <- actor-b's text" --visit 1
```

**See.** The recorded run (Claude Code 2.1.278, headless, 33 turns, 621 s; the
pool's fit calls trimmed to the agent's notes):

```text
[Skill modular-meta]
agent> Only modules/context.md differs between the packs (A: static, B: obey-memory). Now the pool run -
step 1, pool task 1, actor A first (memory arm). ... FREEZE. Best val 0.8966 with hgb,0.1,yes,onehot,balanced.
agent> Now actor B on pool task 1 (obey-memory: read_memory prints the next eight, fit, repeat). No cards yet,
so the policy falls back to the static order. ... Same walk as A. Best 0.8966.
agent> Verifier for A: 4 cards written, 4 new, 0 demoted. Now the verifier with --pack B (B's log is
identical, so the tally should be too - checking rather than assuming). Both actors now carry the same four cards.
agent> Pool task 2 - actor A first (static walk, cards or no cards). FREEZE. Best 0.8847.
agent> Now actor B with two applicable cards (prefer hgb, prefer scale=yes). The policy probes one recipe per
model first (believed model hgb first, with scale=yes). ... Frozen at 24 fits. Best val 0.8945 with
hgb,0.3,yes,onehot,balanced (first reached at t=20).
agent> Verifier for A on task 2: 6 cards written, 4 new. Verifier for B on task 2: 8 cards written, 6 new.
Pool run complete. Step 2 - contrast the two actors over the pool.
$ python ../tools/contrast.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json --a .claude/skills/actor-a --b .claude/skills/actor-b --tasks pool
{"pairs": [{"problem": "pool_trees_1", "skipped": "tie", ...}, {"problem": "pool_trees_2", "success": "actor-b", "failure": "actor-a", "best": {"actor-a": {"val": 0.8847, ...}, "actor-b": {"val": 0.8945, "recipe": {"model": "hgb", "hyper": 0.3, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}, ...}}}],
 "modules_differing": ["modules/context.md"], "module": "modules/context.md", "winner": "actor-b", "wins": {"actor-a": 0, "actor-b": 1}, "texts": {...}, "fits_spent": 0}
[Write runs/modular-meta/patch/modules/context.md]
$ python ../tools/patch_pack.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json --target .claude/skills/actor-a --files @runs/modular-meta/patch --recipe model=hgb,hyper=0.3,scale=yes,encode=onehot,class_weight=balanced --summary "modules/context.md <- actor-b's text" --visit 1
{"id": "g1", "decision": "y", "approved_by": "gate", "gate": {"before": 0.8737, "after": 0.879, "keep": true}, "landed": true, "version": "gen_001", "files": ["modules/context.md"], ...}
agent> contrast.py has answered and patch_pack.py has answered once - done.
Pool run: pool_trees_1 - A 0.8966 / B 0.8966 (no cards yet: identical walks); pool_trees_2 - A 0.8847 / B 0.8945.
On task 2 B's two applicable cards (hgb, scale=yes) sent it into hgb's hyper variants, where
hgb,0.3,yes,onehot,balanced beat anything on A's static grid. Contrast: pool_trees_1 tie, skipped;
pool_trees_2 success actor-b. Module: modules/context.md - the only file whose text differs. Bug localised.
Patch: modules/context.md <- actor-b's text; gate on the private split of pool_trees_2: before 0.8737,
after 0.879 -> keep, landed as gen_001. Actor A now runs the obey-memory policy; the other four modules are
untouched word for word.
[33 turns, 621 s]
```

What to notice: the two actors' logs on pool task 1 are identical (no cards
yet, and `obey-memory` with no applicable card is the static order), so the
contrast is decided by one task; that is what the pool is for, and the
verifier wrote the same cards into both packs so the only difference on
task 2 was the module.

**What the test proves.**

- contrast names `modules/context.md` and the winner (actor B, once the cards exist; pool task 1 is a tie), spends zero fits; the meta pack cannot fit (`test_contrast_names_the_differing_module_and_the_winner`).
- the patch touches exactly one module file, is validated on the pool task's private split (no eval-table run exists), and helps the loser on a fresh seed (`test_patch_touches_exactly_one_module_validated_on_the_pool_and_helps_the_loser`).
- the pool is disjoint from the curriculum and the exam (`test_pool_is_disjoint_from_the_curriculum`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The pool task's private gate; the module boundaries
  (`patches:`), the allow-list and the pool are the human's.
- **The hook.** The locked test.
- **What the script refuses.** A patch outside `modules/*.md`; a fit for the
  meta pack; a patch the private split scores lower (rolled back).
- **What is and is not self-modified.** One module file of one actor, with
  a snapshot. `SKILL.md`, `schema.json`, the verifier and the pool are not.

**Diff from 09.** Modules instead of one procedure; a pool instead of the
curriculum.

---

## Lesson 13: Recuris: memory as a skill package, with a working memory

**The idea.** Recuris (arXiv:2608.24876) keeps two memories: an experiential one - skill
cards, each for a situation - and a small working memory the actor rewrites
per run ("what I am doing, which cards apply"). Here the cards are markdown
files under `skill-memory/cards/` with front matter (`when` tags, one
`then`, `validated`, `horizon`), listed in `manifest.yaml`; the actor names
its situation with need tags (`small`, `categorical`, `imbalanced`,
`multiclass`) and `skill_memory.py --action need` selects every validated
card whose tags all hold - by the situation, never by recency - and rewrites
`working.md`. The meta pack turns one problem's log into ONE localised,
validated card update (`--action update`): the script refuses a `then` that
did not win its comparisons, snapshots the pack, keeps one file per card
and raises the card's `horizon`. The memory is git-native: files you can
diff. L4: persistent state revised from feedback under a validation rule
the human wrote.

**Rung.** L4. The validation rule is human.

**Files.**

```text
step_13_rsi_skill_memory/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-skills/
│   ├── SKILL.md, tools.md, schema.json, eval.md
│   ├── skill-memory/manifest.yaml, cards/onehot-for-categorical.md    the experiential memory
│   └── working.md                                                    the working memory, rewritten per run
├── .claude/skills/skill-memory-meta/         SKILL.md, tools.md
├── .claude/skills/adult-income-curriculum/
└── .agents/skills/...
```

**Build.**

`step_13_rsi_skill_memory/.claude/skills/adult-income-skills/skill-memory/cards/onehot-for-categorical.md`
- a card is a markdown file:

```markdown
---
name: onehot-for-categorical
when: [categorical]
then: encode=onehot
validated: true
horizon: 1
---
The pack arrived with one card: on tables with a categorical column, one-hot encoding beat ordinal on every comparison of the first curriculum problem.
```

`step_13_rsi_skill_memory/.claude/skills/skill-memory-meta/SKILL.md` - one update, validated first:

```markdown
## Procedure
3. Take the first field of `model`, `class_weight`, `encode`, `scale` whose winning value the situation's card does not already hold (a card holds one `then`; a card "for the situation" is one whose `when` tags all hold for this need). Update once, with the existing card's name when the situation has one for that field, else a new name (`<value>-for-<tag>`):
   `python ../tools/skill_memory.py --pack P --task T --action update --as M --card <name> --then <field>=<value> --when <tag,tag> --body "<one sentence: what the log showed>" --visit <n>`
   The script refuses an update whose `then` did not win its comparisons on this problem, keeps one file per card, snapshots the pack under `runs/adult-income-skills/versions/` first, raises the card's `horizon` (the number of problems it was updated on), and refuses a second update in the same visit.
```

`tools/skill_memory.py` - selection by need, and the validation rule:

```python
    if a.action == "need":
        require_tool(run.pack_dir, "skill_memory")
        need = [t.strip() for t in (a.need or "").split(",") if t.strip()] or need_tags(run.profile)
        chosen = [c for c in skill_cards(run.pack_dir) if c.get("validated") and set(c.get("when", [])) <= set(need)]
```

```python
    rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]} for r in run.fit_rows()]
    wins, losses, _ = memory.tally(rows)
    if wins.get((field, value), 0) <= losses.get((field, value), 0):
        raise ValueError(f"not validated: {a.then} did not win its comparisons on {run.problem} "
                         f"({wins.get((field, value), 0)} wins, {losses.get((field, value), 0)} losses); nothing lands")
```

**Run.** Open your agent in `step_13_rsi_skill_memory/` and type:

```text
Use the adult-income-curriculum skill: run the six curriculum problems with the skill-memory meta pack updating one card after each, then the exam, and report the curve, the exam and each card's horizon.
```

The commands the agent runs:

```bash
python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action tags
python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action need --need categorical,imbalanced
python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action update --as .claude/skills/skill-memory-meta --card hgb-for-categorical --then model=hgb --when categorical,imbalanced --body "hgb won 6 of 6 comparisons on adult_income" --visit 1
```

**See.** The recorded run (Claude Code 2.1.278, headless, 70 turns, 1460 s; the
arms' fit calls trimmed to the agent's notes and the tables):

```text
[Skill adult-income-curriculum]
agent> Problem 01, memory arm: need tags small? no (6000 rows); categorical, imbalanced.
$ python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action need --need categorical,imbalanced
{"need": ["categorical", "imbalanced"], "cards": [{"name": "onehot-for-categorical", "when": ["categorical"], "then": "encode=onehot", "horizon": 1}], "prefer": {"encode": "onehot"}, "working": ".../working.md"}
... (the probe, then the hgb family; FREEZE; score once; scorecard) ...
$ python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json --action update --as .claude/skills/skill-memory-meta --card hgb-for-categorical-imbalanced --then model=hgb --when categorical,imbalanced --body "hgb won every model comparison on adult_income" --visit 1
{"card": "hgb-for-categorical-imbalanced", "file": "skill-memory/cards/hgb-for-categorical-imbalanced.md", "horizon": 1, "version": "gen_001", "new": true, "wins": 16, "losses": 0}
agent> Meta updates, one per visit (card -> horizon):
| 1 | adult_income | new hgb-for-categorical-imbalanced (model=hgb), gen_001 |
| 2 | breast_cancer | new hgb-for-small (model=hgb), gen_002 |
| 3 | wine | nothing - all 24 fits tied at 1.0, tally had 0 wins / 0 losses |
| 4 | digits | new hgb-for-imbalanced-multiclass (model=hgb), gen_003 |
| 5 | synth_shift_a | hgb-for-small updated -> model=logreg, when small,categorical, gen_004 |
| 6 | synth_shift_b | new none-for-small-categorical-imbalanced (class_weight=none), gen_005 |
$ python ../tools/curve.py --pack .claude/skills/adult-income-skills --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      0/0/0
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       0/0/0
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/0
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       0/0/0
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       0/0/0
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      0/0/0
agent> never_negative: true; wasted fits total 6 (memory) vs 33 (control).
Final horizons (skill_memory.py --action list): onehot-for-categorical [categorical] encode=onehot - 1;
hgb-for-categorical-imbalanced [categorical, imbalanced] model=hgb - 1; hgb-for-small [small, categorical]
model=logreg - 2; hgb-for-imbalanced-multiclass [imbalanced, multiclass] model=hgb - 1;
none-for-small-categorical-imbalanced [small, categorical, imbalanced] class_weight=none - 1.
$ python ../tools/exam.py --pack .claude/skills/adult-income-skills --task ../tasks/07_exam.json --seeds 0,1,2,3,4
exam: memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap 0.0306; pack unchanged: False; no card written: True
agent> pack_unchanged did not hold as printed (False). The per-boot checksums show the only differing file is
working.md, rewritten by skill_memory.py --action need on the seed-0 memory arm (step 2 of the actor's
procedure). All cards, the manifest and every other pack file are identical across all 10 exam boots; no
card changed. The check flags the actor's own working-memory rewrite, not a change to the memory.
agent> Report names every applicable card that did not transfer - the script reported cards_applicable: []
and did_not_transfer: [] (its card-transfer check reads memory.json cards, not the skill-memory cards), so it
named none. By my reading of the log, two selected cards did not transfer: hgb-for-small (model=logreg -
logreg lost every probe on all 5 seeds; hgb won) and onehot-for-categorical (ordinal beat onehot on seed 0,
where the memory arm lost).
[70 turns, 1460 s]
```

What to notice, honestly: the memory arm reaches the static grid's answer
in 6 wasted fits over the curriculum where the grid needs 33 - the best
figure in the series - because a selected card's `then` goes straight into
the probe; the val gaps are lesson 07's except breast cancer (0 here: the
skill memory had one card, `encode=onehot`, which is a no-op on a table
without categoricals, so the probe ran the default order). The agent
caught two things the scripts got wrong at recording time, and both are
fixed on this page's account: `exam.py` flagged `working.md` - the actor's
own scratch, rewritten by design - as a pack change (it now ignores it,
like lesson 11's `plan.json`), and its "did not transfer" check reads
`memory.json` cards only, so for a skill package it names none; the agent
read the exam log and named `hgb-for-small` (updated to `model=logreg` on
problem 5 and wrong on every exam seed) and `onehot-for-categorical` (wrong
on seed 0). `curve.py`'s cards columns read `memory.json` too and show 0
for this pack; the horizon list above is the card report. The updated
card is the honest one: `hgb-for-small` flipped to `logreg` on the linear
synthetic table and misled the exam - a horizon of 2 is two problems, not
two agreeing problems.

**What the test proves.**

- a card is selected by the working-memory need, not by recency (a newer card for another situation is not selected) (`test_card_selected_by_need_not_recency`).
- an update is localised to one card file (+ manifest), validated before it lands, once per visit; the actor cannot update, the meta pack cannot fit (`test_update_is_localised_validated_and_once_per_visit`).
- over the curriculum the horizons grow, the gain per problem is never negative, and the curve is complete (`test_horizon_report_over_the_curriculum`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The validation rule (the value won its pairwise
  comparisons on this problem's log), written by the human; one update per
  visit; the actor may select cards and may not update them.
- **The hook.** The locked test.
- **What the script refuses.** An unvalidated `then`; a second update per
  visit; an update by the actor; a fit for the meta pack.
- **What is and is not self-modified.** One card file (and a manifest line
  for a new card) per problem, with a snapshot under `versions/`;
  `working.md` per run. `SKILL.md`, `schema.json` and the policy are not.

**Diff from 06.** `memory.json` becomes a directory of markdown cards plus a
working memory.

---

## Lesson 14: The Darwin Gödel Machine lineage: the agent's own source, behind an archive and a gate

**The idea.** The Darwin Gödel Machine (arXiv:2505.22954) keeps an archive of agent
variants with their benchmark scores, picks parents from the archive, and
lets an agent rewrite its own source; the framework paper's verdict on it
(SWE-bench 20 -> 50 %, *reported*) is that the archive and the parent rule
stayed human-fixed - autonomy attribution, not autonomy. This lesson builds
exactly that shape: the meta pack (`dgm-meta`) runs the current actor on a
fixed held-out benchmark (two synthetic tables no curriculum problem
uses), archives the variant with its held-out gain (`archive.py --action
add`), chooses the parent by score - ties to the older, never the latest by
default (`--action parent`, `restore` when it is not the latest) - and
proposes ONE rewrite of the parent's *source*: the `Search policy:` line of
`SKILL.md` and the `policy` field of `loop.json`, the two files `patches:`
allows. `approval: both`: the private gate decides keep-or-rollback first,
then the human sees the diff. A rewrite the gate rejected never runs and
never enters the archive. L5 flavour: the harness source is rewritten; the
archive rule, the gate and the benchmark stay human, and the page says which
files are self-modified and which are not.

**Rung.** L5 flavour. The archive rule, the gate and the benchmark are human.

**Files.**

```text
step_14_rsi_self_modifying/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/          + loop.json (policy field); the two self-modified files
├── .claude/skills/adult-income-verifier/
├── .claude/skills/dgm-meta/              SKILL.md (approval: both, patches: SKILL.md, loop.json), tools.md, held-out/{01,02}_pool_trees_*.json
├── .agents/skills/...
└── runs/adult-income/archive/            archive.json + one snapshot per variant   (after a run)
```

**Build.**

`step_14_rsi_self_modifying/.claude/skills/dgm-meta/SKILL.md`:

```markdown
---
name: dgm-meta
description: The Darwin Goedel Machine lineage - rewrite the actor pack's own source (its SKILL.md and loop.json), one generation deep, from a parent chosen in an archive of variants scored on a fixed held-out benchmark, behind the private gate and the human cycle. Use in rsi/step_14_rsi_self_modifying, one generation per visit.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: both
  patches: ["SKILL.md", "loop.json"]
---
# The Darwin Goedel Machine lineage: the agent's own source, with an archive of stepping stones

## Procedure - one generation
3. Choose the parent: `python ../tools/archive.py --pack M --task T --target P --action parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If `is_latest` is false: `python ../tools/archive.py --pack M --task T --target P --action restore --label <parent>`, then `python ../tools/read_pack.py --pack P --checksums`; you now stand on the parent.

## Rules
- One generation deep: a rewrite of the parent, never of a rewrite that has not run the benchmark.
- A variant that lowered the held-out score is in the archive with its score; the parent rule never picks it over a better one. A rewrite the gate rejected never runs and never enters the archive.
```

`tools/archive.py` - the held-out gain and the parent rule:

```python
            best = max(mine, key=lambda r: r["val_score"])["recipe"]
            base = max(control, key=lambda r: r["val_score"])["recipe"]
            gains[task["name"]] = round(tasks.score_on(task, a.seed, best, "private") - tasks.score_on(task, a.seed, base, "private"), 4)
```

```python
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
```

`tools/patch_pack.py` - `approval: both`, the gate then the human:

```python
        if mode == "both":
            proposals.save(path, record)
            run.log("gate_kept", proposal=record["id"], version=label, gate=verdict)
            return {"id": record["id"], "decision": None, "gate": verdict, "landed": "pending", "version": label, "diff": diff,
```

**Run.** Open your agent in `step_14_rsi_self_modifying/` and type:

```text
Use the dgm-meta skill for generation 1: run the current actor on the held-out benchmark, archive it, choose the parent, and propose the rewrite of its source.
```

The commands the agent runs:

```bash
python ../tools/archive.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --action add --label gen1-static --held-out .claude/skills/dgm-meta/held-out --seed 1
python ../tools/archive.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --action parent
python ../tools/patch_pack.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --files @runs/dgm-meta/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "gen2: obey-memory from gen1-static" --visit 1
```

**You will be asked** after the gate kept the rewrite: approve / edit /
reject. Then the agent runs
`python ../tools/patch_pack.py ... --proposal g1 --approved "<your words>"`.
A "no" rolls the pack back to the snapshot the gate landed on.

**See.** The recorded run (Claude Code 2.1.278, headless, 27 turns + 3, 436 s + 39 s;
the benchmark's fit calls trimmed to the agent's notes):

```text
[Skill dgm-meta]
$ python ../tools/archive.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --action list
{"action": "list", "variants": [], ...}
agent> Empty archive. Step 1, held-out task 1, control arm: ... FREEZE. Best val: hgb,0.1,yes,ordinal,none = 0.9331.
agent> Control arm on task 1 done (val 0.9331, test 0.9093). Now the memory arm on task 1, seed 1. The pack's
policy is static, so read_memory --order static gives the next eight. No cards, policy static -> the memory
arm walks the static list too.
agent> My tally matches the script's (class_weight: balanced 10-2; encode 6-6 tie; model: hgb 16, rf 8-8,
logreg 0-16; scale: no 4-0; no hyper pairs, no errors). Writing the six cards in one call.
agent> Task 1 complete (verifier: 6 cards written, 6 new, 0 demoted). Now task 2, control arm: best val
hgb,0.1,yes,onehot,balanced = 0.8837. Now the memory arm on task 2. Three cards apply now, but the pack's
policy is still static, so the walk is unchanged by them.
agent> Step 1 done: both arms and the verifier on both tasks (verifier task 2: 8 cards, 2 new, 1 demoted -
scale=no was contradicted). Step 2, archive the current variant:
$ python ../tools/archive.py ... --action add --label gen1-static --held-out .claude/skills/dgm-meta/held-out --seed 1
{"action": "add", "label": "gen1-static", "variants": [{"label": "gen1-static", "problem": "pool_trees_2", "held_out": 0.0, "parent": null, "policy": "static"}]}
agent> Held-out score 0.0, as expected - a static memory arm walks exactly the control's path. Step 3, choose the parent:
$ python ../tools/archive.py ... --action parent
{"parent": "gen1-static", "held_out": 0.0, "latest": "gen1-static", "is_latest": true, "policies_in_archive": ["static"]}
agent> Parent gen1-static, is_latest true -> no restore needed. policies_in_archive = [static], so the rewrite
is obey-memory. Step 4: writing both files under runs/dgm-meta/patch/. Evidence recipe: the memory arm's best
val recipe on T was hgb,0.1,yes,onehot,balanced. Submitting the patch to the private gate:
$ python ../tools/patch_pack.py ... --files @runs/dgm-meta/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "gen2: obey-memory from gen1-static" --visit 1
{"id": "g1", "decision": null, "gate": {"before": 0.8737, "after": 0.8737, "keep": true}, "landed": "pending", "version": "gen_001", "diff": "--- a/SKILL.md ... -   Search policy: static\n+   Search policy: obey-memory ... --- a/loop.json ... -  \"policy\": \"static\",\n+  \"policy\": \"obey-memory\", ...", "next": "The gate kept it. Show the diff to the user, ask approve / edit / reject ..."}
agent> The private gate kept the rewrite (proposal g1, before 0.8737 -> after 0.8737, keep: true). Per the
skill, I now need your verdict before it lands.
[27 turns, 436 s]
=== user> approve
$ python ../tools/patch_pack.py ... --proposal g1 --approved "approve"
{"id": "g1", "decision": "y", "landed": true, "version": "gen_001", "files": ["SKILL.md", "loop.json"], "approved_by": "human", "words": "approve"}
$ grep -n "Search policy:" .claude/skills/adult-income/SKILL.md && grep -n '"policy"' .claude/skills/adult-income/loop.json
26:   Search policy: obey-memory
6: "policy": "obey-memory",
agent> Generation 1 is complete. Landed: proposal g1 - approved_by: human, words "approve", version gen_001,
files SKILL.md + loop.json. Archive after this generation: gen1-static | static | held-out 0.0 | parent -.
The rewritten pack (obey-memory from gen1-static) is not in the archive yet - per the one-generation-deep rule
it enters only after it has run the benchmark. That's the next visit: generation 2 ... With three active cards
(model=hgb, class_weight=balanced, encode=ordinal), the memory arm should probe hgb first this time rather
than spending 16 fits on logreg and rf.
[3 turns, 39 s]
```

What to notice, honestly: generation 1's held-out score is 0.0 by
construction (a `static` memory arm walks the control's path), and the gate
kept the rewrite on a tie (0.8737 = 0.8737: the evidence recipe *is* the
incumbent on generation 1). The lesson's claim is not that the rewrite wins;
it is that the rewrite goes through an archive with a score, a parent rule
that ignores recency, a gate, and a human - and that `SKILL.md` and
`loop.json` are the only files it may touch. The test shows the parent rule
skipping a newer, worse variant and the gate rolling back a rewrite whose
evidence recipe scores lower.

**What the test proves.**

- the archive holds every variant with its held-out score; the parent is chosen by score, not recency (a newer, worse variant is skipped); restore works (`test_archive_holds_every_variant_and_the_parent_is_by_score_not_recency`).
- a rewrite whose evidence recipe scores lower on the private split is rolled back and never archived (`test_rewrite_that_lowers_the_private_score_is_rolled_back_and_never_archived`).
- only `SKILL.md` and `loop.json` change; the human comes after the gate and a "no" rolls back; the meta pack cannot score (`test_only_skill_and_loop_are_self_modified_and_the_human_comes_after_the_gate`).
- the held-out benchmark is disjoint from the curriculum and the exam (`test_held_out_is_disjoint_from_the_curriculum`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The gate first (the private split of the last
  held-out task), then the human; the archive rule (best score, ties to the
  older), the benchmark and the one-generation-deep rule are the human's.
- **The hook.** Blocks the second `patch_pack.py` call without the user's
  words; the locked test.
- **What the script refuses.** A patch outside `SKILL.md` / `loop.json`; a
  rewrite the gate scores lower (rolled back, never archived); `archive add`
  without both arms on the benchmark; a fit or a test score for the meta pack.
- **What is and is not self-modified.** `SKILL.md` and `loop.json` are - the
  harness source. `schema.json`, `memory.json` (the verifier's), the
  verifier, the archive rule and the benchmark are not.

**Diff from 09.** The harness source is the patch target; an archive with a
parent rule.

---

## Lesson 15: AIDE²: autoresearch on autoresearch, keep-if-better across the set under one budget

**The idea.** AIDE² (Weco AI, July 2026; tech report announced, code not released -
every number about it here is *reported*) has an inner agent that searches a
tree of solutions with three operators - draft, debug, improve - and an
outer loop that rewrites the operator text and keeps the rewrite only if it
beats the previous version across the whole heterogeneous set under a fixed
cost budget. Here the inner pack (`adult-income-aide`) runs the curriculum
as version `v1` under `operators.md`; the outer pack (`aide-outer`) rewrites
the `improve` operator (expand the best solution -> expand the top three),
lands it at once under `approval: metered`, runs the curriculum again as
`v2`, and `meter.py --decide` applies the rule: per problem `v2 - v1` on
best val, a statistical layer that discards a gain more than 3 MADs above
the median (one lucky problem cannot carry the decision), keep only if the
remaining total is positive and it loses on at most half the problems -
else roll back. Three guards stay in every operator: the anti-overfitting
line (`lint_pack` refuses an operator without it), the re-run of a
suspicious score (`fit_recipe.py` flags `suspicious: true` at >= 0.999 or a
jump > 0.2, and the review operator fits it again), and the statistical
layer. The budget is metered in fits and script calls; there is no token
count, because no harness sees the agent's transcript, and the script says
so. L5 flavour: the improver rewrites the inner agent's procedure; the
budget, the guards and the task set stay human.

**Rung.** L5 flavour. The budget, the guards and the task set are human.

**Files.**

```text
step_15_rsi_aide2/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-aide/         SKILL.md (policy aide-tree), tools.md, schema.json, operators.md, memory.json, memory.schema.json, eval.md
├── .claude/skills/adult-income-verifier/     reads --of v1 / v2
├── .claude/skills/aide-outer/                SKILL.md (approval: metered, patches: operators.md), tools.md
└── .agents/skills/...
```

**Build.**

`step_15_rsi_aide2/.claude/skills/adult-income-aide/operators.md` - the operators, each with
its guard:

```markdown
## improve
Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.

## review
Review: the score of a solution is the `val_score` of its fit result, nothing else. A score at or above 0.999, or one that jumps more than 0.2 above the previous best in one fit, is suspicious - `fit_recipe.py` marks it `suspicious: true` - and is fitted again before it is believed (it costs a fit). A statistical layer at the outer loop discards outlier successes.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.
```

`tools/meter.py` - the outer rule as one function:

```python
def aide_keep(before, after, mad_k=3.0):
    """AIDE2's outer rule as one function. Returns (keep, detail)."""
    problems = sorted(set(before) & set(after))
    gains = {p: round(after[p] - before[p], 4) for p in problems}
    values = sorted(gains.values())
    median = values[len(values) // 2] if values else 0.0
    mad = max(sorted(abs(v - median) for v in values)[len(values) // 2] if values else 0.0, 0.01)   # a floor of one AUC point: rounding is not spread
    outliers = [p for p, g in gains.items() if g - median > mad_k * mad]
    kept = {p: g for p, g in gains.items() if p not in outliers}
    total = round(sum(kept.values()), 4)
    keep = bool(kept) and total > 0 and sum(1 for g in kept.values() if g < 0) <= len(kept) // 2
```

```python
    if budget[a.before] != budget[a.after]:
        raise ValueError(f"the budgets differ: {a.before} spent {budget[a.before]} fits, {a.after} {budget[a.after]}; not comparable")
```

`tools/fit_recipe.py` - the suspicious flag:

```python
    previous = [f["val_score"] for f in run.arm_state["fits"] if f["val_score"] is not None]
    if val is not None and (val >= SUSPICIOUS or (previous and val - max(previous) > JUMP)):
        row["suspicious"] = True
```

**Run.** Open your agent in `step_15_rsi_aide2/` and type:

```text
Use the aide-outer skill: run version v1 over the curriculum, propose the improve rewrite, run v2 under it, and decide keep-or-rollback across the set.
```

The commands the agent runs:

```bash
python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --of v1
python ../tools/patch_pack.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --files @runs/aide-outer/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "improve: top-1 -> top-3" --visit 1
python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --decide --proposal g1 --before v1 --after v2 --tasks ../tasks
```

**See.** The recorded run (Claude Code 2.1.278, headless, 45 turns, 1198 s; the
twelve arms' fit calls trimmed to the outer step):

```text
[Skill aide-outer]
agent> Task 06 v1: best val 0.8571, test 0.9104, 24 fits, 0 suspicious. Verifier: 10 written, 0 new.
Version v1 is complete - meter it.
$ python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --of v1
{"arm": "v1", "fits": 144, "calls": 203, "problems": ["adult_income", "breast_cancer", "digits", "synth_shift_a", "synth_shift_b", "wine"],
 "note": "cost = fits (the budget) + script calls (trace rows); no token count: no harness sees the agent's transcript"}
[Write runs/aide-outer/patch/operators.md]
agent> Land it with patch_pack.py, using v1's best recipe on T (hgb, 0.1, yes, onehot, balanced) as the evidence recipe:
$ python ../tools/patch_pack.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --files @runs/aide-outer/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "improve: top-1 -> top-3" --visit 1
{"id": "g1", "decision": null, "landed": "pending", "version": "gen_001",
 "diff": "--- a/operators.md ... -Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
+Improve: expand the top three solutions - fit their untried neighbours, one field away, nearest first. ...",
 "next": "Run the curriculum under the rewrite (a new arm), then: python ../tools/meter.py --decide --proposal g1 --before <old arm> --after <new arm> --tasks ../tasks"}
agent> (version v2 over the six problems, --arm v2, the verifier after each; the draft roots, then the untried
neighbours of the top three, until FREEZE)
$ python ../tools/meter.py ... --of v2 && python ../tools/meter.py ... --decide --proposal g1 --before v1 --after v2 --tasks ../tasks
{"arm": "v2", "fits": 144, "calls": 211, ...}
{"proposal": "g1", "keep": true, "decision": "y", "version": "gen_001", "budget": {"v1": 144, "v2": 144},
 "best_before": {"adult_income": 0.9172, "breast_cancer": 0.9966, "wine": 1.0, "digits": 0.999, "synth_shift_a": 0.9531, "synth_shift_b": 0.8571},
 "best_after":  {"adult_income": 0.9172, "breast_cancer": 0.9971, "wine": 1.0, "digits": 0.999, "synth_shift_a": 0.9531, "synth_shift_b": 0.8571},
 "gains": {"adult_income": 0.0, "breast_cancer": 0.0005, "digits": 0.0, "synth_shift_a": 0.0, "synth_shift_b": 0.0, "wine": 0.0},
 "outliers_discarded": [], "total_gain": 0.0005, "wins": 1, "losses": 0, "median": 0.0, "mad": 0.01}
agent> meter.py --decide has answered. Outer step complete.
Meter readings: v1 (improve = expand the best) 144 fits, 203 script calls, 6 problems; v2 (improve = expand
the top three) 144 fits, 211 script calls, 6 problems. Both arms spent exactly the same fits (24 x 6). The
cost is metered in fits and script calls only - there is no token count, because no harness sees this transcript.
Verdict: keep. Proposal g1 ("improve: top-1 -> top-3", version gen_001) is decided y, approved by the
metered rule: the total gain is positive and the rewrite lost on zero problems. operators.md stays as
rewritten; every operator kept its guard line word for word.
Worth knowing about the effect size: the top-3 rewrite changed the search path on every problem, but the
best-reached recipe only moved on breast_cancer (logreg C=0.25 found by expanding the logreg root, which
top-1 never got to). On wine every one of the 24 recipes scores 1.0, so each fit was flagged suspicious and
re-run once as the review operator requires - half the budget there goes to re-runs, in both arms alike.
Two v1 arms (wine, digits) were reset and rerun before any verifier or meter call touched them: my first
per-task driver re-ran a suspicious recipe more than once (wine) and mis-parsed a single-recipe fit result
(digits). Both reruns are the arms now on disk and in the meter; the botched traces were deleted.
[45 turns, 1198 s]
```

What to notice, honestly: the rewrite was kept on a total gain of +0.0005
from one problem (breast cancer) and five ties - the rule's floor is
"positive and not losing on more than half", and +0.0005 is positive. The
outlier layer had nothing to discard (median 0, MAD floored at 0.01). The
suspicious-score guard bit on wine as designed and cost half that
problem's budget in both versions alike, which is what "matched budget"
means. The agent wrote itself a per-task driver script (scratch, deleted)
to walk the operators, and when that driver misbehaved on two arms it
deleted their traces and re-ran them *before* any meter or verifier saw
them - a reset the page reports because the meter counts what is on disk.
AIDE²'s own reported numbers are not reproduced here and are not claimed.

**What the test proves.**

- keep-if-better is evaluated across every problem under one metered budget (both arms 144 fits), decided once, kept or rolled back (`test_keep_if_better_across_the_set_under_one_budget`).
- a rewrite that wins on one problem and loses on the set is rejected and `operators.md` restored (`test_a_rewrite_that_wins_on_one_problem_and_loses_on_the_set_is_rejected`).
- every operator carries the guard, lint refuses one without it, only `operators.md` may change, the outer pack cannot fit (`test_guards_in_every_operator_and_only_operators_may_change`).
- a suspicious score is flagged and re-run (the flag is in the trace) (`test_suspicious_score_is_flagged_and_rerun`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The metered rule, written by the human: the whole
  set, the same budget, the outlier layer. No human answers per rewrite;
  the human reads `runs/aide-outer/.../proposals/g1.json`'s `evaluation`.
- **The hook.** The locked test.
- **What the script refuses.** A decision before both arms ran every
  problem to FREEZE; unequal budgets; a second decision; a patch to any file
  but `operators.md`; an operator without its guard (lint); a fit for the
  outer pack.
- **What is and is not self-modified.** `operators.md`, one operator per
  outer step, snapshot first. The guards are checked, not editable away.

**Diff from 09.** Operators as the patch target; the decision after a whole
curriculum, not per problem.

---

## Lesson 16: MetaSkill-Evolve: the improver's skills improve too, slowly

**The idea.** MetaSkill-Evolve (arXiv:2607.05297) runs two timescales on one frozen
model: task skills evolve every problem, meta-skills every k problems, by
the same pipeline, with no extra model or objective. Here the fast loop
(`task-skills-meta`) is lesson 09's meta pack under the gate, but its
procedure's numbers live in five role files - `roles/analyzer.md`,
`retriever.md`, `allocator.md` (`Policy flip threshold: 2`), `proposer.md`
(`Cards per visit: 3`), `evolver.md` - and only the slow loop
(`meta-evolver`, `approval: human`, `patches: ["roles/*.md"]`, `k` in its
`config.json`) may change one line of one of them, every `k` problems, with
the human's word. The fast loop's own version history is a directory you can
diff (`runs/task-skills-meta/versions/`). This is the "and so on": the pack
that patches the pack is itself a pack with a version history, and its
changes are rarer and gated harder. L5 with the human on the slow clock.

**Rung.** L5, with the human on the slow clock.

**Files.**

```text
step_16_rsi_meta_skills/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/, adult-income-verifier/, adult-income-curriculum/
├── .claude/skills/task-skills-meta/          SKILL.md (approval: gate), tools.md, roles/{analyzer,retriever,allocator,proposer,evolver}.md
├── .claude/skills/meta-evolver/              SKILL.md (approval: human, patches: roles/*.md), tools.md, config.json {"k": 3}
└── .agents/skills/...
```

**Build.**

`step_16_rsi_meta_skills/.claude/skills/task-skills-meta/roles/proposer.md` and `roles/allocator.md`
- the numbers the fast loop uses are lines in files:

```markdown
# Role: proposer
One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
Cards per visit: 3
```

```markdown
# Role: allocator
Which task skill gets this visit, in order: the policy line, then a forbid, then cards.
Policy flip threshold: 2
```

`step_16_rsi_meta_skills/.claude/skills/meta-evolver/SKILL.md` - the slow loop:

```markdown
---
name: meta-evolver
description: The slow loop of MetaSkill-Evolve - every k problems, propose one change to one meta-skill file (roles/*.md) of the task-skills-meta pack, by the same evidence pipeline, and land it only with the human's approval. Use in rsi/step_16_rsi_meta_skills on the slow clock (k in config.json), never after every problem.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: human
  patches: ["roles/*.md"]
---
# The slow loop: the improver's own skills, rarely, with a human

## Procedure
1. Check the clock: the problem's index must be a multiple of `k`; otherwise say so and stop.
3. Judge the fast loop by that evidence: the number of active cards the last `k` problems added, and whether the memory arm's best val beat the control's on them. Decide ONE change, one file, one line:
   - the fast loop is adding cards but the gap is not growing: raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster);
   - the actor's policy line is still `static` after `k` problems: lower `Policy flip threshold` in `roles/allocator.md` by one;
   - otherwise nothing: say so and stop.
```

`tools/patch_pack.py` - a pack does not patch itself, and a meta pack
patches only what its front matter allows:

```python
    if Path(target).resolve() == run.pack_dir:
        raise ValueError("a pack does not patch itself: the target is another pack (the actor, or the fast loop's pack)")
```

```python
        if allowed and not any(fnmatch(name, pat) for pat in allowed):
            raise ValueError(f"this meta pack may patch {allowed} only, not {name}")
```

**Run.** Open your agent in `step_16_rsi_meta_skills/` and type:

```text
Use the adult-income-curriculum skill: run the six curriculum problems with task-skills-meta after each and meta-evolver every k problems, then the exam, and report the curve, the exam, the fast decisions and the slow decisions.
```

The commands the agent runs:

```bash
python ../tools/patch_pack.py --pack .claude/skills/meta-evolver --task ../tasks/03_wine.json --target .claude/skills/task-skills-meta --files @runs/meta-evolver/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=none --summary "proposer: Cards per visit 3 -> 4" --visit 1
python ../tools/patch_pack.py --pack .claude/skills/meta-evolver --task ../tasks/03_wine.json --target .claude/skills/task-skills-meta --proposal g1 --approved "<your words>"
```

**You will be asked** on problems 3 and 6 (k = 3), when the slow loop
proposes one role line, for example:

**See.** The recorded run (Claude Code 2.1.278, headless, three turns - 37 turns 652 s,
27 turns 1016 s, 1 turn 6 s; the arms' fit calls trimmed to the visits and
the tables):

```text
[Skill adult-income-curriculum]
agent> Verifier: 9 cards written, 9 new, 0 demoted (4 active). Now the fast visit (M) on problem 1.
agent> Rule (a) applies: policy is static and 4 >= 2 (flip threshold) cards are active. Writing the patched
SKILL.md with only the policy line changed, then proposing it.
agent> Fast visit 1: g1, gate 0.8951 -> 0.8951, kept, landed as gen_001. Problem 1 is not a multiple of k=3,
so no slow visit. On to problem 02 (policy line now obey-memory).
... problems 2 and 3: fast visits propose nothing ...
$ mkdir -p runs/meta-evolver/patch/roles && sed 's/^Cards per visit: 3$/Cards per visit: 4/' .claude/skills/task-skills-meta/roles/proposer.md > runs/meta-evolver/patch/roles/proposer.md && python ../tools/patch_pack.py --pack .claude/skills/meta-evolver --task ../tasks/03_wine.json --target .claude/skills/task-skills-meta --files @runs/meta-evolver/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=none --summary "proposer: Cards per visit 3 -> 4" --visit 1
{"id": "g1", "decision": null, "landed": false, "diff": "--- a/roles/proposer.md
+++ b/roles/proposer.md
@@ -2,2 +2,2 @@
 One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
-Cards per visit: 3
+Cards per visit: 4 ...", ...}
agent> The slow loop (meta-evolver) has a proposal pending and needs your decision before anything lands.
I'm stopping here as its SKILL.md requires.
Slow visit 1 (after problem 3, k=3) - proposal g1 on task-skills-meta, awaiting you: the fast loop added
15 cards over the last 3 problems but the gap isn't growing (0, +0.0012, 0), so its first rule fires:
raise Cards per visit. approve / edit / reject? Your exact words will be passed to patch_pack.py --approved.
[37 turns, 652 s]
=== user> approve
$ python ../tools/patch_pack.py --pack .claude/skills/meta-evolver --task ../tasks/03_wine.json --target .claude/skills/task-skills-meta --proposal g1 --approved "approve"
{"id": "g1", "decision": "y", "landed": true, "version": "gen_001", "files": ["roles/proposer.md"], "approved_by": "human", "words": "approve"}
agent> Landed as gen_001 of the meta pack; roles re-read (Cards per visit: 4, flip threshold 2). Problem 04 (digits).
agent> Fast visit 4: nothing applies (policy flipped, every value has wins, all rule cards already held).
Nothing proposed. Problem 05. ... Fast visit 5: nothing applies. Problem 06. ... Fast visit 6: nothing
applies. Problem 6 is a multiple of k=3 - slow visit 2.
agent> Slow visit 2: nothing - gap growing (0 -> +0.0024 -> +0.0646) and policy already obey-memory. Not asked.
$ python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
{"summary": {"gaps_val": [0.0, 0.0012, 0.0, 0.0, 0.0024, 0.0646], "wasted_memory_total": 20, "wasted_control_total": 33, "never_negative": true}}
$ python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap 0.0308; pack unchanged: True; no card written: True
$ python ../tools/read_pack.py --pack .claude/skills/task-skills-meta --checksums
{"versions": ["gen_001"], ...}      runs/adult-income/versions: gen_001    runs/task-skills-meta/versions: gen_001
agent> Done. Fast decisions (task-skills-meta, gate): problem 1 g1 static -> obey-memory, gate 0.8951 ->
0.8951, landed gen_001; problems 2-6 nothing proposed. Slow decisions (meta-evolver, k=3, human): problem 3
roles/proposer.md Cards per visit: 3 -> 4, "approve", gen_001 under runs/task-skills-meta/versions/;
problem 6 nothing (gap growing and policy already obey-memory), not asked.
Note: the raised Cards per visit never took effect in practice - rule (c) of the fast loop never fired,
because the verifier had already written every rule card before each fast visit.
[27 turns, 1016 s]
=== user> approve
agent> There's nothing pending to approve - the only slow-loop proposal (Cards per visit: 3 -> 4 after
problem 3) already landed with your earlier "approve" as gen_001 of the meta pack, and the second slow visit
(after problem 6) had nothing to propose, so no approval was requested.
[1 turns, 6 s]
```

What to notice, honestly: the two clocks are visible in the two `versions/`
directories - one generation of the actor (the policy flip, problem 1), one
generation of the meta pack (`Cards per visit: 3 -> 4`, problem 3, with the
human) - and the curve and exam are lesson 07's exactly, because the fast
loop's only effective change is the same policy flip and the slow loop's
change touched a rule that never fired afterwards (the verifier had already
written every card the fast loop would have merged). The improver's skill
changed, under a human, on the slow clock, and it made no difference to the
numbers: that is what happened, and the page says so rather than claiming
the "and so on" paid. The third headless turn was superfluous - the agent
had nothing pending and said so.

**What the test proves.**

- task skills change every problem and meta-skills only on the slow clock (counted from the versions and traces); the curve stays non-negative (`test_two_timescales_counted_from_the_traces`).
- a meta-skill change never lands without the human's yes; an edit or a yes lands one role line; the fast loop's version history is a directory you can diff (`test_meta_skill_change_never_lands_without_the_human`).
- the fast loop cannot touch `roles/` and the slow loop cannot touch the actor or fit (`test_fast_loop_cannot_touch_roles_and_slow_loop_cannot_touch_the_actor`).
- the fast loop boots what the slow loop wrote (`test_fast_loop_boots_what_the_slow_loop_wrote`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** The gate approves task-skill patches every
  problem; the human approves meta-skill patches every `k` problems, one
  line of one role file. The clock (`k`) and the role files' shape are the
  human's.
- **The hook.** Blocks the slow loop's second `patch_pack.py` call without
  the user's words; the locked test as always.
- **What the script refuses.** The fast loop patching `roles/` (not in its
  `patches:`) or itself; the slow loop patching the actor; a proposal off
  the clock (the skill), a landing without words (the hook and the script).
- **What is and is not self-modified.** The actor's task skills (fast), the
  fast loop's role files (slow). The slow loop's own `SKILL.md`, the clock
  and the human are not.

**Diff from 09.** The meta pack's numbers become files; a second, slower,
human-gated loop over them.

---

## Lesson 17: The map: the ladder, every recorded curve side by side, and who approved what

**The idea.** You recognise the nouns because you built the toy. This lesson is one
script and one skill: `map.py` prints the ladder of the framework paper
(arXiv:2609.11873) with lessons 00-16 placed on their rungs - the decision
the system takes and what stays human - then every lesson's learning curve
on the same curriculum side by side, read from the `curve.json` its
curriculum skill left (a lesson not run is named, never invented), then the
file-by-file table of what improved and who approved it, the six terms this
series uses on purpose, and every number quoted from elsewhere marked
*reported* with its source. ScienceBuddy (arXiv:2609.17523, harness then
weights) and OpenAI's stated priority are the rungs this series refuses to
touch: no weight update anywhere, and "genuine RSI" by the paper's bar is
not reached here - the map says so.

**Rung.** None: the map reads the other lessons. The acceptance test of the series is its last two columns - which decision moved to the system, and which stayed human.

**Files.**

```text
step_17_map/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/rsi-map/     SKILL.md, tools.md
└── .agents/skills/rsi-map/
```

**Build.**

`step_17_map/.claude/skills/rsi-map/SKILL.md`:

```markdown
---
name: rsi-map
description: Print the map of the rsi series - the ladder of rungs with lessons 00-16 placed, every recorded learning curve on the same curriculum side by side, the file-and-approver table, the terminology, and every external number marked reported - from the runs that exist. Use in rsi/step_17_map.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The map: you recognise the nouns because you built the toy

## Rules
- Print the numbers the script prints; every external number is *reported*, none is measured here.
- Do not run a lesson's curriculum to fill a gap in the table: say it is not run yet.
```

`tools/map.py` - the ladder, and the rule that a missing curve is named:

```python
LADDER = [
    ("not RSI (B0 / AutoML / harness engineering)", ["01", "02", "04"], "none: a fixed procedure", "everything"),
    ("L1  what to improve, how, success - specified by humans; AI executes a generation procedure", ["00", "03", "05", "08"], "renders a pack from task.json", "the spec, the acceptance (y / n / edit), the verifier contract"),
    ("L2  how to improve: the search strategy", ["10", "12"], "ranks policies on the log; names the module to patch", "the policy library, the module boundaries, the pool"),
    ("L3  which experience to acquire", ["11"], "picks the next experiments by uncertainty", "the uncertainty rule, the phase lengths"),
    ("L4  revise persistent state from deployment feedback under an acceptance rule", ["06", "07", "09 (human)", "13"], "writes and demotes cards; one patch per generation", "the verifier contract, the off switches, the human at the prompt"),
    ("L5 flavour  revise the improver / verifier / successor procedure itself", ["09 (gate)", "14", "15", "16"], "rewrites its own policy line, source, operators, meta-skills", "the gate, the archive rule, the budget, the clock, the human on the slow clock"),
]
```

```python
        if curve is None:
            lines.append(f"  {label:<18}  not run yet (run that lesson's curriculum skill)")
            continue
```

**Run.** Open your agent in `step_17_map/` and type:

```text
Use the rsi-map skill: print the map and tell me which lessons have a recorded curve.
```

The commands the agent runs:

```bash
python ../tools/map.py --lessons ..
```

**See.** The map on this machine, after the recorded runs of this series (the
`table` field of `map.py`):

```text
The ladder (arXiv:2609.11873): rung | lessons | the decision the system takes | what stays human
  not RSI (B0 / AutoML / harness engineering)
      lessons 01, 02, 04 | none: a fixed procedure | everything
  L1  what to improve, how, success - specified by humans; AI executes a generation procedure
      lessons 00, 03, 05, 08 | renders a pack from task.json | the spec, the acceptance (y / n / edit), the verifier contract
  L2  how to improve: the search strategy
      lessons 10, 12 | ranks policies on the log; names the module to patch | the policy library, the module boundaries, the pool
  L3  which experience to acquire
      lessons 11 | picks the next experiments by uncertainty | the uncertainty rule, the phase lengths
  L4  revise persistent state from deployment feedback under an acceptance rule
      lessons 06, 07, 09 (human), 13 | writes and demotes cards; one patch per generation | the verifier contract, the off switches, the human at the prompt
  L5 flavour  revise the improver / verifier / successor procedure itself
      lessons 09 (gate), 14, 15, 16 | rewrites its own policy line, source, operators, meta-skills | the gate, the archive rule, the budget, the clock, the human on the slow clock
Learning curves on the same curriculum (memory arm - control arm, best val, per problem):
  lesson               adult_income  breast_cancer           wine         digits  synth_shift_a  synth_shift_b  wasted m/c
  07 proof                  +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
  09 meta (gate)            +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
  10 Dream-RSI              +0.0000        +0.0012        +0.0000        +0.0005        +0.0024        +0.0646       34/33
  11 RSIAgent               +0.0000        +0.0000        +0.0000        +0.0000        +0.0000        -0.0270       27/33
  13 Recuris                +0.0000        +0.0000        +0.0000        +0.0000        +0.0024        +0.0646        6/33
  16 MetaSkill              +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
What improved, and who approved it:
  01 regular           nothing                                                                nobody (nothing changes)
  02 loop              nothing (loop.json is read, the audit log is never read back)          nobody
  03 loop writer       a whole loop pack is generated                                         the human: y / n / edit on the whole pack
  04 graph             nothing (graph.json and paths.json are mutable: false)                 nobody
  05 graph writer      a whole graph pack is generated                                        the human, after lint_pack; edit lands the human's graph
  06 RSI harness       memory.json (cards)                                                    the verifier contract, written by the human
  07 proof             memory.json over problems 1-6; nothing on the exam                     the evaluator is frozen: split, metric, seeds
  08 RSI writer        actor + verifier packs generated                                       the human approves the verifier contract explicitly
  09 meta harness      SKILL.md policy line, schema.json forbid, memory.json                  the human (approval: human) or the private gate (approval: gate); versions/ + rollback.py
  10 Dream-RSI         SKILL.md policy line, chosen by replay at zero fits                    the private gate; the policy library is fixed
  11 RSIAgent          plan.json per phase; memory.json after score_test only                 the uncertainty rule; memory frozen at test
  12 ModularRSI        one of modules/*.md                                                    the pool's private gate; the allow-list
  13 Recuris           one skill card (+ its manifest line)                                   the validation rule: the value won on this problem
  14 DGM lineage       SKILL.md and loop.json (the harness source)                            the archive rule, the private gate, then the human
  15 AIDE2             operators.md (one operator)                                            keep-if-better across the set under one metered budget (meter.py --decide)
  16 MetaSkill-Evolve  task skills every problem; roles/*.md every k problems                 the gate (fast clock); the human (slow clock)
Terminology:
  self-refine                a better answer this turn, nothing persists (B0). Lesson 01 with a smarter prompt would still be this.
  learning                   persistent state changes from feedback: memory.json after lesson 06. Necessary, not sufficient.
  self-organise / emergence  structure that nobody wrote appears; nothing in this series claims it.
  AutoML                     a fixed search over a fixed space: lessons 01-05, however fancy the graph.
  bounded RSI                the loop revises its own state or procedure inside limits a human set: lessons 06-16, every one with an off switch.
  genuine RSI                closed loops with persistence, transferred and attributed autonomy, verified inheritance under matched budgets - the paper's bar; not reached here, and said so.
Numbers quoted from elsewhere (every one *reported*, none measured here):
  reported: Headroom-Closed Index: advanced mathematics 86.4, graduate science 85.8, software engineering 52.6, search / terminal agents 56.8, tool agents 39.9 [arXiv:2609.11873v2]
  reported: Goedel Agent lost ground in 14 % of trials [arXiv:2609.11873v2, Challenge 1]
  reported: DGM raised SWE-bench 20 -> 50 % with a human-fixed archive and parent rule [arXiv:2609.11873v2 / arXiv:2505.22954]
  reported: A-Evolve-Training 0.80 -> 0.86 over four rounds [arXiv:2609.11873v2]
  reported: Recuris +32.2 on the longest tasks [arXiv:2608.24876]
  reported: AIDE2: seven successive improved versions in 100 outer steps, 16x context compression [Weco AI tech report, July 2026; code not released]
  reported: the tutorial's 162x, 71.97 -> 78.98, 47.57 -> 52.43, 8xA100 [the source tutorial; not in the papers' abstracts]
```

The recorded run (Claude Code 2.1.278, headless, 4 turns, 49 s; the table
above is what the script printed):

```text
[Skill rsi-map]
agent> Using the rsi-map skill: running map.py from the lesson directory.
$ python ../tools/map.py --lessons ..
{"ladder": [...], "curves": {...}, "not_run": [], "files": [...], "terms": [...], "reported": [...], "table": "..."}
agent> Six lessons have a recorded curve in runs/<pack>/curve.json: 07 proof, 09 meta (gate), 10 Dream-RSI,
11 RSIAgent, 13 Recuris, and 16 MetaSkill - all six problems present in each, no missing entries, and the
script's not_run list is empty. The remaining lessons (00-06, 08, 12, 14, 15) carry no curve because they
don't run the six-problem curriculum: 00-05 and 08 are generators or fixed procedures with nothing to plot,
and 06, 12, 14, 15 revise cards, modules, harness source or operators rather than producing a
memory-vs-control curve - so nothing there is "not run yet", it is simply not the kind of lesson the curve
table reads. Every figure outside the curve table is reported from its cited source, none measured here.
The series ends on the sentence the map itself states: genuine RSI by the paper's bar - closed loops with
persistence, transferred and attributed autonomy, verified inheritance under matched budgets - is not
reached here, and the map says so.
[4 turns, 49 s]
```

What to notice: the six curves agree on the lessons that share the
`obey-memory` policy flip (07, 09, 16: identical to the fourth decimal), and
differ exactly where the method differs - Dream-RSI's flipping line (34
wasted fits), RSIAgent's uncertainty rule (-0.027 on problem 6), Recuris's
card-first probe (6 wasted fits). `runs/` is git-ignored, so on a fresh
checkout the table names every lesson as not run yet until you run them.

**What the test proves.**

- the ladder places every lesson 00-16 on a rung, with the decision that moved and what stayed human; 09 sits on two rungs (`test_the_ladder_places_every_lesson_on_a_rung`).
- the side-by-side table reads each lesson's `curve.json` and names the lessons not yet run (`test_the_side_by_side_curve_reads_each_lessons_curve_and_names_the_missing`).
- every lesson 01-16 has a file-and-approver row (`test_every_lesson_has_a_file_and_an_approver_row`).
- the six terms are defined, and genuine RSI is marked as not reached (`test_the_six_terms_are_defined`).
- every external number is printed as *reported* with a source, and this page says so (`test_every_external_number_is_marked_reported_with_a_source`).
- the map changes nothing (`test_the_map_changes_nothing`).
- the pack contract (`test_pack_contract`).
- the recorded run reproduces (`RSI_LIVE=1`) (`test_live_claude_code`).

**Governance.**

- **Who approves what.** Nobody: the map reads and prints.
- **The hook.** Installed, idle.
- **What the script refuses.** Nothing to refuse; it invents no number - a
  lesson without a `curve.json` is listed as not run.
- **What is and is not self-modified.** Nothing. The acceptance test of the
  whole series is the ladder's last two columns: for every lesson, which
  decision moved to the system, and which stayed human.

**Diff from 16.** No pack changes anything; one script reads every lesson's `runs/`.

---

## Glossary

**The paper's terms** (arXiv:2609.11873, as this series uses them):

- **B0** - self-refinement: a better answer this turn with no persistent
  change. Excluded from RSI. Lesson 01 with a smarter prompt would still be
  B0.
- **L1** - humans specify what to improve, how, and what counts as success;
  the system executes a generation procedure and a human accepts. Lessons
  00, 03, 05, 08.
- **L2** - the system chooses how to improve: the search strategy. Lessons
  10, 12.
- **L3** - the system chooses which experience to acquire. Lesson 11.
- **L4** - the system revises persistent state from deployment feedback
  under an external acceptance rule. Lessons 06, 07, 09 (human), 13.
- **L5** - the system revises the improver, verifier or successor procedure
  itself. Lessons 09 (gate), 14, 15 as the L5 *flavour*; 16 with the human
  on the slow clock.
- **Structural recursion** - a revised mechanism governs a later round:
  generation n+1 boots what generation n wrote (lesson 09's boot checksums).
- **Effective recursion** - the successor is stronger under a comparable
  budget and an independent evaluation: the memory arm beats the control
  arm at the same budget on the curriculum and on the exam (lesson 07).
- **The three challenges** - *safe inheritance* (version histories,
  rollback, the archive), *autonomy attribution* (which decision moved and
  which stayed human: every lesson's Governance section, `patches:`,
  `tools.md`, the contract), *reliable verification* (a protected evaluator:
  the locked test, the private split, the exam never written to).
- **Bounded RSI** - a loop that revises its own state or procedure inside
  limits a human set, with an off switch: lessons 06-16. **Genuine RSI** -
  the paper's bar; not reached here, and said so.

**Ours:**

- **Pack** - a directory with `SKILL.md` (front matter, then the procedure
  the agent follows, each step an exact command) and sibling files
  (`tools.md`, `schema.json`, `memory.json`, `loop.json`, ...). The agent
  runs it; nothing else configures the agent.
- **Script** - one of `tools/*.py`: arguments in, one JSON object out, exit
  0 even on a refusal (`{"error": ...}`). Every rule a skill states that must
  hold absolutely is a refusal in a script.
- **Hook** - `hooks/gate.py`, installed by every lesson's
  `.claude/settings.json`: blocks `score_test.py` before FREEZE or twice and
  `apply.py` / `patch_pack.py --proposal` without the user's words, before
  the script runs. Agents without hooks get the script's refusal.
- **tools.md** - a pack's Allowed / Forbidden list; a script refuses to act
  for a pack whose `tools.md` does not allow it (`not in <pack>'s tools.md`).
- **Actor / verifier / meta pack** - the pack that fits (the inner pack),
  the pack that turns the log into cards without seeing the actor's
  messages, and the pack that patches another pack between two problems.
  A **writer** (03, 05, 08) is a meta pack whose output is a whole pack.
- **Card** - one typed entry of `memory.json`: IF a profile condition THEN
  prefer or forbid one field value, with `evidence` and `counter` counts. A
  card is active while its evidence is at least twice its counters; a
  forbid card makes `fit_recipe.py` refuse a recipe at no cost. Lesson 13's
  **skill card** is the markdown-file form of the same idea.
- **Approval cycle** - `propose.py` (or `patch_pack.py` stage 1) -> the
  agent shows the diff and asks -> `apply.py --approved "<the user's exact
  words>"` (or `patch_pack.py --proposal ... --approved`). The first word
  decides; anything unclear is a no; `edit` lands the user's version.
  `approval: human | gate | both | metered` in a meta pack's front matter
  says who answers.
- **Budget, FREEZE** - 24 fits per arm, counted in `state.json`; FREEZE is
  the moment the budget is spent (or `freeze.py` forfeits the rest), after
  which the test may be scored once and the memory may not change.
- **Arm** - one run of one pack on one problem and seed: the **memory arm**
  as the pack is, the **control arm** (`--arm control --memory off`) with no
  cards; lesson 15's version arms `v1`, `v2`. The curve is memory minus
  control, per problem.
- **Private split** - the fourth part of the one four-way split (train 55 %,
  val 15 %, private 10 %, test 20 %, one seeded shuffle): the gate's rows,
  which no actor arm ever sees. The **locked test** is the last fifth,
  scored once after FREEZE.
- **Profile** - the five keys a card may condition on (`n_rows`,
  `n_features`, `n_classes`, `imbalance`, `has_categorical`).
- **Curriculum, exam** - `tasks/01..06`, solved in order with the pack
  carried forward; `tasks/07_exam.json`, which no verifier ever wrote from,
  run with `--freeze-memory` over five seeds.
- **Wasted fits** - the fits an arm spent before its first recipe within
  0.005 of the bar (the control arm's best val); the cost half of every
  curve row.
- **Versions** - `runs/<pack>/versions/gen_NNN/`: a snapshot of the target
  pack with a checksum manifest before every patch lands, restored by
  `rollback.py`. Lesson 14's **archive** is the same idea with a held-out
  score per variant and a parent rule.
- **Trace** - `runs/<pack>/<task>/traces.jsonl`, append-only, one JSON line
  per boot, fit, card, proposal, gate verdict, rollback; the verifier reads
  pairs from it, Dream-RSI replays it, the tests assert from it, and who
  approved what is in it.
