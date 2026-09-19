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
  16 MetaSkill        ROW_16
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
- **Files.** What this lesson adds or changes.
- **Build.** One snippet, quoted from the pack or the code.
- **Run.** The prompt to type.
- **See.** The recorded run on this machine.
- **What the test proves.** One line per claim.
- **What to notice.** What the numbers say, including where the method did
  not pay.
- **Diff from the previous lesson.**

---

## Lesson 00: Intent - what to improve, how, and what counts as success

**The idea.** Before any pack exists, a human writes `task.json` (what to
improve, how, the budget, the locked-test rule) and `acceptance.md` (the
scorecard fields and the pass rule); nothing later may widen them.

**Rung.** The L1 precondition. Everything is human.

**Files.** `task.json`, `acceptance.md`, `.claude/skills/intent/` (`SKILL.md`,
`tools.md`, `widened_pack.json`), `.claude/settings.json`; `tools/validate_intent.py`.

**Build.** `tools/validate_intent.py`:

```python
        if "once" not in text or "FREEZE" not in text:
            problems.append("acceptance.md must state the locked-test rule: scored once, after FREEZE")
```

**Run.** `Use the intent skill in .claude/skills/intent: validate this lesson's intent and report.`

**See.** 8 turns, 90 s: `validate_intent.py` -> `ok: true`, budget 24 per
arm, `roc_auc`, one score after FREEZE, 14 scorecard fields;
`lint_pack.py` on the widened pack -> `n_fits 48 != task budget 24`,
`test_rule differs`; seven tasks listed, six curriculum + one exam.

**What the test proves.** The intent validates; the acceptance fields are
exactly the scorecard fields; a widened pack is refused; a bad task is a
result, not a crash; the skill changes nothing on disk.

**What to notice.** The agent's first attempt reached for `Grep` outside
the lesson directory and the sandbox refused it; everything outside the
lesson comes through the scripts.

**Diff from the previous lesson.** The first one.

## Lesson 01: The regular harness - a repeatable trainer, and not RSI

**The idea.** One command fits the 24 static recipes in order, one scores
the test once after FREEZE; next Monday the same text makes the same fits.

**Rung.** Not RSI (B0 / AutoML). Everything is human.

**Files.** `.claude/skills/adult-income-regular/` (`SKILL.md`, `tools.md`,
`schema.json`); `tools/load_splits.py`, `fit_recipe.py`, `score_test.py`,
`save_model.py`, `scorecard.py`, `_lib/state.py`; `hooks/gate.py`.

**Build.** `tools/_lib/state.py`:

```python
    def spend(self):
        """Count one fit before it happens; the 25th raises. An error still counts: a wasted fit is a fit."""
        s = self.arm_state
        if s["frozen"] or s["fits_used"] >= s["n_fits"]:
            raise ValueError(f"budget of {s['n_fits']} fits used; fit {s['fits_used'] + 1} refused (FREEZE)")
```

**Run.** `Use the adult-income-regular skill: train the Adult income classifier and report the scorecard.`

**See.** 9 turns, 89 s: 24 fits, best val 0.9172 (`hgb, 0.1, yes, onehot,
balanced`), test 0.9034, wasted 16.

**What the test proves.** 24 fits in schema order and one test score; the
25th fit and the second score are refusals; `score_test` before FREEZE is
refused by the script and blocked by the hook (exit 2); a bad call is a
result and spends nothing; the trace is append-only and deterministic.

**What to notice.** The agent's closing remarks ("ordinal hurt logreg",
"scale made no difference for trees") are exactly what the static walk
forgets every Monday; `wasted_fits: 16` is the price.

**Diff from 00.** A pack that fits; the budget, the locked test and the
trace as files under `runs/`.

## Lesson 02: Loop engineering - the loop is a file

**The idea.** `loop.json` names the counter, the bound, the body, the exit
and the illegal moves; the scripts enforce what it declares; the audit log
is written and never read back.

**Rung.** Harness engineering, not RSI.

**Files.** `.claude/skills/adult-income-loop/` (+ `loop.json`, `recipes.json`);
`tools/write_loop_log.py`; `fit_recipe.py --range`.

**Build.** `tools/_lib/packs.py`:

```python
    if loop.get("N") != task["budget"]["n_fits"]:
        problems.append(f"loop.json N {loop.get('N')} != task budget {task['budget']['n_fits']}")
```

