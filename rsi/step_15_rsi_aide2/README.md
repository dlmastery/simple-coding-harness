# Lesson 15 - AIDE²: autoresearch on autoresearch, keep-if-better across the set under one budget

AIDE² (Weco AI, July 2026; a tech report announced, code not released) puts
an outer loop around an AIDE-style inner agent: the inner agent tree-searches
solutions with operators (draft, debug, improve, review), and the outer
loop rewrites the operators' text and keeps a rewrite only if it beats the
previous version across a whole heterogeneous set under a fixed budget. Here
the inner pack (`adult-income-aide`) has `operators.md`, each operator
carrying the same guard line, and the outer pack (`aide-outer`) runs the
curriculum as `v1`, rewrites one operator (`improve`: expand the top three
instead of the best), runs the curriculum again as `v2` under the same
budget, and decides with `meter`: per problem, v2's best val minus v1's; a
statistical layer discards a gain more than 3 MADs above the median; the
rewrite stays only if the remaining total gain is positive and it loses on
at most half the problems; otherwise `operators.md` is restored. The three
guards - the anti-overfitting line in every operator, the re-run of a
suspicious score, the statistical layer - are why the score means something.
The budget is metered in fits and helper calls; there is no token count,
because no helper sees the transcript, and the report says so. AIDE²'s own
numbers (seven improved versions in 100 outer steps, 16x context
compression) are *reported*, unverified.

## Getting started

Prerequisites: lesson 09. This lesson adds `operators.md` to the inner pack,
`suspicious: true` to `fit_recipe`'s contract, the `aide-tree` policy, and
`aide-outer` with the `meter` contract (`approval: metered`,
`patches: ["operators.md"]`). Two curricula run: budget the run at an hour.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the aide-outer skill: run one outer step - version v1 over problems 1 to 6 with the verifier, meter it, propose the improve-top-three rewrite, run v2 over the same six, meter it, decide across the set, and report.
   ```

2. No approval: the meter decides across the set.

3. Headless, as recorded:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: every operator carries the
   guard; the outer loop keeps only across the set under one meter, with the
   MAD layer and no token count; the inner agent re-runs a suspicious score.
   `RSI_LIVE=1`: `v1` and `v2` frozen and scored once on all six problems
   with 24 fits each; a `meter` event with a decision; `operators.md` with
   four guards, either the rewrite or the original; a version on disk.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-aide/operators.md`:

```markdown
## improve
Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.

## review
Review: the score of a solution is the `val_score` of its fit result, nothing else. A score at or above 0.999, or one that jumps more than 0.2 above the previous best in one fit, is suspicious - `fit_recipe` marks it `suspicious: true` - and is fitted again before it is believed (it costs a fit). A statistical layer at the outer loop discards outlier successes.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.
```

`.claude/skills/aide-outer/SKILL.md` - the decision:

```markdown
5. Decide, across the whole set: `meter M T --target P --decide --proposal <id> --before v1 --after v2 --tasks ../tasks`. Per problem, v2's best val minus v1's; the statistical layer discards a gain more than 3 MADs above the median; the rewrite is kept only if the remaining total gain is positive and it loses on at most half the problems - otherwise the helper restores `operators.md` from the snapshot. Both arms must have spent the same fits.
```

`.claude/skills/aide-outer/tools.md` - the meter contract:

```markdown
- `meter(pack, task, target, of=<arm>)` - the cost of one version over the whole curriculum: the fits spent and the helper calls made on every problem's `<of>` arm (from the traces and `state.json`); print `fits`, `calls`, `problems`. There is no token count, because no helper sees your transcript - say so. `meter --decide --proposal <id> --before v1 --after v2 --tasks ../tasks`: per curriculum problem, v2's best val minus v1's; discard as an outlier any gain more than 3 MADs above the median (the statistical layer); refuse when the two versions did not spend the same fits; keep the rewrite only if the remaining total gain is positive and it loses on at most half the problems - otherwise restore `operators.md` from the snapshot the proposal made. Append `{"event": "meter", "decision", ...}`, print the gains, the outliers and the verdict.
```

`test_step.py`:

