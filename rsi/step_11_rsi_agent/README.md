# Lesson 11 - RSIAgent: the next experiment, chosen on purpose; the memory, frozen at test

RSIAgent (arXiv:2609.15364) splits the loop into a curriculum module that
picks the next experiment by uncertainty, an actor that runs it, and a
verifier that sees only the world's result. Here the planner
(`adult-income-planner`) scores every model family by
`u = (1 - success) + c / (n + 1)` and writes twelve experiments into the
actor's `plan.json`: a broad phase (`c = 2.0`) that touches every family
before repeating one, then a deep phase (`c = 0.25`) that goes where the
faults are. The actor (`adult-income-actor`) proposes nothing of its own -
every memory-arm fit is an experiment from the plan, and it cannot read the
memory or write a plan (`tools.md`, enforced). The memory is frozen while the
actor runs: the verifier writes after `score_test`, and on the transfer
table (the exam) no card lands at all. L3 in the framework's terms - the
system chooses which experience to acquire; the uncertainty rule and the
phase lengths stay human.

## Getting started

Lesson 07's actor becomes `adult-income-actor` (a `plan.json` added, the
`read_memory` tool removed), the planner is new, the verifier and the
curriculum skill are lesson 07's with the planner inserted. One script:
`../tools/write_plan.py` (`--uncertainty` prints the numbers; `--plan`
writes the file). `fit_recipe.py --recipes @<actor>/plan.json` fits a plan.
Reset after a run: `echo "[]" > .claude/skills/adult-income-actor/memory.json`,
the shipped one-experiment `plan.json`, the mirror, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the six curriculum problems with the planner choosing the actor's experiments, then the exam, and report the curve and the exam.
   ```

   Per memory arm the agent runs the planner twice (broad, then deep) and
   the actor's plan fits:

   ```bash
   python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-actor --uncertainty --c 2.0
   python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-actor --plan '{"phase": "broad", "c": 2.0, "experiments": [ ...12 recipes... ]}'
   python ../tools/fit_recipe.py --pack .claude/skills/adult-income-actor --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-actor/plan.json
   ```

   then the same with `--c 0.25` and `"phase": "deep"`. PowerShell: write
   the plan to a file and pass `--plan '@plan.json'`. No approval prompt.

2. By hand: `python ../tools/write_plan.py --pack .claude/skills/adult-income-actor ...`
   answers `not in adult-income-actor's tools.md` (the actor cannot plan);
   `python ../tools/fit_recipe.py --pack .claude/skills/adult-income-planner ...`
   answers `not in adult-income-planner's tools.md` (the planner cannot fit).

3. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-planner/SKILL.md` - the rule and its numbers:

```markdown
---
name: adult-income-planner
description: RSIAgent's curriculum module - choose the actor's next experiments by uncertainty (a broad phase that touches every model family, then a deep phase that goes where the faults are) and write them to the actor's plan.json. Use in rsi/step_11_rsi_agent before the actor's first fit on a problem and again when its plan runs dry.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# RSIAgent's curriculum: the next experiment, chosen on purpose

## Procedure
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far and `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline). The script prints these per family; check them.
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
   In the broad phase every family starts equal and the large `c` makes the plan round-robin: every family is touched before any is repeated. In the deep phase the small `c` lets `1 - success` dominate: the family with the most faults (fits below the baseline, or errors) comes first.
3. Build the plan greedily: 12 times, take the family with the highest `u` (ties: the family the cards prefer, then schema order), give it its next untried recipe (static recipes of `schema.json` -> `recipes` before hyper variants; inside those, the recipes carrying the most card-preferred values first), and count that experiment as one more fit for the family (recompute `u` with `n + 1` and the same success).
```

`../tools/write_plan.py` - the numbers, and the plan as the only thing the
actor fits:

```python
def uncertainty(rows, c, models):
    """Per family: n, wins, success, u - the numbers the planner ranks families by."""
    baseline = next((r["val_score"] for r in rows if r["val_score"] is not None), None)
    out = {}
    for m in models:
        mine = [r for r in rows if r["recipe"]["model"] == m]
        n = len(mine)
        wins = sum(1 for r in mine if r["val_score"] is not None and baseline is not None and r["val_score"] >= baseline)
        faults = sum(1 for r in mine if r["val_score"] is None or (baseline is not None and r["val_score"] < baseline))
        success = (wins + 1) / (n + 2)
        out[m] = {"n": n, "wins": wins, "faults": faults, "success": round(success, 4), "u": round((1 - success) + c / (n + 1), 4)}
    return out
```

`.claude/skills/adult-income-actor/tools.md` - the actor's world:

```markdown
## Forbidden
- write_plan - the planner writes the plan, run for the planner pack
- read_memory - the cards are the planner's input, not yours: you run experiments
- write_card, read_traces - the verifier's tools
```

RECORDING_11

Files:

```text
step_11_rsi_agent/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-actor/        SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, eval.md, plan.json (scratch)
├── .claude/skills/adult-income-planner/      SKILL.md, tools.md
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/
└── .agents/skills/...
```

## Governance considerations

- **Who approves what.** Nobody per experiment: the human wrote the
  uncertainty rule, `c` for each phase and the phase length, and the
  planner applies them. The verifier writes after the score, never before.
- **The hook.** The locked test.
- **What the script refuses.** `write_plan.py` for the actor; `fit_recipe.py`
  for the planner; a plan that is not `{phase, c, experiments}` or holds a
  recipe outside the schema; `write_card.py` on the exam (frozen memory).
- **What is and is not self-modified.** `plan.json` is rewritten every phase
  (scratch, excluded from the pack's checksums); `memory.json` changes after
  the score, by the verifier; nothing else.

## How to measure it

| Claim | Test |
|---|---|
| the broad phase touches every family before the deep phase repeats one, and stays round-robin under `c = 2.0` | `test_broad_touches_every_family_before_deep_repeats_one` |
| the deep phase's first experiment goes to the family with the most faults | `test_deep_phase_prefers_the_family_with_the_most_faults` |
| the actor fits only what the plan says; it cannot read memory or write a plan; the planner cannot fit | `test_actor_fits_only_the_plan_and_cannot_read_memory_or_write_a_plan` |
| no card lands before `score_test`; on the transfer table the memory is frozen and unchanged | `test_memory_frozen_before_score_and_unchanged_on_the_transfer_table` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 12 - ModularRSI](../step_12_rsi_modular/README.md): a harness module,
evolved off the benchmark. Previous:
[Lesson 10 - Dream-RSI](../step_10_rsi_dream/README.md).