**Run.** `Use the adult-income-loop skill: run the loop in loop.json on the Adult income problem and report the scorecard.`

**See.** 18 turns, 181 s: four slices of six with a log call each, FREEZE
at 24, the same 0.9172 / 0.9034 as lesson 01.

**What the test proves.** `loop.json` is honoured (order, `t` 0..23, the
25th fit, the early score); the audit log has 24 lines and no script reads
it; the pack is byte-identical after a run; lint refuses `N` 48.

**What to notice.** The first take exposed a real bug (`--entries` declared
but not read); the agent worked around it one `--entry` at a time and
flagged it without touching the tool. Fixed, re-recorded.

**Diff from 01.** `loop.json`, `recipes.json`, one write-only script.

## Lesson 03: A meta skill generates the loop harness, under human approval

**The idea.** A writer that never fits renders lesson 02's pack from a
template, lints it, proposes it; the human's words land it, edit it, or
reject it.

**Rung.** L1. The spec and the acceptance are human.

**Files.** `.claude/skills/loop-writer/` (`SKILL.md`, `tools.md`, `task.json`,
`template/`); `tools/propose.py`, `apply.py`, `_lib/proposals.py`, `_lib/render.py`.

**Build.** `tools/_lib/proposals.py`:

```python
def classify(words):
    """The user's words -> y / n / edit, by the first word. Anything unclear is a no: nothing lands by default."""
```

**Run.** `Use the loop-writer skill: generate the loop pack for the task in .claude/skills/loop-writer/task.json and propose it to me.` then `--continue "approve"`.

**See.** 20 turns + 1: the five files rendered, `lint ok`, proposal `p1`,
the question; `apply.py --approved "approve"` lands five files with
`approved_by: human`.

**What the test proves.** The writer cannot fit; "no" leaves the disk
untouched; "yes" lands exactly the proposal; "edit" lands the human's text
and an edit that widens the budget does not lint; the same task twice gives
the same proposal; the generated pack passes lesson 02's checks; `apply`
without words is refused and blocked.

**What to notice.** The agent's `recipes.json` differs from the reference
rendering only in whitespace; the content is identical.

**Diff from 02.** A pack that writes a pack; the approval cycle.

## Lesson 04: Graph engineering with loops - the job is a DAG, a recipe is a path

**The idea.** `graph.json` names nodes, edges and constraints; `paths.json`
binds recipes; `walk_path.py` skips and counts an illegal path and refuses
an invented one.

**Rung.** Harness engineering, not RSI.

**Files.** `.claude/skills/adult-income-graph/` (+ `graph.json`, `paths.json`);
`tools/walk_path.py`, `_lib/graph.py`.

**Build.** `tools/_lib/graph.py`:

```python
    if any(nodes[n].get("gate") == "freeze_only" for n in seq):
        return "reaches score_test, a sink that opens only after FREEZE"
```

**Run.** `Use the adult-income-graph skill: walk the graph's paths on the Adult income problem and report the scorecard.`

**See.** 16 turns, 124 s: four walks of six, 0 illegal paths, 0.9172 / 0.9034.

**What the test proves.** Paths in order; an illegal path counted with its
reason; `p99` refused; `fit_recipe` not a tool of this pack; the graph files
byte-identical after a run; lint refuses a cycle.

**Diff from 02.** The loop iterates paths; two immutable files.

## Lesson 05: A meta skill generates the graph harness, under human approval

**The idea.** Lesson 03's writer emits the graph; lint walks it before a
human looks; `edit` lands the human's version, re-linted.

**Rung.** L1.

**Files.** `.claude/skills/graph-writer/` with six templates.

**Build.** `tools/apply.py`:

```python
            problems = lint_payload(payload, run.task)
            if problems:
                raise ValueError(f"the edited pack does not lint: {problems}; nothing lands")
```

**Run.** The graph-writer prompt, then `--continue "edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else"`.

**See.** 20 turns + 6: the graph shown as nodes and edges and a 24-row path
table; the edit applied to a copy, re-linted, landed with the human's words.

**What the test proves.** A cycle or an illegal path is refused before the
human sees it; the proposal shows nodes and edges; an edit that changes a
binding lands and runs, one that lowers `N` or removes a needed edge does
not.