```python
    operators = (SKILLS / "adult-income-aide" / "operators.md").read_text(encoding="utf-8")
    assert operators.count("Guard: do not tune to the validation split") == 4
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, the two
meter readings and the decision in full):

```text
[Skill aide-outer]
[Read the outer pack's tools.md / config.md, the inner pack's SKILL.md / operators.md / tools.md / schema / eval / config / memory, the verifier's SKILL.md / tools.md]
agent> Now the verifier pack and the tasks.
agent> Python works through Bash with a fixed PATH. Now the tasks and any sibling-lesson helpers I can model on.
[Write runs/adult-income-aide/helpers/{rt.py, tools.py}]  [Write runs/adult-income-verifier/helpers/verify.py]
agent> Now the outer loop's helpers: meter, read_pack, propose, lint_pack, rollback.
[Write runs/aide-outer/helpers/outer.py]
agent> A second session was running the same prompt in this directory and has stood down. Before continuing I'll check that runs/ holds only my helpers and no stray arms.
$ ls -R runs | head; ... (one orphaned helper file removed)
agent> The helpers boot and lint clean. Now version 1 - problem 1 (adult_income) as the inner pack, --arm v1: open the arm, then draft.
$ python $A load_splits $P $T --arm v1 ...; python $A read_memory $P $T --arm v1 --order aide-tree ...; python $A fit_recipe $P $T --arm v1 --recipes @next.json ...
-- aide-tree ['draft: one solution per model family']
1 0.9114  {'model': 'logreg', 'hyper': 1, 'scale': 'yes', 'encode': 'onehot', 'class_weight': 'none'}
2 0.9054  {'model': 'rf', 'hyper': 16, ...}
3 0.915   {'model': 'hgb', 'hyper': 0.1, ...}
agent> Draft done: hgb 0.915 is the root to expand. Review: nothing suspicious. Improve rounds next.
$ ... read_memory --order aide-tree (improve: the untried neighbours of the best, nearest first) ...; fit_recipe ... (x3 until FREEZE)
agent> FREEZE at 24. Best val 0.9172 (hgb, lr 0.1, scaled, onehot, balanced - the earlier of two ties). Score the test once, then the scorecard.
$ python $A score_test $P $T --arm v1 --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}' && python $A scorecard $P $T --arm v1
{'problem': 'adult_income', 'arm': 'v1', 'fits_used': 24, 'wasted_fits': 2, 'best_val_score': 0.9172, 'test_score': 0.9034, 'test_scored_once': True, 'test_touched_before_freeze': False, 'suspicious': 0, 'reruns': 0}
agent> adult_income v1: best val 0.9172, test 0.9034, 24 fits, 0 suspicious. Now the verifier on this arm (--of v1): tally, then write the cards its rule makes.
$ python $V read_traces $P $T --scope problem --tally --of v1 ...; python $V write_card $P $T --as .claude/skills/adult-income-verifier --cards @... --of v1
agent> Pairs check out by hand (logreg 0.9114 > rf 0.9054; hgb 0.915 > logreg; C=0.25 > C=1). Writing the 12 cards the rule makes in one call.
agent> Problem 2, breast_cancer, v1: open, draft, then improve rounds.
agent> breast_cancer v1: best val 0.9971, test 0.9978; verifier wrote 11 cards (7 new). Problem 3, wine - multiclass, where suspicious (>= 0.999) scores and their re-runs are expected.
agent> Wine: 18 pairs, all ties - the rule makes no card, so nothing is written for wine. Problem 4, digits.
agent> digits v1: best val 0.9995 (raw), test 0.9988; 10 cards (5 new). Problem 5, synth_shift_a.
agent> synth_shift_a v1: best val 0.9378 (rf), test 0.8981. Problem 6, synth_shift_b - the last of v1.
agent> Version 1 is complete on all six. Metering it: meter M T --target P --of v1.
$ python runs/aide-outer/helpers/outer.py meter .claude/skills/aide-outer ../tasks/01_adult_income --target .claude/skills/adult-income-aide --of v1 | ...
{'version': 'v1', 'fits': 144, 'calls': 77, 'calls_by_tool': {'load_splits': 6, 'read_memory': 24, 'fit_recipe': 24, 'score_test': 6, 'scorecard': 6, 'read_traces': 6, 'write_card': 5}, 'n_problems': 6, 'missing': [], 'all_frozen': True, 'all_scored_once': True, 'token_count': None, 'note': "there is no token count: no helper sees the agent's transcript; the budget is fits and helper calls"}
  adult_income fits 24 calls 13 best_val 0.9172 test 0.9034 susp 0 reruns 0 errored 0
  breast_cancer fits 24 calls 13 best_val 0.9971 test 0.9978 susp 0 reruns 0 errored 0
  wine fits 24 calls 12 best_val 1.0 test 1.0 susp 13 reruns 11 errored 0
  digits fits 24 calls 13 best_val 0.9995 test 0.9988 susp 8 reruns 5 errored 0
  synth_shift_a fits 24 calls 13 best_val 0.9378 test 0.8981 susp 0 reruns 0 errored 0
  synth_shift_b fits 24 calls 13 best_val 0.7839 test 0.7481 susp 0 reruns 0 errored 0
