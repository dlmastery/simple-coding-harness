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

```text
[Skill adult-income-curriculum]
[Read tools.md]  [Read adult-income/eval.md]  [Read adult-income/SKILL.md]  [Read adult-income-verifier/SKILL.md]  [Read the two tools.md]
agent> Now let me check what exists already: runs/, tasks, hooks, and any helpers from earlier lessons I might reuse.
$ ls -la && ls runs 2>/dev/null; ls ../tasks; cat .claude/settings.json; ls ../step_06_rsi_harness/runs/*/helpers 2>/dev/null; python -c "import sklearn, pandas, numpy; print(sklearn.__version__, pandas.__version__, numpy.__version__)"
01_adult_income 02_breast_cancer 03_wine 04_digits 05_synth_shift_a 06_synth_shift_b 07_exam
rt.py tools.py   verify.py
1.8.0 2.1.4 1.26.4
$ wc -l ../step_06_rsi_harness/runs/adult-income/helpers/*.py ../step_06_rsi_harness/runs/adult-income-verifier/helpers/*.py && for t in ../tasks/*; do echo "== $t"; cat $t/intent.md; done
agent> Let me read the step_06 helpers to see whether they can be reused as the runtime here.
[Read ../step_06_rsi_harness/runs/adult-income/helpers/rt.py]  [Read .../tools.py]  [Read .../verify.py]
$ mkdir -p runs/adult-income/helpers runs/adult-income-verifier/helpers runs/adult-income-curriculum/helpers && cp ../step_06_rsi_harness/runs/adult-income/helpers/rt.py ../step_06_rsi_harness/runs/adult-income/helpers/tools.py runs/adult-income/helpers/ && cp ../step_06_rsi_harness/runs/adult-income-verifier/helpers/verify.py runs/adult-income-verifier/helpers/ && ls runs/*/helpers
agent> Lesson 06's synthetic loader expects data.params; this series' intents list the parameters directly under data. Patching that, then adding a whole-arm runner to tools.py.
[Edit runs/adult-income/helpers/rt.py]  [Edit runs/adult-income/helpers/tools.py (run_arm: open -> policy -> fit until FREEZE -> score_test once -> scorecard)]
agent> Now the curriculum's own helpers, curve and exam.
[Write runs/adult-income-curriculum/helpers/curriculum.py (curve, exam)]
agent> Helpers built. Problem 1, control arm first:
$ python runs/adult-income/helpers/tools.py run_arm .claude/skills/adult-income ../tasks/01_adult_income --arm control --memory off
{"arm": "control", ..., "scorecard": {"best_val_score": 0.9177, "test_score": 0.9049, "fits_used": 24, "wasted_fits": 16, ...}}
agent> Control arm 1 done (best val 0.9177, test 0.9049, 16 wasted). Now the memory arm of problem 1 (empty memory, so it walks the static list) and the verifier.
$ export LOKY_MAX_CPU_COUNT=4 && python runs/adult-income/helpers/tools.py run_arm .claude/skills/adult-income ../tasks/01_adult_income --arm memory ...
calls: [('static (no applicable card)', 24)]   best_val_score 0.9177  test_score 0.9049  wasted_fits 16
agent> Memory arm 1 equals control (empty memory -> static walk), as expected. Now the verifier on problem 1: the tally, then the cards.
$ python runs/adult-income-verifier/helpers/verify.py read_traces .claude/skills/adult-income ../tasks/01_adult_income --scope problem --tally ...
profile {'n_rows': 6000, 'n_features': 14, 'n_classes': 2, 'imbalance': 0.239, 'has_categorical': 1} rows 24 pairs 60
wins {"class_weight": {"none": 8, "balanced": 4}, "encode": {"onehot": 12}, "scale": {"yes": 5, "no": 1}, "model": {"logreg": 3, "hgb": 16, "rf": 5}}
pair {'field': 'class_weight', 'a': 'none', 'b': 'balanced', 'a_score': 0.9114, 'b_score': 0.911, 'result': 'win:"none"'}
...
agent> The hand-check pairs agree (0.9114 vs 0.9110 -> none wins, etc.). Writing the nine cards as V:
$ python runs/adult-income-verifier/helpers/verify.py write_card .claude/skills/adult-income ../tasks/01_adult_income --as .claude/skills/adult-income-verifier --cards @runs/adult-income-verifier/cards_01.json && diff .claude/skills/adult-income/memory.json .agents/skills/adult-income/memory.json && echo mirrors-equal
{"n": 9, "new": 9, "demoted": 5, "total_on_disk": 9, "active": 4}
mirrors-equal
agent> Problem 1 done: 9 cards written, 4 active (hgb, scale yes, onehot, class_weight none), 5 counter cards demoted from birth. Problem 2, both arms:
$ ... run_arm $P ../tasks/02_breast_cancer --arm control --memory off ... && ... run_arm ... --arm memory ...
Exit code 1
KeyError: 'scorecard'
$ cat runs/adult-income/breast_cancer/control/state.json; ... tail -3 .../traces.jsonl
 "fits_used": 24, "frozen": true, "test_scored": 0, ...
$ python -c "(print every fit row of that arm)"
1 logreg yes onehot None ValueError: No valid specification of the columns. Only a sc
... (all 24 fits errored)
$ python -c "(reproduce: sklearn's feature_names are numpy.str_, which ColumnTransformer rejects as column selectors)"
[Edit runs/adult-income/helpers/rt.py]  (feature names cast to str; the profile counts numeric columns from dtypes)
$ rm -rf runs/adult-income/breast_cancer && ... (load every table of the curriculum and print its profile)
agent> Every table loads and fits now, with profiles matching the intents. Problem 2 again, both arms:
$ ... run_arm $P ../tasks/02_breast_cancer --arm control --memory off ... && ... --arm memory ...
CONTROL {'best_val_score': 0.9954, 'test_score': ..., 'fits_used': 24, 'wasted_fits': 0, 'test_touched_before_freeze': False}
MEMORY applicable 1 preferred {'scale': 'yes'}   calls [('obey-memory', 3), ('obey-memory', 8), ('obey-memory', 8), ('obey-memory', 8)]
MEMORY {'best_val_score': 0.996, 'fits_used': 24, 'wasted_fits': 0, ...}
agent> Memory arm won on val (0.9960 vs 0.9954) with only the scale: yes card applicable - the encode card stayed silent as intended. Verifier on problem 2:
$ ... read_traces $P ../tasks/02_breast_cancer --scope problem --tally ... && ... write_card ...
{"n": 6, "new": 3, ...}
agent> Problem 3 (wine, 3 classes):
$ ... run_arm ... 03_wine ...
CONTROL {'best_val_score': 1.0, ...}   MEMORY {'best_val_score': 1.0, ...}
agent> Wine saturates (1.0 on both arms, gap 0 - the honest number). Verifier on problem 3:
$ ... (tally: 0 new cards, counters on the losers)
agent> Problem 4 (digits, 10 classes):
$ ... run_arm ... 04_digits ...
CONTROL {'best_val_score': 0.999, ...}   MEMORY {'best_val_score': 0.999, ...}
agent> Problem 5 (synth A - the "trees always win" superstition test):
$ ... run_arm ... 05_synth_shift_a ...
CONTROL {'best_val_score': 0.9378, 'wasted_fits': 8, ...} {'model': 'rf', ...}   MEMORY {'best_val_score': 0.9378, 'wasted_fits': 2, ...}
agent> Same best (rf, 0.9378) but the memory arm reached it after 2 wasted fits versus 8. Verifier on problem 5:
$ ... read_traces ... --tally ... && ... write_card ...
profile {'n_rows': 800, 'n_features': 8, 'n_classes': 2, 'imbalance': 0.407, 'has_categorical': 0} rows 24 pairs 54
cards_by_rule [('n_rows', '<', 1000, {'field': 'model', 'prefer': 'rf'}, 1, 0), ..., ('imbalance', '>=', 0.35, {'field': 'class_weight', 'prefer': 'none'}, 1, 0), ...]
{"n": 6, "new": 3, ...}
agent> Problem 6 (synth B - rare class, small):
$ ... run_arm ... 06_synth_shift_b ...
CONTROL {'best_val_score': 0.7685, 'test_score': 0.6889, 'fits_used': 24, 'wasted_fits': 9, ...} {'model': 'rf', 'hyper': 16, 'scale': 'yes', 'encode': 'onehot', 'class_weight': 'balanced'}
MEMORY applicable 4 preferred {'model': 'hgb', 'hyper': None, 'scale': None, 'encode': None, 'class_weight': 'none'}
MEMORY {'best_val_score': 0.7685, 'test_score': 0.6889, 'fits_used': 24, 'wasted_fits': 6, ...} {'model': 'rf', ..., 'class_weight': 'balanced'}
$ ... read_traces ... 06_synth_shift_b --tally ... && ... write_card ... && diff ... && echo mirrors-equal
profile {'n_rows': 450, 'n_features': 8, 'n_classes': 2, 'imbalance': 0.158, 'has_categorical': 0} rows 24 pairs 54
cards_by_rule [('n_rows', '<', 1000, {'field': 'model', 'prefer': 'rf'}, 1, 0), ('n_rows', '<', 1000, {'field': 'model', 'prefer': 'hgb'}, 0, 1), ..., ('imbalance', '<', 0.35, {'field': 'class_weight', 'prefer': 'balanced'}, 1, 0), ('imbalance', '<', 0.35, {'field': 'class_weight', 'prefer': 'none'}, 0, 1)]
{"n": 6, "new": 0, ...}
mirrors-equal
agent> Curriculum done; the verifier demoted the hgb card for small tables on problem 6 (rf won there) and countered class_weight: none on the rare class. The learning curve:
$ python runs/adult-income-curriculum/helpers/curriculum.py curve .claude/skills/adult-income --tasks ../tasks ...
problem       | memory_best_val | control_best_val | gap_val | wasted_memory | wasted_control | cards_added | cards_demoted | cards_active
adult_income  | 0.9177          | 0.9177           | 0.0     | 16            | 16             | 9           | 5             | 4
breast_cancer | 0.996           | 0.9954           | 0.0006  | 0             | 0              | 6           | 8             | 7
wine          | 1.0             | 1.0              | 0.0     | 0             | 0              | 0           | 8             | 7
digits        | 0.999           | 0.999            | 0.0     | 0             | 0              | 2           | 9             | 8
synth_shift_a | 0.9378          | 0.9378           | 0.0     | 2             | 8              | 3           | 11            | 9
synth_shift_b | 0.7685          | 0.7685           | 0.0     | 6             | 9              | 0           | 12            | 8
agent> Curve written. Now the exam: record the sha256 of memory.json first, then five seeds, control then memory, no verifier.
$ mkdir -p runs/adult-income/exam && sha256sum .claude/skills/adult-income/memory.json | cut -d' ' -f1 | tee runs/adult-income/exam/memory_sha_before.txt && sha256sum .agents/skills/adult-income/memory.json | cut -d' ' -f1
08e1b5be99a19aef95133efb6038091e06b0f98969ad86c54f533307f80b654d
08e1b5be99a19aef95133efb6038091e06b0f98969ad86c54f533307f80b654d
$ for s in 0 1 2 3 4; do ... run_arm $P ../tasks/07_exam --arm control --seed $s --memory off ...; ... run_arm ... --arm memory --seed $s ...; done
seed 0 CONTROL {'best_val_score': 0.9389, 'test_score': 0.7831, 'wasted_fits': 8} {'model': 'rf', 'hyper': 16, ...}
seed 0 MEMORY  {'best_val_score': 0.9412, 'test_score': 0.7819, 'wasted_fits': 1} {'model': 'rf', 'hyper': None, ...} applicable 4 preferred {'hyper': 16, 'scale': 'yes', 'class_weight': 'none'}
seed 1 CONTROL {'best_val_score': 0.8615, 'test_score': 0.7244, 'wasted_fits': 17} {'model': 'hgb', 'hyper': 0.1, ..., 'class_weight': 'balanced'}
seed 1 MEMORY  {'best_val_score': 0.872, 'test_score': 0.717, 'wasted_fits': 12} {'model': 'hgb', 'hyper': 0.3, ..., 'class_weight': 'none'} applicable 4
seed 2 CONTROL {'best_val_score': 0.7991, 'test_score': 0.8288, 'wasted_fits': 8}   seed 2 MEMORY {'best_val_score': 0.7991, 'test_score': 0.8288, 'wasted_fits': 1}
seed 3 CONTROL {'best_val_score': 0.8245, 'test_score': 0.8335, 'wasted_fits': 8}   seed 3 MEMORY {'best_val_score': 0.8245, 'test_score': 0.8335, 'wasted_fits': 1}
seed 4 CONTROL {'test_score': 0.8178, 'wasted_fits': 16}   seed 4 MEMORY {'test_score': 0.8333, 'wasted_fits': 12}
agent> All ten exam arms froze and scored once. The exam report:
$ python runs/adult-income-curriculum/helpers/curriculum.py exam .claude/skills/adult-income ../tasks/07_exam --seeds 0,1,2,3,4 ... && sha256sum .agents/skills/adult-income/memory.json | cut -d' ' -f1 && ls runs/adult-income/curve.json runs/adult-income/exam.json && diff -r .claude/skills .agents/skills && echo mirrors-identical
seed | memory_test | control_test | memory_wasted | control_wasted | winner  | applicable_cards | not_transferred
0    | 0.7819      | 0.7831       | 1             | 8              | control | 4                | 2
1    | 0.717       | 0.7244       | 12            | 17             | control | 4                | 2
2    | 0.8288      | 0.8288       | 1             | 8              | memory  | 4                | 1
3    | 0.8335      | 0.8335       | 1             | 8              | memory  | 4                | 1
4    | 0.8333      | 0.8178       | 12            | 16             | memory  | 4                | 2
wins 3 of 5 | mean_test_gap 0.0014 | pack_unchanged True | no_card_written True
sha before 08e1b5be...b654d   sha after  08e1b5be...b654d
mirrors-identical
agent> Done. runs/adult-income/curve.json and runs/adult-income/exam.json exist; both mirrors of the pack are identical.
(memory.json ends with 20 cards, 8 active. Every arm: 24 fits, test_scored_once true, test_touched_before_freeze false; save_model never run.)
Exam: wins 3 of 5 - mean_test_gap +0.0014 - pack_unchanged true (sha256 08e1b5be...b654d before and after) - no_card_written true.
Cards that applied but did not transfer: both hyper cards under n_classes < 3 - prefer 16 (evidence 2) and prefer 0.1 (evidence 1). The scale: yes and class_weight: none cards transferred on every seed.
The claims of eval.md:
- Gap never negative - held: gaps are 0, +0.0006, 0, 0, 0, 0.
- Gap larger on problem 6 than on problem 2 - did not hold: gap_6 = 0.0 vs gap_2 = 0.0006. On problems 5 and 6 both arms found the same best recipe; the memory arm's advantage showed up as fewer wasted fits (2 vs 8, 6 vs 9), not a higher val score.
- Exam: memory wins >= 3 of 5 seeds - held (3 of 5: two ties on test score won by fewer wasted fits, one outright win on seed 4; seeds 0 and 1 went to control by 0.0012 and 0.0074).
- memory.json byte-identical across the exam - held; no write_card event in any exam trace - held.
- Every applicable card that did not transfer is named - held.
- Test split locked - held on all 22 arms.
Two things to know about the run: (1) the first problem-2 control arm was burned by a helper bug (sklearn's numpy.str_ column names made every fit error); I fixed rt.py, deleted that arm directory under runs/ - the pack was never touched - and reran it. (2) The helpers were seeded from lesson 06's runtime, with a run_arm tool that performs one whole arm per call (open -> obey-memory/static -> FREEZE -> one score_test -> scorecard), as the curriculum skill allows.
[53 turns, 866 s]
```

What to notice: the agent reused lesson 06's helpers (the skill allows it),
found a real bug in them on the first all-numeric table, fixed it, and said
so - including that it deleted the burned arm directory under `runs/` to
rerun, which is the one thing the trace's append-only rule cannot police.
The curve's val gap is 0 on five problems (wine and digits saturate; the
synthetic tables have one best recipe both arms find), +0.0006 on breast
cancer, and the memory's advantage is in wasted fits on problems 5 and 6
(2 vs 8, 6 vs 9); the claim "gap larger on problem 6 than on 2" did not
hold, and the report says so. The exam: 3 of 5, the pack byte-identical, the
two `hyper` cards that did not transfer named per seed. This is the number
the whole series is honest about: the pack learned where to look, not a
better score, on tables this small.

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