**Diff from 03.** Six templates; the linter walks a DAG.

## Lesson 06: The RSI harness - the first file a later run reads that an earlier run wrote

**The idea.** Typed memory cards (IF profile THEN prefer / forbid one field
value) shape the actor's proposals; a verifier that sees only rows and the
profile writes them; a forbid card makes `fit_recipe.py` refuse at no cost;
`MEMORY_OFF` is the off switch.

**Rung.** L4. The verifier contract, the card schema and the demotion rule
are human.

**Files.** `.claude/skills/adult-income/` (+ `memory.json`, `memory.schema.json`),
`.claude/skills/adult-income-verifier/`; `tools/read_memory.py`, `write_card.py`,
`read_traces.py`, `_lib/memory.py`.

**Build.** `tools/_lib/memory.py`:

```python
def active(card):
    """Some evidence, and at most half as many counterexamples: one counter demotes a one-evidence card."""
    return card["evidence"] >= MIN_EVIDENCE and card["evidence"] >= 2 * card["counter"]
```

**Run.** Both arms on problem 1, the verifier, both arms on problem 2 (the
prompt is on the lesson page).

**See.** 28 turns, 347 s: 9 cards from problem 1; on breast cancer the memory
arm's val 0.9966 / test 0.9883 vs the control's 0.9954 / 0.9844, with the
agent choosing its recipes by the policy text and landing where the
scripted policy lands.

**What the test proves.** `MEMORY_OFF` reproduces lesson 01 exactly; the
verifier's input is rows and the profile; a card naming `test` or `intent`
or an extra field is refused; a wrong card is demoted by one counter; a
forbid card refuses a fit at no cost; the memory arm beats the control arm
on problem 2 after problem 1.

**What to notice.** The agent's own observation - "the model card is keyed
on `n_rows >= 1000`, so hgb's dominance on problem 1 couldn't transfer to a
569-row problem" - is the superstition problem lesson 07's curriculum
exists to catch, made from the profile and the numbers alone.

**Diff from 04.** Two packs; `memory.json` is the first file that changes
because of what happened.

## Lesson 07: Proof - the locked test, the learning curve, the exam

**The idea.** Six problems in order, two arms at the same budget, the
verifier after each; then the frozen pack on the exam over five seeds.
`eval.md` states the claims before the run.

**Rung.** The evidence standard: structural recursion you can see, effective
recursion under a matched budget and an independent evaluation.

**Files.** `eval.md`, `.claude/skills/adult-income-curriculum/`; `tools/curve.py`, `exam.py`.

**Build.** `tools/exam.py`:

```python
        win = gap is not None and (gap > 0 or (gap == 0 and m["wasted_fits"] < c["wasted_fits"]))
```

**Run.** `Use the adult-income-curriculum skill: run the six curriculum problems and the exam, and report the learning curve and the exam tables.`

**See.** 61 turns, 1627 s:

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/11
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/11
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/11
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/1/11
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/11
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      1/0/11
exam: memory arm beats control on 4 of 5 seeds, mean test gap 0.0308; pack unchanged: True; no card written: True
```

**What the test proves.** On the offline curriculum the gap is never
negative and larger on problem 6 than on 2; the test is scored once per
arm; the exam wins >= 3 of 5 with no card written and the pack unchanged;
`config.json` `memory: off` gives the control numbers.

**What to notice.** Wine and digits are saturated and teach nothing; the
curve is carried by the synthetic tables where the model belief and a
demoted `class_weight` card save 14 fits on problem 6; problem 5's test gap
is -0.0003 with a +0.0024 val gap, and the page says so.

**Diff from 06.** `eval.md`, the orchestrator, two measuring scripts.

## Lesson 08: A meta skill generates the RSI harness, under human approval

**The idea.** The writer emits actor and verifier; the proposal shows the
verifier contract first; the human approves a mechanism that will change
itself.

**Rung.** L1 for the generation; what it generates runs at L4.

**Files.** `.claude/skills/rsi-writer/` with `template/actor/` and `template/verifier/`.

**Build.** `tools/_lib/packs.py`:

```python
    if "write_card" in allowed and VERIFIER_CONTRACT not in body:
        problems.append("a verifier pack must state the verifier contract verbatim")
