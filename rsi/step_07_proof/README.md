# Lesson 07 - Proof: the locked test, the learning curve, the exam

Lesson 06 showed a file that changes. This lesson says what would count as
that change being an improvement, and measures it the way the framework
paper's evidence bar demands: matched budgets, a protected evaluator, an
independent held-out problem. Three deliverables. The locked test: scored
once per arm, after FREEZE - you did not peek. The learning curve: problems
1 to 6 in order, the pack carried forward, and on every problem the memory
arm minus the `MEMORY_OFF` arm at the same budget and seed - structural
recursion you can see, problem by problem. The exam: problem 7, which no
verifier ever wrote from, the pack frozen, five seeds - effective recursion
under a matched budget and an independent evaluation, with a report that
names the cards that did *not* transfer. Every later lesson reports this
scorecard and this curve.

## Getting started

Lesson 06 left the actor and verifier packs. This lesson adds `eval.md` to
the actor pack (read at boot: the model knows how it is judged), `run.py
--curriculum` / `--exam`, and in `common/curriculum.py` the runners
`run_curriculum` (with the `MEMORY_OFF` control arm on every problem) and
`run_exam` (frozen pack, five seeds, the did-not-transfer report). This is
Stage 4 (Test) of the playbook; `python run_tests.py rsi` is the continuous
eval.

## How to execute it

1. The curve, then the exam (about 70 s on this machine with the fake
   model; the exam reuses the pack the curriculum left in `runs/work/`):

   ```bash
   cd rsi/step_07_proof
   FAKE_MODEL=1 python run.py --curriculum
   FAKE_MODEL=1 python run.py --exam
   ```

   ```powershell
   cd rsi\step_07_proof
   $env:FAKE_MODEL = "1"; python run.py --curriculum; python run.py --exam
   ```

   No approval prompt in this lesson; nothing is proposed.
2. The delete-the-file check by hand: delete `runs/work/adult-income/memory.json`
   after the curriculum, run the exam again, and compare with `MEMORY_OFF=1`.
3. Tests: `python run_tests.py rsi` (this step's suite runs the whole
   synthetic curriculum and the exam once, about 35 s).

## What it looks like

`skills/adult-income/eval.md` - what the model reads about how it is judged:

```markdown
## The comparison
- Two arms per problem, same seed, same split, same budget of 24 fits: the memory arm (this pack as it is) and the `MEMORY_OFF` arm (the same pack with `memory.json` not loaded, which is lesson 01's static walk).
- The test split is locked: scored once per arm, after FREEZE, never before. `test_touched_before_freeze` must be `no` on every scorecard.
- The delete-the-file check: deleting `memory.json` must give the `MEMORY_OFF` numbers exactly; a difference means something other than the cards changed.
```

The curve runner - control arm first, then the memory arm with the control's
best as the bar for wasted fits, then the verifier:

`../common/curriculum.py`:

```python
    curve = []
    for i, task in enumerate(task_list, 1):
        control, _, _ = run_problem(pack_dir, task, model, run_dir, seed=seed, arm="control", memory_off=True, human=human, quiet=quiet)
        card, inner, _ = run_problem(pack_dir, task, model, run_dir, seed=seed, arm="memory", verifier_dir=verifier_dir, human=human, quiet=quiet,
                                     bar=control["best_val_score"])
        row = curve_row(i, task, card, control)
```

The exam runner freezes the memory and names what did not transfer:

```python
    for seed in seeds:
        control, _, _ = run_problem(pack_dir, exam_task, model, run_dir, seed=seed, arm="control", memory_off=True, memory_frozen=True, quiet=quiet)
        mem, inner, _ = run_problem(pack_dir, exam_task, model, run_dir, seed=seed, arm="memory", memory_frozen=True, quiet=quiet,
                                    bar=control["best_val_score"])
        gap = round(mem["test_score"] - control["test_score"], 4)
        results.append({"seed": seed, "memory": mem, "control": control, "gap_test": gap,
                        "gap_val": round(mem["best_val_score"] - control["best_val_score"], 4),
                        # a win: a higher test score, or the same score reached with fewer wasted fits (same budget)
                        "win": gap > 0 or (gap == 0 and mem["wasted_fits"] < control["wasted_fits"])})
```

```python
    did_not_transfer = [c for c in applicable if "prefer" in c["then"]
                        and sum(1 for b in best if b and b[c["then"]["field"]] == c["then"]["prefer"]) <= len(best) // 2]
```

Expected output, on this machine (`FAKE_MODEL=1`, the real curriculum:
bundled Adult, breast cancer, wine, digits, the two synthetic tables; then
the exam table over seeds 0-4):

