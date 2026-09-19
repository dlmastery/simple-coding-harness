# Lesson 11 - RSIAgent: the next experiment, chosen on purpose; the memory, frozen at test

RSIAgent (arXiv:2609.15364) splits the loop into three roles. Here they are
three packs. The **curriculum** pack picks the actor's next experiments by
uncertainty, `u = (1 - success) + c / (n + 1)`: a broad phase with a large
`c` that touches every model family before repeating one, then a deep phase
with a small `c` that goes where the faults are. The **actor** proposes
nothing of its own - it runs `plan.json`, waits when the plan runs dry, and
is resumed when the curriculum writes the next phase. The **verifier** is
lesson 06's, but it only gets its turn after `score_test`: the memory is
frozen while the actor runs, and on the transfer table it is never written
at all. That freeze is what makes the comparison with `MEMORY_OFF` fair. The
one new tool is `write_plan`; the one new harness verb is `resume`.

## Getting started

Lesson 10 left the policy-choosing meta pack. This lesson replaces the
actor's own search with a plan: `skills/adult-income-actor/` (reads
`plan.json`, may `read_pack` to re-read it), `skills/adult-income-curriculum/`
(reads the trace and the cards, writes the plan), and the verifier. The
runner `agent_problem` in `run.py` is the sequence curriculum -> actor ->
curriculum -> actor (resumed) -> verifier; `common/curriculum.py` takes it
as the `memory_arm` hook for the curve and the exam.

## How to execute it

1. The curriculum, then the exam:

   ```bash
   cd rsi/step_11_rsi_agent
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_11_rsi_agent
   $env:FAKE_MODEL = "1"; python run.py
   ```

   No approval prompt: the curriculum's rule is in its `SKILL.md`, and the
   human wrote it.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-curriculum/SKILL.md`:

```markdown
---
name: adult-income-curriculum
description: Choose the actor's next experiments by uncertainty - a broad phase that touches every model family, then a deep phase that goes where the faults are - and write them to the actor's plan.json. Use before the actor's first fit on a problem and again when its plan runs dry.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
```

```markdown
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far, `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline), and `c` is the phase's exploration weight:
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
```

`skills/adult-income-actor/SKILL.md`:

```markdown
3. When the plan runs dry and fits remain, call `read_pack` to re-read `plan.json`: the curriculum pack may have written the next phase. If there is nothing new, answer in text that the plan is exhausted and wait; the harness resumes you when the plan changes.
```

The tool and the verb:

`../common/tools.py`:

```python
@tool("write_plan", plan="object")
def write_plan(run, plan):
    """Write plan.json into the actor pack: {phase: broad | deep, c: number, experiments: [recipes]}. The actor fits them in order."""
```

`run.py`:

```python
    run = harness.boot(actor, task, seed=seed, arm="memory", run_dir=run_dir, quiet=quiet)
    run.memory_frozen = True                                                # no card lands while the actor runs
    harness.run(run, model)                                                 # fits the broad plan, then waits
    plan = harness.boot(curr, task, seed=seed, arm="memory", run_dir=run_dir, target=actor, quiet=quiet)
    harness.run(plan, model)                                                # deep: from the broad results
    harness.resume(run, model, "plan.json was updated: continue with the new experiments.")
```

Expected output, on this machine (`FAKE_MODEL=1`):

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034    2/16      4/0/4
 2 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       2/0/6
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/6
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/0/8
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    1/0       2/1/9
 6 synth_shift_b            0.7655   0.7925 -0.0270    0.8603     0.834   24/17      1/2/8
  adult_income     broad: logreg rf hgb logreg rf hgb ... | deep: rf rf rf rf rf rf ...
  breast_cancer    broad: logreg rf hgb logreg rf hgb ... | deep: rf rf rf rf rf rf ...
  wine             broad: hgb logreg rf hgb logreg rf ... | deep: hgb hgb hgb hgb hgb hgb ...
  digits           broad: hgb logreg rf hgb logreg rf ... | deep: logreg logreg logreg logreg logreg logreg ...
  synth_shift_a    broad: hgb logreg rf hgb logreg rf ... | deep: rf rf rf rf rf rf ...
  synth_shift_b    broad: logreg rf hgb logreg rf hgb ... | deep: rf rf rf rf rf rf ...
