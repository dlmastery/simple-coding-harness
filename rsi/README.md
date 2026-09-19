# Zero to Hero: Recursive Self-Improvement — a hello world, skills only

**Status: in progress.** The plan of record is [`OUTLINE.md`](OUTLINE.md)
(v3, 19 Sep 2026). Steps land here one at a time; each is a skill pack booted
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
  OUTLINE.md              the plan: definitions, steps, tests, tutorial validation
  common/                 the one skills harness + the tools every skill names
  data/                   bundled Adult sample (6k rows) and how it was made
  step_00_regular_skill/  a repeatable trainer: same SKILL.md every run — not RSI
  step_01_memory_skill/   memory cards + a verifier pack; MEMORY_OFF
  step_02_freeze_and_proof/  freeze, one test score, transfer to a shifted table
  step_03_policy_skill/   rank search policies on the log with zero fits
  step_04_meta_skill/     a meta pack patches the inner pack; private gate; rollback
  step_05_map/            the ladder, the papers, the terminology, the acceptance test
```
