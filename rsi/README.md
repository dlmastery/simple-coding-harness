# Zero to Hero: Recursive Self-Improvement — a hello world, skills only

**Status: in progress.** The plan of record is [`OUTLINE.md`](OUTLINE.md)
(v5, 19 Sep 2026). Steps land here one at a time; each is a skill pack booted
by one tiny skills harness in [`common/`](common/), with a test that runs
without a key (`python run_tests.py rsi` from the repo root).

## What this series is

The third series of this repo. The root codelab builds a coding agent
harness; [`genui/`](../genui/) puts an interface on its output; this one asks
the question the September 2026 papers ask: **can the agent's own files get
better across runs, and how would you know?** It follows the definition and
the evidence standards of *The Last AI Built by Humans: Toward Genuine
Recursive Self-Improvement* (arXiv:2609.11873): persistent changes across
rounds that affect how later improvements are generated, evaluated, selected
or consolidated; structural vs effective recursion; safe inheritance,
autonomy attribution, reliable verification.

The job is real software (an Adult Census Income classifier under a 24-fit
budget), the agent is configured only by skill files, and the thing that
improves is the skill pack: memory cards, a search-policy line, a schema
patch — behind a verifier that cannot see the actor's story, a locked test
that can be scored once, a private gate, and a rollback.

## Layout (when complete)

```text
rsi/
  OUTLINE.md                      the plan: definitions, steps, tests, tutorial validation
  common/                         the one skills harness + the tools every skill names
  data/                           bundled Adult sample (6k rows) and how it was made
  Part 1 - harness engineering, not RSI
  step_00_regular_harness/        a repeatable trainer: same SKILL.md every run
  step_01_loop_harness/           loop engineering: loop.json, a counted while with a freeze
  step_02_graph_harness/          graph engineering with loops: graph.json + paths.json
  step_03_meta_generates_harness/ a meta harness whose output is a harness (one shot, no feedback)
  Part 2 - the first RSI, its proof, the meta harness that makes it
  step_04_rsi_harness/            memory cards + a verifier pack; MEMORY_OFF
  step_05_proof/                  freeze, one test score, transfer to a shifted table, the scorecard
  step_06_meta_generates_rsi_harness/  writer + meta pack: one patch per generation, private gate, rollback
  Part 3 - RSI by method, same job
  step_07_rsi_dream/              Dream-RSI: rank search policies on the trace log, zero fits
  step_08_rsi_agent/              RSIAgent: curriculum / actor / verifier, broad-then-deep, frozen memory
  step_09_rsi_modular/            ModularRSI: five module files, contrastive pairs, benchmark-disjoint pool
  step_10_rsi_skill_memory/       Recuris: memory as a skill package + working memory
  step_11_rsi_self_modifying/     DGM lineage: the meta pack rewrites SKILL.md/loop.json, an archive of variants
  Part 4
  step_12_map/                    the ladder, the papers, file-by-file table, terminology, acceptance test
```
