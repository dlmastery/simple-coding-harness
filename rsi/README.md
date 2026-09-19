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
