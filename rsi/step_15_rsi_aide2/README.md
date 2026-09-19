# Lesson 15 - AIDE²: autoresearch on autoresearch, keep-if-better across the set under one budget

AIDE² (Weco AI, July 2026; a tech report announced, the code not released)
runs an outer loop that rewrites the inner research agent and keeps a
rewrite only when it beats the previous best across a heterogeneous set of
problems under a fixed cost budget. Here the inner pack is lesson 09's
actor as an AIDE-style tree search over solutions - `operators.md` holds
`draft`, `debug`, `improve` and a `review` operator, every one carrying the
same guard line - and the outer pack rewrites one operator's text. The
runner then evaluates the rewrite across every curriculum problem under
the same fits budget (`meter` reads fits and tokens from the trace) and
keeps it only if `aide_keep` says so: better on the set, after the
statistical layer drops outlier successes. Three guards the outer loop must
keep: the anti-overfitting line in every operator prompt (`lint_pack`
refuses an operator without it), a hard guard that re-runs a suspicious
score before believing it (it costs a fit), and the outlier layer. The
report's numbers - seven improved versions in 100 outer steps, 16x context
compression - are *reported* and unverified here.

## Getting started

Lesson 14 left the archive. This lesson adds `skills/adult-income-aide/`
(lesson 09's actor with `operators.md` and `Search policy: aide-tree`),
`skills/aide-outer/` (`patches: ["operators.md"]`), the tool `meter`, the
rule `aide_keep` in `common/tools.py`, the `aide-tree` / `aide-tree-top-3`
policies in `common/policies.py`, and the guard constant `ANTI_OVERFIT`
that `lint_pack` checks per operator section.

## How to execute it

1. One outer step: a lap with the current operators, one rewrite, a lap
   with the rewrite, keep-if-better:

   ```bash
   cd rsi/step_15_rsi_aide2
   FAKE_MODEL=1 HUMAN=script:y python run.py
   ```

   ```powershell
   cd rsi\step_15_rsi_aide2
   $env:FAKE_MODEL = "1"; $env:HUMAN = "script:y"; python run.py
   ```

   Without `HUMAN`, you are asked once, for the operator rewrite; `y`
   lets the runner evaluate it, `n` skips the second lap.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-aide/operators.md` - the `improve` operator, with the
guard every operator carries:

```markdown
## improve
Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.
```

```markdown
## review
Review: the score of a solution is the `val_score` of its fit result, nothing else. A score at or above 0.999, or one that jumps more than 0.2 above the previous best in one fit, is suspicious: fit the same recipe again before believing it (it costs a fit). A statistical layer at the outer loop discards outlier successes.
```

`skills/aide-outer/SKILL.md`:

```markdown
---
name: aide-outer
description: AIDE2's outer loop - rewrite the inner agent's operator text and keep the rewrite only if it beats the previous best across the whole curriculum under one metered budget of fits and tokens. Use after the inner pack has run every curriculum problem once.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: human
  patches: ["operators.md"]
---
```

The keep rule and the guards, in code:

`../common/tools.py`:

```python
def aide_keep(before, after, mad_k=3.0):
    """AIDE2's outer rule: keep a rewrite only if it is better across the whole set under the same budget, after the
    statistical layer drops outlier successes - a per-problem gain more than `mad_k` MADs above the median gain is
    discarded, so one lucky problem cannot carry the decision. Returns (keep, detail)."""
```

```python
SUSPICIOUS = 0.999    # a validation score this close to perfect is re-run before it is believed
JUMP = 0.2            # so is one that jumps this far above the previous best in one fit
```

`../common/packs.py`:

```python
ANTI_OVERFIT = "Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed."
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y`; the
prompt is elided):

```text
meter: {"arm": "all", "fits": 144, "tokens": 46648, "problems": ["adult_income", "breast_cancer", "digits", "synth_shift_a", "synth_shift_b", "wine"]}
rewrite: {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["operators.md"]}
problem           v1 best val  v2 best val     gain
adult_income           0.9172       0.9171  -0.0001
breast_cancer          0.9966       0.9966  +0.0000
wine                      1.0          1.0  +0.0000
digits                  0.999        0.999  +0.0000
synth_shift_a          0.9531       0.9531  +0.0000
synth_shift_b          0.8571       0.8571  +0.0000
fits per lap: v1 144, v2 144; keep-if-better across the set: False {"gains": {"adult_income": -0.0001, "breast_cancer": 0.0, "digits": 0.0, "synth_shift_a": 0.0, "synth_shift_b": 0.0, "wine": 0.0}, "outliers_discarded": [], "total_gain": -0.0001, "wins": 0, "losses": 1}
operators.md now: Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
```

The rewrite (expand the top three instead of the best) changed nothing on
five problems and lost 0.0001 on Adult under the same 144 fits, so the
outer loop rolled it back and the operators read as they did. That is the
whole point of the rule: "a better run" on one table is not "a better
researcher", and the meter says both laps paid the same.

Files:

```text
step_15_rsi_aide2/
  skills/adult-income-aide/
    SKILL.md            lesson 09's actor with `Search policy: aide-tree`
    operators.md        draft, debug, improve, review - each with the guard line
    tools.md, schema.json, memory.schema.json, memory.json, eval.md
  skills/adult-income-verifier/   lesson 06's verifier
  skills/aide-outer/
    SKILL.md            meter, then one rewrite of operators.md; the runner's keep-if-better is the second gate
    tools.md            Allowed: read_traces, read_memory, read_pack, meter, patch_pack
  run.py                outer_step: lap v1 -> rewrite -> lap v2 -> aide_keep -> keep or roll back
  test_step.py          the claims below
  README.md             this lesson
```

## Governance considerations

- Who approves what: the human approves the rewrite (`approval: human`),
  then the set decides (`aide_keep`, the human's rule); the budget meter
  is the runner's, the task set is the curriculum.
- Off switches: `n` at the prompt; the rollback after a rejected lap;
  `versions/`.
- What the model may not do, and which tool enforces it: rewrite anything
  but `operators.md` (`patches:`); drop the guard from an operator
  (`lint_pack`); believe a suspicious score without a re-run (the fake
  follows the review operator; the test asserts the repeated recipe);
  score the test split or fit from the outer pack (`tools.md`).
- What is and is not self-modified: the operator text of the inner pack.
  Not: the guards' wording, the keep rule, the budget, the task set. Rung:
  L5 flavour; effective recursion is claimed only across the whole set
  under one budget, and here it was not achieved - and reported.

## How to measure it

| Claim | Test |
|---|---|
| keep-if-better is evaluated across every problem of the curriculum under one metered budget (asserted from the trace) | `test_keep_if_better_is_evaluated_across_every_problem_under_one_metered_budget` |
| a rewrite that wins on one problem and loses on the set is rejected; one lucky problem is discarded as an outlier | `test_a_rewrite_that_wins_on_one_problem_and_loses_on_the_set_is_rejected` |
| the three guards are present in every operator prompt; `lint_pack` refuses one without; only `operators.md` may be patched | `test_the_guards_are_in_every_operator_and_lint_refuses_one_without` |
| a suspicious score is re-run (scripted: a near-perfect table) | `test_a_suspicious_score_is_re_run` |

Scorecard fields: per-problem best val per lap, the `meter` and
`keep_if_better` trace rows. Run `python run_tests.py rsi` from the repo
root.

## Next lesson

Next: [16 - MetaSkill-Evolve](../step_16_rsi_meta_skills/README.md): the
improver's own skills improve too, slowly. Previous:
[14 - the Darwin Gödel Machine lineage](../step_14_rsi_self_modifying/README.md).
