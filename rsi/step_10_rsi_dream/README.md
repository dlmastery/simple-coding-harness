# Lesson 10 - Dream-RSI: rank the search policies on the log, at zero fits

Dream-RSI (arXiv:2609.14858) replays experience as a simulator. Here the
experience is the fit log, and the thing chosen from it is the actor's
*search policy* - the one line of `SKILL.md` that says how the next 24
recipes are picked. The meta pack, `adult-income-meta-dream`, ranks five
policies (`static`, `obey-memory`, `random`, `neighbours-of-top-3`,
`prefer-untried-family`) by walking each one's first 24 picks against the
log of the problem just finished: a pick the log holds is answered with its
logged score; a pick the log does not hold is `unknown`. No fit is spent -
`rank_policies` reports `fits_spent: 0` and the actor's `state.json` is
unchanged - and the winner is proposed as the policy line behind the private
gate. The honest part is the `unknown` count. The log is an exact gym for
the recipes you visited and silent everywhere else; when every policy's
unknowns are 0 the log is saturated, the next lap will visit nothing new,
and recursion pays only if it does. The page says so instead of hiding it.
This is the paper's L2: the system chooses the search strategy; the policy
library stays human.

## Getting started

Prerequisites: lesson 09 (the gate, `propose`, versions; the actor with
`Search policy: static`). This lesson replaces the meta pack by
`adult-income-meta-dream` (`policies.md`, the `rank_policies` contract,
`patches: ["SKILL.md"]`, `approval: gate`) and teaches the actor the five
policies (`read_memory --order <name>` implements them).

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill with the adult-income-meta-dream meta pack: run the curriculum (problems 1 to 6: control arm, memory arm, verifier, then the replay visit), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report, and list every ranking with its unknown counts and the gate's verdict.
   ```

2. No approval: the winner lands behind the gate or is rolled back.

3. Headless, as recorded:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: `policies.md` names the five
   policies and the actor knows them; the `rank_policies` contract spends
   nothing, counts unknowns and names saturation; only the policy line is
   patched, behind the gate. `RSI_LIVE=1`: every curriculum arm frozen and
   scored once; a `rank` event per problem with `fits_spent` 0; the curve
   and the exam with the pack unchanged; both mirrors equal.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-meta-dream/policies.md`:

```markdown
- `static`: walk `schema.json -> recipes` in order, cards or no cards.
- `obey-memory`: probe one recipe per model (the preferred model first) with the preferred preprocessing; then the believed family - its static recipes, then its hyper variants - ranked by the cards; then the rest of the grid.
- `random`: the 72-recipe grid in a seeded shuffle (`numpy.random.default_rng(seed)`).
- `neighbours-of-top-3`: six static fits, then the untried neighbours (one field away, a model change taking the new model's middle hyper value) of the three best so far, then the static list.
- `prefer-untried-family`: at every step the model family with the fewest fits so far, static recipes before hyper variants.
```

`.claude/skills/adult-income-meta-dream/tools.md` - the simulator contract:

```markdown
- `rank_policies(pack, task, target, policies)` - replay the last problem's memory-arm log as a simulator: for each policy of `policies.md`, walk its first 24 picks (from the cards and, step by step, the picks answered so far); a pick the log holds is answered with the logged `val_score`, a pick the log does not hold is `unknown` and answered with nothing. A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher (a lap that only revisits the log learns nothing). No fit is spent: `fits_spent: 0`, and the target's `state.json` is unchanged. Print the ranking (`policy, best_logged_val, visited, unknown`), `winner`, and `saturated` (true when every policy's unknown count is 0).
```

`.claude/skills/adult-income-meta-dream/SKILL.md` - the rule:

```markdown
## Rules
- Zero fits: `fit_recipe` is forbidden to this pack; `rank_policies` reports `fits_spent: 0` and the actor's budget counter proves it.
- You may patch the `Search policy:` line and nothing else.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new, and recursion pays only if it does.
```

`test_step.py`:

