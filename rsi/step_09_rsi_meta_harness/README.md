# Lesson 09 - The RSI meta harness: a pack that patches the pack, problem by problem

Lesson 06's verifier changes one file, `memory.json`, under a contract.
This lesson adds a pack that may change the actor pack itself - its
`Search policy:` line, its `schema.json` `forbid` list, its cards - one
proposal per visit, between two curriculum problems. `patch_pack.py`
snapshots the actor under `runs/adult-income/versions/gen_NNN/` before
anything lands, refuses a second proposal per visit, a patch outside the
meta pack's `patches:` globs, one that changes more than 20 % of the pack's
text or removes the test rule; then who decides is one line of the meta
pack's front matter. `approval: human` (`adult-income-meta`): the agent shows
the diff, asks, and lands only with the user's exact words. `approval:
gate` (`adult-income-meta-gate`): the evidence recipe is scored against the
incumbent on the private split - rows no actor arm ever sees - and a loss
rolls the pack back; the human reads the log and may `rollback.py`. The
actor ships with `Search policy: static` so that the first patch is
visible: generation 2 boots what generation 1 wrote (its boot row carries
the patched checksums), and that reboot is the recursion. L4 under the
human; L5 flavour under the gate. The gate itself, the archive rule and the
off switch (`{"meta": "off"}`) stay human, and this page says so.

## Getting started

Lesson 08 left the writer; this lesson's packs are lesson 07's actor (policy
line `static`, `schema.json` with `forbid: []`), the verifier, the
curriculum skill extended with a meta visit, and the two meta packs. Four
scripts: `../tools/read_pack.py`, `patch_pack.py`, `private_score.py`,
`rollback.py`. A full curriculum with the gate takes about 28 minutes
headless; the human variant on one problem about seven. Reset after a run:
set the actor's policy line back to `static`, `echo "[]" >
.claude/skills/adult-income/memory.json`, mirror, `rm -rf runs`.

## How to execute it

1. The gate, over the whole curriculum:

   ```text
   Use the adult-income-curriculum skill with the meta pack adult-income-meta-gate: run the six curriculum problems with a gate visit after each, then the exam, and report the curve, the exam and the meta decisions.
   ```

   The meta visit's commands, after each problem's two arms and the verifier:

   ```bash
   python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope all
   python ../tools/read_memory.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
   python ../tools/read_pack.py --pack .claude/skills/adult-income
   python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-gate --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --visit 1 --files @runs/adult-income-meta-gate/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "Search policy static -> obey-memory: 4 cards active after problem 01 (rule a)"
   ```

2. The human, on one problem (two turns):

   ```text
   On ../tasks/01_adult_income.json: use the adult-income skill for the control arm and the memory arm, then the adult-income-verifier skill, then the adult-income-meta skill (approval: human) for meta visit 1 and propose its patch to me.
   ```

   **You will be asked**: the diff of the one-line change, approve / edit /
   reject. The agent then runs
   `python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --proposal g1 --approved "<your words>"`.
   Without your words the hook blocks the call and the script refuses it;
   "no" records a rejection and lands nothing; "edit" lands your version.

3. By hand: `python ../tools/rollback.py --pack .claude/skills/adult-income --list`
   then `--version gen_001` restores the snapshot; `{"meta": "off"}` in a meta
   pack's `config.json` makes `patch_pack.py` propose nothing (META_OFF).

4. Headless: as above with `claude -p` (and `--continue "<your answer>"`
   for the human variant), `--allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-meta/SKILL.md` - one change, the first that
applies; who decides is the front matter:

```markdown
---
name: adult-income-meta
description: Improve the actor pack adult-income between two curriculum problems - one patch per visit to its search-policy line, its schema.json forbid list or its memory cards - and put it through the human approval cycle. Use in rsi/step_09_rsi_meta_harness after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: human
  patches: ["SKILL.md", "schema.json", "memory.json"]
---
# The RSI meta harness: a pack that patches the pack

## Procedure
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change that line to `Search policy: obey-memory` (the whole `SKILL.md`, with that one line changed).
   b. A field value lost every comparison one field apart it was in, at least three times across the whole log, and never won: add `{"field": ..., "value": ...}` to `schema.json` -> `forbid` (`hyper` values are excluded: they belong to one model each).
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet (`read_traces.py --scope problem --tally` lists `cards_by_rule`); merge at most three of them into `memory.json`.
   If none applies, say so and stop: nothing is proposed this visit.
```

`../tools/patch_pack.py` - the rules every patch meets before anyone
decides, and the private gate:

```python
    if changed > SIZE_CAP * total:
        raise ValueError(f"the patch changes {changed} of {total} characters, more than {int(SIZE_CAP * 100)} % of the pack; one small change per generation")
    if "SKILL.md" in changes and changes["SKILL.md"]["after"] and "after FREEZE" not in changes["SKILL.md"]["after"]:
        raise ValueError("a patch may not remove the test rule from SKILL.md")