```

**Run.** The rsi-writer prompt, then `--continue "approve"`.

**See.** Nine files rendered; the contract quoted first and a paragraph on
what is being approved; `apply.py` lands both packs side by side.

**What the test proves.** The contract is in the proposal and required;
"no" lands nothing; the packs land without touching the writer and pass
lesson 06's checks; the same task twice gives the same proposal.

**Diff from 05.** Two sub-packs in one proposal; the contract as the
acceptance rule.

## Lesson 09: The RSI meta harness - a pack that patches the pack, problem by problem

**The idea.** Between problems a meta pack reads the log, the cards and the
actor pack and proposes ONE change - the policy line, a `schema.json`
forbid, or cards - snapshot first; under `approval: human` the user's words
land it, under `approval: gate` the private split decides keep-or-rollback.

**Rung.** L4 under the human; L5 flavour under the gate. The gate, the
archive rule and the off switch stay human.

**Files.** `.claude/skills/adult-income-meta/` (human), `adult-income-meta-gate/`
(gate), the actor with `Search policy: static`; `tools/read_pack.py`,
`patch_pack.py`, `private_score.py`, `rollback.py`.

**Build.** `tools/patch_pack.py`:

```python
def private_gate(run, target_run, candidate):
    """Keep-or-rollback on the private split: the candidate must not score below the incumbent."""
```

**Run.** The curriculum prompt naming `adult-income-meta-gate`; the human
variant is a two-turn recording on the lesson page.

**See.** Under the gate, 76 turns, 1650 s: one patch fires - `g1`, the
policy line `static -> obey-memory` after problem 1, kept by the gate on a
tie (0.8951 = 0.8951) as `gen_001` - and rules (b) and (c) never fire; the
curve and the exam are lesson 07's to the fourth decimal. The human
variant, 24 + 1 turns: the diff shown, the question asked, `--approved
"approve"` landed with the words in the trace.

**What the test proves.** Generation n+1 boots the files generation n wrote
(the boot checksums); no patch lands without the user's yes, an edit lands
the user's version; a patch whose evidence recipe scores lower on the
private split is rejected and `versions/` restores the pack; `META_OFF`
leaves the pack byte-identical; one proposal per visit; the size cap; the
test rule cannot be removed; the meta pack cannot score.

**Diff from 07.** The meta packs; `versions/` under `runs/`; the policy line
starts `static` so the first patch is visible.

## Lesson 10: Dream-RSI - rank the search policies on the log, at zero fits

**The idea.** Replay the log as a simulator: each policy's first 24 picks
scored from the log where it has them and `unknown` where it does not; the
winner becomes the policy line through the gate.

**Rung.** L2. The policy library is human.

**Files.** `.claude/skills/adult-income-meta-dream/` (+ `policies.md`); `tools/rank_policies.py`.

**Build.** `tools/rank_policies.py`:

```python
    ranked.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
```

**Run.** The curriculum prompt naming `adult-income-meta-dream`.

**See.** 70 turns, 1495 s: six visits, six flips (`static -> obey-memory ->
random -> neighbours-of-top-3 -> obey-memory -> neighbours-of-top-3 ->
random`), every one kept by the gate; the curve is lesson 07's except
digits (+0.0005) and problem 6's wasted fits (17 vs 3); exam 4 of 5, mean
+0.0282. The log was never saturated.

**What the test proves.** Zero fits (the state is byte-identical); `static`
replays the log fully, `random` and `neighbours-of-top-3` leave it; the
winner becomes the line and the next lap visits new recipes; a saturated
log is reported; only `SKILL.md` may change.

**Diff from 09.** One script and one meta pack; the actor's policy menu.

## Lesson 11: RSIAgent - the next experiment, chosen on purpose; the memory, frozen at test

**The idea.** A planner scores families by `u = (1 - success) + c / (n + 1)`
and writes twelve experiments per phase (broad, then deep) into the actor's
`plan.json`; the actor proposes nothing of its own; the verifier writes
after the score.

**Rung.** L3. The uncertainty rule and the phase lengths are human.

**Files.** `.claude/skills/adult-income-planner/`, `adult-income-actor/` (+ `plan.json`); `tools/write_plan.py`.

**Build.** `tools/write_plan.py`:

```python
        success = (wins + 1) / (n + 2)
        out[m] = {"n": n, "wins": wins, "faults": faults, "success": round(success, 4), "u": round((1 - success) + c / (n + 1), 4)}
