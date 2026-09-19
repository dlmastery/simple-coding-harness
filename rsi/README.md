# Zero to Hero: Recursive Self-Improvement

## A hello world, skills only: make the agent's own files get better across runs, and prove it

**Status: complete.** Eighteen lessons (00-17), every one a skill pack
booted by one tiny skills harness in [`common/`](common/), with tests that
run without a key (`python run_tests.py rsi`: 84 tests, about four
minutes on this machine) and snippets checked against the code
(`python check_snippets.py rsi`). The plan of record is
[`OUTLINE.md`](OUTLINE.md) (v9, 19 Sep 2026). Layout and lesson format
follow the Claude Academy *AI-native SDLC playbook*: six stages, one lesson
per step, the same seven headings on every page.

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

**The headline, on this machine** (`FAKE_MODEL=1`, the scripted fake model,
seed 0; lesson 07): over the six curriculum problems the memory arm's best
validation score minus the `MEMORY_OFF` arm's at the same budget was
0 / +0.0012 / 0 / 0 / +0.0024 / +0.0646, with the memory arm reaching the
static grid's answer in 19 fits over the curriculum where the grid needed
33; on the exam problem the frozen pack beat `MEMORY_OFF` on 4 of 5 seeds
(mean test gap +0.031), and the report named two cards that did not
transfer. Wine and digits are saturated for this recipe space and teach
nothing; the pages say so.

## What you'll learn

By the end of this course, you'll be able to:

- Say, in the framework paper's terms, what is and is not recursive
  self-improvement - B0 self-refinement, AutoML, a harness you engineered by
  hand, a harness a meta skill generated - and name the rung (L1-L5) each one
  stands on.
- Engineer a harness as files: a loop with a counted budget and a freeze
  gate, a graph whose paths are recipes, and a meta skill that writes such a
  harness from an intent file under a human approval cycle.
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

## Who this course is for

Engineers who build agents with skills and want to know what "the agent
improves itself" means in files, tests and approvals, not slogans. It is a
hello world on purpose: no OSWorld, no GPUs, no weight updates.

## Prerequisites

Python 3.10+, `pip install -r requirements.txt` from the repo root
(scikit-learn, pandas, numpy, pyyaml, jsonschema); the root codelab's stages
4 (skills), 15 (`execute()`), 30 (evals) and 35 (approval prompts) are the
ideas reused here. Tests need no key; `python run.py` in a lesson runs the
scripted fake with `FAKE_MODEL=1` and a real model with `BASE_URL` /
`API_KEY` / `MODEL` like the rest of the repo. Every "Expected output" on a
lesson page is a real `FAKE_MODEL=1` run on this machine.

Estimated time: about an hour of reading; each lesson's run takes under a
minute.

## How to navigate

**Two orders.** The steps are numbered in build order: each one copies the
packs of the one before and changes one idea, so `diff -r` between two step
directories is the lesson. The course page groups the same steps by SDLC
stage, which is the reading order: Plan (00), Design (01, 02, 04), Build
(03, 05, 06, 08), Test (07), Deploy (09), Maintain (10-17). Read in stage
order the first time; come back in build order when you want the diff.

**Where the harness lives.** Nothing in a step directory is a loop. Every
step is packs under `skills/`, a `run.py` that boots them, a `test_step.py`
and a README. The mechanics are built once in `common/`:

```text
common/
  harness.py      boot(pack) -> SKILL.md body as system prompt, tools.md as the allowed set, siblings appended; run() is the stage-15 loop
  tools.py        the tool table: every tool a gate, execute() the one door; unknown / disallowed / malformed -> an `Error:` result
  fake.py         the scripted fake model: a rule table over the same pack files, so every claim is a test without a key
  approve.py      the approval cycle: propose -> show -> y / n / edit -> apply; HUMAN=script:... for a run without a terminal
  packs.py        read, lint, checksum, snapshot and roll back a pack; the verifier contract and the anti-overfit guard as constants
  budget.py       n fits, then it refuses; FREEZE is the budget being spent
  gate.py         the locked test: scored once, after FREEZE, a second call raises
  trace.py        the append-only JSON-lines log every fit, boot, card and verdict lands in
  memory.py       typed cards: validate, activate, demote, prefer, forbid
  curriculum.py   one problem, two arms, the sequence, the exam, the meta visit; the curve every lesson prints
  tasks.py        one task.json per problem under tasks/, the profile, the four-way split (train / val / private / test)
  data.py         the bundled Adult sample, the sklearn built-ins, the split
  synth.py        the seeded synthetic tables (problems 5, 6, the exam, the pool)
  recipe.py       the five-field recipe space and the one fit function
  graph.py        the DAG, a path as a recipe, why a path is illegal
  policies.py     the search policies a `Search policy:` line may name, as one ordering function
  scorecard.py    the fourteen fields every arm reports
  steps.py        the working copy under runs/work/, the step's task, the one-line scorecard
  checks.py       the claim checks a generated pack is held to (lesson 03 reuses 02's, 08 reuses 06's)
  task.schema.json  what a task.json may say; additionalProperties: false
```

The harness copies a pack from `skills/` into `runs/work/` before booting
it, so what you read under `skills/` is what the lesson shipped and what
you find under `runs/` is what the run left. `runs/` is ignored by git.

**Running things.** Every command below runs from the repo root unless it
starts with `cd`.

```bash
cd rsi/step_06_rsi_harness && FAKE_MODEL=1 python run.py      # one lesson, the scripted fake, no key
python run_tests.py rsi/step_06                               # one lesson's tests
python run_tests.py rsi                                       # every lesson's tests (84, about four minutes)
python check_snippets.py rsi                                  # every snippet on every lesson page exists in the code
cd rsi/step_07_proof && FAKE_MODEL=1 python run.py --curriculum   # problems 1..6 in order, the pack carried forward
cd rsi/step_07_proof && FAKE_MODEL=1 python run.py --exam         # the frozen pack on problem 7, five seeds
cd rsi/step_17_map && python run.py                           # the map, read from every lesson's curve.json
```

Lessons 09, 10, 11, 13, 14, 15 and 16 run the whole curriculum by
default (15 runs it twice, one lap per operator version); lesson 12 runs
its pool and one eval table; lesson 06 takes problem names as arguments
(`FAKE_MODEL=1 python run.py breast_cancer wine`); lessons 07 and 11 also
run the exam. The model is chosen by one function:

`common/harness.py`:

```python
def choose_model():
    """FAKE_MODEL=1 -> the scripted fake; otherwise the real model, which needs a key like the rest of the repo."""
    if os.environ.get("FAKE_MODEL") == "1":
        from common.fake import FakeModel
        return FakeModel()
    if not os.environ.get("API_KEY"):
        raise SystemExit("set BASE_URL / API_KEY / MODEL for a live run, or FAKE_MODEL=1 for the scripted fake")
    return openai_model()
```

