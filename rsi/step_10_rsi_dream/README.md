# Lesson 10 - Dream-RSI: rank the search policies on the log, at zero fits

Dream-RSI (arXiv:2609.14858) replays experience as a simulator. Here the
experience is the fit log, and the thing chosen from it is the actor's
*search policy* - the one line of `SKILL.md` that says how the next 24
recipes are picked. The meta pack, `adult-income-meta-dream`, ranks five
policies (`static`, `obey-memory`, `random`, `neighbours-of-top-3`,
`prefer-untried-family`) by walking each one's first 24 picks against the
log of the problem just finished: a pick the log holds is answered with its
logged score; a pick the log does not hold is `unknown`. No fit is spent -
`rank_policies` reports `fits_spent: 0` and the actor's `state.json` is
unchanged - and the winner is proposed as the policy line behind the private
gate. The honest part is the `unknown` count. The log is an exact gym for
the recipes you visited and silent everywhere else; when every policy's
unknowns are 0 the log is saturated, the next lap will visit nothing new,
and recursion pays only if it does. The page says so instead of hiding it.
This is the paper's L2: the system chooses the search strategy; the policy
library stays human.

## Getting started

Prerequisites: lesson 09 (the gate, `propose`, versions; the actor with
`Search policy: static`). This lesson replaces the meta pack by
`adult-income-meta-dream` (`policies.md`, the `rank_policies` contract,
`patches: ["SKILL.md"]`, `approval: gate`) and teaches the actor the five
policies (`read_memory --order <name>` implements them).

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill with the adult-income-meta-dream meta pack: run the curriculum (problems 1 to 6: control arm, memory arm, verifier, then the replay visit), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report, and list every ranking with its unknown counts and the gate's verdict.
   ```

2. No approval: the winner lands behind the gate or is rolled back.

3. Headless, as recorded:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: `policies.md` names the five
   policies and the actor knows them; the `rank_policies` contract spends
   nothing, counts unknowns and names saturation; only the policy line is
   patched, behind the gate. `RSI_LIVE=1`: every curriculum arm frozen and
   scored once; a `rank` event per problem with `fits_spent` 0; the curve
   and the exam with the pack unchanged; both mirrors equal.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-meta-dream/policies.md`:

```markdown
- `static`: walk `schema.json -> recipes` in order, cards or no cards.
- `obey-memory`: probe one recipe per model (the preferred model first) with the preferred preprocessing; then the believed family - its static recipes, then its hyper variants - ranked by the cards; then the rest of the grid.
- `random`: the 72-recipe grid in a seeded shuffle (`numpy.random.default_rng(seed)`).
- `neighbours-of-top-3`: six static fits, then the untried neighbours (one field away, a model change taking the new model's middle hyper value) of the three best so far, then the static list.
- `prefer-untried-family`: at every step the model family with the fewest fits so far, static recipes before hyper variants.
```

`.claude/skills/adult-income-meta-dream/tools.md` - the simulator contract:

```markdown
- `rank_policies(pack, task, target, policies)` - replay the last problem's memory-arm log as a simulator: for each policy of `policies.md`, walk its first 24 picks (from the cards and, step by step, the picks answered so far); a pick the log holds is answered with the logged `val_score`, a pick the log does not hold is `unknown` and answered with nothing. A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher (a lap that only revisits the log learns nothing). No fit is spent: `fits_spent: 0`, and the target's `state.json` is unchanged. Print the ranking (`policy, best_logged_val, visited, unknown`), `winner`, and `saturated` (true when every policy's unknown count is 0).
```

`.claude/skills/adult-income-meta-dream/SKILL.md` - the rule:

```markdown
## Rules
- Zero fits: `fit_recipe` is forbidden to this pack; `rank_policies` reports `fits_spent: 0` and the actor's budget counter proves it.
- You may patch the `Search policy:` line and nothing else.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new, and recursion pays only if it does.
```

`test_step.py`:

```python
    ranks = [r for t in TASKS if (RUNS / "adult-income-meta-dream" / t / "traces.jsonl").exists()
             for r in rows(RUNS / "adult-income-meta-dream" / t / "traces.jsonl") if r.get("event") in ("rank", "rank_policies")]
    assert ranks and all(r.get("fits_spent", 0) == 0 for r in ranks)
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, the
rankings in full):

<!-- transcript -->

Files:

```text
step_10_rsi_dream/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income/                 lesson 09's actor; the five policies named on the policy line's menu
│   ├── adult-income-verifier/
│   ├── adult-income-meta-dream/      SKILL.md, tools.md (rank_policies, propose, gate ...), policies.md, config.md
│   └── adult-income-curriculum/      actor -> verifier -> replay visit, per problem
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income/{..., versions/}, adult-income-meta-dream/{helpers/, patch/, <task>/}
```

## Governance considerations

- **Who approves what.** Nobody per visit: the private gate. The human
  wrote the policy library (`policies.md`) and the replay rule; the system
  chooses among the five.
- **The hook.** `score_test` after `"frozen": true`. The meta pack never
  calls `apply`; the gate lands.
- **What the helper refuses.** `rank_policies` spends nothing (the budget
  counter is the proof); `propose` refuses any file but `SKILL.md`;
  `fit_recipe` is forbidden to the meta pack.
- **What is and is not self-modified.** The actor's policy line (versioned).
  The policy library, the replay rule and the gate do not change.
- **Honesty.** Saturation is reported, not hidden; wine and digits saturate
  fast in this recipe space.

## How to measure it

| Claim | Test |
|---|---|
| `policies.md` names five policies and the actor's `SKILL.md` knows them | `test_policies_md_names_five_and_the_actor_knows_them` |
| `rank_policies` spends nothing, counts unknowns, names saturation, ranks more unknowns higher at a tie | `test_rank_policies_spends_nothing_and_counts_unknowns` |
| only the policy line is patched, behind the gate | `test_only_the_policy_line_is_patched_behind_the_gate` |
| the pack contract for four packs and the seven intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: arms frozen and scored once, `rank` events with `fits_spent` 0, curve, exam unchanged (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 11 - RSIAgent](../step_11_rsi_agent/README.md): the next
experiment chosen by uncertainty; the memory frozen at test. Previous:
[lesson 09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md).
