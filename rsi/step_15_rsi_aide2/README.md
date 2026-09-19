# Lesson 15 - AIDE²: autoresearch on autoresearch, keep-if-better across the set under one budget

AIDE² (Weco AI, July 2026; tech report announced, code not released -
every number about it here is *reported*) has an inner agent that searches a
tree of solutions with three operators - draft, debug, improve - and an
outer loop that rewrites the operator text and keeps the rewrite only if it
beats the previous version across the whole heterogeneous set under a fixed
cost budget. Here the inner pack (`adult-income-aide`) runs the curriculum
as version `v1` under `operators.md`; the outer pack (`aide-outer`) rewrites
the `improve` operator (expand the best solution -> expand the top three),
lands it at once under `approval: metered`, runs the curriculum again as
`v2`, and `meter.py --decide` applies the rule: per problem `v2 - v1` on
best val, a statistical layer that discards a gain more than 3 MADs above
the median (one lucky problem cannot carry the decision), keep only if the
remaining total is positive and it loses on at most half the problems -
else roll back. Three guards stay in every operator: the anti-overfitting
line (`lint_pack` refuses an operator without it), the re-run of a
suspicious score (`fit_recipe.py` flags `suspicious: true` at >= 0.999 or a
jump > 0.2, and the review operator fits it again), and the statistical
layer. The budget is metered in fits and script calls; there is no token
count, because no harness sees the agent's transcript, and the script says
so. L5 flavour: the improver rewrites the inner agent's procedure; the
budget, the guards and the task set stay human.

## Getting started

New: `.claude/skills/adult-income-aide/` (lesson 09's actor with
`operators.md` and the `aide-tree` policy), `.claude/skills/aide-outer/`,
the verifier reading a named arm (`--of v1`). One script:
`../tools/meter.py`; `patch_pack.py` gains `approval: metered`;
`fit_recipe.py` gains the suspicious flag. A full run is two curricula
(about 50 minutes headless). Reset: `git checkout -- .claude/skills/adult-income-aide`,
mirror, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the aide-outer skill: run version v1 over the curriculum, propose the improve rewrite, run v2 under it, and decide keep-or-rollback across the set.
   ```

   The outer step's own commands:

   ```bash
   python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --of v1
   python ../tools/patch_pack.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --files @runs/aide-outer/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "improve: top-1 -> top-3" --visit 1
   python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --decide --proposal g1 --before v1 --after v2 --tasks ../tasks
   ```

   No approval prompt: the metered rule decides.

2. By hand: strip a guard line from `operators.md` and lint the pack -
   `operator 'improve' lacks the anti-overfitting line`; run `meter.py
   --decide` before `v2` has run every problem - `arm 'v2' has not run ...;
   the rule needs every problem under the same budget`.

3. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-aide/operators.md` - the operators, each with
its guard:

```markdown
## improve
Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.

## review
Review: the score of a solution is the `val_score` of its fit result, nothing else. A score at or above 0.999, or one that jumps more than 0.2 above the previous best in one fit, is suspicious - `fit_recipe.py` marks it `suspicious: true` - and is fitted again before it is believed (it costs a fit). A statistical layer at the outer loop discards outlier successes.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.
```

`../tools/meter.py` - the outer rule as one function:

```python
def aide_keep(before, after, mad_k=3.0):
    """AIDE2's outer rule as one function. Returns (keep, detail)."""
    problems = sorted(set(before) & set(after))
    gains = {p: round(after[p] - before[p], 4) for p in problems}
    values = sorted(gains.values())
    median = values[len(values) // 2] if values else 0.0
    mad = max(sorted(abs(v - median) for v in values)[len(values) // 2] if values else 0.0, 0.01)   # a floor of one AUC point: rounding is not spread
    outliers = [p for p, g in gains.items() if g - median > mad_k * mad]
    kept = {p: g for p, g in gains.items() if p not in outliers}
    total = round(sum(kept.values()), 4)
    keep = bool(kept) and total > 0 and sum(1 for g in kept.values() if g < 0) <= len(kept) // 2
```

```python
    if budget[a.before] != budget[a.after]:
        raise ValueError(f"the budgets differ: {a.before} spent {budget[a.before]} fits, {a.after} {budget[a.after]}; not comparable")
```

`../tools/fit_recipe.py` - the suspicious flag:

```python
    previous = [f["val_score"] for f in run.arm_state["fits"] if f["val_score"] is not None]
    if val is not None and (val >= SUSPICIOUS or (previous and val - max(previous) > JUMP)):
        row["suspicious"] = True
```

