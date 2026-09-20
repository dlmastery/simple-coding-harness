# Lesson 12 - ModularRSI: a harness module, evolved off the benchmark

ModularRSI (arXiv:2609.14857) treats the harness as modules - agent loop,
tool use, observation management, context management, task completion - and
evolves one at a time, validated on tasks disjoint from the benchmark. Here
the actor's `SKILL.md` is a one-line pointer and the harness is five files
under `modules/`. Two actors ship, `actor-a` and `actor-b`, identical except
`modules/context.md` (one walks the static list, the other obeys memory).
Both run the two tables of `pool/` - seeded `make_classification` tables no
curriculum or exam problem uses - with the verifier writing to each. Then
the meta pack's `contrast` pairs the success with the failure per pool task,
names the one module whose text differs, and the loser gets the winner's
module: one file, proposed, gated on the pool task's private split, never on
the eval table. A patch that helps both actors improved the workshop, not
one model's quirks; a benchmark-disjoint pool is what kills leaderboard
overfitting. L2 in the choice of what to patch, L5 flavour in patching the
harness text; the module boundaries and the pool stay human.

## Getting started

Prerequisites: lesson 09 (the gate). This lesson ships `pool/` (two
`intent.md` directories, `role: pool`), two five-module actors, the
verifier (writing to whichever actor is named), and `modular-meta` with the
`contrast` contract and `patches: ["modules/*.md"]`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the modular-meta skill: run both actors on the two pool tables (memory arms, the verifier after each), contrast them, patch the losing actor's differing module behind the gate, and report.
   ```

2. No approval: the gate decides on the pool task's private split.

3. Headless, as the live test runs it:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the two actors differ in
   exactly `context.md`; the pool's seeds are disjoint from the curriculum's;
   the meta pack patches one module, on the pool only. `RSI_LIVE=1`: both
   actors frozen and scored once on both pool tables; no curriculum table
   under either actor's `runs/`; a `contrast` event naming `context.md` (or
   `null`); if localised, a `gate` event and a version under the loser.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/actor-a/modules/context.md` and `actor-b`'s - the one line
that differs:

```markdown
# Module: context
- The cards in `memory.json` apply when their `if` holds for the profile, `evidence` >= 1 and `counter * 2 < evidence`.
- Search policy: static
  (static: walk `schema.json -> recipes` in order, cards or no cards.)
- MEMORY_OFF (`--memory off` on the arm, or `config.md`): no card is read; you run the static order.
```

`.claude/skills/actor-a/SKILL.md` - the harness is the modules:

```markdown
## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `memory.schema.json`, `config.md`, `memory.json`. 4. `modules/agent_loop.md`, `modules/tool_use.md`, `modules/observation.md`, `modules/context.md`, `modules/completion.md` - the harness is these five files, and the procedure below only says in which order to read them.

## Procedure
1. Do what `modules/agent_loop.md` says, reading `modules/context.md` for the next recipes, `modules/observation.md` for the result and `modules/completion.md` at FREEZE, under the rules of `modules/tool_use.md`.
```

`.claude/skills/modular-meta/tools.md` - the contrast contract:

```markdown
- `contrast(pack, task, a, b, tasks)` - for every pool problem both actors ran (memory arms), pair the success (the higher best val) with the failure; name the one `modules/*.md` file whose text differs between the two packs (`module`; null when none or several differ), return both texts, and the `winner` (the actor that won more pool problems; null on a tie) with its best pool recipe. No fit is spent.
```

`pool/01_pool_trees_1/intent.md` - a pool problem's front matter:

```markdown
role: pool
data:
  kind: synthetic
  n_samples: 500
  n_features: 8
  n_informative: 4
  n_redundant: 1
  n_clusters_per_class: 3
  class_sep: 0.7
  flip_y: 0.05
  weights: [0.7, 0.3]
  random_state: 101
```

`test_step.py`:

```python
    assert [n for n in a if a[n] != b[n]] == ["context.md"]
```

The recorded run (not yet recorded on this machine; the weekly usage cap was reached
before this lesson's turn - the block below says how to produce it):

```text
Recording pending - this lesson's transcript has not been recorded yet.
Run it here to produce it (about ten minutes in Claude Code; the live test records the run
under runs/_recording/ and asserts on the artifacts):

    RSI_LIVE=1 python -m pytest -q test_step.py -k live -s

Nothing above is invented: the pack, the contracts and the tests are complete, and the
"What to notice" paragraph will be written from the recording.
```

Files:

```text
step_12_rsi_modular/
├── README.md
├── test_step.py
├── pool/01_pool_trees_1/intent.md, 02_pool_trees_2/intent.md   the benchmark-disjoint pool
├── .claude/settings.json
├── .claude/skills/
│   ├── actor-a/                      SKILL.md (a pointer), modules/{agent_loop,tool_use,observation,context,completion}.md, schema.json, memory.json ...
│   ├── actor-b/                      the same, context.md says obey-memory
│   ├── adult-income-verifier/        writes to whichever actor --pack names
│   └── modular-meta/                 SKILL.md, tools.md (contrast, propose, gate ...), config.md
├── .agents/skills/                   the same
└── runs/                             (after a run) actor-a/, actor-b/ (pool tasks only), modular-meta/
```

## Governance considerations

- **Who approves what.** The gate, on the pool's private split. The human
  wrote the module boundaries, the pool and the one-module rule.
- **The hook.** As always.
- **What the helper refuses.** `propose` refuses any file outside
  `modules/*.md` and more than one module; `contrast` names nothing when no
  single module differs; the eval table is never opened by the meta pack.
- **What is and is not self-modified.** One `modules/*.md` of the losing
  actor (versioned). The pool, the module list and the gate do not change.
- **Attribution.** The patch is the winner's text, not the meta pack's
  invention: ModularRSI's contrast localises, it does not compose.

## How to measure it

| Claim | Test |
|---|---|
| the two actors have the same five modules and differ in `context.md` only (static vs obey-memory) | `test_two_actors_differ_in_exactly_one_module` |
| the pool has two `role: pool` problems whose seeds are not the curriculum's | `test_the_pool_is_disjoint_from_the_curriculum` |
| the meta pack patches one module, on the pool, behind the gate; the eval table is never used | `test_meta_patches_one_module_on_the_pool_only` |
| the pack contract for four packs and the two pool intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: both actors on both pool tables, no curriculum table touched, a contrast, a gate and a version when localised (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 13 - Recuris](../step_13_rsi_skill_memory/README.md): memory as a
skill package with a working memory. Previous:
[lesson 11 - RSIAgent](../step_11_rsi_agent/README.md).
