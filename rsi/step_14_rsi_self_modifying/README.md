# Lesson 14 - The Darwin Gödel Machine lineage: the agent's own source, behind an archive and a gate

The Darwin Gödel Machine (arXiv:2505.22954) is the empirical Gödel machine:
an agent that rewrites its own code, keeps an archive of every variant with
its benchmark score, and expands promising stepping stones rather than
always the latest. The framework paper uses it as the attribution example -
SWE-bench 20 -> 50 % while the archive rule and the parent choice stayed
human-fixed. Here the source is the actor's `SKILL.md` and `loop.json` (the
harness text and the loop), the one new tool is `archive`, and the rewrite
is one generation deep: after each problem the current variant runs a fixed
held-out benchmark (two synthetic tables nothing else uses), `archive add`
stores it with its held-out gain over the static walk, `archive parent`
picks the best-scoring variant (ties to the older one, never "the latest"
by default), the meta pack restores that parent and proposes the next
rewrite from it - behind the private gate *and* the human. `patches:`
allows exactly those two files.

## Getting started

Lesson 13 left the skill package. This lesson adds `loop.json` to lesson
09's actor (its `policy` field mirrors the `Search policy:` line),
`skills/dgm-meta/` with `approval: both`, `patches: ["SKILL.md", "loop.json"]`
and `held_out: held-out` (the benchmark directory), the tool `archive`, and
`approval: both` in `patch_pack` (the gate decides first, then the human
sees what the gate kept).

## How to execute it

1. The curriculum with an archive step and a rewrite after every problem:

   ```bash
   cd rsi/step_14_rsi_self_modifying
   FAKE_MODEL=1 python run.py
   FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py     # scripted approvals
   ```

   ```powershell
   cd rsi\step_14_rsi_self_modifying
   $env:FAKE_MODEL = "1"; python run.py
   ```

   At each prompt the diff is a rewrite of `SKILL.md` and `loop.json` that
   the private gate already kept; `n` rolls it back.
2. Read `runs/curriculum/archive/archive.json`: every variant, its problem,
   its held-out gain, its checksums.
3. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/dgm-meta/SKILL.md`:

```markdown
---
name: dgm-meta
description: Rewrite the actor pack's own source - its SKILL.md and loop.json - one generation deep, from a parent chosen in an archive of variants scored on a fixed held-out benchmark, behind the private gate and the human cycle. Use after a problem's actor and verifier runs are done.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: both
  patches: ["SKILL.md", "loop.json"]
  held_out: held-out
---
```

```markdown
3. Call `archive` with action `parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If the parent is not the latest, call `archive` with action `restore` and that label, then `read_pack` again: you now stand on the parent.
```

`skills/adult-income/loop.json` - the second self-modified file:

```json
 "policy": "static",
 "body": [
  "recipe = next recipe of the Search policy",
  "fit_recipe(recipe)"
 ],
```

The archive's two rules, in the tool:

`../common/tools.py`:

```python
        # the parent is the best held-out score, ties to the older variant: never "the latest" by default
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
```

```python
        # the held-out score: over every problem the arm ran, the private score of its best recipe minus the
        # control arm's on the same problem and seed - a gain over the static walk on a fixed benchmark
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y`;
the prompts are elided):

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

Read the archive column. The `obey-memory` rewrite ran problem 2 well
(+0.0012 on val) but scored -0.040 on the held-out benchmark - the cards it
obeyed came from Adult and breast cancer and did not fit two small tree
tables - so it never became a parent; neither did `neighbours-of-top-3`
(-0.036). The parent stayed `adult_income-static`, each rewrite started from
it, and once every variant was in the archive the meta pack had nothing
new to propose. Problems 5 and 6 ran the parent, `static`, and gained
nothing: on this benchmark the lineage found no rewrite better than what it
started with, and the archive says so with a number per variant. A negative
result with a version history is what safe inheritance looks like.

Files:

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
  README.md             this lesson
  runs/curriculum/archive/    (created by run.py) one directory per variant and archive.json
```

## Governance considerations

- Who approves what: the private gate first, then the human, on every
  rewrite (`approval: both`); the human wrote the archive rule (best
  held-out gain, ties to the older), the held-out benchmark and the
  allow-list.
- Off switches: `n` at any prompt (the gate's keep is rolled back);
  `versions/`; the archive's `restore`.
- What the model may not do, and which tool enforces it: rewrite anything
  but `SKILL.md` and `loop.json` (`patches:`, enforced by `patch_pack`);
  make a variant with a worse held-out score the parent (`archive parent`
  is a rule, not a choice); score its own variants (`archive add` reads the
  held-out arm's fits from the trace; the meta pack cannot fit); rewrite a
  rewrite that has not run (one proposal per visit, one archive entry per
  generation).
- What is and is not self-modified: `SKILL.md` and `loop.json` of the
  actor - the harness source. Not: the archive rule, the gate, the
  benchmark, the verifier, `schema.json`, `tools.md`. Rung: L5 flavour,
  with the DGM's own caveat spelled out - the archive rule and the parent
  choice are the human's.

## How to measure it

| Claim | Test |
|---|---|
| the archive holds every variant with its held-out score on the fixed benchmark, and the benchmark shares no problem with the curriculum | `test_the_archive_holds_every_variant_with_its_held_out_score` |
| the parent is chosen from the archive, not always the latest | `test_the_parent_is_chosen_from_the_archive_not_always_the_latest` |
| a rewrite that lowers the held-out score never becomes a parent | `test_a_rewrite_that_lowers_the_held_out_score_never_becomes_a_parent` |
| `SKILL.md` and `loop.json` are the only self-modified files (every apply lists them; other files are refused; the rewrites keep the budget and lint) | `test_skill_md_and_loop_json_are_the_only_self_modified_files` |
| the human can refuse what the gate kept, and the pack rolls back | `test_the_human_can_refuse_what_the_gate_kept` |

Scorecard fields reported: all fourteen per problem and arm, plus the
archive (label, problem, held-out gain per benchmark table) and the apply
rows with the files each rewrite touched. Run `python run_tests.py rsi`
from the repo root.

## Next lesson

Next: [15 - AIDE²](../step_15_rsi_aide2/README.md): autoresearch on
autoresearch, keep-if-better across the whole curriculum under one budget.
Previous: [13 - Recuris](../step_13_rsi_skill_memory/README.md).
