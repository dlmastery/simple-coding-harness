# Lesson 11 - RSIAgent: the next experiment, chosen on purpose; the memory, frozen at test

RSIAgent (arXiv:2609.15364) splits the loop into a curriculum module that
chooses experiments, an actor that runs them, and a verifier that sees only
the world result. Here that is three packs. The planner
(`adult-income-planner`) scores every model family by uncertainty
`u = (1 - success) + c / (n + 1)` - a broad phase with `c` 2.0 that
round-robins every family before any is repeated, then a deep phase with
`c` 0.25 that goes where the faults are - and writes 12 experiments at a
time to the actor's `plan.json`. The actor (`adult-income-actor`) runs the
plan and, before it scores the test, freezes its memory: `freeze_memory`
sets `"memory": "frozen"` in the arm's state and every card write refuses
from then on. The verifier writes for the *next* problem. The same 24 fits
buy higher-information experiments, and the comparison at test time is
against a memory that cannot move. L3 (the system chooses which experience
to acquire) plus L4; the verifier stays human-written.

## Getting started

Prerequisites: lesson 07 (the curriculum and the verifier). This lesson adds
the planner pack (`write_plan` contract), `plan.json` and the
`freeze_memory` contract to the actor, and a curriculum that asks the
planner twice per memory arm.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the curriculum (problems 1 to 6: control arm; memory arm with the planner's broad plan, then its deep plan, then freeze_memory before the test; the verifier after the test), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report.
   ```

2. No approval: the planner's rule and the verifier contract are the
   acceptance rules, written beforehand.

3. Headless, as recorded:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the planner states the
   uncertainty rule with both `c` values and 12 experiments per phase; the
   actor runs `plan.json`, never writes it, and freezes the memory before
   `score_test`; `write_plan` refuses a second plan per phase.
   `RSI_LIVE=1`: on every problem the first three fits touch all three
   families, the plan events are `broad` then `deep`, `freeze_memory`
   precedes `score_test` and the state says `frozen`; the exam is unchanged.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-planner/SKILL.md`:

```markdown
2. Score every model family by uncertainty `u = (1 - success) + c / (n + 1)`, where `n` is the family's fits on this problem so far and `success` is `(wins + 1) / (n + 2)` with a win = a val_score at least the first fit's (the baseline). The helper prints these per family; check them.
   Broad c: 2.0
   Deep c: 0.25
   Experiments per phase: 12
   In the broad phase every family starts equal and the large `c` makes the plan round-robin: every family is touched before any is repeated. In the deep phase the small `c` lets `1 - success` dominate: the family with the most faults (fits below the baseline, or errors) comes first.
3. Build the plan greedily: 12 times, take the family with the highest `u` (ties: the family the cards prefer, then schema order), give it its next untried recipe (static recipes of `schema.json -> recipes` before hyper variants; inside those, the recipes carrying the most card-preferred values first), and count that experiment as one more fit for the family (recompute `u` with `n + 1` and the same success).
```

`.claude/skills/adult-income-actor/SKILL.md` - the plan and the freeze:

```markdown
3. Search, in two phases the planner writes:
   - control arm: walk `schema.json -> recipes` in order, in one call.
   - memory arm: ask the planner (`.claude/skills/adult-income-planner/SKILL.md`) for the broad plan; fit the 12 experiments of `plan.json` in order (`fit_recipe P T --arm memory --recipes <the 12>`); ask the planner again for the deep plan; fit its 12. A recipe a `forbid` card rules out is refused and costs no fit. When `plan.json` holds no untried experiment and fits remain, take the static list's next untried recipe. The 24th fit says `FREEZE`.
   Search policy: planned
   Freeze the memory before the test: `freeze_memory P T --arm memory` sets `"memory": "frozen"` in the arm's state; from then on a card write refuses on this arm; the verifier, run afterwards by the curriculum skill, writes to `memory.json` for the *next* problem, never for the arm that was just scored.
```

`.claude/skills/adult-income-actor/tools.md` - the two contracts:

```markdown
- `freeze_memory(pack, task, arm)` - set `"memory": "frozen"` in the arm's `state.json` and append `{"event": "freeze_memory"}`; refuse before FREEZE. From then on `write_card` refuses for this arm: the comparison at test time is against a memory that cannot move.
```

```markdown
- `write_plan(pack, task, target, plan)` / `write_plan(..., uncertainty=True, c=<c>)` - with `uncertainty`: per model family on this problem's memory arm, `n` (fits so far), `wins` (val at or above the first fit's), `success = (wins + 1) / (n + 2)`, `faults` (fits below the first fit's, or errored) and `u = (1 - success) + c / (n + 1)`; print them. With `plan`: refuse a plan without `phase` (`broad` | `deep`), `c` and exactly 12 `experiments` from `schema.json -> fields`, refuse a second plan in the same phase on the same problem; write it to `<target>/plan.json` (both mirrors), append `{"event": "plan", "phase", "c"}` and print the families in order.
```

`test_step.py`:

```python
        first = fits_of(task)[:3]
        assert {r["recipe"]["model"] for r in first} == {"logreg", "rf", "hgb"}, f"broad phase did not touch every family first on {task}"
        plans = [r for r in rows(RUNS / "adult-income-actor" / task / "memory" / "traces.jsonl") if r.get("event") == "plan"]
        assert [p["phase"] for p in plans] == ["broad", "deep"], task
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, one
planner visit in full):

```text
[Skill adult-income-curriculum]
[Read the curriculum's tools.md, the actor's eval.md / SKILL.md / tools.md, the planner's SKILL.md / tools.md, the verifier's SKILL.md / tools.md, plan.json, schema, memory schema, config, memory.json]
[Write runs/adult-income-actor/helpers/actor.py]  [Write runs/adult-income-planner/helpers/planner.py]  [Write runs/adult-income-verifier/helpers/verifier.py]  [Write runs/adult-income-curriculum/helpers/curriculum.py]
agent> Helpers are built. Problem 1, control arm: open, then walk the static list in one call.
$ ... actor.py load_splits $P $T --arm control --memory off; ... fit_recipe ... --recipes @static; ... score_test ...; ... scorecard ...
{"best_val_score": 0.9177, "test_score": 0.9049, "fits_used": 24, "wasted_fits": 16, ...}
agent> Problem 1 memory arm: open, then the planner's broad plan.
$ P=.claude/skills/adult-income-actor; C=.claude/skills/adult-income-planner; T=../tasks/01_adult_income; A="python runs/adult-income-actor/helpers/actor.py"; PL="python runs/adult-income-planner/helpers/planner.py"; $A load_splits $P $T --arm memory | ... && $PL write_plan $C $T --target $P --uncertainty --c 2.0 | ... && $PL write_plan $C $T --target $P --plan '{"phase": "broad", "c": 2.0, "experiments": [...12...]}'
{'profile': {'n_rows': 6000, 'n_features': 14, 'n_classes': 2, 'imbalance': 0.239, 'has_categorical': 1}, 'memory': 'on', 'cards_applicable': [], 'preferred': {...null...}, 'forbidden': {...}}
{"problem": "adult_income", "arm": "memory", "fits_so_far": 0, "baseline": null, "families": {"logreg": {"n": 0, "wins": 0, "success": 0.5, "faults": 0, "u": 2.5}, "rf": {... "u": 2.5}, "hgb": {... "u": 2.5}}, "c": 2.0}
{"phase": "broad", "c": 2.0, "families_in_order": ["logreg", "rf", "hgb", "logreg", "rf", "hgb", "logreg", "rf", "hgb", "logreg", "rf", "hgb"], "written": ".claude/skills/adult-income-actor/plan.json"}
$ ... $A fit_recipe $P $T --arm memory --recipes plan | ...
1 logreg 1 yes onehot none 0.9114
2 rf 16 yes onehot none 0.9054
3 hgb 0.1 yes onehot none 0.9177
4 logreg 1 yes onehot balanced 0.911
5 rf 16 yes onehot balanced 0.9033
6 hgb 0.1 yes onehot balanced 0.917
... (6 more: the round-robin continues)
$ ... $PL write_plan $C $T --target $P --uncertainty --c 0.25 | ... && $PL write_plan ... --plan '{"phase": "deep", "c": 0.25, "experiments": [...12...]}'
{"families": {"logreg": {"n": 4, "wins": 1, "success": 0.333, "faults": 3, "u": 0.717}, "rf": {"n": 4, "wins": 0, "success": 0.167, "faults": 4, "u": 0.883}, "hgb": {"n": 4, "wins": 4, "success": 0.833, "faults": 0, "u": 0.217}}, "c": 0.25}
{"phase": "deep", "c": 0.25, "families_in_order": ["rf", "rf", "rf", "rf", "rf", "rf", "rf", "rf", "rf", "rf", "rf", "rf"], ...}
$ ... $A fit_recipe $P $T --arm memory --recipes plan | ...
13 rf 16 no onehot none 0.9049
14 rf 16 no onehot balanced 0.9034
... 17 rf 8 yes onehot none 0.9112 ... 24 ... FREEZE
$ $A freeze_memory $P $T --arm memory && $A score_test $P $T --arm memory --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}' && $A scorecard $P $T --arm memory
{"memory": "frozen", "event": "freeze_memory"}
{"arm": "memory", "recipe": {...}, "test_score": 0.9049, "test_scored": 1}
{"best_val_score": 0.9177, "test_score": 0.9049, "fits_used": 24, "wasted_fits": 2, ...}
agent> Problem 1 verifier: the tally, then the cards.
$ ... verifier.py read_traces $P $T --scope problem --tally ...; ... write_card $P $T --as $V --cards ...
profile {...} rows 24 pairs ... ; {"n": 9, "new": 9, ...}
... (problems 2-6 the same way: control arm, broad plan, 12 fits, deep plan, 12 fits, freeze_memory, score_test once, scorecard, verifier)
agent> Problem 5 (synth_shift_a).
... (the exam: for s in 0..4, control arm and memory arm with the planner's two plans; no verifier)
agent> Exam done for all five seeds. The exam report:
$ python runs/adult-income-curriculum/helpers/curriculum.py exam .claude/skills/adult-income-actor ../tasks/07_exam --seeds 0,1,2,3,4 | ...; sha256sum .claude/skills/adult-income-actor/memory.json .agents/skills/adult-income-actor/memory.json; diff -r .claude/skills .agents/skills && echo MIRRORS_IDENTICAL; ls runs/adult-income-actor/
(the table below)
MIRRORS_IDENTICAL
agent> Both tables were produced by the helpers; runs/adult-income-actor/curve.json and exam.json exist, .claude/skills == .agents/skills.
## Learning curve
| problem       | memory_best_val | control_best_val | gap_val | wasted_memory | wasted_control | cards_added | cards_demoted | cards_active |
| adult_income  | 0.9177 | 0.9177 | 0.0 | 2  | 16 | 9 | 0 | 4 |
| breast_cancer | 0.9954 | 0.9954 | 0.0 | 0  | 0  | 5 | 0 | 6 |
| wine          | 1.0    | 1.0    | 0.0 | 0  | 0  | 0 | 0 | 6 |
| digits        | 0.999  | 0.999  | 0.0 | 0  | 0  | 4 | 0 | 8 |
| synth_shift_a | 0.9378 | 0.9378 | 0.0 | 2  | 8  | 0 | 1 | 7 |
| synth_shift_b | 0.7685 | 0.7685 | 0.0 | 14 | 9  | 2 | 2 | 6 |
Test scores were identical per arm on every problem (0.9049, 0.9806, 1.0, 0.9984, 0.8981, 0.6889). Every memory arm ends with frozen: true, memory: "frozen", freeze_memory before score_test, and test_touched_before_freeze: false on all 22 scorecards.
## Plans per problem (phase -> families in order)
| adult_income  | broad: logreg, rf, hgb x4 (round-robin)          | deep: rf x12 (4 faults) |
| breast_cancer | broad: logreg, rf, hgb x4                        | deep: rf x12 (4 faults) |
| wine          | broad: hgb, logreg, rf x4 (hgb card breaks the tie) | deep: hgb, logreg, rf x4 (no faults, all tied) |
| digits        | broad: hgb, logreg, rf x4                        | deep: logreg x12 (4 faults; hyper 0.25 / 4 variants) |
| synth_shift_a | broad: hgb, logreg, rf x4                        | deep: logreg x12 (4 faults) |
| synth_shift_b | broad: hgb, logreg, rf x4                        | deep: hgb, logreg, rf x4 (all tied at baseline) |
| exam, seeds 0-4 | broad: logreg, rf, hgb x4                      | deep: logreg, rf, hgb x4 |
## Exam
| seed | memory_test | control_test | test_gap | memory_wasted | control_wasted | winner | cards_applied |
| 0 | 0.7831 | 0.7831 | 0.0 | 1 | 8  | memory | 2 |
| 1 | 0.7244 | 0.7244 | 0.0 | 5 | 17 | memory | 2 |
| 2 | 0.8288 | 0.8288 | 0.0 | 1 | 8  | memory | 2 |
| 3 | 0.8335 | 0.8335 | 0.0 | 1 | 8  | memory | 2 |
| 4 | 0.8178 | 0.8178 | 0.0 | 2 | 16 | memory | 2 |
wins 5/5 - mean_test_gap 0.0 - pack_unchanged true (sha256 980fc464...4d0c before and after) - no_card_written true.
Cards that did not transfer: hyper -> prefer 8 (if n_classes < 3, evidence 2) on all five seeds - the best recipe held hyper 16 (seeds 0, 2, 3) or 0.1 (seeds 1, 4). The scale -> yes (n_features >= 10) card transferred on every seed.
## The claims of eval.md
- gap_val never negative - held: 0.0 on all six problems.
- gap larger on problem 6 than on problem 2 - did not hold: 0.0 vs 0.0; this recipe space saturates (wine, digits) and the planner reaches the same best on every problem, so the memory shows up in wasted fits (2 vs 16 on problem 1, 2 vs 8 on problem 5), not in the best val - and on problem 6 the inherited class_weight: none card cost fits (14 vs 9) before the verifier demoted it.
- test split scored once, after FREEZE - held: test_scored_once true and test_touched_before_freeze false on every scorecard, and the hook never fired.
- exam: memory beats control on >= 3 of 5 seeds - held, 5/5, every win on the tie-break (same test score, fewer wasted fits), none on a higher test score.
- memory.json byte-identical before and after the exam - held. The report names every applicable card that did not transfer - held: the hyper-8 card, on all five seeds.
Two notes on how I read the contracts: the planner helper builds the greedy plan from the rule and writes it through the same write_plan validation (the uncertainty table is printed and checked first each phase); and write_card refuses on a frozen arm only until that arm's test is scored, since the curriculum calls the verifier after freeze_memory + score_test and the write is for the next problem - the literal "memory frozen" refusal would otherwise block every verifier visit.
[55 turns, 1597 s]
```

What to notice: the broad phase is visibly round-robin (`logreg, rf, hgb`
x4, or the card-preferred family first) and the deep phase goes where the
faults are (`rf x12` on Adult, `logreg x12` on digits); the uncertainty
table is printed before each plan. The memory arm's test score equals the
control's on every problem and every exam seed - the same best recipe both
ways - and the whole effect is in wasted fits (2 vs 16 on problem 1, 5 vs
17 on exam seed 1), so the exam "held" 5 of 5 on the tie-break alone; the
page says so. On problem 6 an inherited card cost fits before the verifier
demoted it (14 vs 9): a card can hurt, and the curve shows it. The agent
also explains a contract reading it made (`write_card` on a frozen arm
refuses until that arm's test is scored, because the verifier writes for the
next problem) - the kind of judgement a pure-skills runtime leaves to the
agent, recorded rather than hidden. This recording is `02.jsonl`: a second
session started by mistake at the same time (`01.jsonl`), noticed the
collision, stood by and exited without opening an arm.

Files:

```text
step_11_rsi_agent/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income-planner/         SKILL.md (the uncertainty rule), tools.md (write_plan, read_memory)
│   ├── adult-income-actor/           SKILL.md (runs plan.json, freeze_memory before the test), tools.md, plan.json, memory.json, eval.md ...
│   ├── adult-income-verifier/
│   └── adult-income-curriculum/
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income-actor/, adult-income-planner/helpers/, adult-income-verifier/helpers/
```

## Governance considerations

- **Who approves what.** Nobody per experiment: the planner's rule is the
  human's, the verifier contract is the human's. `plan.json` is written by
  the planner only (`write_plan` refuses a second plan per phase).
- **The hook.** As always.
- **What the helper refuses.** `freeze_memory` before FREEZE; a card write
  on a frozen arm; a plan with the wrong shape.
- **What is and is not self-modified.** `plan.json` (twice per problem) and
  `memory.json` (after the test, for the next problem). The planner's rule
  and its two `c` values are files a human wrote; lesson 16 shows what it
  means to let a slow loop change such numbers.
- **The evidence standard.** Frozen memory at test is what makes the
  comparison fair: the memory arm at `score_test` time holds exactly what it
  held when its 24 fits were chosen.

## How to measure it

| Claim | Test |
|---|---|
| the planner states `u`, `c` broad / deep, 12 per phase, round-robin then faults first | `test_planner_states_the_uncertainty_rule` |
| the actor runs `plan.json`, never writes it, freezes memory before `score_test`; `plan.json` ships empty | `test_actor_runs_the_plan_and_freezes_memory_before_the_test` |
| `write_plan` refuses a second plan per phase and a plan without 12 experiments | `test_write_plan_contract_refuses_a_second_plan_per_phase` |
| the pack contract for four packs | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: broad touches every family first, `broad` then `deep`, `freeze_memory` before `score_test`, the exam unchanged (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 12 - ModularRSI](../step_12_rsi_modular/README.md): a harness module
evolved off the benchmark. Previous: [lesson 10 - Dream-RSI](../step_10_rsi_dream/README.md).
