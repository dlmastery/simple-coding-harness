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

<!-- transcript -->

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
