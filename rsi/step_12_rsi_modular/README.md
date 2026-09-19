# Lesson 12 - ModularRSI: a harness module, evolved off the benchmark

ModularRSI (arXiv:2609.14857) treats the agent harness as modules - agent
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

## Getting started

New: `.claude/skills/actor-a/` and `actor-b/` (the actor split into
`modules/agent_loop.md`, `tool_use.md`, `observation.md`, `context.md`,
`completion.md`; `SKILL.md` only names them), `.claude/skills/modular-meta/`,
the verifier (run once per actor), and `pool/` with two task files. One
script: `../tools/contrast.py`. Reset after a run: `git checkout --
.claude/skills pool`, mirror, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the modular-meta skill: run both actors on the pool, contrast them, and patch the losing actor's module if the bug is localised.
   ```

   After the pool run (both actors, memory arms, the verifier for each on
   both tasks) the meta pack runs:

   ```bash
   python ../tools/contrast.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json --a .claude/skills/actor-a --b .claude/skills/actor-b --tasks pool
   python ../tools/patch_pack.py --pack .claude/skills/modular-meta --task pool/02_pool_trees_2.json --target .claude/skills/actor-a --files @runs/modular-meta/patch --recipe model=hgb,hyper=0.3,scale=yes,encode=onehot,class_weight=balanced --summary "modules/context.md <- actor-b's text" --visit 1
   ```

   No approval prompt: the pool's private gate decides.

2. By hand: patch `SKILL.md` instead - `may patch ['modules/*.md'] only`;
   ask the meta pack to fit - `not in modular-meta's tools.md`.

3. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/actor-a/modules/context.md` - the one module the two actors
differ in (actor B's says `obey-memory`):

```markdown
# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter` is at most half the `evidence`.
- Search policy: static
  (static: walk `schema.json` -> `recipes` in order, cards or no cards: `--recipes @P/schema.json`.)
- MEMORY_OFF (`--memory off` on the arm, or `config.json`): no card is read; you run the static order.
```

`.claude/skills/modular-meta/SKILL.md`:

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

`../tools/contrast.py`:

```python
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
```

```python
    winner = max((na, nb), key=lambda n: wins[n]) if decided and wins[na] != wins[nb] else None
    module = differing[0] if len(differing) == 1 else None
```

The recorded run (Claude Code 2.1.278, headless, 33 turns, 621 s; the
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

Files:

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

## Governance considerations

- **Who approves what.** The pool task's private gate; the module boundaries
  (`patches:`), the allow-list and the pool are the human's.
- **The hook.** The locked test.
- **What the script refuses.** A patch outside `modules/*.md`; a fit for the
  meta pack; a patch the private split scores lower (rolled back).
- **What is and is not self-modified.** One module file of one actor, with
  a snapshot. `SKILL.md`, `schema.json`, the verifier and the pool are not.

## How to measure it

| Claim | Test |
|---|---|
| contrast names `modules/context.md` and the winner (actor B, once the cards exist; pool task 1 is a tie), spends zero fits; the meta pack cannot fit | `test_contrast_names_the_differing_module_and_the_winner` |
| the patch touches exactly one module file, is validated on the pool task's private split (no eval-table run exists), and helps the loser on a fresh seed | `test_patch_touches_exactly_one_module_validated_on_the_pool_and_helps_the_loser` |
| the pool is disjoint from the curriculum and the exam | `test_pool_is_disjoint_from_the_curriculum` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

What to notice: the pool tables carry 1500 rows because on 400-row tables
the 40-row private split disagreed with validation (0.9427 vs 0.9068 for
recipes ranked the other way on val) and rejected a patch that helped; a
gate on a split that small is a coin, and the lesson says so.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 13 - Recuris](../step_13_rsi_skill_memory/README.md). Previous:
[Lesson 11 - RSIAgent](../step_11_rsi_agent/README.md).