```

**Run.** The curriculum prompt on the lesson page.

**See.** 48 turns, 1368 s: broad phases round-robin, deep phases all to
the faultiest family; gaps 0 / 0 / 0 / 0 / 0 / -0.027 (problem 6 lost: the
deep phase never fitted the control's best recipe), wasted 27 vs 33, exam 4
of 5 on ties broken by wasted fits (0 / 6 / 9 vs 16 / 17 / 18), mean test
gap +0.0006.

**What the test proves.** The broad phase is round-robin; the deep phase
goes to the family with the most faults; the actor fits only the plan and
cannot read memory or plan; no card lands before the score and the memory
is unchanged on the transfer table.

**Diff from 09.** The choice of the next experiment moves to a pack.

## Lesson 12: ModularRSI - a harness module, evolved off the benchmark

**The idea.** The actor's procedure is five module files; two actors differ
in one; `contrast.py` pairs their successes and failures on a
benchmark-disjoint pool and names the module; the loser gets the winner's
text, validated on the pool's private split.

**Rung.** L2 -> L5 flavour. The module boundaries and the pool are human.

**Files.** `.claude/skills/actor-a/`, `actor-b/` (with `modules/`),
`modular-meta/`; `pool/`; `tools/contrast.py`.

**Build.** `tools/contrast.py`:

```python
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
```

**Run.** `Use the modular-meta skill: run both actors on the pool, contrast them, and patch the losing actor's module if the bug is localised.`

**See.** 33 turns, 621 s: pool task 1 a tie (no cards yet), pool task 2 B
0.8945 vs A 0.8847; `contrast.py` names `modules/context.md`, winner B;
the patch lands on A after the pool's private gate (0.8737 -> 0.879).

**What the test proves.** Contrast names `modules/context.md` and the
winner; the patch touches exactly that file, is validated on the pool (no
eval-table run exists) and helps the loser on a fresh seed; the pool is
disjoint from the curriculum.

**What to notice.** The pool tables carry 1500 rows because on 400-row
tables the 40-row private split disagreed with validation and rejected a
patch that helped; the page says so.

**Diff from 09.** Modules instead of one procedure; a pool instead of the
curriculum.

## Lesson 13: Recuris - memory as a skill package, with a working memory

**The idea.** Cards are markdown files selected by the situation the working
memory names, never by recency; the meta pack lands one validated card
update per problem and the horizon counts the problems it was updated on.

**Rung.** L4. The validation rule is human.

**Files.** `.claude/skills/adult-income-skills/` (+ `skill-memory/`, `working.md`),
`skill-memory-meta/`; `tools/skill_memory.py`.

**Build.** `tools/skill_memory.py`:

```python
        chosen = [c for c in skill_cards(run.pack_dir) if c.get("validated") and set(c.get("when", [])) <= set(need)]
```

**Run.** The curriculum prompt on the lesson page.

**See.** 70 turns, 1460 s: five card updates over six problems (wine
had no decided pair), horizons 1 / 1 / 2 / 1 / 1; gaps 0 / 0 / 0 / 0 /
+0.0024 / +0.0646 with 6 wasted fits vs 33; exam 4 of 5, mean +0.0306. The
agent caught `exam.py` flagging `working.md` (the actor's own scratch;
fixed) and named the two cards that did not transfer itself, because the
transfer check reads `memory.json` cards only.

**What the test proves.** Selection by need, not recency; an update is one
file, validated, once per visit, by the meta pack only; horizons grow over
the curriculum and the gain is never negative.

**Diff from 06.** `memory.json` becomes a directory of markdown cards plus a
working memory.

## Lesson 14: The Darwin Gödel Machine lineage - the agent's own source, behind an archive and a gate

