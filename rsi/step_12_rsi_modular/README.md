# Lesson 12 - ModularRSI: a harness module, evolved off the benchmark

ModularRSI (arXiv:2609.14857) treats the agent harness as modules - agent
loop, tool use, observation management, context management, task completion
detection - and evolves them one at a time on data the benchmark never sees.
Here the actor's procedure is split into those five files under
`modules/`, two actor packs differ in exactly one of them (`context.md`: the
search policy), and both run a **pool** of synthetic tables that no
curriculum or exam problem uses. The one new tool, `contrast`, pairs the
success and the failure on each pool table and names the module whose text
differs. The meta pack may patch `modules/*.md` only, one file per visit,
under the private gate of the pool table; the eval table is never touched
until the patched pack is checked on it afterwards - with two fake actors of
different quirks, because a patch that helps one model's habits is not a
better workshop.

## Getting started

Lesson 11 left three packs and `resume`. This lesson adds
`skills/actor-a/` and `skills/actor-b/` (identical but for
`modules/context.md`), `skills/modular-meta/` (`patches: ["modules/*.md"]`,
`approval: gate`), the pool under `pool/` (two `task.json` files with seeds
203 and 206), the tool `contrast`, and the fake model's `style` quirk
(`default` walks lists forwards, `reverse` backwards).

## How to execute it

1. Run the pool, the contrast, the patch and the transfer check:

   ```bash
   cd rsi/step_12_rsi_modular
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_12_rsi_modular
   $env:FAKE_MODEL = "1"; python run.py
   ```

   No prompt: the meta pack runs under `approval: gate`, so the pool
   table's private split decides and you read the verdict in the output.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/actor-a/SKILL.md` - the procedure is now five files:

```markdown
## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `memory.schema.json`, `memory.json`, `eval.md`. 4. The five modules, in this order: `modules/agent_loop.md`, `modules/tool_use.md`, `modules/observation.md`, `modules/context.md`, `modules/completion.md`. Follow them as one procedure; each owns one concern and a meta pack patches one at a time.
```

`skills/actor-a/modules/context.md` (actor-b's says `obey-memory`):

```markdown
# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: static
```

`skills/modular-meta/SKILL.md`:

```markdown
---
name: modular-meta
description: Localise a harness bug to one module by contrasting two actor packs on a benchmark-disjoint pool, patch that one module of the losing pack with the winning text, and validate on the pool before it lands. Use after both actors have run every pool task.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: gate
  patches: ["modules/*.md"]
---
```

The tool:

`../common/tools.py`:

```python
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
    problems = sorted({r["problem"] for r in run.trace.rows("fit", arm=a)} & {r["problem"] for r in run.trace.rows("fit", arm=b)})
```

```python
        success, failure = (a, b) if (best[a]["val"] or 0) > (best[b]["val"] or 0) else (b, a)
        pairs.append({"problem": problem, "success": success, "failure": failure, "best": best})
```

And the allow-list `patch_pack` enforces:

```python
        if allowed_paths and not any(fnmatch(name, pat) for pat in allowed_paths):
            raise ValueError(f"this meta pack may patch {allowed_paths} only, not {name}")
```

Expected output, on this machine (`FAKE_MODEL=1`; the eval table is
curriculum problem 6, `synth_shift_b`):

```text
contrast: module modules/context.md, winner actor-b, wins {"actor-a": 0, "actor-b": 2}
  pool_trees_1: success actor-b (0.8624) vs failure actor-a (0.8399)
  pool_trees_2: success actor-b (0.8962) vs failure actor-a (0.8638)
patch: {"id": "g1", "decision": "y", "gate": {"before": 0.9068, "after": 0.9068, "keep": true}, "landed": true, "version": "gen_001", "files": ["modules/context.md"]}
actor-a on the eval table synth_shift_b before the patch: {"default": 0.7925, "reverse": 0.7925}; after: {"default": 0.8571, "reverse": 0.8571}
modules of actor-a now equal to actor-b's: True
```

Two pool tables, two wins for actor-b, one module named, one patch through
the pool's private gate; then the eval table, untouched until now, agrees
for both fake actors: 0.7925 -> 0.8571. The pool did the localising; the
eval table only confirmed.

Files:

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
  pool/01_pool_trees_1.json, pool/02_pool_trees_2.json   the benchmark-disjoint tables
  run.py                      both actors on the pool -> contrast -> patch -> the eval table with two fake actors
  test_step.py                the claims below
  README.md                   this lesson
```

## Governance considerations

- Who approves what: the pool table's private split (`approval: gate`);
  the human chose the pool, the module boundaries and the allow-list.
- Off switches: `META_OFF` is not wired here (one visit, no loop); the
  gate's rollback is the stop.
- What the model may not do, and which tool enforces it: patch anything
  outside `modules/*.md` (`patches:` in the front matter, enforced by
  `patch_pack`); patch two modules at once (the meta's rule, and the test
  asserts the diff); validate on the eval table (the meta pack is booted
  on a pool task, so `private_gate` scores the pool's private split); fit
  or score (`tools.md`).
- What is and is not self-modified: one module file of actor-a. The other
  four modules, the pool, the gate and the actor quirks are not. Rung: L2
  for the choice, L5 flavour for a harness module changing off-benchmark,
  with the boundaries and the pool human.

## How to measure it

| Claim | Test |
|---|---|
| `contrast` names the module whose text differs between the success and the failure, per pool table | `test_contrast_names_the_module_whose_text_differs` |
| the patch touches exactly one module file; `SKILL.md` is refused by the allow-list | `test_the_patch_touches_exactly_one_module_file` |
| validation runs on the pool, never the eval table (the gate's problem is a pool table; the pool log holds no other) | `test_validation_runs_on_the_pool_never_the_eval_table` |
| the patched module helps both fake actors on the eval table | `test_the_patched_module_helps_both_fake_actors` |

Scorecard fields: the pool runs and the eval checks report best val per
arm; the `contrast` and `gate` trace rows carry the pairs and the verdict.
Run `python run_tests.py rsi` from the repo root.

## Next lesson

Next: [13 - Recuris](../step_13_rsi_skill_memory/README.md): memory as a
skill package with a working memory. Previous:
[11 - RSIAgent](../step_11_rsi_agent/README.md).
