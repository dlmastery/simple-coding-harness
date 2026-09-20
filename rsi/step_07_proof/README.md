# Lesson 07 - The proof: a locked test, a learning curve, an exam

Lesson 06 showed one problem learning from itself. This lesson asks the
question the framework paper asks of every loop: did the successor get
stronger *under a comparable budget and an independent evaluation*? Three
instruments, all written as contracts the agent implements. The locked test:
one score per arm per problem, after `FREEZE`, never before - `score_test`
and the hook both refuse, and `test_touched_before_freeze` is on every
scorecard. The learning curve: problems 1 to 6 in order, the pack carried
forward, the verifier writing after each memory arm, and per problem the
memory arm's best validation score minus the control arm's at the same
budget, plus the fits each arm wasted before reaching the control arm's
answer. The exam: a seventh table the pack never wrote to, run over five
seeds with the memory read but never written - `write_card` refuses on an
exam problem - and the pack's `memory.json` byte-identical before and after.
`eval.md` in the actor pack states the claims and the scorecard; the
`adult-income-curriculum` skill orchestrates; the helpers measure. Wine and
digits saturate this recipe space and teach nothing; the page says so, and
the numbers are honest about it.

## Getting started

Prerequisites: lesson 06 (the actor and verifier packs are the same, plus
`eval.md`); the seven intents under `../tasks/`. This lesson adds `eval.md`
to the actor, the curriculum pack (`SKILL.md`, `tools.md` with the `curve`
and `exam` contracts), and a run that takes about half an hour in Claude
Code - the helpers do the fits, the agent does the orchestration, and a
helper is allowed to run a whole arm in one call as long as every step
writes what its contract says.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the curriculum (problems 1 to 6, both arms, the verifier after each memory arm), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report.
   ```

2. No approval: the acceptance rule is `eval.md`, written beforehand. The
   hook blocks `score_test` until an arm's `state.json` says `"frozen": true`.

3. Headless, as recorded:

   ```bash
   claude -p "Use the adult-income-curriculum skill: run the curriculum (problems 1 to 6, both arms, the verifier after each memory arm), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: `eval.md` states the three
   claims and the 14-field scorecard; the curriculum runs six problems then
   the exam without a verifier; the exam intent forbids writing and the
   verifier contract refuses on it; the `curve` and `exam` contracts never
   invent a missing number. `RSI_LIVE=1`: for each of the six problems both
   arms are frozen and scored once, `test_touched_before_freeze` is false,
   a `write_card` event follows the memory arm; `curve.json` has six rows;
   ten exam arms (`control`, `memory`, `control-s1` .. `memory-s4`) are
   frozen and scored once with no `write_card` event; `exam.json` says
   `pack_unchanged` and `no_card_written`; both mirrors equal.

5. To reset: restore the two packs (`git checkout -- .claude .agents`) and
   `rm -rf runs`.

## What it looks like

`.claude/skills/adult-income/eval.md` - how the pack is judged:

```markdown
## The comparison
- Two arms per problem, same seed, same split, same helper, same budget of 24 fits: the memory arm (this pack as it is) and the control arm (`--arm control --memory off`: `memory.json` not read, which is lesson 01's static walk).
- The test split is locked: scored once per arm, after FREEZE, never before. `test_touched_before_freeze` must be `false` on every scorecard; `score_test` and the hook refuse anything else.
- The delete-the-file check: `memory: off` in `config.md` must give the control arm's numbers exactly; a difference means something other than the cards changed.

## The learning curve
Problems 1 to 6 in order, the pack carried forward, the verifier writing after each memory arm. Per problem: `gap_val` = memory best val - control best val; `wasted` = fits before reaching the control arm's best (within 0.005), plus every fit that errored; cards added / demoted / active. The claim: the gap is never negative, and larger on the last problem than on the second. The numbers are this machine's - the agent wrote the fit helper - but both arms share it, so the gap is real.

## The exam
Problem 7 is never written to: `write_card` refuses on an exam problem, and the curriculum runs no verifier there. Five seeds of the split. The claim: the memory arm beats the control arm on at least 3 of 5 seeds (a higher test score, or the same score with fewer wasted fits), the pack's `memory.json` is byte-identical before and after, and the report names every applicable card that did not transfer.
```

`.claude/skills/adult-income-curriculum/SKILL.md` - the orchestration:

```markdown
## Procedure
1. Build the helpers once: the actor's set under `runs/adult-income/helpers/` (as `P/SKILL.md` says), the verifier's under `runs/adult-income-verifier/helpers/`, and `curve` and `exam` under `runs/adult-income-curriculum/helpers/`. Reuse what exists. A helper may run a whole arm in one call (open, `read_memory --order`, fit, repeat until FREEZE, score once, scorecard) as long as every step writes what its contract says.
2. For each curriculum task `T`, in order (01 .. 06):
   a. Control arm: follow `P/SKILL.md` with `--arm control --memory off` (open, fit the static list in one call, score the best once after FREEZE, scorecard).
   b. Memory arm: follow `P/SKILL.md` with the default arm (open, `read_memory --order obey-memory` for the next recipes, fit them, repeat until FREEZE, score once, scorecard).
   c. Verifier: follow `V/SKILL.md` on `T` (the tally, then the cards, written with `--as V`).
   Do not run `save_model` in this lesson; the models are not the deliverable.
3. The learning curve: `curve P --tasks ../tasks`. Show the table. The claim of `eval.md`: `gap_val` never negative, larger on problem 6 than on problem 2.
4. The exam, on `../tasks/07_exam`, for each seed `s` in 0, 1, 2, 3, 4: the control arm with `--arm control --seed s --memory off`, then the memory arm with `--seed s` (both as in step 2, `--seed s` on every command; the arm directories are `control-s<s>` and `memory-s<s>` for s > 0). No verifier: a card write on the exam problem is refused, and you do not ask for one. Record the sha256 of `P/memory.json` before the first exam arm.
5. The exam report: `exam P ../tasks/07_exam --seeds 0,1,2,3,4`. Show the table: wins out of 5, the mean test gap, the cards that did not transfer, `pack_unchanged` and `no_card_written` (both must be true).
```

