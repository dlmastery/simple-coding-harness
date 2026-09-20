# Lesson 11 - RSIAgent: the next experiment, chosen on purpose; the memory, frozen at test

RSIAgent (arXiv:2609.15364) splits the loop into a curriculum module that
chooses experiments, an actor that runs them, and a verifier that sees only
the world result. Here that is three packs. The planner
(`adult-income-planner`) scores every model family by uncertainty
`u = (1 - success) + c / (n + 1)` - a broad phase with `c` 2.0 that
round-robins every family before any is repeated, then a deep phase with
`c` 0.25 that goes where the faults are - and writes 12 experiments at a
time to the actor's `plan.json`. The actor (`adult-income-actor`) runs the
plan and, before it scores the test, freezes its memory: `freeze_memory`
sets `"memory": "frozen"` in the arm's state and every card write refuses
from then on. The verifier writes for the *next* problem. The same 24 fits
buy higher-information experiments, and the comparison at test time is
against a memory that cannot move. L3 (the system chooses which experience
to acquire) plus L4; the verifier stays human-written.

## Getting started

Prerequisites: lesson 07 (the curriculum and the verifier). This lesson adds
the planner pack (`write_plan` contract), `plan.json` and the
`freeze_memory` contract to the actor, and a curriculum that asks the
planner twice per memory arm.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the curriculum (problems 1 to 6: control arm; memory arm with the planner's broad plan, then its deep plan, then freeze_memory before the test; the verifier after the test), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report.
   ```

2. No approval: the planner's rule and the verifier contract are the
   acceptance rules, written beforehand.

3. Headless, as recorded:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the planner states the
   uncertainty rule with both `c` values and 12 experiments per phase; the
   actor runs `plan.json`, never writes it, and freezes the memory before
   `score_test`; `write_plan` refuses a second plan per phase.
   `RSI_LIVE=1`: on every problem the first three fits touch all three
   families, the plan events are `broad` then `deep`, `freeze_memory`
   precedes `score_test` and the state says `frozen`; the exam is unchanged.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-planner/SKILL.md`:

```markdown
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far and `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline). The helper prints these per family; check them.
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
   In the broad phase every family starts equal and the large `c` makes the plan round-robin: every family is touched before any is repeated. In the deep phase the small `c` lets `1 - success` dominate: the family with the most faults (fits below the baseline, or errors) comes first.
3. Build the plan greedily: 12 times, take the family with the highest `u` (ties: the family the cards prefer, then schema order), give it its next untried recipe (static recipes of `schema.json -> recipes` before hyper variants; inside those, the recipes carrying the most card-preferred values first), and count that experiment as one more fit for the family (recompute `u` with `n + 1` and the same success).
```

`.claude/skills/adult-income-actor/SKILL.md` - the plan and the freeze:

```markdown
3. Search, in two phases the planner writes:
   - control arm: walk `schema.json -> recipes` in order, in one call.
   - memory arm: ask the planner (`.claude/skills/adult-income-planner/SKILL.md`) for the broad plan; fit the 12 experiments of `plan.json` in order (`fit_recipe P T --arm memory --recipes <the 12>`); ask the planner again for the deep plan; fit its 12. A recipe a `forbid` card rules out is refused and costs no fit. When `plan.json` holds no untried experiment and fits remain, take the static list's next untried recipe. The 24th fit says `FREEZE`.
   Search policy: planned
   Freeze the memory before the test: `freeze_memory P T --arm memory` sets `"memory": "frozen"` in the arm's state; from then on a card write refuses on this arm; the verifier, run afterwards by the curriculum skill, writes to `memory.json` for the *next* problem, never for the arm that was just scored.
```

`.claude/skills/adult-income-actor/tools.md` - the two contracts:

```markdown
- `freeze_memory(pack, task, arm)` - set `"memory": "frozen"` in the arm's `state.json` and append `{"event": "freeze_memory"}`; refuse before FREEZE. From then on `write_card` refuses for this arm: the comparison at test time is against a memory that cannot move.
```

```markdown
- `write_plan(pack, task, target, plan)` / `write_plan(..., uncertainty=True, c=<c>)` - with `uncertainty`: per model family on this problem's memory arm, `n` (fits so far), `wins` (val at or above the first fit's), `success = (wins + 1) / (n + 2)`, `faults` (fits below the first fit's, or errored) and `u = (1 - success) + c / (n + 1)`; print them. With `plan`: refuse a plan without `phase` (`broad` | `deep`), `c` and exactly 12 `experiments` from `schema.json -> fields`, refuse a second plan in the same phase on the same problem; write it to `<target>/plan.json` (both mirrors), append `{"event": "plan", "phase", "c"}` and print the families in order.
```

`test_step.py`:

```python
        first = fits_of(task)[:3]
        assert {r["recipe"]["model"] for r in first} == {"logreg", "rf", "hgb"}, f"broad phase did not touch every family first on {task}"
        plans = [r for r in rows(RUNS / "adult-income-actor" / task / "memory" / "traces.jsonl") if r.get("event") == "plan"]
        assert [p["phase"] for p in plans] == ["broad", "deep"], task
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, one
planner visit in full):

<!-- transcript -->

Files:

```text
step_11_rsi_agent/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income-planner/         SKILL.md (the uncertainty rule), tools.md (write_plan, read_memory)
│   ├── adult-income-actor/           SKILL.md (runs plan.json, freeze_memory before the test), tools.md, plan.json, memory.json, eval.md ...
│   ├── adult-income-verifier/
│   └── adult-income-curriculum/
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income-actor/, adult-income-planner/helpers/, adult-income-verifier/helpers/
```

## Governance considerations

- **Who approves what.** Nobody per experiment: the planner's rule is the
  human's, the verifier contract is the human's. `plan.json` is written by
  the planner only (`write_plan` refuses a second plan per phase).
- **The hook.** As always.
- **What the helper refuses.** `freeze_memory` before FREEZE; a card write
  on a frozen arm; a plan with the wrong shape.
- **What is and is not self-modified.** `plan.json` (twice per problem) and
  `memory.json` (after the test, for the next problem). The planner's rule
  and its two `c` values are files a human wrote; lesson 16 shows what it
  means to let a slow loop change such numbers.
- **The evidence standard.** Frozen memory at test is what makes the
  comparison fair: the memory arm at `score_test` time holds exactly what it
  held when its 24 fits were chosen.

## How to measure it

| Claim | Test |
|---|---|
| the planner states `u`, `c` broad / deep, 12 per phase, round-robin then faults first | `test_planner_states_the_uncertainty_rule` |
| the actor runs `plan.json`, never writes it, freezes memory before `score_test`; `plan.json` ships empty | `test_actor_runs_the_plan_and_freezes_memory_before_the_test` |
| `write_plan` refuses a second plan per phase and a plan without 12 experiments | `test_write_plan_contract_refuses_a_second_plan_per_phase` |
| the pack contract for four packs | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: broad touches every family first, `broad` then `deep`, `freeze_memory` before `score_test`, the exam unchanged (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 12 - ModularRSI](../step_12_rsi_modular/README.md): a harness module
evolved off the benchmark. Previous: [lesson 10 - Dream-RSI](../step_10_rsi_dream/README.md).
