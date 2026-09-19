# Lesson 16 - MetaSkill-Evolve: the improver's skills improve too, slowly

MetaSkill-Evolve (arXiv:2607.05297) runs two timescales on one frozen
model: task skills evolve every task, and the meta-skills that do the
evolving - analyzer, retriever, allocator, proposer, evolver - evolve every
k tasks by the same pipeline, with no extra model and no extra objective.
Here the fast loop is lesson 09's meta pack under the private gate,
rewritten to *read its own five role files* under `roles/` for the numbers
it works with (`Policy flip threshold`, `Cards per visit`); the slow loop is
a second meta pack, `meta-evolver`, whose target is the fast meta pack, whose
`patches:` allow-list is `roles/*.md`, and whose approval is the human. It
boots every k problems, judges the fast loop by the same evidence the fast
loop uses, changes one line of one role file, and the human answers. This
is the "and so on": the pack that patches the pack is itself a pack with a
version history, and its changes are rarer and gated harder.

## Getting started

Lesson 15 left the outer loop. This lesson adds `skills/task-skills-meta/`
(lesson 09's gate-mode meta with `roles/analyzer.md`, `retriever.md`,
`allocator.md`, `proposer.md`, `evolver.md`), `skills/meta-evolver/`, and
the clock in `run.py` (`K = 3`). No new tool: the slow loop is `patch_pack`
pointed at a different target, with a different allow-list and a human.

## How to execute it