The recorded run (Claude Code 2.1.278, headless, 45 turns, 1198 s; the
twelve arms' fit calls trimmed to the outer step):

```text
[Skill aide-outer]
agent> Task 06 v1: best val 0.8571, test 0.9104, 24 fits, 0 suspicious. Verifier: 10 written, 0 new.
Version v1 is complete - meter it.
$ python ../tools/meter.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --of v1
{"arm": "v1", "fits": 144, "calls": 203, "problems": ["adult_income", "breast_cancer", "digits", "synth_shift_a", "synth_shift_b", "wine"],
 "note": "cost = fits (the budget) + script calls (trace rows); no token count: no harness sees the agent's transcript"}
[Write runs/aide-outer/patch/operators.md]
agent> Land it with patch_pack.py, using v1's best recipe on T (hgb, 0.1, yes, onehot, balanced) as the evidence recipe:
$ python ../tools/patch_pack.py --pack .claude/skills/aide-outer --task ../tasks/01_adult_income.json --target .claude/skills/adult-income-aide --files @runs/aide-outer/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "improve: top-1 -> top-3" --visit 1
{"id": "g1", "decision": null, "landed": "pending", "version": "gen_001",
 "diff": "--- a/operators.md ... -Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
+Improve: expand the top three solutions - fit their untried neighbours, one field away, nearest first. ...",
 "next": "Run the curriculum under the rewrite (a new arm), then: python ../tools/meter.py --decide --proposal g1 --before <old arm> --after <new arm> --tasks ../tasks"}
agent> (version v2 over the six problems, --arm v2, the verifier after each; the draft roots, then the untried
neighbours of the top three, until FREEZE)
$ python ../tools/meter.py ... --of v2 && python ../tools/meter.py ... --decide --proposal g1 --before v1 --after v2 --tasks ../tasks
{"arm": "v2", "fits": 144, "calls": 211, ...}
{"proposal": "g1", "keep": true, "decision": "y", "version": "gen_001", "budget": {"v1": 144, "v2": 144},
 "best_before": {"adult_income": 0.9172, "breast_cancer": 0.9966, "wine": 1.0, "digits": 0.999, "synth_shift_a": 0.9531, "synth_shift_b": 0.8571},
 "best_after":  {"adult_income": 0.9172, "breast_cancer": 0.9971, "wine": 1.0, "digits": 0.999, "synth_shift_a": 0.9531, "synth_shift_b": 0.8571},
 "gains": {"adult_income": 0.0, "breast_cancer": 0.0005, "digits": 0.0, "synth_shift_a": 0.0, "synth_shift_b": 0.0, "wine": 0.0},
 "outliers_discarded": [], "total_gain": 0.0005, "wins": 1, "losses": 0, "median": 0.0, "mad": 0.01}
agent> meter.py --decide has answered. Outer step complete.
Meter readings: v1 (improve = expand the best) 144 fits, 203 script calls, 6 problems; v2 (improve = expand
the top three) 144 fits, 211 script calls, 6 problems. Both arms spent exactly the same fits (24 x 6). The
cost is metered in fits and script calls only - there is no token count, because no harness sees this transcript.
Verdict: keep. Proposal g1 ("improve: top-1 -> top-3", version gen_001) is decided y, approved by the
metered rule: the total gain is positive and the rewrite lost on zero problems. operators.md stays as
rewritten; every operator kept its guard line word for word.
Worth knowing about the effect size: the top-3 rewrite changed the search path on every problem, but the
best-reached recipe only moved on breast_cancer (logreg C=0.25 found by expanding the logreg root, which
top-1 never got to). On wine every one of the 24 recipes scores 1.0, so each fit was flagged suspicious and
re-run once as the review operator requires - half the budget there goes to re-runs, in both arms alike.
Two v1 arms (wine, digits) were reset and rerun before any verifier or meter call touched them: my first
per-task driver re-ran a suspicious recipe more than once (wine) and mis-parsed a single-recipe fit result
(digits). Both reruns are the arms now on disk and in the meter; the botched traces were deleted.
[45 turns, 1198 s]
```

What to notice, honestly: the rewrite was kept on a total gain of +0.0005
from one problem (breast cancer) and five ties - the rule's floor is
"positive and not losing on more than half", and +0.0005 is positive. The
outlier layer had nothing to discard (median 0, MAD floored at 0.01). The
suspicious-score guard bit on wine as designed and cost half that
problem's budget in both versions alike, which is what "matched budget"
means. The agent wrote itself a per-task driver script (scratch, deleted)
to walk the operators, and when that driver misbehaved on two arms it
deleted their traces and re-ran them *before* any meter or verifier saw
them - a reset the page reports because the meter counts what is on disk.
AIDE²'s own reported numbers are not reproduced here and are not claimed.

Files:

```text
step_15_rsi_aide2/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income-aide/         SKILL.md (policy aide-tree), tools.md, schema.json, operators.md, memory.json, memory.schema.json, eval.md
├── .claude/skills/adult-income-verifier/     reads --of v1 / v2
├── .claude/skills/aide-outer/                SKILL.md (approval: metered, patches: operators.md), tools.md
└── .agents/skills/...
```

## Governance considerations

- **Who approves what.** The metered rule, written by the human: the whole
  set, the same budget, the outlier layer. No human answers per rewrite;
  the human reads `runs/aide-outer/.../proposals/g1.json`'s `evaluation`.
- **The hook.** The locked test.
- **What the script refuses.** A decision before both arms ran every
  problem to FREEZE; unequal budgets; a second decision; a patch to any file
  but `operators.md`; an operator without its guard (lint); a fit for the
  outer pack.
- **What is and is not self-modified.** `operators.md`, one operator per
  outer step, snapshot first. The guards are checked, not editable away.

## How to measure it

| Claim | Test |
|---|---|
| keep-if-better is evaluated across every problem under one metered budget (both arms 144 fits), decided once, kept or rolled back | `test_keep_if_better_across_the_set_under_one_budget` |
| a rewrite that wins on one problem and loses on the set is rejected and `operators.md` restored | `test_a_rewrite_that_wins_on_one_problem_and_loses_on_the_set_is_rejected` |
| every operator carries the guard, lint refuses one without it, only `operators.md` may change, the outer pack cannot fit | `test_guards_in_every_operator_and_only_operators_may_change` |
| a suspicious score is flagged and re-run (the flag is in the trace) | `test_suspicious_score_is_flagged_and_rerun` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 16 - MetaSkill-Evolve](../step_16_rsi_meta_skills/README.md).
Previous: [Lesson 14 - the DGM lineage](../step_14_rsi_self_modifying/README.md).