```

```python
def private_gate(run, target_run, candidate):
    """Keep-or-rollback on the private split: the candidate must not score below the incumbent."""
    before = tasks.score_on(run.task, run.seed, incumbent_recipe(target_run), "private")
    after = tasks.score_on(run.task, run.seed, candidate, "private")
    keep = after is not None and (before is None or after >= before)
```

```python
        if not verdict["keep"]:
            packs.rollback(target, versions, label)
            record.update(decision="n", approved_by="gate", applied=False)
```

`../tools/_lib/proposals.py` - the snapshot every patch takes first:

```python
def land_patch(target, versions_dir, patch):
    """Snapshot the target under versions/gen_NNN, then write the patched files. Returns the snapshot label."""
    versions_dir = Path(versions_dir)
    label = f"gen_{len(list(versions_dir.glob('gen_*'))) + 1:03d}" if versions_dir.exists() else "gen_001"
    packs.snapshot(target, versions_dir, label)
```

The recorded run under the gate (Claude Code 2.1.278, headless, 76 turns,
1650 s; the arms' fit calls trimmed to the agent's notes):

```text
[Skill adult-income-curriculum]
agent> The pack's policy line is static and there are no cards, so the memory arm walks the static list.
agent> Verifier: 9 cards written, 9 new, 0 demoted (4 active prefer cards, 5 counter-only). Now meta visit 1 -
read everything the meta pack may see.
$ python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope all
$ python ../tools/read_memory.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
$ python ../tools/read_pack.py --pack .claude/skills/adult-income
agent> Rule (a) applies: the policy line is static and 4 cards are active. I write the whole SKILL.md with
that one line changed to the patch scratch dir.
[Write runs/adult-income-meta-gate/patch/SKILL.md]
$ diff .claude/skills/adult-income/SKILL.md runs/adult-income-meta-gate/patch/SKILL.md; python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-gate --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --visit 1 --files @runs/adult-income-meta-gate/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "Search policy static -> obey-memory: 4 cards active after problem 01 (rule a)"
26c26
<    Search policy: static
---
>    Search policy: obey-memory
{"id": "g1", "decision": "y", "approved_by": "gate", "gate": {"before": 0.8951, "after": 0.8951, "keep": true}, "landed": true, "version": "gen_001", "files": ["SKILL.md"], ...}
agent> Meta visit 1: proposal g1, gate before 0.8951 / after 0.8951, keep -> landed as gen_001. The actor's
policy is now obey-memory.
agent> Problem 02 control: best val 0.9954, test 0.9844, wasted 0. Re-reading the actor's policy line before
the memory arm, then opening it.
...
agent> Meta visit 4: (a) no; (b) no non-hyper value has zero wins; (c) all six problem-04 cards_by_rule are
already held in memory (2 added, 4 merged). Nothing proposed.
agent> Meta visit 5: ... Nothing proposed.   agent> ... Meta visit 6.
agent> Curve written; never_negative: true, gap on problem 6 (+0.0646) > problem 2 (+0.0012). Now the exam
over five seeds ...
agent> Done. curve.json and exam.json exist under runs/adult-income/, and both tables were produced. No pack
file was edited by hand; cards went through write_card.py, the one patch through patch_pack.py.
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/11
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/11
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/11
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       2/1/11
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/11
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      1/0/11
exam: memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score won by fewer wasted fits), mean test gap 0.0308; pack unchanged: True; no card written: True
Meta decisions (adult-income-meta-gate, approval: gate):
| 1 | adult_income | g1: rule (a) - Search policy: static -> obey-memory (4 cards active) | gate 0.8951 / 0.8951, keep -> landed | gen_001 |
| 2 | breast_cancer | none - (a) already obey-memory; (b) only hyper 0.05 never won, and hyper is excluded; (c) all 6 cards_by_rule already in memory | nothing proposed |
| 3-6 | ... | none - every card already held (wine: every pair tied) | nothing proposed |
read_pack.py --checksums: versions = ['gen_001'] - one generation, one landed patch.
[76 turns, 1650 s]
```

The recorded human visit (two turns; the arms trimmed):

```text
[Skill adult-income] ... [Skill adult-income-verifier] ... [Skill adult-income-meta]
agent> Everything ran; here is where things stand and the patch waiting on you.
Problem 01 (adult_income, seed 0) - both arms: control 0.9172 / test 0.9034 / 24 fits / 16 wasted; memory
the same. Identical, as expected: memory.json was empty, so the memory arm ran the same static walk (gap_val
= 0; the delete-the-file check holds). Test scored once per arm, after FREEZE.
Verifier: tally checked by hand against the script's (model hgb 16-0, encode onehot 10-2, class_weight none
8-4, scale yes 6-1, no errors). Wrote 9 cards, 9 new, 0 demoted. Four are active prefer cards for this
profile: model=hgb, scale=yes, encode=onehot, class_weight=none.
$ python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --files @runs/adult-income-meta/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "Search policy static -> obey-memory: 4 cards active after problem 01 (model=hgb, scale=yes, encode=onehot, class_weight=none), rule (a)"
{"id": "g1", "decision": null, "landed": false, "diff": "--- a/SKILL.md
+++ b/SKILL.md
@@ -25,3 +25,3 @@ ...
-   Search policy: static
+   Search policy: obey-memory ...", "next": "Show the diff to the user. Ask: approve / edit / reject. Then: python ../tools/patch_pack.py ... --proposal g1 --approved \"<the user's exact words>\""}
agent> Meta visit 1 - proposal g1 (snapshot taken, nothing landed). Rule (a) applied first: the actor's
search policy is static and 4 cards are active. One change to .claude/skills/adult-income/SKILL.md:
-   Search policy: static
+   Search policy: obey-memory
One thing worth knowing before you decide: the cards say class_weight=none (8-4 across all pairs), but the
single best recipe used balanced - it won only within hgb+onehot. Under obey-memory the actor will probe
hgb/yes/onehot/none first and reach the hgb family by fit ~3 instead of fit 17, so the expected gain is in
wasted fits, not in best val.
approve / edit / reject? I'll run nothing until you answer, then pass your exact words to patch_pack.py --proposal g1.
[24 turns, 218 s]
=== user> approve
$ python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --proposal g1 --approved "approve"
{"id": "g1", "decision": "y", "landed": true, "version": "gen_001", "files": ["SKILL.md"], "approved_by": "human", "words": "approve"}
agent> Landed. Proposal g1 - approved (your words: "approve"), approved_by human. Version gen_001 - the
pre-patch actor pack is snapshotted under runs/adult-income/versions/gen_001/; rollback can restore it.
Files changed: .claude/skills/adult-income/SKILL.md - Search policy: static -> Search policy: obey-memory.
```

What to notice: the whole curriculum under the gate reproduces lesson 07's
numbers to the fourth decimal - because the one patch that fires (the
policy flip after problem 1) turns the actor into lesson 07's actor before
problem 2, and rules (b) and (c) never fire on this curriculum (no
non-hyper value loses every comparison; the verifier already holds every
card the rule would merge). The gate kept the flip on a tie (0.8951 =
0.8951: the evidence recipe *is* the incumbent), which is honest and thin;
lesson 14 shows the same gate rolling a bad rewrite back. One `versions/`
entry after six problems is the right number, and the page does not dress
it up.

Files:

```text
step_09_rsi_meta_harness/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/              the actor, Search policy: static, schema.json forbid: []
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/   + the meta visit
├── .claude/skills/adult-income-meta/         approval: human
├── .claude/skills/adult-income-meta-gate/    approval: gate
├── .agents/skills/...
└── runs/adult-income/versions/gen_001/       (after a run: the snapshot before the first patch)
```

## Governance considerations

- **Who approves what.** Under `approval: human`, the human, per patch, with
  their words in the trace; under `approval: gate`, the private split, per
  patch, with the numbers in the trace and `rollback.py` in the human's
  hand. The rule that picks the change (a / b / c), the size cap, the
  `patches:` list and `META_OFF` are the human's.
- **The hook.** Blocks `patch_pack.py --proposal` without the user's words;
  the locked test.
- **What the script refuses.** A second proposal per visit; a file outside
  `patches:`; more than 20 % of the pack; removing the test rule; a pack
  patching itself; `score_test.py` / `fit_recipe.py` for the meta pack; a
  gate loss (rolled back).
- **What is and is not self-modified.** The actor's policy line, forbid
  list and cards - through a snapshot. The verifier, `eval.md`, the gate and
  the meta pack's own procedure are not (lesson 16 changes that last one).

## How to measure it

| Claim | Test |
|---|---|
| under `approval: human` "no" lands nothing, "yes" lands the patch as `gen_001`, and generation 2 boots the patched checksums | `test_human_no_lands_nothing_yes_lands_and_the_next_generation_boots_it` |
| "edit" lands the user's version | `test_human_edit_lands_the_users_version` |
| the gate keeps a good patch; a patch whose evidence recipe scores lower on the private split is rejected and `versions/` restores the pack byte for byte | `test_gate_keeps_a_good_patch_and_rolls_back_a_bad_one` |
| `META_OFF` leaves the pack byte-identical; one proposal per visit; the 20 % cap; the test rule cannot be removed; the meta pack cannot score or fit | `test_meta_off_one_per_visit_size_cap_and_no_score_test` |
| the offline curriculum under the gate flips the policy line on problem 1 and keeps the curve non-negative | `test_curriculum_under_the_gate_improves_the_policy_line` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 10 - Dream-RSI](../step_10_rsi_dream/README.md). Previous:
[Lesson 08 - the RSI writer](../step_08_meta_generates_rsi/README.md).