1. Six problems, a fast visit after each, a slow visit after problems 3
   and 6:

   ```bash
   cd rsi/step_16_rsi_meta_skills
   FAKE_MODEL=1 python run.py
   FAKE_MODEL=1 HUMAN=script:y,y python run.py     # scripted: yes to both meta-skill changes
   ```

   ```powershell
   cd rsi\step_16_rsi_meta_skills
   $env:FAKE_MODEL = "1"; python run.py
   ```

   The only prompts are the slow loop's: a one-line diff of a role file.
   `n` lands nothing; the task-skill patches go through the gate without
   asking.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/task-skills-meta/roles/allocator.md` and `roles/proposer.md` - the
meta-skills are files with the numbers in them:

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

`skills/task-skills-meta/roles/evolver.md`:

```markdown
# Role: evolver
These five files are the meta-skills. They change on the slow clock only: every k problems the `meta-evolver` pack proposes one change to one of them and a human answers y or n. The fast loop never edits them.
```

`skills/meta-evolver/SKILL.md`:

```markdown
---
name: meta-evolver
description: The slow loop of MetaSkill-Evolve - every k problems, propose one change to one meta-skill file (roles/*.md) of the task-skills-meta pack, by the same evidence pipeline, and land it only with the human's y. Use on the slow clock, never after every problem.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: human
  patches: ["roles/*.md"]
---
```

```markdown
2. Judge the fast loop by the same evidence it uses: the number of active cards the last k problems added, and whether the memory arm's best val beat the control's on them. If the fast loop is adding cards but the gap is not growing, raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster); if the policy line is still `static` after k problems, lower `Policy flip threshold` in `roles/allocator.md` by one. One file, one line.
```

The clock, in the runner:

`run.py`:

```python
    def visit(task, i):
        fast = curriculum.meta_visit(meta, actor, task, model, run_dir, human=human, quiet=quiet)
        slow = None
        if i % k == 0:
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y,y`; the
prompts are elided):

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/7
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       3/1/9
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    2/17      2/2/13
  after problem 1: task skills changed (["SKILL.md"]); meta-skills: not this clock
  after problem 2: task skills unchanged (null); meta-skills: not this clock
  after problem 3: task skills unchanged (null); meta-skills changed ({"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["roles/proposer.md"]})
  after problem 4: task skills unchanged (null); meta-skills: not this clock
  after problem 5: task skills changed (["memory.json"]); meta-skills: not this clock
  after problem 6: task skills unchanged (null); meta-skills changed ({"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_002", "files": ["roles/allocator.md"]})
meta pack versions: ['gen_001', 'gen_002']
  gen_001/roles/allocator.md -> now: --- a/roles/allocator.md | +++ b/roles/allocator.md | @@ -2,2 +2,2 @@ |  Which task skill gets this visit, in order: the policy line, then a forbid, then cards. | -Policy flip threshold: 2 | +Policy flip threshold: 1
  gen_001/roles/proposer.md -> now: --- a/roles/proposer.md | +++ b/roles/proposer.md | @@ -2,2 +2,2 @@ |  One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each. | -Cards per visit: 3 | +Cards per visit: 4
  gen_002/roles/allocator.md -> now: --- a/roles/allocator.md | +++ b/roles/allocator.md | @@ -2,2 +2,2 @@ |  Which task skill gets this visit, in order: the policy line, then a forbid, then cards. | -Policy flip threshold: 2 | +Policy flip threshold: 1
roles/allocator.md: Which task skill gets this visit, in order: the policy line, then a forbid, then cards. / Policy flip threshold: 1
roles/proposer.md: Cards per visit: 4
```

Two clocks in one table. The task skills moved after problems 1 (the
policy line) and 5 (cards) through the gate, and the verifier's cards
moved on every problem the log allowed; the meta-skills moved exactly twice,
after problems 3 and 6, each time one line of one role file, each time
with a `y`, each time leaving a version you can diff. The curve is lesson
09's: the slow loop's two edits changed how the fast loop *would* act, and
the next problems will tell whether that was wise.

Files:

```text
step_16_rsi_meta_skills/
  skills/adult-income/            lesson 09's actor (Search policy: static)
  skills/adult-income-verifier/   lesson 06's verifier
  skills/task-skills-meta/
    SKILL.md                      the fast loop: one task-skill patch per problem under the gate, reading roles/
    tools.md                      lesson 09's meta tools
    roles/analyzer.md             read the log and the cards
    roles/retriever.md            read the actor pack: which files are task skills
    roles/allocator.md            the order of changes; Policy flip threshold: 2
    roles/proposer.md             one patch per visit; Cards per visit: 3
    roles/evolver.md              the slow clock and the human, stated
  skills/meta-evolver/
    SKILL.md                      the slow loop: one line of one role file, every k problems, with the human
    tools.md                      Allowed: read_traces, read_memory, read_pack, patch_pack
  run.py                          the two clocks (K = 3); the versions and the diffs of the meta pack
  test_step.py                    the claims below
  README.md                       this lesson
  runs/curriculum/meta/           (created by run.py) the slow loop's log and versions/
```

## Governance considerations

- Who approves what: the private gate approves task-skill patches (fast
  clock); the human approves meta-skill patches (slow clock). The clock
  itself (`K`), the role boundaries and the allow-lists are the human's.
- Off switches: `n` at the slow prompt; `META_OFF` on the fast loop;
  two separate version histories.
- What the model may not do, and which tool enforces it: the fast loop may
  not touch `roles/` (its `patches:` is unset for those, and the test
  checks the meta pack's checksums only change after slow visits); the
  slow loop may not touch anything but `roles/*.md` (`patches:`, enforced
  by `patch_pack`), may not fit (`tools.md`), and lands nothing without a
  `y` (`approval: human`).
- What is and is not self-modified: the actor's task skills (fast) and the
  meta pack's role files (slow). Not: the evolver pack itself, the clock,
  the verifier, the gate. Rung: L5 - the procedure that improves the
  improver is revised - with the human on the slow clock as the acceptance
  rule, which is what the framework paper's industry loops do.

## How to measure it

| Claim | Test |
|---|---|
| the fast loop visits every problem and task skills move between problems; the meta pack changes only after a slow visit (every k), one role file at a time | `test_task_skills_change_every_problem_and_meta_skills_only_every_k` |
| a meta-skill change never lands without the human `y`; the slow loop cannot touch `SKILL.md` or fit | `test_a_meta_skill_change_never_lands_without_the_human_y` |
| the meta pack's version history is a file you can diff (`versions/gen_001/roles/...`, a one-line diff) | `test_the_meta_packs_version_history_is_a_file_you_can_diff` |

Scorecard fields reported: all fourteen per problem and arm, plus per
problem the fast visit's patch and, on the slow clock, the meta-skill
patch. Run `python run_tests.py rsi` from the repo root.

## Next lesson

Next: [17 - the map](../step_17_map/README.md): the ladder, every method's
curve side by side, and who approved what. Previous:
[15 - AIDE²](../step_15_rsi_aide2/README.md).
