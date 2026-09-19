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

The recorded run (Claude Code 2.1.278, headless, 48 turns, 1368 s; fit
calls trimmed to the agent's notes and the tables):

```text
[Skill adult-income-curriculum]
agent> Now the memory arm: open, then the planner's broad phase.
$ python ../tools/write_plan.py --pack .claude/skills/adult-income-planner --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-actor --uncertainty --c 2.0
{"phase": "broad", "c": 2.0, "fits_so_far": 0, "families": {"logreg": {"n": 0, "wins": 0, "faults": 0, "success": 0.5, "u": 2.5}, "rf": {...same...}, "hgb": {...same...}}, "tried": []}
$ python ../tools/write_plan.py ... --plan '{"phase": "broad", "c": 2.0, "experiments": [ ...12 recipes... ]}'
{"written": ".../adult-income-actor/plan.json", "phase": "broad", "c": 2.0, "experiments": 12, "families": ["logreg", "rf", "hgb", "logreg", "rf", "hgb", "logreg", "rf", "hgb", "logreg", "rf", "hgb"]}
agent> Broad phase: round-robin logreg/rf/hgb x4, as the rule predicts. Actor fits it.
$ python ../tools/fit_recipe.py --pack .claude/skills/adult-income-actor --task ../tasks/01_adult_income.json --recipes @.claude/skills/adult-income-actor/plan.json
agent> Plan ran dry, 12 fits remain. Planner's deep phase (c = 0.25).
$ python ../tools/write_plan.py ... --uncertainty --c 0.25
{"phase": "deep", "c": 0.25, "fits_so_far": 12, "families": {"logreg": {"n": 4, "wins": 1, "faults": 3, "success": 0.3333, "u": 0.7167}, "rf": {"n": 4, "wins": 0, "faults": 4, "success": 0.1667, "u": 0.8833}, "hgb": {"n": 4, "wins": 4, "faults": 0, "success": 0.8333, "u": 0.2167}}, ...}
agent> Deep phase: rf has the most faults (4/4 below baseline), so all 12 go to rf. Actor fits it.
agent> FREEZE. Best memory-arm val: 0.9172 (hgb 0.1 yes onehot balanced). Score test, scorecard, then the verifier.
agent> Tally checks out against my own count. Writing the 9 cards as V.
agent> Problem 02: gap 0 (0.9954 both), wasted 0 vs 0; 5 cards written, 4 active cards applied. On to 03.
...
$ python ../tools/curve.py --pack .claude/skills/adult-income-actor --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      9/0/9
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       5/0/9
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/9
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       4/0/9
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    1/0       0/1/9
 6 synth_shift_b            0.7655   0.7925 -0.0270    0.8603     0.834   24/17      2/0/9
$ python ../tools/exam.py --pack .claude/skills/adult-income-actor --task ../tasks/07_exam.json --seeds 0,1,2,3,4
exam: memory arm beats control on 4 of 5 seeds (1 on test score, 4 same score; a tie won by fewer wasted fits), mean test gap 0.0006; pack unchanged: True; no card written: True
  did not transfer: n_classes < 3 -> hyper 8; has_categorical == 1 -> encode onehot (evidence 2, counter 1); n_classes < 3 -> hyper 1
agent> The claims of eval.md:
- Curve, gap never negative: did not hold - problem 6 has gap_val = -0.027 (memory best val 0.7655 vs
control 0.7925). The class_weight: none card (evidence from problems 1 and 4) pushed every none recipe
ahead in the broad phase, and the deep phase went to the two faultiest families (logreg, rf), so
hgb/onehot/balanced - the control's best - was never fitted; the memory arm wasted all 24 fits by the
curve's definition, though its test score was higher (0.8603 vs 0.834).
- Curve, gap larger on problem 6 than on problem 2: did not hold - -0.027 vs 0.000.
- Exam, memory beats control on >= 3 of 5 seeds: held - 4 of 5 (one on test score, three ties won on
fewer wasted fits; seed 1 lost by one wasted fit).
The planner's greedy rule was applied through a scratch helper (runs/_planner_scratch/build_plan.py,
gitignored under runs/) that reproduces SKILL.md step 3 from the numbers write_plan.py --uncertainty and
read_memory.py printed; the deep phase consistently sent all 12 experiments to the faultiest family,
which is what the small c in the rule produces.
[48 turns, 1368 s]
```

What to notice, honestly: RSIAgent's uncertainty rule is the one method
in this series that *loses* the curve on problem 6 (-0.027 val, all 24
fits wasted by the curve's definition, though the test score is higher),
because the deep phase spends its twelve experiments on the faultiest
family instead of the best one - it goes where the faults are, as the
paper says, and on a trees-shaped table with a linear-looking profile that
is the wrong place. The wasted-fits column is where it pays: 2 vs 16 on
problem 1, 27 vs 33 over the curriculum, and 0 / 6 / 9 vs 16 / 17 / 18 on
three exam seeds; the exam is won 4 of 5 on ties broken by fewer wasted
fits, with a mean test gap of +0.0006. The agent wrote itself a helper
script for the greedy plan (under `runs/`, scratch) rather than
hand-ranking twelve recipes per phase; the numbers it ranked by were the
script's.

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
