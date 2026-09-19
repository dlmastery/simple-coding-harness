# Zero to Hero: Recursive Self-Improvement

## A hello world, skills only: make the agent's own files get better across runs, and prove it

**Status: in progress.** The plan of record is [`OUTLINE.md`](OUTLINE.md)
(v8, 19 Sep 2026). Lessons land here one at a time; each is a skill pack
booted by one tiny skills harness in [`common/`](common/), with a test that
runs without a key. Layout and lesson format follow the Claude Academy
*AI-native SDLC playbook*: six stages, one lesson per step.

The job is real software: a sequence of simple ML problems (Adult income,
breast cancer, wine, digits, two synthetic tables, and a held-out exam), each
under a 24-fit budget, solved in order so that what the harness learned on
problem 1 makes it better at problem 2, then 3 — until the pack is the expert. The agent is configured only by skill files. The thing that improves
is the skill pack — memory cards, a search-policy line, a schema patch, the
harness text itself — behind a verifier that cannot see the actor's story, a
locked test that can be scored once, a human approval cycle, a private gate
and a rollback. Definitions and evidence standards are those of *The Last AI
Built by Humans: Toward Genuine Recursive Self-Improvement*
(arXiv:2609.11873).

## What you'll learn

By the end of this course, you'll be able to:

- Say, in the framework paper's terms, what is and is not recursive
  self-improvement — B0 self-refinement, AutoML, a harness you engineered by
  hand, a harness a meta skill generated — and name the rung (L1–L5) each one
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
  Recuris, the Darwin Gödel Machine, AIDE² and MetaSkill-Evolve each change —
  and point at the file.

## Who this course is for

Engineers who build agents with skills and want to know what "the agent
improves itself" means in files, tests and approvals, not slogans. It is a
hello world on purpose: no OSWorld, no GPUs, no weight updates.

## Prerequisites

Python 3.10+, `pip install -r requirements.txt` from the repo root; the root
codelab's stages 4 (skills), 15 (`execute()`), 30 (evals) and 35 (approval
prompts) are the ideas reused here. Tests need no key; `python run.py` in a
lesson needs `BASE_URL` / `API_KEY` / `MODEL` like the rest of the repo.

Estimated time: about an hour of reading; each lesson's run takes minutes.

## Lessons

```text
rsi/
  OUTLINE.md                          the plan: definitions, format, steps, tests, tutorial validation
  common/                             the one skills harness, the tools every skill names, the approval cycle
  data/                               bundled Adult sample (6k rows) and how it was made
  tasks/                              the curriculum: one task.json per problem, in order, plus the exam
  Stage 1: Plan
  step_00_intent/                     capture what to improve, how, and what counts as success: task.json + acceptance.md
  Stage 2: Design
  step_01_regular_harness/            a repeatable trainer: same SKILL.md every run - not RSI
  step_02_loop_harness/               loop engineering: loop.json, a counted while with a freeze
  step_04_graph_harness/              graph engineering with loops: graph.json + paths.json
  Stage 3: Build
  step_03_meta_generates_loop/        a meta skill writes the loop pack; the human approves, edits or rejects
  step_05_meta_generates_graph/       a meta skill writes the graph pack; lint, then human approval
  step_06_rsi_harness/                memory cards + a verifier pack; MEMORY_OFF
  step_08_meta_generates_rsi/         a meta skill writes the RSI packs; the human approves the verifier contract
  Stage 4: Test
  step_07_proof/                      freeze, one test score per problem, the learning curve across problems, the exam
  Stage 5: Deploy
  step_09_rsi_meta_harness/           problem by problem: inner -> meta -> inner; approval: human or gate; versions + rollback
  Stage 6: Maintain
  step_10_rsi_dream/                  Dream-RSI: rank search policies on the trace log, zero fits
  step_11_rsi_agent/                  RSIAgent: curriculum / actor / verifier, broad-then-deep, frozen memory
  step_12_rsi_modular/                ModularRSI: five module files, contrastive pairs, benchmark-disjoint pool
  step_13_rsi_skill_memory/           Recuris: memory as a skill package + working memory
  step_14_rsi_self_modifying/         DGM lineage: rewrites of SKILL.md/loop.json, an archive of variants
  step_15_rsi_aide2/                  AIDE2: tree-search inner agent, outer loop keeps a rewrite only if better across all problems under one budget
  step_16_rsi_meta_skills/            MetaSkill-Evolve: task skills evolve fast, the meta pack's own skills evolve slowly
  step_17_map/                        the ladder, the papers, every method's learning curve side by side, who approved what
```

Steps are numbered in build order (each reuses the one before); the stage
grouping above is the reading order of the course page.
