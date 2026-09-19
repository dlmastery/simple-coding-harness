# Lesson 07 - The proof: a locked test, a learning curve, an exam

Lesson 06 showed a card helping on one problem. This lesson is the evidence
standard the framework paper sets: **structural** recursion (a revised
mechanism governs a later round) is not enough; **effective** recursion
needs stronger successors under comparable budgets and independent
evaluation. So: the curriculum skill runs the six problems in order with
the memory arm and the control arm at the same 24-fit budget on every
problem, the verifier writing after each memory arm, and `curve.py` prints
the learning curve - memory best val minus control best val, wasted fits,
cards added / demoted / active. Then the frozen pack meets the exam problem
it never wrote to, over five seeds, and `exam.py` counts the wins and names
every applicable card that did not transfer. `eval.md` in the actor pack
states the claims before the run; the scorecard fields are lesson 00's; the
test split is scored once per arm, after FREEZE, and the scripts refuse
anything else. The agent orchestrates; the scripts measure.

## Getting started

Lesson 06 left the actor and the verifier. This lesson adds `eval.md` to the
actor, the orchestrator skill `.claude/skills/adult-income-curriculum/`, and
three scripts: `scorecard.py` (used since lesson 01), `curve.py`, `exam.py`.
A full run takes about 25 minutes in Claude Code (61 turns in the
recording) and fills `memory.json` with 23 cards; reset with `echo "[]" >
.claude/skills/adult-income/memory.json` (and the mirror) and `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the six curriculum problems and the exam, and report the learning curve and the exam tables.
   ```

   Per problem the agent runs the control arm (one static call), the memory
   arm (`read_memory.py --order obey-memory` then `fit_recipe.py --recipes`
   in calls of eight until FREEZE), and the verifier; then:

   ```bash
   python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
   # the exam: for s in 0 1 2 3 4, both arms with --seed s --freeze-memory (the control arm also --arm control --memory off)
   python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
   ```

   No approval prompt. Nothing to quote differently in PowerShell except
   the `--recipes '[...]'` JSON (use a file and `'@file'`).

2. The delete-the-file check by hand: put `{"memory": "off"}` into
   `.claude/skills/adult-income/config.json` and rerun a memory arm on any
   problem with a new seed - it walks the static list and lands on the
   control arm's numbers exactly.

3. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi` (the offline synthetic curriculum, under a minute).

## What it looks like

`.claude/skills/adult-income/eval.md` - the claims, written before the run:

```markdown
## The learning curve
Problems 1 to 6 in order, the pack carried forward, the verifier writing after each memory arm. Per problem: `gap_val` = memory best val - control best val; `wasted` = fits before reaching the control arm's best (within 0.005), plus every fit that errored; cards added / demoted / active. The claim: the gap is never negative, and larger on the last problem than on the second.

## The exam
Problem 7 is never written to: both arms open with `--freeze-memory` (`write_card.py` refuses), and the exam is run over five seeds. The claim: the memory arm beats the control arm on at least 3 of 5 seeds (a higher test score, or the same score reached with fewer wasted fits), and the report names every applicable card that did not transfer.
```

`.claude/skills/adult-income-curriculum/SKILL.md` - the orchestrator:

```markdown
---
name: adult-income-curriculum
description: Run the actor pack adult-income over the six curriculum problems in order with the verifier writing after each, print the learning curve, then run the frozen pack on the exam problem over five seeds and print the exam report. Use in rsi/step_07_proof and later, to produce the proof of a lesson.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The proof: the learning curve and the exam

## Procedure
1. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open the arm, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open, `read_memory.py --order obey-memory` for the next recipes, fit them, repeat until FREEZE, score once, scorecard).
   c. Verifier: follow `V/SKILL.md` on `T` (the tally, then the cards, written with `--as V`).
2. The learning curve:
   `python ../tools/curve.py --pack P --tasks ../tasks`
3. The exam, on `../tasks/07_exam.json`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off --freeze-memory`, then the memory arm with `--seed s --freeze-memory` (both as in step 1, with `--seed s` on every command). No verifier: the memory is frozen and `write_card.py` refuses.
4. The exam report:
   `python ../tools/exam.py --pack P --task ../tasks/07_exam.json --seeds 0,1,2,3,4`
```

`../tools/_lib/scorecard.py` - wasted fits, the second number of the curve:

