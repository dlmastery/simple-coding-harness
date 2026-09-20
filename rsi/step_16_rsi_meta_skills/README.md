# Lesson 16 - MetaSkill-Evolve: the improver's skills improve too, slowly

MetaSkill-Evolve (arXiv:2607.05297) runs two timescales on one frozen
model: task skills evolve every problem, meta-skills - the improver's own
procedures - evolve every k problems by the same pipeline, with no extra
model and no extra objective. Here the fast loop is `task-skills-meta`, a
lesson-09 meta pack whose numbers (`Policy flip threshold`, `Cards per
visit`) and order of business live in five role files under `roles/`
(analyzer, retriever, allocator, proposer, evolver), patching the actor's
task skills behind the private gate after every problem. The slow loop is
`meta-evolver`: after problems `k`, `2k`, ... (`k: 3` in its `config.md`)
it reads the same evidence the fast loop reads, judges the fast loop by it,
and proposes one change to one line of one role file - which lands only
with the human's `approve` and is snapshotted under the meta pack's own
`versions/`. This is the "and so on": the pack that patches the pack is
itself a pack with a version history, and its changes are rarer and gated
harder. The paper's L5, with the clock and the human yes on every meta
change staying human.

## Getting started

Prerequisites: lesson 09 (the gate variant is this lesson's fast loop with
its numbers moved into `roles/`). This lesson adds `roles/*.md` to
`task-skills-meta` and the `meta-evolver` pack (`config.md` with `k: 3`,
`approval: human`, `patches: ["roles/*.md"]`).

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill with the task-skills-meta fast loop and the meta-evolver slow loop: run the curriculum (problems 1 to 6: control arm, memory arm, verifier, the fast loop under the gate; after problems 3 and 6 the slow loop - show me its diff and ask), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report, and list every fast and slow decision with its version.
   ```

2. After problem 3 and after problem 6 the agent shows a one-line diff of a
   role file (or says there is nothing to change) and asks. Answer
   `approve` (as recorded), `edit: ...` or `reject`.

3. Headless, as recorded (the test continues with `approve` at every
   question):

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "approve" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: five roles carrying the
   numbers the fast loop uses; two timescales, two gates (`gate` with
   `patches:` on the actor's task skills; `human` with `patches:` on
   `roles/*.md`); `k: 3`; the meta pack has a version history.
   `RSI_LIVE=1`: every arm scored once; the slow loop's events only on
   `wine` and `synth_shift_b`; every landed role change carries the word
   `approve`; as many `versions/` under `task-skills-meta` as landed changes,
   at most two; curve and exam.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/task-skills-meta/roles/allocator.md` and `proposer.md` - the
numbers the fast loop reads:

```markdown
# Role: allocator
Which task skill gets this visit, in order: the policy line, then a forbid, then cards.
Policy flip threshold: 2
```

```markdown
# Role: proposer
One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
Cards per visit: 3
```

`.claude/skills/meta-evolver/SKILL.md` - the slow clock and the one change:

```markdown
1. Check the clock: the problem's index must be a multiple of `k`; otherwise say so and stop.
3. Judge the fast loop by that evidence: the number of active cards the last `k` problems added, and whether the memory arm's best val beat the control's on them. Decide ONE change, one file, one line:
   - the fast loop is adding cards but the gap is not growing: raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster);
   - the actor's policy line is still `static` after `k` problems: lower `Policy flip threshold` in `roles/allocator.md` by one;
   - otherwise nothing: say so and stop.
4. Write the changed role file under `runs/meta-evolver/patch/roles/<file>` (your Write tool) and `propose E T --target task-skills-meta --files runs/meta-evolver/patch --recipe <the last problem's best val recipe> --summary "<role>: <old> -> <new>" --visit <index / k>`. `patches: ["roles/*.md"]`: `propose` refuses any other file. `approval: human`: show the user the diff, ask **approve / edit / reject**, wait, then write their words to `runs/meta-evolver/<task>/proposals/<id>.approved` and `apply E T <id> --approved "<the user's exact words>"`. Nothing lands on a no. Every apply snapshots `M` under `runs/task-skills-meta/versions/gen_NNN/`: the meta pack's version history is a directory you can diff.
```

`.claude/skills/meta-evolver/config.md`:

```markdown
---
meta: "on"
k: 3
---
```

`test_step.py`:

```python
    assert all(r.get("problem", "") in ("", "wine", "synth_shift_b") for r in slow)
    applied = [r for r in slow if r["event"] == "apply"]
    assert all(r["approved"] == "approve" for r in applied)
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, the
fast-loop verdicts in one line each, the slow-loop visits in full):

```text
[Skill adult-income-curriculum]
[Read the five packs' SKILL.md / tools.md, eval.md, roles/*.md, the two config.md, schema, memory schema, memory.json]
[Write runs/adult-income/helpers/{rt.py, tools.py, show.py}]  [Write runs/adult-income-verifier/helpers/verify.py]  [Write runs/task-skills-meta/helpers/meta.py]  [Write runs/meta-evolver/helpers/evolve.py]  [Write runs/adult-income-curriculum/helpers/curriculum.py]
$ ... problem 1: run_arm control; run_arm memory (policy line static) ...
agent> Both arms of problem 1 identical (0.9177 val, 0.9049 test) as expected with no cards. Now the verifier on problem 1.
$ ... read_traces --tally; write_card ... --as .claude/skills/adult-income-verifier ...
{"n": 9, "new": 9, "demoted": 5, "active": 4}
agent> Rule (a) applies: policy is static and 4 cards are active (>= threshold 2). The patch is the whole SKILL.md with the one line flipped to obey-memory.
$ ... meta.py propose ... --visit 1; ... meta.py gate ... p001
{"decision": "keep", "before": 0.8977, "after": 0.8977, "landed": true, "version": "gen_001"}
$ ... problem 2 (breast_cancer): control 0.9954, memory 0.996 (obey-memory, one card applicable); verifier; fast loop visit 2 ...
agent> Rule (b) applies on visit 2: encode=ordinal lost all 12 of its one-field comparisons across the log and never won. The patch adds it to schema.json -> forbid.
{"decision": "keep", "before": 1.0, "after": 1.0, "landed": true, "version": "gen_002"}
agent> Wine saturates (1.0 on both arms, gap 0 - the honest number). Verifier on problem 3:
$ ... fast loop visit 3: nothing to propose ...
$ python $H clock $E $T ...; python $H judge $E $T ...
{'problem': 'wine', 'index': 3, 'k': 3, 'on_clock': True, 'visit': 1, 'meta': 'on'}
agent> Now the slow-loop proposal: Cards per visit: 3 -> 4 in roles/proposer.md.
$ ... python - <<'EOF' (rewrite the one line of roles/proposer.md under runs/meta-evolver/patch/roles/) ... ; python $H propose $E $T --target task-skills-meta --files runs/meta-evolver/patch --recipe ... --summary "proposer: Cards per visit 3 -> 4" --visit 1
patch written
{"id": "p001", "visit": 1, "target": "task-skills-meta", "files": ["roles/proposer.md"], "changed_lines": 1, "lint": "ok", ...}
agent> Progress so far (problems 1-3 done):
| 1 adult_income  | 0.9177 | 0.9177 | 0.0     | p001: Search policy: static -> obey-memory (4 cards active >= threshold 2) - gate keep (0.8977 vs 0.8977) | gen_001 |
| 2 breast_cancer | 0.9954 | 0.9960 | +0.0006 | p002: schema.json forbid encode=ordinal (lost 12/12 comparisons across the log) - gate keep (1.0 vs 1.0) | gen_002 |
| 3 wine          | 1.0    | 1.0    | 0.0 (saturated) | nothing to propose | - |
Slow loop after problem 3 (meta-evolver, visit 1, on the clock: 3 = 1*k). Its judgement of the fast loop over problems 1-3: 8 active cards were added, but the gap is not growing (0.0 -> 0.0006 -> 0.0), so by its rule it raises Cards per visit by one. Proposal p001 (target task-skills-meta, one line of one role file):
--- a/task-skills-meta/roles/proposer.md
+++ b/task-skills-meta/roles/proposer.md
 # Role: proposer
 One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
-Cards per visit: 3
+Cards per visit: 4
approve / edit / reject? Nothing lands until you answer; on approve it is snapshotted under runs/task-skills-meta/versions/gen_001/ and applied to both mirrors, then I continue with problems 4-6.
[41 turns, 728 s]

--- turn 2: claude -p --continue "approve"
[Write runs/meta-evolver/wine/proposals/p001.approved]
$ python $H apply $E $T p001 --approved "approve"
{"id": "p001", "approved": "approve", "version": "gen_001", "files": ["roles/proposer.md"], "landed": true}
agent> Landed: Cards per visit: 4, meta pack snapshotted as runs/task-skills-meta/versions/gen_001. Continuing with problem 4 (digits).
$ ... problems 4, 5, 6: both arms, verifier, fast loop visits 4-6 (nothing to propose) ...
agent> Fast loop visit 6: nothing to propose. Now the slow loop after problem 6 (visit 2, on the clock: 6 = 2*k).
$ python $H clock $E $T | ...; python $H read_memory $P $T | ...; python $H read_pack $M | ...; python $H judge $E $T | ...
{'problem': 'synth_shift_b', 'index': 6, 'k': 3, 'on_clock': True, 'visit': 2, 'meta': 'on'}
cards 25 active 9
roles {'policy_flip_threshold': 2, 'cards_per_visit': 4} versions ['gen_001']
$ ... propose p002 (roles/proposer.md: Cards per visit 4 -> 5) --visit 2
agent> Problems 4-6 done. Learning curve so far (the full table follows after the exam):
| 4 digits        | 0.999  | 0.999  | 0.0 | 0 / 0 | nothing to propose |
| 5 synth_shift_a | 0.9378 | 0.9378 | 0.0 | 1 / 4 | nothing to propose |
| 6 synth_shift_b | 0.7685 | 0.7685 | 0.0 | 4 / 5 | nothing to propose |
The fast loop found nothing on visits 3-6: the verifier had already written every card the pairs yield (rule c), no field value lost every comparison across the log (rule b), and the policy line had already flipped (rule a).
Slow loop after problem 6 (meta-evolver, visit 2, on the clock: 6 = 2*k). Its judgement of the fast loop over problems 4-6: cards are still being added (9 written, active count 8 -> 9) but the gap is not growing (0.0 -> 0.0 -> 0.0; the memory arm beat control on none of the three, though it wasted fewer fits on 5 and 6). By its rule it raises Cards per visit again. Proposal p002:
-Cards per visit: 4
+Cards per visit: 5
One honest caveat: raising this number has had no observable effect, because rule c never fired (the verifier writes all cards before the fast loop visits). Rejecting is a reasonable answer too.
approve / edit / reject? On approve it is snapshotted as runs/task-skills-meta/versions/gen_002 and applied; then I run the curve, the exam over seeds 0-4, and the report.
[11 turns, 240 s]

--- turn 3: claude -p --continue "approve"
$ python $H apply $E $T p002 --approved "approve"
{"id": "p002", "approved": "approve", "version": "gen_002", "files": ["roles/proposer.md"], "landed": true}
agent> Landed as gen_002. Now the learning curve, then the exam (sha256 of memory.json recorded first).
$ python runs/adult-income-curriculum/helpers/curriculum.py curve $P --tasks ../tasks | ...; sha256sum $P/memory.json | cut -d' ' -f1 | tee runs/adult-income/exam/memory_sha_before.txt
(the table below)
c5ddb70d57d97e56fd1ced5c32e03b1520972fb461a2607fd55e5c838a8261d4
$ for s in 0 1 2 3 4; do ... run_arm $P ../tasks/07_exam --arm control --memory off --seed $s | show.py; ... run_arm ... --arm memory --seed $s | show.py; done
exam control s0 memory=off policy=static applicable=0
   static [(1, 0.827, None), (2, 0.8355, None), ..., (24, 0.9062, None)]
  best_val=0.9389 best={"model": "rf", "hyper": 16, ...} test=0.7831 fits=24 wasted=4 touched_before_freeze=False
exam memory s0 memory=on policy=obey-memory applicable=4 preferred={'hyper': 16, 'scale': 'yes', 'class_weight': 'none'}
   obey-memory [(1, 0.827, None), (2, 0.9389, None), (3, 0.9146, None)]
   obey-memory [(4, 0.9389, None), ..., (8, 0.9412, None), ...]
... (8 more arms)
$ python runs/adult-income-curriculum/helpers/curriculum.py exam $P ../tasks/07_exam --seeds 0,1,2,3,4 | ...; ... read_pack $P --checksums ...
(the table below)
agent> Done. curve.json and exam.json are under runs/adult-income/, both mirrors identical, every arm scored once after FREEZE.
## Learning curve
| adult_income  | 0.9177 | 0.9177 | 0.0     | 16 | 16 | 9 | 5  | 4  |
| breast_cancer | 0.996  | 0.9954 | +0.0006 | 0  | 0  | 6 | 8  | 7  |
| wine          | 1.0    | 1.0    | 0.0     | 0  | 0  | 1 | 8  | 8  |
| digits        | 0.999  | 0.999  | 0.0     | 0  | 0  | 3 | 10 | 9  |
| synth_shift_a | 0.9378 | 0.9378 | 0.0     | 1  | 4  | 5 | 14 | 10 |
| synth_shift_b | 0.7685 | 0.7685 | 0.0     | 4  | 5  | 1 | 16 | 9  |
## Exam
| 0 | 0.7819 | 0.7831 | 1 | 4 | control | 4 | 2 |
| 1 | 0.7170 | 0.7244 | 7 | 9 | control | 4 | 2 |
| 2 | 0.8288 | 0.8288 | 1 | 4 | memory  | 4 | 1 |
| 3 | 0.8335 | 0.8335 | 1 | 4 | memory  | 4 | 1 |
| 4 | 0.8333 | 0.8178 | 7 | 8 | memory  | 4 | 2 |
wins 3 of 5, mean test gap +0.0014, pack_unchanged true (sha256 c5ddb70d...8261d4 before and after), no_card_written true.
Cards that applied but did not transfer: the two n_classes < 3 -> hyper cards - prefer 0.1 (evidence 1) on every seed, prefer 16 (evidence 2) on seeds 0, 1, 4. Hyper cards are per-model values conditioned on a table-level key, so they carry poorly across the model that won.
## Meta decisions and versions
Fast loop (task-skills-meta, private gate, runs/adult-income/versions/): p001 policy flip (rule a) -> gate keep, gen_001; p002 forbid encode=ordinal (rule b) -> gate keep, gen_002; visits 3-6 nothing applied.
Slow loop (meta-evolver, human, k=3, runs/task-skills-meta/versions/): after problem 3, p001 roles/proposer.md Cards per visit: 3 -> 4 - you: approve - gen_001; after problem 6, p002 Cards per visit: 4 -> 5 - you: approve - gen_002.
Final actor pack: policy obey-memory, forbid [encode=ordinal], 25 cards (9 active). Final meta pack: Policy flip threshold: 2, Cards per visit: 5.
## Claims of eval.md
- Gap never negative: held - 0.0, +0.0006, 0.0, 0.0, 0.0, 0.0.
- Gap larger on problem 6 than on problem 2: did not hold - gap_6 = 0.0 < gap_2 = 0.0006. Wine and digits saturate, and on the two synthetic tables both arms reached the same best recipe (rf, depth 16); memory's edge there was in wasted fits (1 vs 4, 4 vs 5), which gap_val does not measure.
- Test split locked: held - test_touched_before_freeze false and test_scored_once true on all 22 arms.
- Exam: memory wins >= 3 of 5 - held, exactly 3 of 5. memory.json byte-identical - held. Every non-transferred card named - held.
[6 turns, 188 s]
```

What to notice: two clocks, two gates, both visible. The fast loop patched
the actor twice behind the private gate (the same two patches as lesson
09) and then had nothing to propose four times; the slow loop asked the
human exactly twice, after problems 3 and 6 (`on_clock: True, visit: 1` /
`visit: 2`), each time a one-line diff of one role file, and each landing
put a snapshot under the *meta pack's own* `versions/` - the improver has a
history you can diff. The agent added a caveat the skill did not ask for
and the page keeps: raising `Cards per visit` had no observable effect,
because the verifier writes every card before the fast loop visits, so
rule (c) never fired; "rejecting is a reasonable answer too". The exam held
at 3 of 5, as in lessons 07 and 09.

Files:

```text
step_16_rsi_meta_skills/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income/                 lesson 09's actor
│   ├── adult-income-verifier/
│   ├── task-skills-meta/             the fast loop: SKILL.md, tools.md, config.md, roles/{analyzer,retriever,allocator,proposer,evolver}.md
│   ├── meta-evolver/                 the slow loop: SKILL.md, tools.md, config.md (k: 3)
│   └── adult-income-curriculum/
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income/{..., versions/}, task-skills-meta/{helpers/, versions/ (the meta pack's own history)}, meta-evolver/
```

## Governance considerations

- **Who approves what.** Task-skill patches: the private gate, every
  problem. Meta-skill changes: the human, every k problems, one line of one
  role file, with the diff shown. The clock, the judging rule and the
  human yes are fixed.
- **The hook.** `apply` only with `.approved`; the fast loop's `gate` never
  touches `roles/`.
- **What the helper refuses.** The slow loop off the clock; a proposal
  outside `roles/*.md`; the fast loop touching `roles/`, `eval.md` or the
  verifier.
- **What is and is not self-modified.** The actor's task skills (fast,
  gated) and the meta pack's role files (slow, human) - both versioned. The
  slow loop itself, the verifier and the curriculum do not change.
- **Rung.** L5 by the paper's definition (the improver's procedure is
  revised), with a human acceptance rule on every such revision - the page
  claims no more than that.

## How to measure it

| Claim | Test |
|---|---|
| five role files carry the numbers the fast loop reads (`Policy flip threshold: 2`, `Cards per visit: 3`) | `test_five_roles_carry_the_numbers_the_fast_loop_uses` |
| two timescales, two gates; `k: 3`; the slow loop only on the clock and never on the actor; the fast loop never on `roles/` | `test_two_timescales_two_gates` |
| the meta pack's changes are snapshotted under its own `versions/` | `test_meta_pack_has_a_version_history` |
| the pack contract for five packs and the seven intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: slow-loop events only on problems 3 and 6, landed only on `approve`, one version per landing, at most two; curve and exam (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 17 - the map](../step_17_map/README.md): the ladder, every recorded
curve side by side, and who approved what. Previous:
[lesson 15 - AIDE²](../step_15_rsi_aide2/README.md).