agent> v1 meter: 144 fits, 77 helper calls, no token count. Now the single rewrite: improve from top-1 to top-3, every guard line kept word for word.
[Write runs/aide-outer/patch/operators.md (19 lines)]
$ python runs/aide-outer/helpers/outer.py propose .claude/skills/aide-outer ../tasks/01_adult_income --target adult-income-aide --files runs/aide-outer/patch --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}' --summary "improve: top-1 -> top-3" --visit 1
{"id": "p001", "visit": 1, "target": "adult-income-aide", "files": ["operators.md"], "changed_lines": 2, "pack_lines": 849, "lint": "ok", "landed": "pending", "version": "gen_001", ...}
$ ... read_pack .claude/skills/adult-income-aide ...; (problem 1 as v2: open, draft, improve under aide-tree-top-3 ...)
mirrors_identical True improve_top_k 3 versions ['gen_001'] boots_as []
open adult_income v2 improve_top_k 3 applicable 5 preferred {'model': 'hgb', 'hyper': None, 'scale': 'yes', 'encode': 'onehot', 'class_weight': None}
-- aide-tree-top-3 ['draft: one solution per model family']
1 0.9114  {'model': 'logreg', ...}
2 0.9054  {'model': 'rf', ...}
3 0.915   {'model': 'hgb', ...}
... (the same 24 recipes in the same order as v1)
$ ... score_test --arm v2 ...; scorecard --arm v2; verifier --of v2 ...
{'problem': 'adult_income', 'arm': 'v2', 'fits_used': 24, 'wasted_fits': 2, 'best_val_score': 0.9172, 'test_score': 0.9034, ...}
agent> Wine v2: all ties again, no card. Problem 4, digits v2.
agent> The last v2 arm: synth_shift_b.
agent> Version 2 complete. Meter v2, then the decision across the set.
$ ... meter ... --of v2 ...
{'version': 'v2', 'fits': 144, 'calls': 77, 'calls_by_tool': {... identical ...}, 'all_frozen': True, 'all_scored_once': True, 'token_count': None, ...}
$ python runs/aide-outer/helpers/outer.py meter .claude/skills/aide-outer ../tasks/01_adult_income --target .claude/skills/adult-income-aide --decide --proposal p001 --before v1 --after v2 --tasks ../tasks
{"proposal": "p001", "target": "adult-income-aide", "before": "v1", "after": "v2", "fits": {"v1": 144, "v2": 144, "equal": true}, "gains": {"adult_income": 0.0, "breast_cancer": 0.0, "wine": 0.0, "digits": 0.0, "synth_shift_a": 0.0, "synth_shift_b": 0.0}, "median": 0.0, "mad": 0.0, "outliers": [], "total_gain_remaining": 0.0, "losses": 0, "decision": "rollback", "restored": "gen_001", ...}
agent> Verdict: rollback - every gain is exactly 0. Verifying the final state on disk (guards, mirrors, the meter event, the version).
$ ... read_pack ...; grep -c "Guard: do not tune to the validation split" .claude/skills/adult-income-aide/operators.md .agents/skills/adult-income-aide/operators.md; grep -n "^Improve:" .claude/skills/adult-income-aide/operators.md; diff -r .claude/skills .agents/skills && echo "mirrors: identical"; cat runs/aide-outer/adult_income/traces.jsonl | ...
mirrors_identical True improve_top_k 1 versions ['gen_001'] boots_as []
.claude/skills/adult-income-aide/operators.md:4
.agents/skills/adult-income-aide/operators.md:4
14:Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
mirrors: identical
{"event": "meter", "of": "v1", "fits": 144, "calls": 77, "token_count": null}
{"event": "propose", "id": "p001", ...}  {"event": "meter", "of": "v2", ...}  {"event": "meter", "decision": "rollback", "total_gain_remaining": 0.0, "outliers": [], ...}  {"event": "rollback", "version": "gen_001"}
agent> One outer step is complete; meter --decide has answered.
## Meter readings
| v1 | 144 (6 x 24) | 77 | load_splits 6, read_memory 24, fit_recipe 24, score_test 6, scorecard 6, read_traces 6, write_card 5 |
| v2 | 144 (6 x 24) | 77 | identical |
There is no token count: no helper sees my transcript, so the budget is metered in fits and helper calls only. Both versions spent the same fits, as the decision requires.
## Per-problem gains (v2 best val - v1 best val)
| adult_income  | 0.9172 | 0.9172 | 0.0000 | 0.9034 / 0.9034 |
| breast_cancer | 0.9971 | 0.9971 | 0.0000 | 0.9978 / 0.9978 |
| wine          | 1.0000 | 1.0000 | 0.0000 | 1.0 / 1.0 |
| digits        | 0.9995 | 0.9995 | 0.0000 | 0.9988 / 0.9988 |
| synth_shift_a | 0.9378 | 0.9378 | 0.0000 | 0.8981 / 0.8981 |
| synth_shift_b | 0.7839 | 0.7839 | 0.0000 | 0.7481 / 0.7481 |
Statistical layer: median 0, MAD 0, threshold 0 - no outlier discarded. Remaining total gain 0.0, losses on 0 of 6.
## Verdict: rollback
The rule keeps a rewrite only if the remaining total gain is positive; zero is not. meter restored operators.md from the snapshot gen_001 in both mirrors - it reads "expand the best solution" again, all four guard lines intact, mirrors identical. Proposal p001 ("improve: top-1 -> top-3", 2 of 849 lines, lint ok) is recorded as landed-then-rolled-back; the events meter (v1), propose, meter (v2), meter (decision), rollback are in runs/aide-outer/adult_income/traces.jsonl.
## Why the gain was exactly zero - worth knowing
v2 fitted the same 24 recipes in the same order as v1 on every problem. My aide-tree policy never lets the tree stall: when the best solution's untried neighbours (at most 7) don't fill a batch of eight, it continues into the second- and third-best solutions' neighbours, ordered nearest-first. Under batches of eight that is operationally the same walk as "top three, nearest first" on all six tables, so the rewrite changed the text but not the search. An honest meter reports that as a zero, not a headline.
Other things to note from the run:
- Guards fired as designed: wine (every score 1.0) spent 11 of 24 fits re-running suspicious results; digits re-ran 5. On digits the raw top score (0.9995 at t=24) was suspicious with no budget left, so the highest believed score (0.9991) went to the test split, while the scorecard/meter report the raw max - same rule on both versions.
- Verifier: 12 / 11 / 0 / 10 / 9 / 11 cards per problem on v1 (wine was all ties, nothing written); v2 added evidence to existing cards only (28 on disk, 9 active). The cards only reach aide-tree through forbid cards, and none were written, so they did not confound the comparison.
- Test split touched once per arm, after FREEZE, on all 12 arms; synth_shift_a went to rf (0.9378) rather than the intent's expected linear model on this split.
- A second Claude session started the same prompt in this directory and stood down before any arm was opened; I removed its one orphaned helper file so runs/ holds a single coherent helper set.
[81 turns, 1738 s]
```

What to notice: the outer loop did exactly what AIDE² prescribes and got a
zero - v2 fitted the same 24 recipes in the same order as v1 on every
problem, because the agent's `aide-tree` helper already spills into the
second- and third-best solutions' neighbours when the best one's do not
fill a batch of eight, so "top three" changed the operator's text and not
the search. The meter said so (median 0, MAD 0, no outliers, total gain
0.0) and rolled `operators.md` back to `gen_001`; the four guard lines never
moved. The guards also cost real fits: wine re-ran 11 suspicious 1.0 scores,
digits 5, and on digits a suspicious top score with no budget left was
*not* believed - the highest believed score went to the test split. The
meter has no token count and says why. As in lesson 11, this is `02.jsonl`;
a duplicate session (`01.jsonl`) stood down without opening an arm, and the
recorded agent removed its one orphaned helper file.

Files:

```text
step_15_rsi_aide2/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income-aide/            SKILL.md (aide-tree), operators.md, tools.md, schema.json, memory.json, eval.md ...
│   ├── adult-income-verifier/        reads the version arm the outer loop names
│   └── aide-outer/                   SKILL.md, tools.md (meter, propose, lint_pack ...), config.md
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income-aide/{<task>/{v1, v2}/, versions/}, aide-outer/{helpers/, patch/, adult_income/}
```

## Governance considerations

- **Who approves what.** Nobody per rewrite: the meter's rule across the
  set. The human wrote the rule, the guards, the task set and the budget.
- **The hook.** As always; the outer loop never calls `apply`.
- **What the helper refuses.** `lint_pack`: an operator without its guard;
  `propose`: any file but `operators.md`; `meter --decide`: two versions
  that did not spend the same fits.
- **What is and is not self-modified.** `operators.md` (versioned, and
  restored on a loss). The guards stay word for word; the meter and the
  task set do not change.
- **Honesty.** A kept rewrite on a tiny total gain is a kept rewrite on a
  tiny total gain; the page reports the gains per problem and the outliers
  discarded, not a headline.

## How to measure it

| Claim | Test |
|---|---|
| every operator carries the guard, word for word; `improve` expands the best solution; review marks suspicious scores | `test_every_operator_carries_the_guard` |
| the outer loop keeps only across the whole set under one meter, with the MAD layer, no token count, equal fits | `test_outer_loop_keeps_only_across_the_set_under_one_meter` |
| the inner agent re-runs a suspicious score and runs `aide-tree` | `test_inner_agent_re_runs_a_suspicious_score` |
| the pack contract for three packs and the six curriculum intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: `v1` and `v2` frozen and scored once with equal fits, a meter decision, four guards, a version (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 16 - MetaSkill-Evolve](../step_16_rsi_meta_skills/README.md): the
improver's skills improve too, slowly. Previous:
[lesson 14 - the DGM lineage](../step_14_rsi_self_modifying/README.md).