`.claude/skills/adult-income-curriculum/tools.md` - the two contracts:

```markdown
- `curve(pack, tasks)` - for every curriculum problem (`role: curriculum`, index order) with both arms scored, the row `problem, memory_best_val, control_best_val, gap_val (memory - control), wasted_memory, wasted_control (fits each arm spent before reaching the control arm's best val within 0.005), cards_added, cards_demoted, cards_active`; a problem without both scorecards is listed as `missing`, never invented. Write `runs/<pack name>/curve.json` and print the table.
- `exam(pack, task, seeds)` - for the exam problem, per seed: both arms' `test_score`, `wasted_fits`, the winner (higher test score, or the same score with fewer wasted fits); `wins` out of the seeds, `mean_test_gap` (memory - control), `not_transferred`: every card that applied whose preferred value is absent from the memory arm's best recipe on that seed; `pack_unchanged` (sha256 of `memory.json` before the first exam arm equals the one after the last) and `no_card_written` (no `write_card` event in any exam trace). Write `runs/<pack name>/exam.json`, print the table.
```

`test_step.py` - the exam assertions:

```python
    exam = json.loads((RUNS / "adult-income" / "exam.json").read_text(encoding="utf-8"))
    assert exam["pack_unchanged"] is True and exam["no_card_written"] is True and 0 <= exam["wins"] <= 5
    for s in range(5):
        for arm in ("control", "memory"):
            name = arm if s == 0 else f"{arm}-s{s}"
            st = state("adult-income", "exam", name)
            assert st["frozen"] is True and st["test_scored"] == 1 and st["seed"] == s, name
            assert not any(r.get("event") == "write_card" for r in rows(RUNS / "adult-income" / "exam" / name / "traces.jsonl"))
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed to their
scorecards, the curve and exam tables in full):

<!-- transcript -->

Files:

```text
step_07_proof/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json
│   └── skills/
│       ├── adult-income/                 lesson 06's actor + eval.md
│       ├── adult-income-verifier/        lesson 06's verifier
│       └── adult-income-curriculum/
│           ├── SKILL.md                  six problems x (control, memory, verifier); curve; the exam over five seeds; exam
│           └── tools.md                  curve, exam (the actor's and verifier's helpers are theirs)
├── .agents/skills/                       the same three packs
└── runs/                                 (after a run) adult-income/{helpers/, <task>/{control,memory}/, exam/{control,memory,control-s1..memory-s4}/, curve.json, exam.json}
```

## Governance considerations

- **Who approves what.** Nobody during the run; the human wrote `eval.md`
  before it. The verifier writes cards under its contract after every
  curriculum problem and never on the exam.
- **The hook.** `score_test` after `"frozen": true` only - on every one of
  the 22 arms.
- **What the helper refuses.** `write_card` on the exam (`role: exam`);
  a second `score_test`; `curve` and `exam` refuse to invent a missing row.
- **What is and is not self-modified.** `memory.json` changes six times
  (both mirrors) and not once during the exam; `exam.json` carries the
  sha256 proof. Nothing else in the packs changes.
- **The evidence standard.** Matched budget (24 and 24), one test score per
  arm, five seeds on a held-out table, and the report names the cards that
  did not transfer. This is *structural* recursion made visible (a later
  round runs under files an earlier round wrote) and the exam is the
  *effective* test. The numbers are this machine's; the comparison is the
  claim.

## How to measure it

| Claim | Test |
|---|---|
| `eval.md` states the comparison, the curve, the exam and the 14-field scorecard | `test_eval_states_the_three_claims_and_the_scorecard` |
| the curriculum runs 01..06 then the exam over five seeds, no verifier on the exam, no `save_model` | `test_curriculum_runs_six_then_the_exam_without_a_verifier` |
| the exam intent forbids writing; `write_card` refuses on `role: exam` | `test_the_exam_intent_forbids_writing` |
| `curve` and `exam` never invent a missing number; the exam proves the pack unchanged and no card written | `test_curve_and_exam_contracts_never_invent` |
| the pack contract for the three packs and the seven intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: six problems x two arms frozen and scored once, a card write after each memory arm, six curve rows, ten exam arms with no card write, `pack_unchanged`, `no_card_written` (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields: all 14, on 22 arms.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 08 - a meta skill generates the RSI harness](../step_08_meta_generates_rsi/README.md):
the writer emits actor and verifier, and the human approves the contract.
Previous: [lesson 06 - the RSI harness](../step_06_rsi_harness/README.md).