exam exam: memory arm beats MEMORY_OFF on 4 of 5 seeds (1 on test score, 4 same score; a tie won by fewer wasted fits), mean test gap +0.0006; pack unchanged: True
  seed 0: memory test 0.8691 val 0.8778 wasted 24 | control test 0.8661 val 0.8858 wasted 19 | gap +0.0030 win
  seed 1: memory test 0.8077 val 0.9167 wasted 11 | control test 0.8077 val 0.9167 wasted 10 | gap +0.0000 loss
  seed 2: memory test 0.9208 val 0.9131 wasted 6 | control test 0.9208 val 0.9131 wasted 17 | gap +0.0000 win
  seed 3: memory test 0.9215 val 0.8766 wasted 9 | control test 0.9215 val 0.8766 wasted 18 | gap +0.0000 win
  seed 4: memory test 0.8881 val 0.9117 wasted 0 | control test 0.8881 val 0.9117 wasted 16 | gap +0.0000 win
```

Read it honestly. The broad phase round-robins the families (the cards move
the believed family to the front from problem 3 on), so the memory arm
reaches the static grid's best in 2 fits on Adult where the grid needs 16.
The deep phase then spends its twelve fits on the *faultiest* family - that
is what the uncertainty rule asks for - which on problem 6 means twelve
random forests on a table a boosted model wins, and the val gap goes
negative (-0.027) while the test gap stays positive (+0.026). On the exam
the frozen memory wins four of five seeds, almost all on cost, not score.
Broad-then-deep buys information and cards, not validation points; the
lesson keeps the number.

Files:

```text
step_11_rsi_agent/
  skills/adult-income-actor/
    SKILL.md            run plan.json; re-read it when dry; wait; score_test once after FREEZE; MEMORY_OFF walks the static list
    tools.md            Allowed: load_splits, fit_recipe, read_pack, score_test, save_model
    plan.json           the current phase's experiments (rewritten by the curriculum pack on every visit)
    schema.json, memory.schema.json, memory.json, eval.md    lesson 07's
  skills/adult-income-curriculum/
    SKILL.md            u = (1 - success) + c / (n + 1); Broad c 2.0, Deep c 0.25, 12 experiments per phase
    tools.md            Allowed: read_traces, read_memory, write_plan
  skills/adult-income-verifier/   lesson 06's verifier
  run.py                agent_problem: curriculum -> actor -> curriculum -> actor (resumed) -> verifier; the curve and the exam
  test_step.py          the claims below
  README.md             this lesson
```

## Governance considerations

- Who approves what: nobody at run time. The uncertainty rule, its two `c`
  values and the phase length are the human's, in the curriculum pack's
  `SKILL.md`.
- Off switches: `MEMORY_OFF` (the actor ignores `plan.json` and walks the
  static list: lesson 01's control arm); the frozen memory on the exam.
- What the model may not do, and which tool enforces it: the actor may not
  invent an experiment (the test asserts every fit is a plan entry) and may
  not write a plan (`write_plan` is not in its `tools.md`); the curriculum
  pack may not fit or write cards (`tools.md`); nobody may write a card
  before `score_test` (`memory_frozen` on the actor's run; the verifier
  boots after).
- What is and is not self-modified: `plan.json` (per run, scratch) and
  `memory.json` (after each problem's test, by the verifier). The
  curriculum rule is not. Rung: L3 (which experience to acquire) plus L4.

## How to measure it

| Claim | Test |
|---|---|
| the broad phase touches every family before the deep phase repeats one (and the broad `c` exceeds the deep `c`) | `test_broad_phase_touches_every_family_before_deep_repeats_one` |
| the deep phase prefers the family with the most faults, and the actor fits it | `test_deep_phase_prefers_the_family_with_the_most_faults` |
| the actor proposes nothing of its own, waits when the plan runs dry, cannot write a plan; both packs lint | `test_the_actor_proposes_nothing_of_its_own_and_waits_for_a_plan` |
| the memory is frozen before `score_test` (no card between the actor's boot and its test) and unchanged on the transfer table | `test_memory_is_frozen_before_score_test_and_unchanged_on_the_transfer_table` |

Scorecard fields reported: all fourteen, plus the `plan` trace rows (phase,
`c`, families). Run `python run_tests.py rsi` from the repo root.

## Next lesson

Next: [12 - ModularRSI](../step_12_rsi_modular/README.md): a harness module
evolved off the benchmark. Previous: [10 - Dream-RSI](../step_10_rsi_dream/README.md).