```python
def wasted_fits(rows, bar=None):
    """Fits spent before the first recipe that reaches the bar (within 0.005), plus every fit that errored.
    The bar is the MEMORY_OFF arm's best val score on the same problem and seed - the static grid's answer -
    or, for that arm itself and for a run with no control, the arm's own best. Experience is measured by
    how many fits it saved on the way to the same answer."""
    scored = [r for r in rows if r["val_score"] is not None]
    if not scored:
        return len(rows)
    target = (max(r["val_score"] for r in scored) if bar is None else bar) - GOOD
    first_good = next((i for i, r in enumerate(rows) if r["val_score"] is not None and r["val_score"] >= target), len(rows))
    return first_good + sum(1 for r in rows[first_good:] if r["val_score"] is None)
```

`../tools/exam.py` - a win, and the cards that did not transfer:

```python
        gap = None if m["test_score"] is None or c["test_score"] is None else round(m["test_score"] - c["test_score"], 4)
        win = gap is not None and (gap > 0 or (gap == 0 and m["wasted_fits"] < c["wasted_fits"]))
```

```python
    did_not_transfer = [c for c in applicable if "prefer" in c["then"]
                        and sum(1 for b in best if b and b[c["then"]["field"]] == c["then"]["prefer"]) <= len(best) // 2]
```