**The idea.** The meta pack rewrites the actor's `SKILL.md` and `loop.json`
(the policy line and the loop's `policy` field), one generation deep, from a
parent chosen in an archive of variants scored on a fixed held-out
benchmark; the private gate first, then the human.

**Rung.** L5 flavour. The archive rule, the gate and the benchmark are human.

**Files.** `.claude/skills/dgm-meta/` (+ `held-out/`), the actor with
`loop.json`; `tools/archive.py`.

**Build.** `tools/archive.py`:

```python
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
```

**Run.** `Use the dgm-meta skill for generation 1: ...` then `--continue "approve"`.

**See.** 27 + 3 turns: `gen1-static` archived at held-out 0.0 (a static
memory arm walks the control's path), parent `gen1-static`, the rewrite to
`obey-memory` kept by the gate on a tie (0.8737 = 0.8737), then `approve`
landed `SKILL.md` + `loop.json` as `gen_001`.

**What the test proves.** The archive holds every variant with its
held-out score; the parent is chosen by score, not recency; a rewrite that
lowers the private score is rolled back and never archived; only `SKILL.md`
and `loop.json` change; the human comes after the gate.

**Diff from 09.** The harness source is the patch target; an archive with a
parent rule.

## Lesson 15: AIDE² - autoresearch on autoresearch, keep-if-better across the set under one budget

**The idea.** The inner agent is a tree search with operators; the outer
loop rewrites one operator, runs the whole curriculum again as a new
version, and keeps the rewrite only if it is better across the set under
the same budget after an outlier layer.

**Rung.** L5 flavour. The budget, the guards and the task set are human.

**Files.** `.claude/skills/adult-income-aide/` (+ `operators.md`), `aide-outer/`;
`tools/meter.py`; `approval: metered`.

**Build.** `tools/meter.py`:

```python
    keep = bool(kept) and total > 0 and sum(1 for g in kept.values() if g < 0) <= len(kept) // 2
```

**Run.** `Use the aide-outer skill: run version v1 over the curriculum, propose the improve rewrite, run v2 under it, and decide keep-or-rollback across the set.`

**See.** 45 turns, 1198 s: v1 144 fits / 203 calls, v2 144 fits / 211
calls; gains 0 / +0.0005 / 0 / 0 / 0 / 0, no outlier, total +0.0005, kept.
On wine every fit is flagged suspicious and re-run, in both versions alike.

**What the test proves.** The decision needs every problem under equal
budgets (144 fits each) and is made once; a rewrite that wins on one
problem and loses on the set is rolled back; every operator carries the
guard; a suspicious score is flagged and re-run.

**What to notice.** There is no token count: no harness sees the agent's
transcript, so the meter counts fits and script calls and says so. AIDE²'s
own numbers (seven improved versions in 100 outer steps, 16x compression)
are *reported*, from a tech report with no released code.

**Diff from 09.** Operators as the patch target; the decision after a whole
curriculum, not per problem.

## Lesson 16: MetaSkill-Evolve - the improver's skills improve too, slowly

**The idea.** The fast loop's numbers live in role files; the slow loop
changes one line of one role file every k problems, with the human; the
fast loop boots what the slow loop wrote.

**Rung.** L5, with the human on the slow clock.

**Files.** `.claude/skills/task-skills-meta/` (+ `roles/`), `meta-evolver/` (+ `config.json`).

**Build.** `tools/patch_pack.py`:

```python
    if Path(target).resolve() == run.pack_dir:
        raise ValueError("a pack does not patch itself: the target is another pack (the actor, or the fast loop's pack)")
```

**Run.** The curriculum prompt on the lesson page, with your answer at each
slow visit.

**See.** SEE_16

**What the test proves.** Task skills change every problem and meta-skills
only on the clock; a meta-skill change never lands without the human; the
fast loop cannot touch `roles/`, the slow loop cannot touch the actor; the
fast loop boots what the slow loop wrote.

**Diff from 09.** The meta pack's numbers become files; a second, slower,
human-gated loop over them.

## Lesson 17: The map - the ladder, every recorded curve side by side, and who approved what

**The idea.** One script prints the ladder with every lesson placed, the
recorded curves side by side (a lesson not run is named, not invented), the
file-and-approver table, the six terms and every external number marked
*reported*.

**Files.** `.claude/skills/rsi-map/`; `tools/map.py`.

**Run.** `Use the rsi-map skill: print the map and tell me which lessons have a recorded curve.`

**See.** See the lesson page: the ladder, the six recorded curves side by side,
the table of files and approvers, the terms, the reported numbers.

**What the test proves.** Every lesson is on a rung (09 on two); the
side-by-side table reads each lesson's `curve.json` and names the missing;
every lesson has a file-and-approver row; the six terms are defined and
genuine RSI is marked not reached; every external number is *reported* with
a source; the map changes nothing.

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