```text
learning curve (memory arm - MEMORY_OFF arm, same budget, same seed):
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/7
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       3/1/9
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    2/17      2/2/12
cards after problem 6: 15, active 12
exam exam: memory arm beats MEMORY_OFF on 4 of 5 seeds (3 on test score, 1 same score; a tie won by fewer wasted fits), mean test gap +0.0308; pack unchanged: True
  seed 0: memory test 0.865 val 0.8985 wasted 8 | control test 0.8661 val 0.8858 wasted 19 | gap -0.0011 loss
  seed 1: memory test 0.9057 val 0.9318 wasted 16 | control test 0.8077 val 0.9167 wasted 10 | gap +0.0980 win
  seed 2: memory test 0.9208 val 0.9131 wasted 4 | control test 0.9208 val 0.9131 wasted 17 | gap +0.0000 win
  seed 3: memory test 0.9314 val 0.887 wasted 5 | control test 0.9215 val 0.8766 wasted 18 | gap +0.0099 win
  seed 4: memory test 0.9352 val 0.9389 wasted 0 | control test 0.8881 val 0.9117 wasted 16 | gap +0.0471 win
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 0.1} (evidence 1, counter 0)
  did not transfer: {"key": "n_classes", "op": "<", "value": 3} -> {"field": "hyper", "prefer": 1} (evidence 1, counter 0)
```

How to read it. Problems 3 and 4 are too easy for this recipe space (every
recipe scores 1.0 or 0.999): ties teach nothing, and the verifier writes
nothing on wine. Problem 5 is the superstition test - a linear signal after
tree-shaped ones; the memory arm's probe catches it (`wasted 1`) and one
card is demoted. Problem 6 is where the experience pays: the memory arm
reaches the static grid's best in 2 fits instead of 17 and ends 0.065 higher
on validation, 0.076 higher on the locked test. The exam: four wins of five
(three on the test score, one on cost at the same score), one loss of
0.001, and two hyper-parameter cards that did not transfer - named, not
hidden.

Files:

```text
step_07_proof/
  skills/adult-income/          lesson 06's actor pack plus eval.md
    eval.md                     the comparison, the curve, the exam, the scorecard - read by the model at boot
  skills/adult-income-verifier/ lesson 06's verifier, unchanged
  run.py                        --curriculum: problems 1..6; --exam: problem 7 over five seeds
  test_step.py                  the claims below (the synthetic curriculum, once, shared by the tests)
  README.md                     this lesson
  runs/curriculum/curve.json    (created by run.py) the curve rows; runs/exam/exam.json the exam report
```

## Governance considerations

- Who approves what: nobody at run time; the human wrote `eval.md` and
  `acceptance.md`, and the exam problem is the human's choice.
- Off switches: `MEMORY_OFF`; the frozen memory during the exam
  (`write_card` refuses); the locked test.
- What the model may not do, and which tool enforces it: score the test
  before FREEZE or twice (`LockedTest`); write a card during the exam
  (`write_card` with `memory_frozen`); change the exam problem or the seeds
  (they are `run.py`'s, not the pack's).
- What is and is not self-modified: `memory.json`, over problems 1-6 only.
  The exam changes nothing (`pack unchanged: True` is a checksum). The
  evaluator - split, metric, seeds - is the human's and stays the same
  across generations: the paper's "freeze evaluators per epoch". Rung: the
  evidence standard, not a rung of its own.

## How to measure it

| Claim | Test |
|---|---|
| the test is scored exactly once per problem and arm, never before FREEZE, on the curriculum and on the exam | `test_test_is_scored_exactly_once_per_problem_and_arm` |
| every scorecard has exactly the fourteen fields; `eval.md` names them all | `test_every_scorecard_field_is_present` |
| problems 1->6 carry the pack forward (checksums of `memory.json` change); the gap is >= 0 on every problem and larger on 6 than on 2; the memory arm wastes fewer fits in total | `test_the_pack_is_carried_forward_and_the_learning_curve_grows` |
| on the exam the frozen pack beats `MEMORY_OFF` on >= 3 of 5 seeds, writes nothing, and the report names a card that did not transfer | `test_the_frozen_pack_beats_memory_off_on_the_exam` |

Scorecard fields reported: all fourteen, per arm, per problem, per seed, in
`runs/curriculum/curve.json` and `runs/exam/exam.json`. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [08 - a meta skill generates the RSI harness](../step_08_meta_generates_rsi/README.md):
the human approves a mechanism that will change itself. Previous:
[06 - the RSI harness](../step_06_rsi_harness/README.md).