The recorded run (Claude Code 2.1.278, headless, 61 turns, 1627 s; 55
script calls, trimmed to the agent's own notes and the two tables):

```text
[Skill adult-income-curriculum]
agent> Pack state is clean (empty memory, no runs). Starting problem 01, control arm.
agent> Problem 01 done: both arms 0.9172 val / 0.9034 test, 16 wasted each; verifier wrote 9 cards
(9 new, 0 demoted, 4 active). On to problem 02, control arm.
agent> One applicable card (scale: yes); no model preference, so the probe is the three models in grid
order with scale=yes. Probe winner: hgb. Now its family ... The order matches the rule (hgb family,
scale=yes recipes first, then hyper variants). I'll take the script's `next` in calls of eight until FREEZE.
agent> Memory arm: val 0.9966 vs control 0.9954, test 0.9883 vs 0.9844. Verifier on problem 02.
agent> Problem 02 verified: 6 cards (6 new, 0 demoted). Problem 03, control arm.
agent> Every recipe hits 1.0 on wine's val split; the first one is the best by tie order.
agent> Wine is saturated: every pair ties, so cards_by_rule is empty. Nothing to write for problem 03.
agent> Problem 04 verified: 6 cards written, 2 new, 1 demoted (class_weight: none for imbalance < 0.35).
agent> Problem 05 verified: 10 written, 5 new, 1 demoted (class_weight: balanced for imbalance >= 0.35).
agent> Model is tied (hgb vs logreg, 1 each) so no model preference; class_weight has no active card
(both demoted). Running the memory arm. ... Eight cards.
agent> Curriculum done. The learning curve:
$ python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/11
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/11
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/11
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/1/11
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/11
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      1/0/11
{"summary": {"gaps_val": [0.0, 0.0012, 0.0, 0.0, 0.0024, 0.0646], "wasted_memory_total": 20, "wasted_control_total": 33, "never_negative": true}}
agent> Curve claim holds: gap_val never negative (min 0.0), and problem 6 (+0.0646) > problem 2 (+0.0012).
Now the exam, seed 0, control arm first. ... Seeds 1-4, same procedure; one call per arm per seed.
agent> All five seeds done. The exam report:
$ python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
exam exam: memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap 0.0308; pack unchanged: True; no card written: True
  seed 0: memory test 0.865 val 0.8985 wasted 8 | control test 0.8661 val 0.8858 wasted 19 | gap -0.0011 loss
  seed 1: memory test 0.9057 val 0.9318 wasted 16 | control test 0.8077 val 0.9167 wasted 10 | gap 0.098 win
  seed 2: memory test 0.9208 val 0.9131 wasted 4 | control test 0.9208 val 0.9131 wasted 17 | gap 0.0 win
  seed 3: memory test 0.9314 val 0.887 wasted 5 | control test 0.9215 val 0.8766 wasted 18 | gap 0.0099 win
  seed 4: memory test 0.9352 val 0.9389 wasted 0 | control test 0.8881 val 0.9117 wasted 16 | gap 0.0471 win
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 0.1} (evidence 1, counter 0)
  did not transfer: {"key": "n_rows", "op": "<", "value": 1000} -> {"field": "model", "prefer": "logreg"} (evidence 1, counter 0)
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 1} (evidence 1, counter 0)
agent> The claims of eval.md:
- Test split locked - held: test_touched_before_freeze is false and test_scored_once is true on all 22 scorecards.
- Learning curve, gap never negative - held: min gap_val is 0.0.
- Learning curve, gap larger on problem 6 than problem 2 - held: +0.0646 vs +0.0012.
- Exam, memory beats control on >= 3 of 5 seeds - held: 4 of 5 (seed 0 lost on test by 0.0011 despite a higher val score).
- Exam names every applicable card that did not transfer - held: three listed above.
- Exam never written to - held: pack_unchanged: true, no_card_written: true.
Not run, per the skill: save_model.py and the delete-the-file check, which eval.md describes but this
lesson's procedure does not call for.
[61 turns, 1627 s]
```

What to notice, honestly: wine and digits are saturated for this recipe
space (every recipe scores 1.0 / 0.999 on val) and teach nothing - the gap
is 0 and the verifier writes no card on wine. The curve is carried by the
two synthetic tables, where the model belief (`hgb` for tables under 1000
rows, learned on problems 2 and 5) and the demotion of `class_weight:
balanced` are what save 14 wasted fits on problem 6 and add +0.0646 val /
+0.0764 test. Problem 5's test gap is -0.0003 with a +0.0024 val gap: the
claim is on val, and the README does not pretend otherwise. On the exam
seed 0 is a loss by 0.0011 on test with a higher val score - noise of a
700-row table - and the three cards that did not transfer are exactly the
kind the profile cannot justify (a hyper value or a model conditioned on
`n_rows`). After the run the actor's `memory.json` holds 23 cards, 11
active; the shipped file is `[]`.

Files:

```text
step_07_proof/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/              the actor + eval.md (memory.json shipped as [])
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/   SKILL.md, tools.md: the orchestrator
├── .agents/skills/...
└── runs/adult-income/                        (after a run)
    ├── <problem>/state.json, traces.jsonl, scorecard_{memory,control}_0.json   x 6
    ├── exam/state.json (10 arms), traces.jsonl, scorecards
    ├── curve.json
    └── exam.json
```

## Governance considerations

- **Who approves what.** Nobody per card (lesson 06's rule); the human
  wrote the claims (`eval.md`) and the acceptance fields (lesson 00) before
  the run, and reads the two tables after it. The exam problem is the
  human's independent evaluation: no pack ever writes on it.
- **The hook.** The locked test, as always - and it is now exercised 22
  times per run.
- **What the script refuses.** `write_card.py` under `--freeze-memory`;
  `score_test.py` before FREEZE or twice, per arm and seed; `curve.py` and
  `exam.py` never invent a missing arm (they list it as missing).
- **What is and is not self-modified.** `memory.json`, by the verifier,
  between problems - and not on the exam. Everything else is byte-identical
  (`pack_unchanged: true` compares the checksums at the first exam boot with
  the pack after the last seed).

## How to measure it

| Claim | Test |
|---|---|
| on the offline curriculum the gap is never negative, larger on problem 6 than on 2, the memory arm wastes fewer fits in total, cards are added and a superstition is demoted | `test_curve_gap_never_negative_and_growing` |
| the test is scored exactly once per problem and arm; every scorecard has exactly the acceptance fields | `test_test_scored_once_per_problem_and_arm_with_every_field` |
| on the exam the frozen pack beats the control arm on >= 3 of 5 seeds; no card is written; the pack is unchanged; the report names the cards that did not transfer | `test_exam_frozen_pack_beats_control_on_most_seeds` |
| `{"memory": "off"}` in `config.json` gives the control arm's numbers exactly | `test_memory_off_config_gives_control_numbers` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`, about 25 minutes) | `test_live_claude_code` |

The headline on this machine (the real curriculum, seed 0, recorded above):
gaps 0 / +0.0012 / 0 / 0 / +0.0024 / +0.0646 val; wasted fits 20 vs 33;
exam 4 of 5 seeds, mean test gap +0.0308; three cards did not transfer.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 08 - a meta skill generates the RSI harness](../step_08_meta_generates_rsi/README.md).
Previous: [Lesson 06 - the RSI harness](../step_06_rsi_harness/README.md).