```python
    ranks = [r for t in TASKS if (RUNS / "adult-income-meta-dream" / t / "traces.jsonl").exists()
             for r in rows(RUNS / "adult-income-meta-dream" / t / "traces.jsonl") if r.get("event") in ("rank", "rank_policies")]
    assert ranks and all(r.get("fits_spent", 0) == 0 for r in ranks)
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, the
rankings in full):

```text
[Skill adult-income-curriculum]
agent> I'll follow the boot order: tools.md, P/eval.md, then the three SKILL.md files.
[Read ... the actor's tools.md, schema, memory schema, config, memory.json; the verifier's and meta's tools.md, policies.md, meta config]
agent> No helpers exist yet - the runs/ directory is empty. Let me look at the tasks, the README, the test file, and whether sibling lessons already have helper implementations I can adapt.
agent> Lesson 07 left a runtime I can adapt (the contracts are the same base). Let me read those helpers.
[Read ../step_07_proof/runs/adult-income/helpers/{rt.py, tools.py}, .../verify.py, .../curriculum.py]
agent> Now the policies in rt.py - replacing the search-policies section with all five plus a dispatcher.
[Write runs/adult-income/helpers/rt.py]  [Edit rt.py]
agent> Now tools.py: read_memory --order for all five policies, and run_arm following the actor's Search policy: line.
[Write runs/adult-income/helpers/tools.py]  [Write runs/adult-income-verifier/helpers/verify.py]  [Write runs/adult-income-meta-dream/helpers/meta.py]  [Write runs/adult-income-curriculum/helpers/curriculum.py]
agent> Quick sanity check of the five policies before spending any fits:
$ python -c "(walk each policy's first eight picks on an empty log)"
agent> One fix: with fewer than six fits, neighbours-of-top-3 should offer only the six static fits (so the live arm's batch stops there before the neighbours are computed).
[Edit runs/adult-income/helpers/rt.py]
agent> Helpers are built. Now problem 1 (01_adult_income): control arm, then memory arm (policy line is static).
$ python runs/adult-income/helpers/tools.py run_arm .claude/skills/adult-income ../tasks/01_adult_income --arm control --memory off | ...
$ grep -n "Search policy:" .claude/skills/adult-income/SKILL.md && python runs/adult-income/helpers/tools.py run_arm ... --arm memory | ...
26:   Search policy: static
agent> Both arms identical on problem 1 (no cards yet, static). Now the verifier: tally, then the cards.
$ ... read_traces ... --scope problem --tally ... ; ... write_card ... --as .claude/skills/adult-income-verifier --cards @runs/adult-income-verifier/cards_01.json
profile {'n_rows': 6000, 'n_features': 14, 'n_classes': 2, 'imbalance': 0.239, 'has_categorical': 1} rows 24 pairs 60
{"n": 9, "new": 9, "demoted": 5, ...}
$ M=.claude/skills/adult-income-meta-dream && python runs/adult-income-meta-dream/helpers/meta.py read_pack .claude/skills/adult-income | ... && python runs/adult-income-meta-dream/helpers/meta.py rank_policies $M ../tasks/01_adult_income --target adult-income --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family | ...
policy_line static mirrors_equal True versions []
{"problem": "adult_income", "target": "adult-income", "current_policy": "static", "log_size": 24, "fits_spent": 0,
 "ranking": [{"policy": "obey-memory", "best_logged_val": 0.9177, "visited": 10, "unknown": 14}, {"policy": "neighbours-of-top-3", "best_logged_val": 0.9177, "visited": 18, "unknown": 6}, {"policy": "static", "best_logged_val": 0.9177, "visited": 24, "unknown": 0}, {"policy": "prefer-untried-family", ...}, {"policy": "random", "best_logged_val": 0.917, "visited": 5, "unknown": 19}],
 "winner": "obey-memory", "saturated": false}
$ file .claude/skills/adult-income/SKILL.md && python -c "(check LF and the trailing newline, so the patch stays a one-line diff)"
[Write runs/adult-income-meta-dream/patch/SKILL.md (44 lines)]
$ diff .claude/skills/adult-income/SKILL.md runs/adult-income-meta-dream/patch/SKILL.md; python runs/adult-income-meta-dream/helpers/meta.py propose $M ../tasks/01_adult_income --target adult-income --files runs/adult-income-meta-dream/patch --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}' --summary "policy -> obey-memory: best logged val 0.9177, unknown 14" --visit 1
26c26
<    Search policy: static
---
>    Search policy: obey-memory
{"id": "p001", ...}
agent> Proposal p001 - a one-line diff. Now the gate (private split decides; nobody is asked):
$ python runs/adult-income-meta-dream/helpers/meta.py gate .claude/skills/adult-income-meta-dream ../tasks/01_adult_income p001 && grep -n "Search policy:" .claude/skills/adult-income/SKILL.md .agents/skills/adult-income/SKILL.md && ls runs/adult-income/versions
{"decision": "keep", "id": "p001", "summary": "policy -> obey-memory: best logged val 0.9177, unknown 14", "before": 0.8977, "after": 0.8977, ..., "landed": true, "version": "gen_001"}
gen_001
$ ... problem 2 (02_breast_cancer), both arms, under the line obey-memory ...
control policy static | fits [0.9937, 0.9909, ..., 0.9954 x8] | best_val 0.9954 test 0.9806 wasted 0
memory policy obey-memory applicable 1 preferred {'scale': 'yes'} | best_val 0.996 ...
$ ... verifier on problem 2 ... ; ... rank_policies ... 02_breast_cancer ...
agent> Winner random (ties at 0.9960 with obey-memory and neighbours-of-top-3; 18 unknown picks break the tie). Propose and gate:
{'id': 'p002', 'visit': 2, 'summary': 'policy -> random: best logged val 0.996, unknown 18', 'lines_changed': 2}
{'decision': 'keep', 'id': 'p002', 'before': 1.0, 'after': 1.0, 'landed': True, 'version': 'gen_002', 'policy_line_now': 'random'}
agent> Gate: keep (private 1.0 vs 1.0), gen_002; the actor's policy line is now random. Problem 3 (03_wine):
agent> Wine saturates: both arms 1.0 (gap 0, as eval.md warns). Verifier, then meta visit 3:
agent> All five tie at 1.0 on the wine log; static wins on unknowns (19, ahead of prefer-untried-family on list order). Propose policy -> static and gate:
agent> Gate: keep (1.0 vs 1.0), gen_003; policy line back to static. Problem 4 (04_digits):
agent> Digits under static: identical arms (gap 0; the policy line the gate chose ignores the cards). Verifier, then meta visit 4:
agent> Gate: keep (0.9989 vs 0.9989), gen_004; policy random. Problem 5 (05_synth_shift_a, the linear-model superstition test):
agent> Problem 5: both arms best 0.9378 (gap 0), but the memory arm's random walk reached it with 0 wasted fits vs 8 for the control. Verifier, then meta visit 5:
agent> Winner static (all but obey-memory tie at 0.9378; static has the most unknowns at 19, ahead on list order). Propose and gate:
agent> Gate: keep (0.9466 vs 0.9466), gen_005; policy static. Problem 6 (06_synth_shift_b, imbalanced, small):
agent> Problem 6 under static: identical arms again (gap 0). Verifier, then the last meta visit:
agent> Winner random (all tie at 0.7685; 19 unknowns). Propose and gate:
agent> Gate: keep (0.5321 vs 0.5321), gen_006; the pack enters the exam with Search policy: random. The learning curve:
$ python runs/adult-income-curriculum/helpers/curriculum.py curve .claude/skills/adult-income --tasks ../tasks | ...
(the table below)
$ ... the exam: sha256 of memory.json, then for s in 0..4 both arms ...
1688fc523b05b6d164cd155d79477397d6ebe91ca0d7347796c81161b84e72e1
26:   Search policy: random
seed 0 control policy static | best_val 0.9389 {'model': 'rf', 'hyper': 16, ...} test 0.7831 wasted 8
seed 0 memory policy random applicable 3 | best_val 0.9412 {'model': 'rf', 'hyper': None, 'scale': 'no', ...} test 0.7819 wasted 11
... (8 more arms)
agent> All ten exam arms frozen and scored once. The exam report, then read_pack --checksums:
$ python runs/adult-income-curriculum/helpers/curriculum.py exam .claude/skills/adult-income ../tasks/07_exam --seeds 0,1,2,3,4 | ... && ... read_pack ... --checksums ... && cat runs/adult-income-meta-dream/*/traces.jsonl | ... && diff -r .claude/skills .agents/skills && echo MIRRORS_EQUAL
(the table below)
rank_policies adult_income p001 fits_spent=0 ... gate keep gen_001 ... (six visits) ... MIRRORS_EQUAL
agent> Done. A quick run of the lesson's offline tests to confirm the pack contract still holds after six patches:
$ python -m pytest test_step.py -q 2>&1 | tail -3
(moved to the background after 180 s)
$ echo "RSI_LIVE=[$RSI_LIVE]"; ls runs/adult-income | head; grep -n "Search policy:" .claude/skills/adult-income/SKILL.md | head -1
RSI_LIVE=[1]
ls: cannot access 'runs/adult-income': No such file or directory
26:   Search policy: static
agent> RSI_LIVE=1 is set in this environment - the test's live path fired reset(), which wiped runs/ and restored the packs, and it is now launching a headless claude -p. Stopping it immediately:
[TaskStop]  (the nested run killed)
agent> The packs are back to the shipped state and runs/ is gone. Rebuilding the helpers exactly as before (copy from lesson 07, re-apply the same edits, re-write meta.py):
... (the whole curriculum again: six problems, six visits, the curve, the exam)
agent> Everything reproduces to the digit. Visit 6, then the curve:
agent> The run is complete: runs/adult-income/curve.json and exam.json exist, both mirrors are identical, and only SKILL.md (policy line) and memory.json (cards) changed in the actor pack - through gate and write_card respectively.
## Learning curve
| problem       | memory_best_val | control_best_val | gap_val | wasted_memory | wasted_control | cards_added | cards_demoted | cards_active |
| adult_income  | 0.9177 | 0.9177 | 0.0    | 16 | 16 | 9 | 5  | 4 |
| breast_cancer | 0.996  | 0.9954 | 0.0006 | 0  | 0  | 6 | 8  | 7 |
| wine          | 1.0    | 1.0    | 0.0    | 0  | 0  | 0 | 8  | 7 |
| digits        | 0.999  | 0.999  | 0.0    | 0  | 0  | 0 | 8  | 7 |
| synth_shift_a | 0.9378 | 0.9378 | 0.0    | 0  | 8  | 6 | 13 | 8 |
| synth_shift_b | 0.7685 | 0.7685 | 0.0    | 9  | 9  | 2 | 16 | 7 |
Every arm: 24 fits, frozen, test scored once, test_touched_before_freeze false. Problems 4 and 6 ran with the policy line the gate had just set to static, so the memory arm was the control arm by construction there.
## Meta visits: ranking (policy, best logged val, visited, unknown), winner, gate
| 1 adult_income (line: static)     | obey-memory 0.9177/10/14 - neighbours-of-top-3 0.9177/18/6 - static 0.9177/24/0 - prefer-untried-family 0.9177/24/0 - random 0.917/5/19 | obey-memory | p001 -> keep (0.8977 / 0.8977) | gen_001 |
| 2 breast_cancer (line: obey-memory) | random 0.996/6/18 - neighbours-of-top-3 0.996/14/10 - obey-memory 0.996/23/1 - static 0.9954/10/14 - prefer-untried-family 0.9954/10/14 | random | p002 -> keep (1.0 / 1.0) | gen_002 |
| 3 wine (line: random)             | static 1.0/5/19 - prefer-untried-family 1.0/5/19 - neighbours-of-top-3 1.0/7/17 - obey-memory 1.0/8/16 - random 1.0/24/0 | static | p003 -> keep (1.0 / 1.0) | gen_003 |
| 4 digits (line: static)           | random 0.999/5/19 - obey-memory 0.999/10/14 - neighbours-of-top-3 0.999/16/8 - static 0.999/24/0 - prefer-untried-family 0.999/24/0 | random | p004 -> keep (0.9989 / 0.9989) | gen_004 |
| 5 synth_shift_a (line: random)    | static 0.9378/5/19 - prefer-untried-family 0.9378/5/19 - neighbours-of-top-3 0.9378/6/18 - random 0.9378/24/0 - obey-memory 0.8555/8/16 | static | p005 -> keep (0.9466 / 0.9466) | gen_005 |
| 6 synth_shift_b (line: static)    | random 0.7685/5/19 - obey-memory 0.7685/10/14 - neighbours-of-top-3 0.7685/17/7 - static 0.7685/24/0 - prefer-untried-family 0.7685/24/0 | random | p006 -> keep (0.5321 / 0.5321) | gen_006 |
Every rank_policies event records fits_spent: 0 and the actor's state.json unchanged. No log was saturated (unknown counts of 19 dominate), but note what the tie-break does: in every visit the policies tie on best logged val, so the policy that revisits the log least wins - the line oscillated static -> obey-memory -> random -> static -> random -> static -> random. The gate kept all six: the evidence recipe was the problem's own best-val recipe and scored identically to the incumbent on the private split every time. The pack enters the exam with Search policy: random.
## Exam
| seed | memory_test | control_test | memory_wasted | control_wasted | winner  | not_transferred |
| 0 | 0.7819 | 0.7831 | 11 | 8  | control | 3 |
| 1 | 0.7170 | 0.7244 | 13 | 17 | control | 2 |
| 2 | 0.8040 | 0.8288 | 0  | 8  | control | 2 |
| 3 | 0.8335 | 0.8335 | 1  | 8  | memory  | 2 |
| 4 | 0.8333 | 0.8178 | 11 | 16 | memory  | 2 |
- wins: 2 of 5, mean test gap -0.0036
- pack_unchanged: true (sha256 1688fc52... before and after, both mirrors); no_card_written: true (no verifier ran; 3 cards applied on every seed)
- Cards that applied but did not transfer: scale -> yes (n_features >= 10, evidence 2) on seeds 0 and 3; hyper -> 0.1 and hyper -> 16 (n_classes < 3, evidence 1 each - tied, so no preference) on every seed.
## Claims of eval.md
- Gap never negative - held (0, 0.0006, 0, 0, 0, 0).
- Gap larger on problem 6 than on problem 2 - did not hold: 0.0 vs 0.0006.
- Test split scored once per arm, after FREEZE - held on all 22 arms.
- Exam: memory beats control on >= 3 of 5 seeds - did not hold: 2 of 5 (the random policy the gate landed ignores the cards; on the two wins it was fewer wasted fits at a tie, and a higher test score on seed 4).
- Exam: memory.json byte-identical, every non-transferred card named - held.
read_pack --checksums: six versions gen_001-gen_006, one per proposal, all kept.
One thing to flag: midway I ran the lesson's test_step.py as a sanity check; RSI_LIVE=1 is set in this environment, so its live path deleted runs/ and reset the packs. I stopped it before it launched a nested run, rebuilt the helpers, and re-ran the whole curriculum and exam - every number reproduced exactly (the fits are seeded). The artifacts above are from the second, complete pass.
[96 turns, 2191 s]
```

What to notice: this is the lesson where the method did not pay, and the
transcript says so in the agent's own words. On every visit the five
policies tied on best logged val - the log holds one best recipe and every
policy finds it - so the contract's tie-break (more unknown picks ranks
higher) chose whichever policy revisits the log *least*, and the line
oscillated between `random` and `static`. The gate kept every patch because
the evidence recipe was the incumbent. The exam then ran under `random`,
which ignores the cards: 2 of 5, mean test gap -0.0036, and the claim did
not hold. Dream-RSI's honest result on a log this small is that the
simulator is exact where you visited and silent elsewhere, and the
tie-break rewards the silence. Also on the page: the agent ran the lesson's
own test mid-run with `RSI_LIVE=1` inherited from the recording
environment, which reset the packs; it stopped the nested run, redid the
curriculum, and every number reproduced - the tests now strip that
variable from the recorded agent's environment.

Files:

```text
step_10_rsi_dream/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income/                 lesson 09's actor; the five policies named on the policy line's menu
│   ├── adult-income-verifier/
│   ├── adult-income-meta-dream/      SKILL.md, tools.md (rank_policies, propose, gate ...), policies.md, config.md
│   └── adult-income-curriculum/      actor -> verifier -> replay visit, per problem
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income/{..., versions/}, adult-income-meta-dream/{helpers/, patch/, <task>/}
```

## Governance considerations

- **Who approves what.** Nobody per visit: the private gate. The human
  wrote the policy library (`policies.md`) and the replay rule; the system
  chooses among the five.
- **The hook.** `score_test` after `"frozen": true`. The meta pack never
  calls `apply`; the gate lands.
- **What the helper refuses.** `rank_policies` spends nothing (the budget
  counter is the proof); `propose` refuses any file but `SKILL.md`;
  `fit_recipe` is forbidden to the meta pack.
- **What is and is not self-modified.** The actor's policy line (versioned).
  The policy library, the replay rule and the gate do not change.
- **Honesty.** Saturation is reported, not hidden; wine and digits saturate
  fast in this recipe space.

## How to measure it

| Claim | Test |
|---|---|
| `policies.md` names five policies and the actor's `SKILL.md` knows them | `test_policies_md_names_five_and_the_actor_knows_them` |
| `rank_policies` spends nothing, counts unknowns, names saturation, ranks more unknowns higher at a tie | `test_rank_policies_spends_nothing_and_counts_unknowns` |
| only the policy line is patched, behind the gate | `test_only_the_policy_line_is_patched_behind_the_gate` |
| the pack contract for four packs and the seven intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: arms frozen and scored once, `rank` events with `fits_spent` 0, curve, exam unchanged (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 11 - RSIAgent](../step_11_rsi_agent/README.md): the next
experiment chosen by uncertainty; the memory frozen at test. Previous:
[lesson 09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md).