**Approvals: what to type.** Every "generate" (03, 05, 08) and every
"improve" under `approval: human` (09, 10, 14, 15, 16's slow clock) goes
through `common/approve.py`. The meta pack calls `propose` or
`patch_pack`, the harness prints the whole pack (or a unified diff plus the
evidence recipe) between `--- proposal p1` and `--- end of proposal`, and
asks:

```text
  approve p1 (pack)? [y/n/edit]
```

Type `y` to land it as proposed, `n` to land nothing, or `edit`; after
`edit` the prompt reads `edit>` and you paste the edited payload as JSON on
one line - `{"SKILL.md": "...", ...}` for a pack, `{"files": {...},
"recipe": {...}}` for a patch - and the human's version is what lands.
Ctrl-C, end of input or invalid JSON count as `n`. For a run without a
terminal, script the answers: `HUMAN=script:y` or `HUMAN=script:y,n,y`, one
answer per prompt in order; when the answers run out every further prompt
is `n`. Under `approval: gate` (09, 12, 16's fast clock) there is no prompt
at all: the private split decides and the log shows the verdict.

`common/approve.py`:

```python
    @classmethod
    def from_env(cls):
        spec = os.environ.get("HUMAN", "")
        if spec.startswith("script:"):
            return cls([a.strip() for a in spec[len("script:"):].split(",") if a.strip()])
        return cls(None)
```

**The off switches.**

- `FAKE_MODEL=1` - the scripted fake instead of a model. Not an off switch
  for learning: the fake reads the same cards, policy line and files a real
  model would, which is why the tests can prove every claim without a key.
- `MEMORY_OFF=1` - the harness does not load `memory.json` (the prompt says
  so instead) and `write_card` refuses; the pack runs its static order with
  the same 24 fits. This is the control arm of every curve, and lesson 06's
  first test is that it reproduces lesson 01 exactly.
- `META_OFF=1` - lesson 09's `run.py` skips the meta visit after every
  problem; the actor's fixed files stay byte-identical and no version is
  made. It is read by lesson 09's `run.py` only; the method lessons 10-16
  run their meta visits unconditionally, and `n` at the prompt (or the
  gate's rollback) is their stop.
- `n` at any prompt; `rollback` to any `versions/gen_NNN`; the budget
  object (fit 25 is refused) and the locked test (a second `score_test` is
  refused) are always on.

**A real model.** Drop `FAKE_MODEL` and set `BASE_URL`, `API_KEY` and
`MODEL` like the rest of the repo (`MODEL` defaults to
`deepseek/deepseek-v4-flash`); the call goes through the `openai` package
and returns the same `{content, tool_calls}` shape as the fake. Without
`API_KEY` the run stops with the one-line message above. Every prompt then
asks you, unless `HUMAN=script:...` is set.

## Lessons

```text
rsi/
  OUTLINE.md                          the plan: definitions, format, steps, tests, tutorial validation
  common/                             the one skills harness, the tool table with execute(), the approval cycle, the fake model
  data/                               bundled Adult sample (6k rows) and how it was made
  tasks/                              the curriculum: one task.json per problem, in order, plus the exam
  Stage 1: Plan
  step_00_intent/                     task.json + acceptance.md: what to improve, how, what counts as success; lint_pack refuses a wider pack
  Stage 2: Design
  step_01_regular_harness/            a repeatable trainer: same SKILL.md every run, 24 fits, one test score - not RSI
  step_02_loop_harness/               loop engineering: loop.json, a counted while with a freeze; an audit log nothing reads
  step_04_graph_harness/              graph engineering with loops: graph.json + paths.json; an illegal path is skipped and counted
  Stage 3: Build
  step_03_meta_generates_loop/        a meta skill writes the loop pack; the human approves, edits or rejects; twice gives the same
  step_05_meta_generates_graph/       a meta skill writes the graph pack; lint kills cycles first; an edit removes an edge
  step_06_rsi_harness/                memory cards behind a verifier contract; MEMORY_OFF reproduces lesson 01 exactly
  step_08_meta_generates_rsi/         a meta skill writes actor + verifier; the human approves the contract first
  Stage 4: Test
  step_07_proof/                      one test score per problem, the learning curve over problems 1-6, the exam over 5 seeds
  Stage 5: Deploy
  step_09_rsi_meta_harness/           inner -> meta -> inner across the curriculum; approval: human | gate; versions + rollback
  Stage 6: Maintain
  step_10_rsi_dream/                  Dream-RSI: rank search policies on the trace log at zero fits; the log is silent elsewhere
  step_11_rsi_agent/                  RSIAgent: curriculum / actor / verifier, broad then deep, memory frozen before the test
  step_12_rsi_modular/                ModularRSI: five module files, contrast on a benchmark-disjoint pool, one module patched
  step_13_rsi_skill_memory/           Recuris: memory as a skill package + working memory; one validated card update per problem
  step_14_rsi_self_modifying/         DGM lineage: rewrites of SKILL.md / loop.json from an archive of variants scored held-out
  step_15_rsi_aide2/                  AIDE2: a tree-search inner agent; the outer loop keeps a rewrite only if better on the set
  step_16_rsi_meta_skills/            MetaSkill-Evolve: task skills every problem, the meta pack's own role files every k, with a human
  step_17_map/                        the ladder, every method's curve side by side, who approved what, the terms, the reported numbers
```

Steps are numbered in build order (each reuses the one before); the stage
grouping above is the reading order of the course page.

## The numbers, side by side

From [lesson 17](step_17_map/README.md), read from each lesson's run on the
real curriculum (memory arm minus `MEMORY_OFF` arm, best validation score,
per problem; `wasted m/c` is the fits the memory / control arm spent before
reaching the static grid's answer, summed over the curriculum):

```text
  lesson               adult_income  breast_cancer           wine         digits  synth_shift_a  synth_shift_b  wasted m/c
  07 proof                  +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  09 meta (human)           +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  09 meta (gate)            +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  10 Dream-RSI              +0.0000        +0.0012        +0.0000        +0.0001        +0.0000        +0.0646       29/33
  11 RSIAgent               +0.0000        +0.0000        +0.0000        +0.0000        +0.0000        -0.0270       27/33
  13 Recuris                +0.0000        +0.0000        +0.0000        +0.0000        +0.0024        +0.0646        6/33
  14 DGM                    +0.0000        +0.0012        +0.0000        +0.0000        +0.0000        +0.0000       33/33
  16 MetaSkill              +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
```

Three methods are reported on their own pages instead: ModularRSI patched
one module and the eval table went 0.7925 -> 0.8571 for both fake actors;
AIDE²'s operator rewrite lost 0.0001 on the set and was rolled back; the
DGM lineage's rewrites all scored below `static` on the held-out benchmark
and the archive says so. Every number quoted from a paper anywhere in the
series is marked *reported*.

## How the series is built

- `common/harness.py` boots a pack (`SKILL.md` body -> system prompt,
  `tools.md` -> the allowed set, sibling files appended) and runs the
  stage-15 loop; `common/tools.py` is the tool table, every tool a gate,
  `execute()` the one door. `common/fake.py` is a rule table over the same
  pack files, so every claim is a test without a key.
- Every step directory holds packs, `run.py`, `test_step.py` and a README
  with the same seven headings - never a Python loop of its own.
- `diff -r` between two steps shows exactly what became RSI.

## How to read a lesson

Every lesson section below has the same shape; every lesson README has the
seven playbook headings (concept, Getting started, How to execute it, What
it looks like, Governance considerations, How to measure it, Next lesson)
and says more than this page does.

- **The idea.** One sentence.
- **Rung.** Where the lesson stands on the paper's ladder, and what stays
  human.
- **Files that change.** The tree of what this lesson adds or edits, one
  line per file. Packs carried over unchanged are named in one line.
- **Build.** One or two snippets, quoted from the pack or the code, with
  the file named above each.
- **Run.** The command, bash and PowerShell, with the fake model.
- **See.** The recorded output of that run on this machine, as the lesson
  page records it.
- **What the test proves.** One line per claim, with the test's name.
- **What to notice.** What the numbers say, including where the method
  did not pay.

---

## Lesson 00: Intent - what to improve, how, and what counts as success

**The idea.** Before any pack exists, a human writes down what should get
better (`task.json`) and what evidence would prove it did
(`acceptance.md`), and nothing downstream may widen it.

**Rung.** The L1 precondition: the designer specifies the objective, the
procedure and the acceptance rule, and every later rung is measured by which
of those decisions moved to the system. Everything stays human here; no
model runs.

**Files that change.**

```text
step_00_intent/
  task.json         the intent: target, metric, budget, allowed models, test rule, profile keys
  acceptance.md     the scorecard fields and the pass rule, written before any pack exists
  run.py            validates both and shows lint_pack refusing a widened pack
  test_step.py      the claims below
common/task.schema.json   what a task.json may say; additionalProperties: false
tasks/01_adult_income.json .. 07_exam.json   the curriculum, one task per problem, problem 7 the exam
```

**Build.** `task.json` names the target, the metric, a budget of 24 fits
per arm, the allowed models, the locked-test rule (`scores: 1, after:
FREEZE`) and the profile keys a card may condition on. `acceptance.md` lists
the fourteen scorecard fields under `## The scorecard` and the pass rule
(you did not peek; the memory arm is at least the control arm on every
problem and wastes fewer fits; the frozen pack wins at least 3 of 5 exam
seeds). `run.py` reads the bullets back and compares them with the tuple the
code enforces.

`step_00_intent/run.py`:

```python
def acceptance_fields(path=HERE / "acceptance.md"):
    """The `- field` bullets under `## The scorecard`: the contract every later scorecard meets."""
    text = path.read_text(encoding="utf-8")
    section = text.split("## The scorecard")[1].split("## ")[0]
    return tuple(FIELD_LINE.findall(section))
```

`common/scorecard.py`:

```python
SCORECARD_FIELDS = (
    "problem", "arm", "seed", "n_fits", "fits_used", "wasted_fits",
    "best_val_score", "best_recipe", "test_score", "test_scored_once",
    "test_touched_before_freeze", "cards_active", "cards_added", "cards_demoted",
)
```

**Run.** No model, no key, no prompt.

```bash
cd rsi/step_00_intent
python run.py
```

```powershell
cd rsi\step_00_intent
python run.py
```

**See.**

```text
task.json valid: adult_income - Adult Census Income (> 50k); metric roc_auc; budget 24 fits per arm
acceptance.md names 14 scorecard fields; matches common/scorecard.py: True
lint_pack on step 01's pack: ok
lint_pack on a pack with n_fits 48: ['schema.json n_fits 48 != task budget 24']
lint_pack on a pack with two test scores: ["schema.json test_rule differs from the task's"]
```

**What the test proves.**

- `task.json` validates against the schema (`test_task_json_validates_against_the_schema`).
- A widened task - budget, test rule, an extra field - is rejected (`test_a_widened_task_is_rejected`).
- Every curriculum task validates, in order, with the same budget and test rule (`test_every_curriculum_task_validates_and_is_in_order`).
- A pack that raises the budget or touches the test rule, the metric or the models is rejected by `lint_pack` (`test_lint_pack_rejects_a_raised_budget_or_a_touched_test_rule`).
- The acceptance fields are exactly the scorecard fields every later step reports (`test_acceptance_fields_are_exactly_the_scorecard_fields`).

**What to notice.** The two `lint_pack` refusals at the end are the whole
governance of the series in miniature: every pack a later lesson writes or
generates is linted against this file, so a writer or a meta pack cannot
buy a better number with a 25th fit or a second look at the test split. The
fourteen fields are the same ones every arm of every later lesson prints.

## Lesson 01: The regular harness - a repeatable trainer, and not RSI

**The idea.** A pack that trains the same way every run - 24 recipes in
schema order, best validation score, one test score, save, stop - is the
control arm of the whole series, and it is not RSI.

**Rung.** Not RSI: B0 / AutoML, a fixed procedure with no persistent
change. Everything stays human. This is where the machinery arrives - the
harness, `execute()`, the budget object, the locked test, the append-only
trace - so that everything later is a diff against this pack.

**Files that change.**

```text
step_01_regular_harness/
  skills/adult-income-regular/
    SKILL.md        the procedure: 24 fits in order, best val, score_test once, save_model
    tools.md        Allowed: load_splits, fit_recipe, score_test, save_model; Forbidden: the rest
    schema.json     the task, n_fits 24, the test rule, the recipe fields, the baseline and the 24 recipes
  run.py            boot the pack on Adult (FAKE_MODEL=1 or a real model)
  test_step.py      the claims below
common/harness.py, tools.py, budget.py, gate.py, trace.py   arrive here and never move into a step
```

**Build.** The front matter of `SKILL.md` names the pack and when it
triggers (`rsi: "off"`); the body is the system prompt. `tools.md` is the
allowed set: anything else the model calls is an `Error:` result it reads.
The harness runs the stage-15 loop and every call goes through one door.

`common/harness.py`:

```python
def run(session, model, max_calls=MAX_CALLS, user="Begin. Follow the procedure in your instructions."):
    """The loop. `model(messages, tool_schemas) -> {content, tool_calls}`; every call goes through execute()."""
    session.messages = [{"role": "system", "content": session.system}]
    resume(session, model, user, max_calls)
```

The budget is an object, and FREEZE is the moment it is spent:

`common/budget.py`:

```python
    @property
    def frozen(self):
        """FREEZE: every fit is spent. The test split may be scored once, the memory may not change."""
        return self.used >= self.n

    def spend(self):
        """Count one fit before it happens. An error still counts: a wasted fit is a fit."""
        if self.frozen:
            raise BudgetExhausted(f"budget of {self.n} fits used; fit {self.used + 1} refused")
        self.used += 1
        return self.used
```

**Run.**

```bash
cd rsi/step_01_regular_harness
FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_01_regular_harness
$env:FAKE_MODEL = "1"; python run.py
```

**See.** The bundled 6,000-row Adult sample, 28 model calls, about 15 s.

```text
Done. Best val 0.9172 with {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}; test 0.9034; 24 fits.
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
model calls 28; trace C:\Users\evija\simple-coding-harness\rsi\step_01_regular_harness\runs\adult-income-regular\traces.jsonl
```

**What the test proves.**

- The fake model follows `SKILL.md`: 24 fits in schema order, best-val pick, one `score_test` (`test_fake_follows_skill_md_24_fits_in_schema_order_best_val_one_test`).
- The 25th `fit_recipe` and the second `score_test` are `Error:` results (`test_25th_fit_and_second_score_test_are_error_results`).
- `score_test` before FREEZE is refused (`test_score_test_before_freeze_is_refused`).
- An unknown, disallowed or malformed tool call is an `Error:` result and the loop continues (`test_unknown_disallowed_malformed_calls_are_errors_and_the_loop_continues`).
- The trace is append-only (`test_trace_is_append_only`).
- The same pack twice gives the same log (`test_same_pack_twice_gives_the_same_log`).
- The pack is byte-identical after a run (`test_pack_is_byte_identical_after_a_run`).

**What to notice.** `wasted 16`: sixteen fits went by before the first
recipe within 0.005 of the arm's best - the eight logistic regressions and
the eight random forests of the static list. Run it again tomorrow and it
wastes the same sixteen. That number, 16 on Adult and 33 over the
curriculum, is what every RSI lesson is measured against.

## Lesson 02: Loop engineering - the loop is a file

**The idea.** The procedure moves from prose into `loop.json` - a counted
while with a named counter, a budget `N`, an exit sequence and an illegal
list - and the tools enforce what the file declares.

**Rung.** Harness engineering, not RSI. The audit log the pack writes is
never read back, and generation n+1 loads the same `loop.json`; a log that
is written and never read is not memory. Everything stays human.

**Files that change.**

```text
step_02_loop_harness/
  skills/adult-income-loop/
    SKILL.md        run loop.json as written; the illegal list is binding
    tools.md        Allowed: load_splits, fit_recipe, write_loop_log, score_test, save_model
    schema.json     the recipe fields, n_fits 24, the test rule, the baseline (the recipe list moved out)
    loop.json       counted_while, N 24, counter t, body, exit, illegal
    recipes.json    the 24 recipes the loop iterates over (middle hyper value, grid order)
  run.py            boot the pack on Adult; count the audit lines; checksum the pack
  test_step.py      the claims below
common/tools.py    + write_loop_log
common/packs.py    + lint_loop: kind, N against the task, error_still_counts, exit FREEZE then score_test
```

**Build.** The loop, the gate and the illegal moves in one file:

`step_02_loop_harness/skills/adult-income-loop/loop.json`:

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

The one new tool, and the sentence that matters in its docstring:

`common/tools.py`:

```python
@tool("write_loop_log", entry="object")
def write_loop_log(run, entry):
    """Append one audit line to loop_log.jsonl. Nothing reads it back: there is no tool that does."""
    with open(run.run_dir / "loop_log.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"problem": run.problem, "arm": run.arm, **entry}) + "\n")
    return "logged"
```

**Run.**

```bash
cd rsi/step_02_loop_harness
FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_02_loop_harness
$env:FAKE_MODEL = "1"; python run.py
```

**See.**

```text
Done. Best val 0.9172 with {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}; test 0.9034; 24 fits.
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
loop_log.jsonl: 24 lines, read back by: nobody; pack byte-identical after the run: True
```

**What the test proves.**

- `loop.json` is honoured by the tools: N fits in `recipes.json` order, the 25th fit and a pre-FREEZE `score_test` refused, the pack lints (`test_loop_json_is_honoured_by_the_tools`).
- The audit log is written (24 lines) and never read back - the only tool that touches it writes (`test_the_audit_log_is_written_and_never_read_back`).
- The pack is byte-identical after a run and no `memory.json` appeared (`test_pack_is_byte_identical_after_a_run`).
- Generation n+1 loads the same loop: two runs, one log (`test_generation_n_plus_1_loads_the_same_loop`).

**What to notice.** The same numbers as lesson 01, by construction: same
recipes, same order, same budget. What changed is who enforces the order.
Two entries of the illegal list - "reorder recipes", "a second while" - are
advisory (checked by the test, not by a tool), and the lesson page says so;
the other three are refused by `Budget.spend`, `LockedTest` and `execute`
whatever the model believes `N` is.

## Lesson 03: A meta skill generates the loop harness, under human approval

**The idea.** A pack whose output is another pack: `loop-writer` renders
lesson 02's pack from `task.json`, lints it, proposes it, and nothing lands
until a human answers `y`, `n` or `edit`.

**Rung.** L1: humans specify what, how and success; the system executes a
generation procedure; a human accepts. The spec and the acceptance stay
human. Two facts keep it below RSI: generating twice from the same
`task.json` gives byte-identical proposals, and running the generated pack
never changes it or reaches back to the writer.

**Files that change.**

```text
step_03_meta_generates_loop/
  skills/loop-writer/
    SKILL.md              read the task, render the template, lint, propose, apply if approved
    tools.md              Allowed: read_task, lint_pack, propose, apply; Forbidden: fit_recipe, score_test, save_model
    task.json             the intent of lesson 00
    template/SKILL.md     lesson 02's SKILL.md with {{name}}, {{title}}, {{metric}}, {{n_fits}} placeholders
    template/tools.md     lesson 02's tools.md
    template/schema.json  {{name}}, {{metric}}, {{n_fits}}, {{test_rule}}, {{models}}
    template/loop.json    lesson 02's loop with N = {{n_fits}}
    template/recipes.json {{recipes}}
  run.py                  generate -> approve -> run the generated pack on Adult
  test_step.py            the claims below
common/approve.py         the approval cycle arrives: propose -> show -> y / n / edit -> apply
common/tools.py           + read_task, lint_pack, propose, apply
```

**Build.** A proposal is decided the moment it is made and applied only on
request, only if approved; an `edit` replaces the payload with the human's
version before anything can land.

`common/approve.py`:

```python
    def propose(self, kind, payload, summary=""):
        pid = f"p{len(self.items) + 1}"
        proposal = {"id": pid, "kind": kind, "payload": payload, "summary": summary, "decision": None, "applied": False}
        self.items[pid] = proposal
        if not self.quiet:
            show(proposal)
        decision, edited = self.human.decide(proposal)
        proposal["decision"] = decision
        if decision == "edit":
            proposal["payload"] = edited     # the human's version is what may land
        return proposal
```

`common/tools.py`:

```python
@tool("apply", id="string")
def apply(run, id):
    """Land an approved proposal on the target pack. Refuses one the human answered n to, or never saw."""
    if not run.proposals.approved(id):
        raise ValueError(f"proposal {id} is not approved; nothing lands")
```

**Run.** Answer at the prompt, or script it.

```bash
cd rsi/step_03_meta_generates_loop
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 HUMAN=script:y python run.py
```

```powershell
cd rsi\step_03_meta_generates_loop
$env:FAKE_MODEL = "1"; python run.py
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y"; python run.py
```

**See.** The proposal - every file - is printed between the two marker
lines and is elided here.

```text
--- proposal p1: pack - a pack for adult_income from the template
### SKILL.md
---
name: adult-income-loop
description: Train a classifier for Adult Census Income (> 50k) by running the counted loop in loop.json over recipes.json. Generated from task.json by loop-writer.
...
--- end of proposal
Proposal p1 decided y: applied p1 (y) to adult-income-loop.
lint of the landed pack: ok
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
generated pack byte-identical after its run: True
```

**What the test proves.**

- The writer cannot call `fit_recipe`: not in its `tools.md`, so an `Error:` (`test_writer_cannot_fit`).
- The proposal is shown before anything lands; scripted `n` leaves the disk untouched (`test_proposal_is_shown_before_anything_lands_and_n_lands_nothing`).
- `y` lands exactly the proposal (`test_y_lands_exactly_the_proposal`).
- `edit` lands the human's text (`test_edit_lands_the_humans_text`).
- Generating twice from the same `task.json` gives byte-identical proposals (`test_generating_twice_gives_byte_identical_proposals`).
- The generated pack boots, passes lesson 02's checks, and running it changes none of its files (`test_generated_pack_boots_and_passes_step_02_checks`).

**What to notice.** The generated pack gives lesson 02's numbers exactly:
it is lesson 02's pack with the task's values filled in, and the template's
`"N": {{n_fits}}` means the writer cannot pick its own budget. Most "an
agent built an agent" demos stop exactly here, and the ladder says why it
is not RSI: no result of the generated pack's run ever reaches the writer.

## Lesson 04: Graph engineering with loops - the job is a DAG, a recipe is a path

**The idea.** The job becomes `graph.json` (nodes are legal operators,
edges are hard dependencies, `score_test` a sink that opens only after
FREEZE), a recipe is a path with bindings, and the loop walks the 24 paths
of `paths.json` with one rule for an illegal path: skip and count, never
repair, never invent.

**Rung.** Harness engineering, not RSI. Both files are `mutable: false`.
Everything stays human - but the whole search space is now a picture a
human can approve, which lesson 05 uses.

**Files that change.**

```text
step_04_graph_harness/
  skills/adult-income-graph/
    SKILL.md        walk paths[t] for t in 0..N-1; skip and count an illegal path; score_test after FREEZE
    tools.md        Allowed: load_splits, walk_path, score_test, save_model; fit_recipe is Forbidden
    schema.json     the recipe fields, n_fits 24, the test rule, the baseline
    graph.json      nodes, edges, constraints; mutable: false
    paths.json      24 paths (p00 = the baseline) with bindings; mutable through the graph's flag
    loop.json       counted_while over paths; illegal: add or repair a path
  run.py            boot the pack on Adult; count illegal paths; checksum the pack
  test_step.py      the claims below
common/graph.py    why_illegal, lint_graph, path_recipe
common/tools.py    + walk_path
```

**Build.** The one rule, in the pack and in the tool:

`step_04_graph_harness/skills/adult-income-graph/SKILL.md`:

```markdown
2. `counted_while` with counter `t` from 0 to `N` - 1: call `walk_path` with `paths[t].id`. The tool checks the path against the graph: a legal path fits the recipe its bindings form; an illegal one is skipped and still counts as a fit. You never repair a path and never invent one.
```

`common/graph.py`:

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

**Run.**

```bash
cd rsi/step_04_graph_harness
FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_04_graph_harness
$env:FAKE_MODEL = "1"; python run.py
```

**See.**

```text
Done. Best val 0.9172 with {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}; test 0.9034; 24 fits.
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
paths walked 24, illegal (skipped and counted) 0; graph.json and paths.json byte-identical after the run: True
```

**What the test proves.**

- The loop iterates the paths in order and the pack lints (`test_loop_walks_the_paths_in_order_and_the_pack_lints`).
- An illegal path is skipped and counted, never replaced; `paths.json` is not repaired (`test_illegal_path_is_skipped_and_counted_never_replaced`).
- `score_test` is unreachable before FREEZE: the sink's gate, and the locked test behind it (`test_score_test_is_unreachable_before_freeze`).
- `graph.json` and `paths.json` are byte-identical after a run (`test_graph_and_paths_are_byte_identical_after_a_run`).
- `fit_recipe` is not a way around the graph, nor is an invented path id (`test_fit_recipe_is_not_a_way_around_the_graph`).

**What to notice.** Same numbers a third time, and `fit_recipe` is now
Forbidden: the only way to spend a fit is a path the graph allows. Break a
path by hand in `runs/work/adult-income-graph/paths.json` (drop `"encode"`
from one path's `nodes`) and boot that copy: the path is skipped, the
budget still counts it, and the file is not repaired - the test does
exactly this.

## Lesson 05: A meta skill generates the graph harness, under human approval

**The idea.** Lesson 03's writer extended to six files, with `lint_pack`
walking the graph before any human sees it and the proposal showing the
graph as a node / edge list, so the interesting answer is `edit`: the
human removes an edge, and the human's graph is what lands.

**Rung.** L1. The writer never sees the run results of what it wrote, so
the edit never feeds back. Still no loop, still not RSI; but the acceptance
now covers a whole search space at once.

**Files that change.**

```text
step_05_meta_generates_graph/
  skills/graph-writer/
    SKILL.md              read the task, render six files, lint (loop + graph), propose, apply if approved
    tools.md              Allowed: read_task, lint_pack, propose, apply
    task.json             the intent of lesson 00
    template/SKILL.md     lesson 04's SKILL.md with placeholders
    template/tools.md     lesson 04's tools.md
    template/schema.json  lesson 03's schema template
    template/graph.json   lesson 04's graph, verbatim: the operators are not the writer's to choose
    template/paths.json   {{paths}}
    template/loop.json    lesson 04's loop with N = {{n_fits}}
  run.py                  lesson 03's generate -> approve -> run, pointed at graph-writer
  test_step.py            the claims below
common/approve.py         show() prints a graph.json as nodes and edges
common/graph.py           + lint_graph, run by lint_pack on any pack with a graph.json
```

**Build.** The lint that runs before the human is asked, and the `propose`
tool refusing a pack that does not pass it:

`common/graph.py`:

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
```

`common/tools.py`:

```python
    if kind == "pack":
        problems = lint_pack(run, payload)
        if problems != "ok":
            raise ValueError(f"lint_pack refuses this pack before the human sees it: {problems['problems']}")
```

**Run.**

```bash
cd rsi/step_05_meta_generates_graph
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 HUMAN=script:y python run.py
```

```powershell
cd rsi\step_05_meta_generates_graph
$env:FAKE_MODEL = "1"; python run.py
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y"; python run.py
```

**See.** The files of the proposal are elided.

```text
### graph.json as a graph
nodes: load, scale, encode, model, fit, score_test
edges: load -> scale; scale -> encode; encode -> model; model -> fit; fit -> score_test
### graph.json
...
Proposal p1 decided y: applied p1 (y) to adult-income-graph.
lint of the landed pack: ok
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
generated pack byte-identical after its run: True
```

**What the test proves.**

- `lint_pack` rejects a proposal with a cycle before the human ever sees it (`test_lint_rejects_a_cycle_before_the_human_sees_it`).
- `lint_pack` rejects a path that violates a constraint - a node twice, the sink reached (`test_lint_rejects_a_path_that_violates_a_constraint`).
- The human sees the graph as a node / edge list (`test_the_human_sees_the_graph_as_nodes_and_edges`).
- An `edit` that removes an edge lands and the pack still boots and runs (`test_an_edit_that_removes_an_edge_lands_and_the_pack_still_boots`).
- `y` lands a graph pack that passes lesson 04's checks (`test_y_lands_a_graph_pack_that_passes_step_04_checks`).

**What to notice.** The template's `graph.json` is lesson 04's verbatim:
the operators are not the writer's to choose, only the paths are rendered
from the task's allowed models. What the human is being asked to accept is
a search space, and that is exactly the shape of the question lessons 08
and 09 ask.

## Lesson 06: The RSI harness - the first file that changes because of what happened

**The idea.** Two packs: an actor that proposes one recipe at a time under
a search policy the cards shape, and a verifier that boots after the run
is frozen, sees only `{recipe, val_score, error, profile}` rows, and writes
typed cards into `memory.json` - the first file that changes because of
what happened.

**Rung.** L4: deployment feedback revises persistent state under an
acceptance rule a human wrote (the verifier contract). What stays human:
the contract, the card schema and the off switch. `MEMORY_OFF` is the off
switch: same pack, same 24 fits, no cards, and the numbers must fall back to
lesson 01's exactly.

**Files that change.**

```text
step_06_rsi_harness/
  skills/adult-income/
    SKILL.md            the actor: boot order, the search policy line, the off switch
    tools.md            Allowed: load_splits, fit_recipe, read_memory, score_test, save_model; write_card Forbidden
    schema.json         the recipe fields, n_fits 24, the test rule, the static list, a (still empty) forbid list
    memory.schema.json  the JSON Schema of a card: if / then / evidence / counter, nothing else
    memory.json         [] - the first RSI file
  skills/adult-income-verifier/
    SKILL.md            the contract line, the comparison rule, the card thresholds
    tools.md            Allowed: read_traces, write_card; fit_recipe and score_test Forbidden
    memory.schema.json  the same schema; write_card validates against this copy
  run.py                actor -> verifier per problem, both arms, the pack carried forward
  test_step.py          the claims below
common/memory.py        cards: validate, active, forbidden, preferred, compare, merge
common/tools.py         + read_memory, write_card, read_traces; fit_recipe refuses a forbidden recipe
common/curriculum.py    run_problem: actor then verifier on one problem, the scorecard
```

**Build.** The contract line is checked verbatim by `lint_pack`; the
procedure under it is the rule the fake model and a real one both apply.

`step_06_rsi_harness/skills/adult-income-verifier/SKILL.md`:

```markdown
# The verifier: no one grades their own homework

Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.
```

A card is typed, so a tool can enforce it, and it is demoted by its own
counterexamples:

`common/memory.py`:

```python
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

**Run.** Four small problems in a row, both arms; problem names may be
given; `MEMORY_OFF=1` is the off switch.

```bash
cd rsi/step_06_rsi_harness
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 python run.py adult_income breast_cancer
MEMORY_OFF=1 FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_06_rsi_harness
$env:FAKE_MODEL = "1"; python run.py
$env:MEMORY_OFF = "1"; python run.py
```

**See.** `mem` is the memory arm, `ctl` the `MEMORY_OFF` arm at the same
budget and seed; `wasted` counts fits before the arm reached the control
arm's best; `cards +/-/act` is cards activated / demoted / active. Two of
the eight card lines are shown.

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       1/0/1
 2 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/1
 3 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/0/6
 4 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      2/0/8
memory.json after 4 problems: 8 cards, 8 active
  {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "hgb"}, "evidence": 2, "counter": 0}
  {"if": {"key": "has_categorical", "op": "==", "value": 1}, "then": {"field": "encode", "prefer": "onehot"}, "evidence": 2, "counter": 0}
```

**What the test proves.**

- The verifier pack's transcript contains no actor text; its rows have the contract's keys only (`test_verifier_transcript_contains_no_actor_text`).
- `write_card` refuses a card mentioning `test` or `intent`, or carrying any extra field (`test_write_card_refuses_a_card_that_names_the_test_or_the_intent`).
- A planted wrong card is demoted after two counterexamples (`test_a_planted_wrong_card_is_demoted_after_two_counterexamples`).
- `fit_recipe` refuses a forbidden recipe, at no cost to the budget (`test_fit_recipe_refuses_a_forbidden_recipe`).
- Same seeds and budget: the memory arm is at least the `MEMORY_OFF` arm and wastes fewer fits (`test_memory_arm_beats_memory_off_at_the_same_budget`).
- `MEMORY_OFF` reproduces lesson 01's numbers exactly (`test_memory_off_reproduces_step_01_exactly`).

**What to notice.** On problem 1 the arms are identical (no card yet); by
problem 4 the memory arm reaches the static grid's best within 3 fits
instead of 17, and its own best is 0.065 higher on validation and 0.076
higher on the locked test, because the cards sent it to the `hgb` family
first and the freed budget explored that family's learning rates. Wine sits
at 1.0 for every recipe: ties teach nothing, and the verifier wrote nothing.
`runs/work/adult-income/memory.json` after the run is the whole difference
between the two arms.

## Lesson 07: Proof - the locked test, the learning curve, the exam

**The idea.** What would count as lesson 06's change being an improvement,
measured the way the paper's evidence bar demands: a test scored once after
FREEZE, a curve over problems 1-6 at a matched budget, and an exam on a
problem no verifier ever wrote from, the pack frozen, five seeds.

**Rung.** Not a rung: the evidence standard every later lesson reports.
The evaluator - split, metric, seeds, the exam problem - is the human's and
stays the same across generations (the paper's "freeze evaluators per
epoch"). This is Stage 4 (Test); `python run_tests.py rsi` is the
continuous eval.

**Files that change.**

```text
step_07_proof/
  skills/adult-income/          lesson 06's actor pack plus eval.md
    eval.md                     the comparison, the curve, the exam, the scorecard - read by the model at boot
  skills/adult-income-verifier/ lesson 06's verifier, unchanged
  run.py                        --curriculum: problems 1..6; --exam: problem 7 over five seeds
  test_step.py                  the claims below (the synthetic curriculum, once, shared by the tests)
  runs/curriculum/curve.json    (created by run.py) the curve rows; runs/exam/exam.json the exam report
common/curriculum.py            + run_curriculum (the MEMORY_OFF control arm on every problem), run_exam (frozen pack, five seeds, the did-not-transfer report)
```

**Build.** The model reads how it is judged:

`step_07_proof/skills/adult-income/eval.md`:

```markdown
## The comparison
- Two arms per problem, same seed, same split, same budget of 24 fits: the memory arm (this pack as it is) and the `MEMORY_OFF` arm (the same pack with `memory.json` not loaded, which is lesson 01's static walk).
- The test split is locked: scored once per arm, after FREEZE, never before. `test_touched_before_freeze` must be `no` on every scorecard.
- The delete-the-file check: deleting `memory.json` must give the `MEMORY_OFF` numbers exactly; a difference means something other than the cards changed.
```

The exam runner freezes the memory, counts a tie won on cost as a win, and
names what did not transfer:

`common/curriculum.py`:

```python
    for seed in seeds:
        control, _, _ = run_problem(pack_dir, exam_task, model, run_dir, seed=seed, arm="control", memory_off=True, memory_frozen=True, quiet=quiet)
        mem, inner, _ = run_problem(pack_dir, exam_task, model, run_dir, seed=seed, arm="memory", memory_frozen=True, quiet=quiet,
                                    bar=control["best_val_score"])
        gap = round(mem["test_score"] - control["test_score"], 4)
        results.append({"seed": seed, "memory": mem, "control": control, "gap_test": gap,
                        "gap_val": round(mem["best_val_score"] - control["best_val_score"], 4),
                        # a win: a higher test score, or the same score reached with fewer wasted fits (same budget)
                        "win": gap > 0 or (gap == 0 and mem["wasted_fits"] < control["wasted_fits"])})
```

```python
    did_not_transfer = [c for c in applicable if "prefer" in c["then"]
                        and sum(1 for b in best if b and b[c["then"]["field"]] == c["then"]["prefer"]) <= len(best) // 2]
```

**Run.** About 70 s with the fake model; the exam reuses the pack the
curriculum left in `runs/work/`.

```bash
cd rsi/step_07_proof
FAKE_MODEL=1 python run.py --curriculum
FAKE_MODEL=1 python run.py --exam
```

```powershell
cd rsi\step_07_proof
$env:FAKE_MODEL = "1"; python run.py --curriculum; python run.py --exam
```

**See.** The real curriculum, then the exam over seeds 0-4.

```text
learning curve (memory arm - MEMORY_OFF arm, same budget, same seed):
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/7
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       3/1/9
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    2/17      2/2/12
cards after problem 6: 15, active 12
exam exam: memory arm beats MEMORY_OFF on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap +0.0308; pack unchanged: True
  seed 0: memory test 0.865 val 0.8985 wasted 8 | control test 0.8661 val 0.8858 wasted 19 | gap -0.0011 loss
  seed 1: memory test 0.9057 val 0.9318 wasted 16 | control test 0.8077 val 0.9167 wasted 10 | gap +0.0980 win
  seed 2: memory test 0.9208 val 0.9131 wasted 4 | control test 0.9208 val 0.9131 wasted 17 | gap +0.0000 win
  seed 3: memory test 0.9314 val 0.887 wasted 5 | control test 0.9215 val 0.8766 wasted 18 | gap +0.0099 win
  seed 4: memory test 0.9352 val 0.9389 wasted 0 | control test 0.8881 val 0.9117 wasted 16 | gap +0.0471 win
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 0.1} (evidence 1, counter 0)
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 1} (evidence 1, counter 0)
```

**What the test proves.**

- The test is scored exactly once per problem and arm, never before FREEZE, on the curriculum and on the exam (`test_test_is_scored_exactly_once_per_problem_and_arm`).
- Every scorecard has exactly the fourteen fields; `eval.md` names them all (`test_every_scorecard_field_is_present`).
- Problems 1 to 6 carry the pack forward (the checksums of `memory.json` change); the gap is at least 0 on every problem and larger on 6 than on 2; the memory arm wastes fewer fits in total (`test_the_pack_is_carried_forward_and_the_learning_curve_grows`).
- On the exam the frozen pack beats `MEMORY_OFF` on at least 3 of 5 seeds, writes nothing, and the report names a card that did not transfer (`test_the_frozen_pack_beats_memory_off_on_the_exam`).

**What to notice.** Problems 3 and 4 are too easy for this recipe space
(every recipe scores 1.0 or 0.999): ties teach nothing, and the verifier
writes nothing on wine. Problem 5 is the superstition test - a linear signal
after tree-shaped ones; the memory arm's probe catches it (`wasted 1`) and
one card is demoted. Problem 6 is where the experience pays: the memory arm
reaches the static grid's best in 2 fits instead of 17 and ends 0.065
higher on validation, 0.076 higher on the locked test. The exam: four wins
of five (three on the test score, one on cost at the same score), one loss
of 0.001, and two hyper-parameter cards that did not transfer - named, not
hidden. This is the headline of the course page.

## Lesson 08: A meta skill generates the RSI harness, under human approval

**The idea.** The writer emits two packs - the actor with `memory.json`,
`memory.schema.json` and `eval.md`, and the verifier with its contract -
and what the human approves is a mechanism that will change itself later,
so the contract is printed first and `lint_pack` refuses a verifier without
it.

**Rung.** L1 for the generation; what it generates runs at L4. The paper's
attribution challenge in one prompt: the human is approving an improver,
not a result. After the `y`, cards land under the contract without a
prompt - that is the decision being delegated, and the summary says so.

**Files that change.**

```text
step_08_meta_generates_rsi/
  skills/rsi-writer/
    SKILL.md                      read the task, render two packs, lint both, propose, apply if approved
    tools.md                      Allowed: read_task, lint_pack, propose, apply
    task.json                     the intent of lesson 00
    template/actor/SKILL.md       lesson 07's actor with {{slug}}, {{title}}, {{n_fits}}
    template/actor/tools.md       lesson 07's actor tools
    template/actor/schema.json    {{name}}, {{n_fits}}, {{test_rule}}, {{models}}, {{recipes}}; forbid []
    template/actor/memory.schema.json  {{card_schema}}
    template/actor/memory.json    []
    template/actor/eval.md        lesson 07's eval.md
    template/verifier/SKILL.md    lesson 07's verifier, the contract line verbatim
    template/verifier/tools.md    read_traces, write_card
    template/verifier/memory.schema.json  {{card_schema}}
  run.py                          generate -> approve -> run both packs over two problems
  test_step.py                    the claims below
common/packs.py                   the multi-pack lint; VERIFIER_CONTRACT and the two rules that hold a verifier to it
common/approve.py                 show() prints the contract first when a proposal carries it
```

**Build.** The contract as a constant, and the two lint rules:

`common/packs.py`:

```python
VERIFIER_CONTRACT = ("Contract: the verifier sees only {recipe, val_score, error, profile}; "
                     "it never sees the actor's transcript, the test split or the intent.")
```

```python
    if "write_card" in allowed and VERIFIER_CONTRACT not in body:
        problems.append("a verifier pack must state the verifier contract verbatim")
    if "write_card" in allowed and any(t in allowed for t in ("fit_recipe", "score_test", "walk_path")):
        problems.append("a verifier pack may not fit or score: no one grades their own homework")
```

What the human sees first:

`common/approve.py`:

```python
        if any(VERIFIER_CONTRACT in text for text in payload.values()):
            print(f"### verifier contract (the acceptance rule you are approving)\n{VERIFIER_CONTRACT}", file=out)
```

**Run.**

```bash
cd rsi/step_08_meta_generates_rsi
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 HUMAN=script:y python run.py
```

```powershell
cd rsi\step_08_meta_generates_rsi
$env:FAKE_MODEL = "1"; python run.py
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y"; python run.py
```

**See.** The files of the proposal are elided.

```text
--- proposal p1: pack - a pack for adult_income from the template; this pack will change its own memory.json on every problem it runs
### verifier contract (the acceptance rule you are approving)
Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.
### actor/SKILL.md
...
--- end of proposal
Proposal p1 decided y: applied p1 (y) to rsi.
lint of the landed packs: ok
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       1/0/1
 2 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      3/0/4
```

**What the test proves.**

- The proposal contains the verifier contract verbatim, the human sees it first, the summary names the self-change, `n` lands nothing (`test_proposal_contains_the_verifier_contract_and_the_human_sees_it_first`).
- `lint_pack` refuses a proposal whose verifier lacks the contract or can fit, before the human is asked (`test_lint_refuses_a_proposal_without_the_contract`).
- The generated packs pass lesson 06's checks: isolation, the word test refused, `MEMORY_OFF` equals lesson 01, memory at least control (`test_generated_packs_pass_step_06_checks`).
- Generating twice gives the same proposal; the writer has no budget (`test_generating_twice_gives_the_same_proposal`).

**What to notice.** The generated packs are lesson 07's with the task's
values filled in, so they learn what lesson 06's did: after one problem of
evidence the second problem's memory arm ends 0.065 higher on validation
and 0.076 higher on the locked test. An `edit` that drops the contract is
refused by `lint_pack` when it is proposed again: the human can change the
mechanism, not remove its acceptance rule.

## Lesson 09: The RSI meta harness - a pack that patches the pack, problem by problem

**The idea.** A third pack boots between two problems, reads the trace,
the cards and every file of the actor, and makes one proposal - the
`Search policy:` line, a `schema.json` forbid, or new cards - through the
same approval cycle; every generation is a snapshot under `versions/`, and
generation n+1 boots what generation n wrote.

**Rung.** Under `approval: human`, L4: the human is the acceptance rule for
every patch. Under `approval: gate`, one line apart, the L5 flavour: the
private split - rows the actor never sees - decides keep-or-rollback and
the system revises its own improver's policy line behind a protected
evaluator. What stays human in both: the gate itself, the archive rule, the
verifier contract, the size cap, the curriculum and the exam. `META_OFF`
is the off switch. This is Stage 5 (Deploy): approval cycles as gates.

**Files that change.**

```text
step_09_rsi_meta_harness/
  skills/adult-income/            lesson 07's actor with `Search policy: static` and an empty forbid list
  skills/adult-income-verifier/   lesson 07's verifier
  skills/adult-income-meta/
    SKILL.md                      read log, cards, pack; one change (policy line | forbid | cards); patch_pack
    tools.md                      Allowed: read_traces, read_memory, read_pack, patch_pack, private_score, rollback
  skills/adult-income-meta-gate/  the same pack with `approval: gate`
  run.py                          --approval human | gate; META_OFF; prints the curve, the generations, the boot checksums
  test_step.py                    the claims below
  runs/curriculum_<mode>/         (created by run.py) traces.jsonl, curve.json, versions/gen_NNN/ with CHECKSUMS.json
common/tools.py                   + read_pack, patch_pack, private_score, rollback; private_gate
common/packs.py                   + snapshot, rollback: the version history
common/curriculum.py              + meta_visit: boot the meta pack after each problem with the actor as its target
```

**Build.** The meta pack's rule, in its `SKILL.md`, and the one line that
moves a decision:

`step_09_rsi_meta_harness/skills/adult-income-meta/SKILL.md`:

```markdown
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change the line to `obey-memory`.
   b. A field value lost every comparison one field apart it was in, at least three times across the log, and never won: add `{"field": ..., "value": ...}` to `schema.json` -> `forbid`. (`hyper` values are excluded: they belong to one model each.)
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet; merge at most three of them into `memory.json`.
```

The tool: one proposal per visit, a size cap, the test rule kept, and the
gate's keep-or-rollback on the private split:

`common/tools.py`:

```python
    if run.visits.get("patch_pack", 0) >= 1:
        raise ValueError("one proposal per visit; this visit already made one")
```

```python
    if changed_chars > SIZE_CAP * total:
        raise ValueError(f"the patch changes {changed_chars} of {total} characters, more than {int(SIZE_CAP * 100)} % of the pack; one small change per generation")
    if "SKILL.md" in changes and changes["SKILL.md"]["after"] and "after FREEZE" not in changes["SKILL.md"]["after"]:
        raise ValueError("a patch may not remove the test rule from SKILL.md")
```

```python
def private_gate(run, candidate):
    """Keep-or-rollback on the private split: the candidate recipe must not score below the incumbent."""
    before = tasks.score_on(run.task, run.seed, incumbent_recipe(run), "private")
    after = tasks.score_on(run.task, run.seed, candidate, "private")
    keep = after is not None and (before is None or after >= before)
```

**Run.** Under the human you are asked after every problem (a unified diff
and the evidence recipe); under the gate there is no prompt.

```bash
cd rsi/step_09_rsi_meta_harness
FAKE_MODEL=1 python run.py --approval human
FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py --approval human
FAKE_MODEL=1 python run.py --approval gate
META_OFF=1 FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_09_rsi_meta_harness
$env:FAKE_MODEL = "1"; python run.py --approval human
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y,y,y,y,y,y"; python run.py --approval human
$env:FAKE_MODEL = "1"; python run.py --approval gate
```

**See.** `--approval human` with six scripted yeses; the first prompt is
shown, the rest elided.

```text
--- proposal p1: patch - search policy: obey the cards (>= 2 active)
--- a/SKILL.md
+++ b/SKILL.md
@@ -18,3 +18,3 @@
-   Search policy: static
+   Search policy: obey-memory
(evidence recipe: {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"})
--- end of proposal
...
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/7
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       3/1/9
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    2/17      2/2/13
  after problem 1: adult-income-meta -> {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["SKILL.md"]}
  after problem 2: adult-income-meta -> null
  after problem 3: adult-income-meta -> null
  after problem 4: adult-income-meta -> null
  after problem 5: adult-income-meta -> {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_002", "files": ["memory.json"]}
  after problem 6: adult-income-meta -> null
versions: ['gen_001', 'gen_002']; actor pack byte-identical to skills/: False
actor boots (checksums of SKILL.md / schema.json / memory.json per generation):
  adult_income     e1da1f5b2fe7 fe416aeb708b 37517e5f3dc6
  breast_cancer    9ffc716fca7d fe416aeb708b 66d72d59372c
  wine             9ffc716fca7d fe416aeb708b cf17a31704bc
  digits           9ffc716fca7d fe416aeb708b cf17a31704bc
  synth_shift_a    9ffc716fca7d fe416aeb708b f455c8ffb4e0
  synth_shift_b    9ffc716fca7d fe416aeb708b 4cf3925c8ac1
```

**What the test proves.**

- Generation n+1 boots the files generation n wrote: the boot checksums equal the apply checksums, and `versions/gen_001` holds the old text (`test_generation_n_plus_1_boots_the_files_generation_n_wrote`).
- Under `approval: human` no patch lands without a `y` (`test_under_human_approval_nothing_lands_without_a_y`).
- Under `approval: human` an `edit` lands the human's version (`test_under_human_approval_an_edit_lands_the_humans_version`).
- Under `approval: gate` a patch that raises val and lowers `private_score` is rejected and `versions/` restores the previous pack; a second proposal per visit is refused (`test_under_the_gate_a_patch_that_raises_val_and_lowers_private_is_rejected_and_rolled_back`).
- Under `approval: gate` a patch that holds on the private split lands, and the verdict is in the log (`test_under_the_gate_a_patch_that_holds_on_private_lands`).
- `META_OFF` leaves the pack's fixed files byte-identical and makes no version (`test_meta_off_leaves_the_pack_byte_identical`).
- The meta pack cannot call `score_test`, `fit_recipe` or `write_card`; both meta packs lint (`test_the_meta_pack_cannot_call_score_test_or_fit`).

**What to notice.** Read the last block: `SKILL.md` changes once
(generation 1 flipped the policy line, and every later problem booted that
text), `schema.json` never (no value lost every comparison it was in),
`memory.json` on every problem the verifier learned something. `null`
after a problem means the meta pack found nothing to propose and said so.
Under `--approval gate` the same two patches land with `"gate": {"before":
0.8951, "after": 0.8951, "keep": true}` and `{"before": 0.9395, "after":
0.9395, "keep": true}`: the evidence recipe of a policy patch is the
incumbent itself, so the gate holds. With `META_OFF=1` every line reads
`META_OFF`, `versions: none`, and the curve is lesson 07's for problem 1
and flat after it: the actor never learned to obey its cards. The curve
itself equals lesson 07's because the meta pack's first move is to flip the
line lesson 07's actor already had.

## Lesson 10: Dream-RSI - rank the search policies on the log, at zero fits

**The idea.** One tool, `rank_policies`, replays each named policy's first
24 picks against this problem's log - a pick the log has is answered for
free, one it does not have counts as unknown - and the meta pack proposes
the winner as the actor's `Search policy:` line, at zero fits.

**Rung.** L2 (how to improve), with the acceptance rule human: the policy
library (`policies.md`, `common/policies.py`) is the human's, and the
system chooses among strategies it did not write. Each policy change is a
`y` at the prompt.

**Files that change.**

```text
step_10_rsi_dream/
  skills/adult-income/              lesson 09's actor (Search policy: static, an empty forbid list)
  skills/adult-income-verifier/     lesson 09's verifier
  skills/adult-income-meta-dream/
    SKILL.md                        read log, cards, pack; rank_policies; patch the policy line to the winner; patches: ["SKILL.md"]
    tools.md                        Allowed: read_traces, read_memory, read_pack, rank_policies, patch_pack
    policies.md                     the five policies and what each does
  run.py                            the curriculum with a Dream-RSI visit after every problem
  test_step.py                      the claims below
common/tools.py                     + rank_policies; patch_pack honours the `patches:` allow-list
common/policies.py                  policy_order: the one ordering function the fake model and the replay share
```

**Build.** The policy library the human wrote:

`step_10_rsi_dream/skills/adult-income-meta-dream/policies.md`:

```markdown
- `static`: walk `schema.json` -> `recipes` in order, cards or no cards.
- `obey-memory`: probe one recipe per model (the believed model first) with the preferred preprocessing; then the believed family - its static recipes, then its hyper variants - ranked by the cards; then the rest of the grid.
- `random`: the 72-recipe grid in a seeded shuffle.
- `neighbours-of-top-3`: six static fits, then the untried neighbours (one field away) of the three best so far, then the static list.
- `prefer-untried-family`: at every step the model family with the fewest fits so far, static recipes before hyper variants.
```

The replay, and the tie-break that rewards novelty:

`common/tools.py`:

```python
            tried.append(pick)
            if recipe.key(pick) in logged:      # the log answers for free
                fits.append(({"recipe": pick}, {"n": n, "val_score": logged[recipe.key(pick)]}))
            else:                               # the gym is silent here: the policy would have to fit to know
                unknown += 1
```

```python
    ranking.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
```

**Run.**

```bash
cd rsi/step_10_rsi_dream
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py
```

```powershell
cd rsi\step_10_rsi_dream
$env:FAKE_MODEL = "1"; python run.py
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y,y,y,y,y,y"; python run.py
```

**See.** Six scripted yeses; the prompts are elided.

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       1/0/8
 4 digits                   0.9991    0.999 +0.0001    0.9988    0.9984    0/0       1/0/9
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    9/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    4/17      1/0/13
  after problem 1: log 24 recipes, fits spent 0; winner obey-memory (best logged 0.9172, unknown 14); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["SKILL.md"]}
  after problem 2: log 38 recipes, fits spent 0; winner random (best logged 0.9966, unknown 12); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_002", "files": ["SKILL.md"]}
  after problem 3: log 42 recipes, fits spent 0; winner random (best logged 1.0, unknown 12); patch null
  after problem 4: log 41 recipes, fits spent 0; winner random (best logged 0.9991, unknown 12); patch null
  after problem 5: log 41 recipes, fits spent 0; winner obey-memory (best logged 0.9507, unknown 9); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_003", "files": ["SKILL.md"]}
  after problem 6: log 38 recipes, fits spent 0; winner random (best logged 0.8571, unknown 12); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_004", "files": ["SKILL.md"]}
policy line now: Search policy: random
```

**What the test proves.**

- `rank_policies` makes zero fits - the budget counter and the trace prove it - and the meta pack cannot fit (`test_rank_policies_makes_zero_fits`).
- A policy preferring unvisited recipes scores unknown; `static` on its own log has none; an unknown policy name is an error (`test_a_policy_preferring_unvisited_recipes_scores_unknown`).
- The winner is proposed as the search-policy line, lands under `y`, and the next lap adds recipes the log never saw (`test_the_winner_is_proposed_and_the_next_lap_visits_new_recipes`).

**What to notice.** Read it against lesson 09's curve. After problem 1 the
replay picks `obey-memory` and problem 2 improves as before. After problem
2 the replay credits `random` with the 0.9966 that `obey-memory` actually
found - a replay gives a policy credit for any logged recipe it happens to
pick - and the actor runs random on problems 3 and 4, where everything ties
anyway, then pays for it on problem 5 (`wasted 9`, gap 0 where lesson 09
had +0.0024). After problem 5 `obey-memory` wins again, problem 6 repeats
lesson 09's +0.065, and the replay on problem 6's log hands the line back
to `random` for whatever comes next. Zero fits were spent on any of these
decisions. History is an exact gym for the recipes you visited and silent
everywhere else: that is the method and its price in one table.

## Lesson 11: RSIAgent - the next experiment, chosen on purpose; the memory, frozen at test

**The idea.** Three packs: a curriculum pack picks the actor's next
experiments by uncertainty, `u = (1 - success) + c / (n + 1)`, broad then
deep; the actor runs `plan.json` and waits when it runs dry; the verifier
only gets its turn after `score_test`, so the memory is frozen while the
actor runs.

**Rung.** L3 (which experience to acquire) plus L4. The uncertainty rule,
its two `c` values and the phase length are the human's, in the curriculum
pack's `SKILL.md`. Nobody approves at run time. The freeze is what makes the
comparison with `MEMORY_OFF` fair.

**Files that change.**

```text
step_11_rsi_agent/
  skills/adult-income-actor/
    SKILL.md            run plan.json; re-read it when dry; wait; score_test once after FREEZE; MEMORY_OFF walks the static list
    tools.md            Allowed: load_splits, fit_recipe, read_pack, score_test, save_model
    plan.json           the current phase's experiments (rewritten by the curriculum pack on every visit)
    schema.json, memory.schema.json, memory.json, eval.md    lesson 07's
  skills/adult-income-curriculum/
    SKILL.md            u = (1 - success) + c / (n + 1); Broad c 2.0, Deep c 0.25, 12 experiments per phase
    tools.md            Allowed: read_traces, read_memory, write_plan
  skills/adult-income-verifier/   lesson 06's verifier
  run.py                agent_problem: curriculum -> actor -> curriculum -> actor (resumed) -> verifier; the curve and the exam
  test_step.py          the claims below
common/tools.py         + write_plan
common/harness.py       + resume: continue a transcript with a new user message, same budget, same tools
```

**Build.** The rule, in the curriculum pack:

`step_11_rsi_agent/skills/adult-income-curriculum/SKILL.md`:

```markdown
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far, `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline), and `c` is the phase's exploration weight:
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
```

The sequence, with the freeze and the one new harness verb:

`step_11_rsi_agent/run.py`:

```python
    run = harness.boot(actor, task, seed=seed, arm="memory", run_dir=run_dir, quiet=quiet)
    run.memory_frozen = True                                                # no card lands while the actor runs
    harness.run(run, model)                                                 # fits the broad plan, then waits
    plan = harness.boot(curr, task, seed=seed, arm="memory", run_dir=run_dir, target=actor, quiet=quiet)
    harness.run(plan, model)                                                # deep: from the broad results
    harness.resume(run, model, "plan.json was updated: continue with the new experiments.")
```

**Run.** The curriculum, then the exam; no prompt.

```bash
cd rsi/step_11_rsi_agent
FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_11_rsi_agent
$env:FAKE_MODEL = "1"; python run.py
```

**See.**

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      4/0/4
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       2/0/6
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/6
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/0/8
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    1/0       2/1/9
 6 synth_shift_b            0.7655   0.7925 -0.0270    0.8603     0.834   24/17      1/2/8
  adult_income     broad: logreg rf hgb logreg rf hgb ... | deep: rf rf rf rf rf rf ...
  breast_cancer    broad: logreg rf hgb logreg rf hgb ... | deep: rf rf rf rf rf rf ...
  wine             broad: hgb logreg rf hgb logreg rf ... | deep: hgb hgb hgb hgb hgb hgb ...
  digits           broad: hgb logreg rf hgb logreg rf ... | deep: logreg logreg logreg logreg logreg logreg ...
  synth_shift_a    broad: hgb logreg rf hgb logreg rf ... | deep: rf rf rf rf rf rf ...
  synth_shift_b    broad: logreg rf hgb logreg rf hgb ... | deep: rf rf rf rf rf rf ...
exam exam: memory arm beats MEMORY_OFF on 4 of 5 seeds (1 on test score, 4 same score; a tie won by fewer wasted fits), mean test gap +0.0006; pack unchanged: True
  seed 0: memory test 0.8691 val 0.8778 wasted 24 | control test 0.8661 val 0.8858 wasted 19 | gap +0.0030 win
  seed 1: memory test 0.8077 val 0.9167 wasted 11 | control test 0.8077 val 0.9167 wasted 10 | gap +0.0000 loss
  seed 2: memory test 0.9208 val 0.9131 wasted 6 | control test 0.9208 val 0.9131 wasted 17 | gap +0.0000 win
  seed 3: memory test 0.9215 val 0.8766 wasted 9 | control test 0.9215 val 0.8766 wasted 18 | gap +0.0000 win
  seed 4: memory test 0.8881 val 0.9117 wasted 0 | control test 0.8881 val 0.9117 wasted 16 | gap +0.0000 win
```

**What the test proves.**

- The broad phase touches every family before the deep phase repeats one, and the broad `c` exceeds the deep `c` (`test_broad_phase_touches_every_family_before_deep_repeats_one`).
- The deep phase prefers the family with the most faults, and the actor fits it (`test_deep_phase_prefers_the_family_with_the_most_faults`).
- The actor proposes nothing of its own, waits when the plan runs dry, cannot write a plan; both packs lint (`test_the_actor_proposes_nothing_of_its_own_and_waits_for_a_plan`).
- The memory is frozen before `score_test` - no card between the actor's boot and its test - and unchanged on the transfer table (`test_memory_is_frozen_before_score_test_and_unchanged_on_the_transfer_table`).

**What to notice.** This is the flat curve of the series, kept on purpose.
The broad phase round-robins the families (the cards move the believed
family to the front from problem 3 on), so the memory arm reaches the
static grid's best in 2 fits on Adult where the grid needs 16 - but the gap
column is zero on five problems and the deep phase then spends its twelve
fits on the *faultiest* family, which on problem 6 means twelve random
forests on a table a boosted model wins: the val gap goes to -0.027 while
the test gap stays positive (+0.026). On the exam the frozen memory wins
four of five seeds, almost all on cost, not score (mean test gap +0.0006
against lesson 07's +0.0308). Broad-then-deep buys information and cards,
not validation points; the lesson keeps the number.

## Lesson 12: ModularRSI - a harness module, evolved off the benchmark

**The idea.** The actor's procedure is split into five module files, two
actor packs differ in exactly one of them, both run a pool of synthetic
tables no curriculum or exam problem uses, and the one new tool `contrast`
names the module whose text differs between the success and the failure;
the meta pack patches that one module under the pool's private gate, and
only afterwards is the eval table looked at - with two fake actors of
different quirks.

**Rung.** L2 for the choice of module; the L5 flavour for a harness module
changing off-benchmark. What stays human: the module boundaries, the pool,
the allow-list (`patches: ["modules/*.md"]`). `approval: gate`, so there is
no prompt; `META_OFF` is not wired here (one visit, no loop).

**Files that change.**

```text
step_12_rsi_modular/
  skills/actor-a/
    SKILL.md                  boot order: the five modules
    modules/agent_loop.md     the counted loop
    modules/tool_use.md       what a recipe is, what a refusal costs
    modules/observation.md    what a fit result carries
    modules/context.md        the cards' rule, the Search policy line (static), MEMORY_OFF
    modules/completion.md     score_test once after FREEZE, save_model, stop
    tools.md, schema.json, memory.schema.json, memory.json (three cards), eval.md
  skills/actor-b/             the same pack with context.md saying obey-memory
  skills/modular-meta/
    SKILL.md                  Target / Actor A / Actor B lines; contrast; one module patch under the gate
    tools.md                  Allowed: read_traces, read_memory, read_pack, contrast, patch_pack
  skills/adult-income-verifier/   lesson 06's verifier (unused by run.py; the pool runs carry the shipped cards)
  pool/01_pool_trees_1.json, pool/02_pool_trees_2.json   the benchmark-disjoint tables (seeds 203 and 206)
  run.py                      both actors on the pool -> contrast -> patch -> the eval table with two fake actors
  test_step.py                the claims below
common/tools.py               + contrast
common/fake.py                the `style` quirk: `default` walks lists forwards, `reverse` backwards
```

**Build.** The one module the two actors disagree on:

`step_12_rsi_modular/skills/actor-a/modules/context.md`:

```markdown
# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: static
```

The tool pairs a success and a failure per pool table and names the
differing module; the allow-list keeps the patch inside `modules/`:

`common/tools.py`:

```python
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
    problems = sorted({r["problem"] for r in run.trace.rows("fit", arm=a)} & {r["problem"] for r in run.trace.rows("fit", arm=b)})
```

```python
        if allowed_paths and not any(fnmatch(name, pat) for pat in allowed_paths):
            raise ValueError(f"this meta pack may patch {allowed_paths} only, not {name}")
```

**Run.**

```bash
cd rsi/step_12_rsi_modular
FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_12_rsi_modular
$env:FAKE_MODEL = "1"; python run.py
```

**See.** The eval table is curriculum problem 6, `synth_shift_b`.

```text
contrast: module modules/context.md, winner actor-b, wins {"actor-a": 0, "actor-b": 2}
  pool_trees_1: success actor-b (0.8624) vs failure actor-a (0.8399)
  pool_trees_2: success actor-b (0.8962) vs failure actor-a (0.8638)
patch: {"id": "g1", "decision": "y", "gate": {"before": 0.9068, "after": 0.9068, "keep": true}, "landed": true, "version": "gen_001", "files": ["modules/context.md"]}
actor-a on the eval table synth_shift_b before the patch: {"default": 0.7925, "reverse": 0.7925}; after: {"default": 0.8571, "reverse": 0.8571}
modules of actor-a now equal to actor-b's: True
```

**What the test proves.**

- `contrast` names the module whose text differs between the success and the failure, per pool table (`test_contrast_names_the_module_whose_text_differs`).
- The patch touches exactly one module file; `SKILL.md` is refused by the allow-list (`test_the_patch_touches_exactly_one_module_file`).
- Validation runs on the pool, never the eval table: the gate's problem is a pool table and the pool log holds no other (`test_validation_runs_on_the_pool_never_the_eval_table`).
- The patched module helps both fake actors on the eval table (`test_the_patched_module_helps_both_fake_actors`).

**What to notice.** Two pool tables, two wins for actor-b, one module
named, one patch through the pool's private gate; then the eval table,
untouched until now, agrees for both fake actors: 0.7925 -> 0.8571. The
pool did the localising; the eval table only confirmed. This lesson is not
in the side-by-side table because it never runs the curriculum
arm-against-arm; its number is the one line above. A patch that helped one
model's habits would not have been a better workshop, which is why there
are two actors with different quirks.

## Lesson 13: Recuris - memory as a skill package, with a working memory

**The idea.** The experiential memory is `skill-memory/manifest.yaml` plus
one markdown card per situation, the working memory is `working.md` the
actor rewrites per run, and the one new tool `skill_memory` selects every
validated card whose tags all hold for the named need - by the situation,
never by which card is newest - and, after each problem, lands one
localised, validated card update.

**Rung.** L4: memory consolidation under a human acceptance rule. The
validation rule (the value must have won its comparisons on this problem),
the need tags and the shipped card are the human's; no prompt.

**Files that change.**

```text
step_13_rsi_skill_memory/
  skills/adult-income-skills/
    SKILL.md                      name the situation, get the cards, obey them, score_test once after FREEZE
    tools.md                      Allowed: load_splits, skill_memory (need), fit_recipe, score_test, save_model
    working.md                    rewritten every run: Need and Cards
    skill-memory/manifest.yaml    the package index: name and file per card
    skill-memory/cards/onehot-for-categorical.md   the one shipped card; everything else it learns
    schema.json, eval.md          lesson 07's
  skills/skill-memory-meta/
    SKILL.md                      tally the problem's pairs; one validated update of one card
    tools.md                      Allowed: read_traces, read_memory, read_pack, skill_memory (update)
  run.py                          the curriculum with a meta visit per problem; the gain-by-horizon report
  test_step.py                    the claims below
common/tools.py                   + skill_memory: `need` for the actor, `update` for the meta
```

**Build.** A card is a markdown file with typed front matter:

`step_13_rsi_skill_memory/skills/adult-income-skills/skill-memory/cards/onehot-for-categorical.md`:

```markdown
---
name: onehot-for-categorical
when: [categorical]
then: encode=onehot
validated: true
horizon: 1
---
```

The tool's two halves - selection by need, and the update that must have
won:

`common/tools.py`:

```python
        # selection by need, not by recency: every card whose situation tags all hold, in manifest order
        chosen = [c for c in skill_cards(run.target) if c.get("validated") and set(c.get("when", [])) <= set(need)]
```

```python
        wins, losses, _ = memory.tally(rows)
        if wins.get((field, value), 0) <= losses.get((field, value), 0):
            raise ValueError(f"not validated: {then} did not win its comparisons on {run.problem} "
                             f"({wins.get((field, value), 0)} wins, {losses.get((field, value), 0)} losses); nothing lands")
        if run.visits.get("skill_update", 0) >= 1:
            raise ValueError("one card update per visit")
```

**Run.**

```bash
cd rsi/step_13_rsi_skill_memory
FAKE_MODEL=1 python run.py
```

```powershell
cd rsi\step_13_rsi_skill_memory
$env:FAKE_MODEL = "1"; python run.py
```

**See.**

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      0/0/0
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       0/0/0
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/0
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       0/0/0
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       0/0/0
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      0/0/0
gain by horizon (problems seen so far -> val gap, cards in the package, highest card horizon, working memory):
  horizon 1: gap +0.0000, cards 2, max horizon 1, need ['categorical', 'imbalanced'], applied ['onehot-for-categorical'], updated this problem: True
  horizon 2: gap +0.0000, cards 3, max horizon 1, need ['small'], applied [], updated this problem: True
  horizon 3: gap +0.0000, cards 3, max horizon 1, need ['small', 'imbalanced', 'multiclass'], applied ['model-when-small'], updated this problem: False
  horizon 4: gap +0.0000, cards 4, max horizon 1, need ['imbalanced', 'multiclass'], applied [], updated this problem: True
  horizon 5: gap +0.0024, cards 4, max horizon 2, need ['small', 'categorical'], applied ['onehot-for-categorical', 'model-when-small'], updated this problem: True
  horizon 6: gap +0.0646, cards 4, max horizon 3, need ['small', 'categorical', 'imbalanced'], applied ['onehot-for-categorical', 'model-when-categorical-imbalanced', 'model-when-small'], updated this problem: True
```

**What the test proves.**

- A skill card is selected by the working-memory need, not by recency; `working.md` says which; the probes obey it (`test_a_card_is_selected_by_need_not_by_recency`).
- An update is localised to one card plus its manifest line and validated before it lands; a contradicted one is refused; one per visit (`test_an_update_is_localised_to_one_card_and_validated_first`).
- The horizon report shows the gain per sequence length: cards and horizons grow, the gap does not fall, the versions are files (`test_the_horizon_report_shows_the_gain_per_sequence_length`).

**What to notice.** The `cards +/-/act` columns read 0 because this pack
keeps no `memory.json`; the package's own counts are on the horizon lines:
one card shipped, four by the end, the `model-when-small` card updated on
three problems (horizon 3). The shipped card already put Adult's memory arm
at the grid's best in 2 fits instead of 16 - which is why this lesson has
the fewest wasted fits in the side-by-side table (6 against 19) - and the
cards learned on problems 1-5 give problem 6 the same +0.065 as lesson 09,
with the reasons now readable in each card's body. `git diff` the package
under `runs/work/` against `skills/`: that is the memory.

## Lesson 14: The Darwin Gödel Machine lineage - the agent's own source, behind an archive and a gate

**The idea.** The source is the actor's `SKILL.md` and `loop.json`; after
each problem the current variant runs a fixed held-out benchmark, `archive
add` stores it with its held-out gain over the static walk, `archive
parent` picks the best-scoring variant (ties to the older one, never "the
latest" by default), and the meta pack proposes the next rewrite from that
parent - behind the private gate and then the human.

**Rung.** The L5 flavour, with the DGM's own caveat spelled out: the
archive rule, the parent choice, the held-out benchmark and the allow-list
(`patches: ["SKILL.md", "loop.json"]`) are the human's. `approval: both`:
the gate decides first, then the human sees what the gate kept and may
still refuse it.

**Files that change.**

```text
step_14_rsi_self_modifying/
  skills/adult-income/
    SKILL.md            lesson 09's actor; the Search policy line is what the rewrites change
    loop.json           the counted loop with a `policy` field the rewrites keep in step with SKILL.md
    tools.md, schema.json, memory.schema.json, memory.json, eval.md
  skills/adult-income-verifier/   lesson 06's verifier
  skills/dgm-meta/
    SKILL.md            archive add -> parent -> restore -> one rewrite of SKILL.md + loop.json; approval: both
    tools.md            Allowed: read_traces, read_memory, read_pack, archive, patch_pack
    held-out/           the fixed benchmark: lesson 12's two pool tables
  run.py                the curriculum; each generation runs the held-out benchmark under its own arm before the meta visit
  test_step.py          the claims below
  runs/curriculum/archive/    (created by run.py) one directory per variant and archive.json
common/tools.py         + archive; patch_pack learns `approval: both`
```

**Build.** The parent rule, in the pack and in the tool:

`step_14_rsi_self_modifying/skills/dgm-meta/SKILL.md`:

```markdown
3. Call `archive` with action `parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If the parent is not the latest, call `archive` with action `restore` and that label, then `read_pack` again: you now stand on the parent.
```

`common/tools.py`:

```python
        # the parent is the best held-out score, ties to the older variant: never "the latest" by default
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
```

**Run.**

```bash
cd rsi/step_14_rsi_self_modifying
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py
```

```powershell
cd rsi\step_14_rsi_self_modifying
$env:FAKE_MODEL = "1"; python run.py
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y,y,y,y,y,y"; python run.py
```

**See.** Six scripted yeses; the prompts are elided.

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/4
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       1/1/4
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    0/0       3/0/7
 6 synth_shift_b            0.7925   0.7925 +0.0000     0.834     0.834   17/17      1/0/5
archive (variant, problem it ran, held-out gain over the static walk on the fixed benchmark):
  adult_income-static                adult_income     +0.0000
  breast_cancer-obey-memory          breast_cancer    -0.0398
  wine-neighbours-of-top-3           wine             -0.0363
  digits-prefer-untried-family       digits           +0.0000
  synth_shift_a-static               synth_shift_a    +0.0000
  synth_shift_b-static               synth_shift_b    +0.0000
  after problem 1: {"id": "g1", "decision": "y", "gate": {"before": 0.8951, "after": 0.8951, "keep": true}, "landed": true, "version": "gen_001", "files": ["SKILL.md", "loop.json"]}
  after problem 2: {"id": "g1", "decision": "y", "gate": {"before": 0.9973, "after": 1.0, "keep": true}, "landed": true, "version": "gen_002", "files": ["SKILL.md", "loop.json"]}
  after problem 3: {"id": "g1", "decision": "y", "gate": {"before": 1.0, "after": 1.0, "keep": true}, "landed": true, "version": "gen_003", "files": ["SKILL.md", "loop.json"]}
  after problem 4: null
  after problem 5: null
  after problem 6: null
versions ['gen_001', 'gen_002', 'gen_003']; files the meta pack ever rewrote: ['SKILL.md', 'loop.json']; files that differ across the archive: ['SKILL.md', 'loop.json', 'memory.json']
policy line now: Search policy: static
```

**What the test proves.**

- The archive holds every variant with its held-out score on the fixed benchmark, and the benchmark shares no problem with the curriculum (`test_the_archive_holds_every_variant_with_its_held_out_score`).
- The parent is chosen from the archive, not always the latest (`test_the_parent_is_chosen_from_the_archive_not_always_the_latest`).
- A rewrite that lowers the held-out score never becomes a parent (`test_a_rewrite_that_lowers_the_held_out_score_never_becomes_a_parent`).
- `SKILL.md` and `loop.json` are the only self-modified files: every apply lists them, other files are refused, the rewrites keep the budget and lint (`test_skill_md_and_loop_json_are_the_only_self_modified_files`).
- The human can refuse what the gate kept, and the pack rolls back (`test_the_human_can_refuse_what_the_gate_kept`).

**What to notice.** Read the archive column: this lineage never left
`static`. The `obey-memory` rewrite ran problem 2 well (+0.0012 on val) but
scored -0.040 on the held-out benchmark - the cards it obeyed came from
Adult and breast cancer and did not fit two small tree tables - so it never
became a parent; neither did `neighbours-of-top-3` (-0.036). The parent
stayed `adult_income-static`, each rewrite started from it, and once every
variant was in the archive the meta pack had nothing new to propose.
Problems 5 and 6 ran the parent and gained nothing: 33 wasted fits over the
curriculum, the same as the static walk, and a flat last row where lessons
07, 09, 13 and 16 show +0.065. On this benchmark the lineage found no
rewrite better than what it started with, and the archive says so with a
number per variant. A negative result with a version history is what safe
inheritance looks like.

## Lesson 15: AIDE² - autoresearch on autoresearch, keep-if-better across the set under one budget

**The idea.** The inner pack is an AIDE-style tree search whose operators
(`draft`, `debug`, `improve`, `review`) live in `operators.md`, every one
carrying the same guard line; the outer pack rewrites one operator's text,
and the runner keeps the rewrite only if it beats the previous operators
across every curriculum problem under the same metered budget, after a
statistical layer drops outlier successes.

**Rung.** The L5 flavour. The human approves the rewrite (`approval:
human`), then the set decides (`aide_keep`, the human's rule). What stays
human: the guards' wording, the keep rule, the budget meter, the task set.
Effective recursion is claimed only across the whole set under one budget,
and here it was not achieved - and reported.

**Files that change.**

```text
step_15_rsi_aide2/
  skills/adult-income-aide/
    SKILL.md            lesson 09's actor with `Search policy: aide-tree`
    operators.md        draft, debug, improve, review - each with the guard line
    tools.md, schema.json, memory.schema.json, memory.json, eval.md
  skills/adult-income-verifier/   lesson 06's verifier
  skills/aide-outer/
    SKILL.md            meter, then one rewrite of operators.md; the runner's keep-if-better is the second gate; patches: ["operators.md"]
    tools.md            Allowed: read_traces, read_memory, read_pack, meter, patch_pack
  run.py                outer_step: lap v1 -> rewrite -> lap v2 -> aide_keep -> keep or roll back
  test_step.py          the claims below
common/tools.py         + meter, aide_keep, SUSPICIOUS / JUMP (the hard guard's thresholds)
common/policies.py      + aide-tree, aide-tree-top-3
common/packs.py         + ANTI_OVERFIT, checked by lint_pack per operator section
```

**Build.** The `improve` operator with the guard every operator carries:

`step_15_rsi_aide2/skills/adult-income-aide/operators.md`:

```markdown
## improve
Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.
```

The keep rule and the hard guard, in code:

`common/tools.py`:

```python
def aide_keep(before, after, mad_k=3.0):
    """AIDE2's outer rule: keep a rewrite only if it is better across the whole set under the same budget, after the
    statistical layer drops outlier successes - a per-problem gain more than `mad_k` MADs above the median gain is
    discarded, so one lucky problem cannot carry the decision. Returns (keep, detail)."""
```

```python
SUSPICIOUS = 0.999    # a validation score this close to perfect is re-run before it is believed
JUMP = 0.2            # so is one that jumps this far above the previous best in one fit
```

**Run.** One outer step: a lap with the current operators, one rewrite, a
lap with the rewrite, keep-if-better. Without `HUMAN` you are asked once.

```bash
cd rsi/step_15_rsi_aide2
FAKE_MODEL=1 HUMAN=script:y python run.py
```

```powershell
cd rsi\step_15_rsi_aide2
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y"; python run.py
```

**See.** The prompt is elided.

```text
meter: {"arm": "all", "fits": 144, "tokens": 46648, "problems": ["adult_income", "breast_cancer", "digits", "synth_shift_a", "synth_shift_b", "wine"]}
rewrite: {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["operators.md"]}
problem           v1 best val  v2 best val     gain
adult_income           0.9172       0.9171  -0.0001
breast_cancer          0.9966       0.9966  +0.0000
wine                      1.0          1.0  +0.0000
digits                  0.999        0.999  +0.0000
synth_shift_a          0.9531       0.9531  +0.0000
synth_shift_b          0.8571       0.8571  +0.0000
fits per lap: v1 144, v2 144; keep-if-better across the set: False {"gains": {"adult_income": -0.0001, "breast_cancer": 0.0, "digits": 0.0, "synth_shift_a": 0.0, "synth_shift_b": 0.0, "wine": 0.0}, "outliers_discarded": [], "total_gain": -0.0001, "wins": 0, "losses": 1}
operators.md now: Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
```

**What the test proves.**

- Keep-if-better is evaluated across every problem of the curriculum under one metered budget, asserted from the trace (`test_keep_if_better_is_evaluated_across_every_problem_under_one_metered_budget`).
- A rewrite that wins on one problem and loses on the set is rejected; one lucky problem is discarded as an outlier (`test_a_rewrite_that_wins_on_one_problem_and_loses_on_the_set_is_rejected`).
- The three guards are present in every operator prompt; `lint_pack` refuses one without; only `operators.md` may be patched (`test_the_guards_are_in_every_operator_and_lint_refuses_one_without`).
- A suspicious score is re-run - scripted with a near-perfect table (`test_a_suspicious_score_is_re_run`).

**What to notice.** The rewrite (expand the top three instead of the best)
changed nothing on five problems and lost 0.0001 on Adult under the same
144 fits, so the outer loop rolled it back and `operators.md` reads as it
did. That rollback is the lesson: "a better run" on one table is not "a
better researcher", and the meter says both laps paid the same. The
report's numbers - seven improved versions in 100 outer steps, 16x context
compression - are *reported* and unverified here; this page has one outer
step and a rejected rewrite.

## Lesson 16: MetaSkill-Evolve - the improver's skills improve too, slowly

**The idea.** Two timescales on one frozen model: the fast loop is lesson
09's meta pack under the gate, reading its own five role files under
`roles/` for the numbers it works with; the slow loop is a second meta
pack, `meta-evolver`, whose target is the fast meta pack, whose allow-list
is `roles/*.md`, which boots every k problems and changes one line of one
role file with the human's `y`.

**Rung.** L5: the procedure that improves the improver is revised, with the
human on the slow clock as the acceptance rule - which is what the paper's
industry loops do. The clock (`K = 3`), the role boundaries and both
allow-lists are the human's; the private gate approves task-skill patches,
the human approves meta-skill patches.

**Files that change.**

```text
step_16_rsi_meta_skills/
  skills/adult-income/            lesson 09's actor (Search policy: static)
  skills/adult-income-verifier/   lesson 06's verifier
  skills/task-skills-meta/
    SKILL.md                      the fast loop: one task-skill patch per problem under the gate, reading roles/
    tools.md                      lesson 09's meta tools
    roles/analyzer.md             read the log and the cards
    roles/retriever.md            read the actor pack: which files are task skills
    roles/allocator.md            the order of changes; Policy flip threshold: 2
    roles/proposer.md             one patch per visit; Cards per visit: 3
    roles/evolver.md              the slow clock and the human, stated
  skills/meta-evolver/
    SKILL.md                      the slow loop: one line of one role file, every k problems, with the human; patches: ["roles/*.md"]
    tools.md                      Allowed: read_traces, read_memory, read_pack, patch_pack
  run.py                          the two clocks (K = 3); the versions and the diffs of the meta pack
  test_step.py                    the claims below
  runs/curriculum/meta/           (created by run.py) the slow loop's log and versions/
```

No new tool: the slow loop is `patch_pack` pointed at a different target,
with a different allow-list and a human.

**Build.** A meta-skill is a file with a number in it:

`step_16_rsi_meta_skills/skills/task-skills-meta/roles/proposer.md`:

```markdown
# Role: proposer
One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
Cards per visit: 3
```

The clock, in the runner:

`step_16_rsi_meta_skills/run.py`:

```python
    def visit(task, i):
        fast = curriculum.meta_visit(meta, actor, task, model, run_dir, human=human, quiet=quiet)
        slow = None
        if i % k == 0:
```

**Run.** Six problems, a fast visit after each, a slow visit after
problems 3 and 6; the only prompts are the slow loop's.

```bash
cd rsi/step_16_rsi_meta_skills
FAKE_MODEL=1 python run.py
FAKE_MODEL=1 HUMAN=script:y,y python run.py
```

```powershell
cd rsi\step_16_rsi_meta_skills
$env:FAKE_MODEL = "1"; python run.py
$env:FAKE_MODEL = "1"; $env:HUMAN = "script:y,y"; python run.py
```

**See.** Two scripted yeses; the prompts are elided, and one of the three
version diffs is shown.

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/7
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       3/1/9
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    2/17      2/2/13
  after problem 1: task skills changed (["SKILL.md"]); meta-skills: not this clock
  after problem 2: task skills unchanged (null); meta-skills: not this clock
  after problem 3: task skills unchanged (null); meta-skills changed ({"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["roles/proposer.md"]})
  after problem 4: task skills unchanged (null); meta-skills: not this clock
  after problem 5: task skills changed (["memory.json"]); meta-skills: not this clock
  after problem 6: task skills unchanged (null); meta-skills changed ({"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_002", "files": ["roles/allocator.md"]})
meta pack versions: ['gen_001', 'gen_002']
  gen_001/roles/proposer.md -> now: --- a/roles/proposer.md | +++ b/roles/proposer.md | @@ -2,2 +2,2 @@ |  One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each. | -Cards per visit: 3 | +Cards per visit: 4
roles/allocator.md: Which task skill gets this visit, in order: the policy line, then a forbid, then cards. / Policy flip threshold: 1
roles/proposer.md: Cards per visit: 4
```

**What the test proves.**

- The fast loop visits every problem and task skills move between problems; the meta pack changes only after a slow visit (every k), one role file at a time (`test_task_skills_change_every_problem_and_meta_skills_only_every_k`).
- A meta-skill change never lands without the human `y`; the slow loop cannot touch `SKILL.md` or fit (`test_a_meta_skill_change_never_lands_without_the_human_y`).
- The meta pack's version history is a file you can diff: `versions/gen_001/roles/...`, a one-line diff (`test_the_meta_packs_version_history_is_a_file_you_can_diff`).

**What to notice.** Two clocks in one table. The task skills moved after
problems 1 (the policy line) and 5 (cards) through the gate, and the
verifier's cards moved on every problem the log allowed; the meta-skills
moved exactly twice, after problems 3 and 6, each time one line of one
role file, each time with a `y`, each time leaving a version you can diff.
The curve is lesson 09's: the slow loop's two edits changed how the fast
loop *would* act, and the next problems will tell whether that was wise.
This is the "and so on" of the series: the pack that patches the pack is
itself a pack with a version history, and its changes are rarer and gated
harder.

## Lesson 17: The map - the ladder, every method's curve side by side, and who approved what

**The idea.** The map back to the literature: the paper's ladder with
lessons 01-16 placed on it by the decision each moved, every method's curve
on the same curriculum read from the `curve.json` each lesson's `run.py`
wrote, the file-and-approver table, the terms, and the acceptance test.

**Rung.** None: nothing runs, nothing is proposed. The tables are the
human's reading of the series, and the page may not claim more than the L5
*flavour* - it does not.

**Files that change.**

```text
step_17_map/
  run.py          the map as data: LADDER, FILES, TERMS, CURVES, REPORTED; reads every lesson's curve.json
  test_step.py    the claims below
  README.md       the ladder, the file-and-approver table, the rungs refused, the terminology, the acceptance test, the reported numbers
```

**Build.** The map is data:

`step_17_map/run.py`:

```python
LADDER = [
    ("not RSI (B0 / AutoML / harness engineering)", ["01", "02", "04"], "none: a fixed procedure", "everything"),
```

```python
CURVES = {
    "07 proof": "step_07_proof/runs/curriculum/curve.json",
```

**Run.** No model, no key, no approval: it reads files. Run the other
lessons first, or read the table on the course page.

```bash
cd rsi/step_17_map
python run.py
```

```powershell
cd rsi\step_17_map
python run.py
```

**See.** After every lesson's `run.py` had been run once with
`FAKE_MODEL=1`; the ladder, the file table, the terms and the reported
numbers are elided (they are the tables on the lesson page).

```text
Learning curves on the same curriculum (memory arm - MEMORY_OFF arm, best val, per problem):
  lesson               adult_income  breast_cancer           wine         digits  synth_shift_a  synth_shift_b  wasted m/c
  07 proof                  +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  09 meta (human)           +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  09 meta (gate)            +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  10 Dream-RSI              +0.0000        +0.0012        +0.0000        +0.0001        +0.0000        +0.0646       29/33
  11 RSIAgent               +0.0000        +0.0000        +0.0000        +0.0000        +0.0000        -0.0270       27/33
  13 Recuris                +0.0000        +0.0000        +0.0000        +0.0000        +0.0024        +0.0646        6/33
  14 DGM                    +0.0000        +0.0012        +0.0000        +0.0000        +0.0000        +0.0000       33/33
  16 MetaSkill              +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
```

**What the test proves.**

- The ladder places every lesson 00-16 on a rung, with the decision that moved and what stayed human; 09 sits on two rungs (`test_the_ladder_places_every_lesson_on_a_rung`).
- The side-by-side table reads each lesson's `curve.json` and names the lessons not yet run (`test_the_side_by_side_curve_reads_each_lessons_curve_and_names_the_missing`).
- Every lesson 01-16 has a file-and-approver row (`test_every_lesson_has_a_file_and_an_approver_row`).
- The six terms are defined, and genuine RSI is marked as not reached (`test_the_six_terms_are_defined`).
- Every external number is printed as reported with a source, and every source is cited on the page (`test_every_external_number_is_marked_reported_with_a_source`).

**What to notice.** The cards-and-policy-line family (07, 09, 16) reaches
the same +0.065 on problem 6 and wastes 19 fits over the curriculum against
the static walk's 33; Recuris (13) gets the same gain from its skill
package with the fewest wasted fits (6). Dream-RSI (10) flips the line to
`random` on the easy problems and pays for it on problem 5. RSIAgent (11)
is flat and loses 0.027 on problem 6. The DGM lineage (14) never left
`static`. AIDE² (15) and ModularRSI (12) do not run the curriculum
arm-against-arm and are not in this table. The lesson page also lists the
rungs this series refuses to touch - ScienceBuddy's outer RL loop over the
weights, OpenAI's stated priority - and the five-point acceptance test
(structural recursion, safe inheritance, autonomy attribution, reliable
verification, effective recursion), each of which is a test somewhere in
`python run_tests.py rsi`.

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
  generation n+1 boots what generation n wrote (lesson 09's checksums).
- **Effective recursion** - the successor is stronger under a comparable
  budget and an independent evaluation: the memory arm beats `MEMORY_OFF`
  at the same budget on the curriculum and on the exam (lesson 07).
- **The three challenges** - *safe inheritance* (transfer tests, version
  histories, rollback: `versions/`, `rollback`, the archive), *autonomy
  attribution* (which decision moved and which stayed human: every lesson's
  Governance section, `patches:`, `tools.md`, the contract), *reliable
  verification* (a protected evaluator: the locked test, the private split,
  the exam never written to, evaluators frozen per epoch).
- **Bounded RSI** - a loop that revises its own state or procedure inside
  limits a human set, with an off switch: lessons 06-16. **Genuine RSI** -
  the paper's bar; not reached here, and said so.

**Ours:**

- **Pack** - a directory with `SKILL.md` (front matter, then the body that
  becomes the system prompt) and sibling files (`tools.md`, `schema.json`,
  `memory.json`, `loop.json`, ...). The harness boots it; the model is
  configured by nothing else.
- **Actor / verifier / meta pack** - the pack that fits (the inner pack),
  the pack that turns the log into cards without seeing the actor's
  transcript, and the pack that patches another pack between two problems.
  A **writer** (03, 05, 08) is a meta pack whose output is a whole pack.
- **Card** - one typed entry of `memory.json`: IF a profile condition THEN
  prefer or forbid one field value, with `evidence` and `counter` counts. A
  card is active while its evidence is at least twice its counters; a
  forbid card makes `fit_recipe` refuse a recipe at no cost. Lesson 13's
  **skill card** is the markdown-file form of the same idea.
- **Gate** - a tool that enforces what a skill says: the budget refuses fit
  25, the locked test refuses a second `score_test`, `write_card` refuses
  a card that names the test, `patch_pack` refuses a file outside
  `patches:`. The **private gate** (09, 12, 14, 16) is keep-or-rollback
  decided by a score on the private split.
- **Approval cycle** - `propose` -> show -> `y` / `n` / `edit` -> `apply`.
  The human is the acceptance rule; `n` lands nothing, `edit` lands the
  human's version. `approval: human`, `gate` or `both` in a meta pack's
  front matter says who answers.
- **Budget, FREEZE** - 24 fits per arm, counted by an object; FREEZE is the
  moment the budget is spent, after which the test may be scored once and
  the memory may not change.
- **Arm** - one run of one pack on one problem and seed: the **memory arm**
  as the pack is, the **control arm** (`MEMORY_OFF`) with no cards loaded.
  The curve is memory minus control, per problem.
- **Private split** - the fourth part of the one four-way split (train 55 %,
  val 15 %, private 10 %, test 20 %, one seeded shuffle): the gate's rows,
  which no inner pack ever sees. The **locked test** is the fifth of those
  rows scored once after FREEZE.
- **Profile** - the five keys a card may condition on (`n_rows`,
  `n_features`, `n_classes`, `imbalance`, `has_categorical`), computed per
  problem, given to the verifier with the log.
- **Curriculum, exam** - `tasks/01..06`, solved in order with the pack
  carried forward; `tasks/07_exam.json`, which no verifier ever wrote from,
  run with the pack frozen over five seeds.
- **Wasted fits** - the fits an arm spent before its first recipe within
  0.005 of the bar (the control arm's best val); the cost half of every
  curve row.
- **Versions** - `versions/gen_NNN/` under a run: a snapshot of the target
  pack with a checksum manifest before every patch lands, restored by
  `rollback`. Lesson 14's **archive** is the same idea with a held-out
  score per variant and a parent rule.
- **Trace** - `traces.jsonl`, append-only, one JSON line per fit, boot,
  card, verdict; the verifier reads pairs from it, Dream-RSI replays it, the
  tests assert from it.
